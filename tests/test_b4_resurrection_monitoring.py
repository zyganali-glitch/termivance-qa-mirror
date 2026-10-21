"""Tests for B4 Resurrection Monitoring and Current-Truth Downgrade.

Validates:
1. Historical receipt authority: a schema-correct dictionary with plausible
   fields (mutation_attempted, accepted, OBSERVED_ABSENT, parseable
   timestamp) is NOT proof — the full authoritative receipt chain (durable
   ledger CONSUMED_ACCEPTED, exact endpoint, authorization record, pre-state
   publication, post-action read-backs, temporal coherence) must validate;
2. Current-observation binding: the observation must be for the same exact
   target (project ID and full path) and the same served URL as the
   historical receipt;
3. Current-truth downgrade semantics after a genuinely verified absence
   (reappearance, redeployment mechanism, staleness, probe failure,
   multi-surface corroboration);
4. Protected project refusal (87779099, 87777871, 87786164);
5. Anti-self-award of RESURRECTION_CONTROLLED;
6. Historical receipt immobility;
7. Injectable http_getter in observe_target_surfaces.

All tests are network-free and exercise the production code paths through
injected transports and real ledger primitives.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from conftest import FakeTransport

from termivance.authorization import Authorization
from termivance.decay import FreshnessState
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.ledger import AuthorizationLedger
from termivance.resurrection_monitor import (
    CurrentTruthStatus,
    RedeploymentRisk,
    ResurrectionControlStatus,
    TargetCurrentObservation,
    monitor_resurrection,
    observe_target_surfaces,
    validate_historical_absence_receipt,
)
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 21, 12, 0, 0, tzinfo=UTC)
TARGET = TargetIdentity(
    87785099,
    "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
    "GITLAB_PAGES_SITE",
)
COMMIT_SHA = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
SERVED_URL = "https://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/"


def _forged_history(**overrides) -> dict[str, object]:
    """A deliberately forged, schema-correct receipt with plausible fields.

    This is exactly the shape the auditor rejected: it must NEVER validate.
    """
    ts = (NOW - timedelta(seconds=200)).isoformat()
    receipt: dict[str, object] = {
        "schema": "termivance.retirement_receipt/v3",
        "target": TARGET.to_dict(),
        "action": "UNPUBLISH_PAGES",
        "authorization_binding": "auth_binding_hash_1234567890abcdef",
        "operation_id": "op_20261021_87785099_unpublish",
        "mutation_attempted": True,
        "mutation": {
            "accepted": True,
            "status": 204,
        },
        "verdict": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": ts,
        "preflight": {"observed_at": ts, "commit_sha": COMMIT_SHA},
    }
    receipt.update(overrides)
    return receipt


def _genuine_receipt(tmp_path, *, verdict="OBSERVED_ABSENT"):
    """Build a genuine bounded historical receipt through the real contracts.

    Uses the production Authorization/AuthorizationLedger primitives to
    consume and finalize an operation, then constructs the v3 receipt with
    the full chain: pre-state publication, accepted DELETE on the exact
    endpoint, and post-action read-backs of the same URL.
    """
    from termivance.authorization import OperatorApproval

    ledger_file = tmp_path / f"durable_ledger_{verdict}.json"
    ledger = AuthorizationLedger(ledger_file)
    ledger.health_check()

    auth = Authorization.issue(TARGET, "unpublish_pages", nonce="nonce-rm-1", now=NOW)
    auth.approval = OperatorApproval(
        operator="op",
        statement=(
            f"I authorize exactly one unpublish_pages using /projects/{TARGET.project_id}/pages"
        ),
        approved_at=NOW,
        channel="web_ui",
        binding=auth.binding(),
    )
    consumption = ledger.consume(auth, operation_id="op-rm-1", now=NOW)
    ledger.finalize(consumption.binding, outcome="ACCEPTED")

    eligibility_at = NOW - timedelta(seconds=100)
    requested_at = NOW - timedelta(seconds=50)
    absence_at = NOW - timedelta(seconds=40)

    receipt = {
        "schema": "termivance.retirement_receipt/v3",
        "target": TARGET.to_dict(),
        "action": "unpublish_pages",
        "authorization_binding": auth.binding(),
        "authorization_record": {
            "binding": auth.binding(),
            "nonce": "nonce-rm-1",
            "action": "unpublish_pages",
            "target_key": TARGET.key_string(),
        },
        "operation_id": "op-rm-1",
        "mutation_attempted": True,
        "verdict": verdict,
        "eligibility": {
            "established_at": eligibility_at.isoformat(),
            "pre_state": {
                "served_url": SERVED_URL,
                "marker": "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a",
                "marker_observed": True,
                "marker_sha256": "a" * 64,
                "deployment_present": True,
                "observed_at": eligibility_at.isoformat(),
                "genuinely_published": True,
            },
        },
        "mutation": {
            "accepted": True,
            "status": 204,
            "method": "DELETE",
            "endpoint": f"/projects/{TARGET.project_id}/pages",
            "requested_at": requested_at.isoformat(),
        },
        "absence": {
            "verdict": "OBSERVED_ABSENT",
            "pages_api": {"status": 404, "error": None},
            "served_url": {"http_status": 404, "error": None},
            "observation": {
                "served_url": SERVED_URL,
                "marker": "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a",
                "marker_observed": False,
                "deployment_present": False,
                "observed_at": absence_at.isoformat(),
            },
            "notes": ["post-action read-backs of the same exact URL"],
        },
        "observed_at": absence_at.isoformat(),
        "preflight": {"observed_at": absence_at.isoformat(), "commit_sha": COMMIT_SHA},
        "commit_sha": COMMIT_SHA,
    }
    return receipt, ledger_file


def _make_obs(
    *,
    commit_sha: str = COMMIT_SHA,
    full_path: str | None = None,
    project_id: int = TARGET.project_id,
    has_mechanism: bool = True,
    signals: tuple[str, ...] = ("pages_true", "pages_keyword"),
    pages_api_status: int = 403,
    pages_api_deployment_count: int = 0,
    served_status: int | None = 200,
    served_url: str | None = SERVED_URL,
    marker_observed: bool = True,
    observed_at: datetime = NOW,
) -> TargetCurrentObservation:
    return TargetCurrentObservation(
        project_id=project_id,
        full_path=full_path or TARGET.full_path,
        default_branch="main",
        commit_sha=commit_sha,
        ci_config_present=True,
        redeployment_mechanism=has_mechanism,
        redeployment_signals=signals,
        pages_api_status=pages_api_status,
        pages_api_accessible=(pages_api_status < 400),
        served_url=served_url,
        served_http_status=served_status,
        served_marker_observed=marker_observed,
        observed_at=observed_at,
        pages_api_deployment_count=pages_api_deployment_count,
    )


# ---------------------------------------------------------------------------
# Historical receipt authority: forged receipts never validate.
# ---------------------------------------------------------------------------


def test_forged_schema_correct_receipt_is_not_proof(tmp_path):
    """The auditor's exact adversarial shape: plausible schema + accepted
    mutation + OBSERVED_ABSENT + parseable timestamp must NOT validate."""
    ok, reason = validate_historical_absence_receipt(
        _forged_history(), TARGET, ledger=None
    )
    assert ok is False
    assert "durable authorization ledger" in reason


def test_forged_receipt_fails_even_with_empty_durable_ledger(tmp_path):
    ledger_file = tmp_path / "empty_ledger.json"
    ledger = AuthorizationLedger(ledger_file)
    ledger.health_check()
    ok, reason = validate_historical_absence_receipt(
        _forged_history(), TARGET, ledger=ledger
    )
    assert ok is False
    assert "authoritative receipt chain" in reason


def test_tampered_genuine_receipt_fails_validation(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    ledger = AuthorizationLedger(ledger_file)
    ok, _reason = validate_historical_absence_receipt(receipt, TARGET, ledger=ledger)
    assert ok is True

    tampered = json.loads(json.dumps(receipt))
    tampered["mutation"]["status"] = 500  # tamper: mutation no longer accepted
    ok, reason = validate_historical_absence_receipt(
        tampered, TARGET, ledger=AuthorizationLedger(ledger_file)
    )
    assert ok is False


def test_absent_mutation_ledger_fails_validation(tmp_path):
    """A genuine receipt shape whose operation was never sealed in a ledger."""
    receipt, _ledger_file = _genuine_receipt(tmp_path)
    empty_ledger = tmp_path / "other_ledger.json"
    AuthorizationLedger(empty_ledger).health_check()
    ok, reason = validate_historical_absence_receipt(
        receipt, TARGET, ledger=AuthorizationLedger(empty_ledger)
    )
    assert ok is False
    assert "no durable ledger record exists" in reason.lower()


def test_wrong_full_path_receipt_fails_validation(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    wrong_path_target = TargetIdentity(
        TARGET.project_id, "evil-namespace/termivance-pages-disposable", "GITLAB_PAGES_SITE"
    )
    ok, reason = validate_historical_absence_receipt(
        receipt, wrong_path_target, ledger=AuthorizationLedger(ledger_file)
    )
    assert ok is False
    assert "full path mismatch" in reason


def test_missing_post_action_readbacks_fail_validation(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    del receipt["absence"]
    ok, reason = validate_historical_absence_receipt(
        receipt, TARGET, ledger=AuthorizationLedger(ledger_file)
    )
    assert ok is False
    assert "post-action absence read-back" in reason


def test_access_denied_post_action_readback_fails_validation(tmp_path):
    """A 403 Pages API read-back is an access boundary, not absence."""
    receipt, ledger_file = _genuine_receipt(tmp_path)
    receipt["absence"]["pages_api"]["status"] = 403
    ok, reason = validate_historical_absence_receipt(
        receipt, TARGET, ledger=AuthorizationLedger(ledger_file)
    )
    assert ok is False
    assert "access boundary is not absence" in reason


def test_clock_inversion_fails_validation(tmp_path):
    """Absence observed before the mutation request violates temporal coherence."""
    receipt, ledger_file = _genuine_receipt(tmp_path)
    receipt["absence"]["observation"]["observed_at"] = (
        NOW - timedelta(seconds=120)
    ).isoformat()  # predates requested_at (NOW - 50s)
    ok, reason = validate_historical_absence_receipt(
        receipt, TARGET, ledger=AuthorizationLedger(ledger_file)
    )
    assert ok is False
    assert "Clock inversion" in reason


def test_wrong_url_post_action_readback_fails_validation(tmp_path):
    """Post-action absence must read back the SAME URL as the pre-state."""
    receipt, ledger_file = _genuine_receipt(tmp_path)
    receipt["absence"]["observation"]["served_url"] = (
        "https://unrelated-site.gitlab.io/other/"
    )
    ok, reason = validate_historical_absence_receipt(
        receipt, TARGET, ledger=AuthorizationLedger(ledger_file)
    )
    assert ok is False
    assert "different URL" in reason


def test_genuine_bounded_historical_receipt_validates(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    ok, reason = validate_historical_absence_receipt(
        receipt, TARGET, ledger=AuthorizationLedger(ledger_file)
    )
    assert ok is True
    assert "verified against the durable ledger chain" in reason


def test_non_absence_verdict_receipt_fails(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path, verdict="BLOCKED")
    ok, reason = validate_historical_absence_receipt(
        receipt, TARGET, ledger=AuthorizationLedger(ledger_file)
    )
    assert ok is False
    assert "not 'OBSERVED_ABSENT'" in reason


def test_protected_target_receipt_fails(tmp_path):
    receipt, _ledger_file = _genuine_receipt(tmp_path)
    canonical_target = TargetIdentity(87779099, "group/canonical", "GITLAB_PAGES_SITE")
    ok, reason = validate_historical_absence_receipt(receipt, canonical_target)
    assert ok is False
    assert "is protected" in reason


# ---------------------------------------------------------------------------
# Current-observation binding.
# ---------------------------------------------------------------------------


def test_wrong_current_observation_target_is_mismatch(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(
            project_id=99999999, full_path="other/project"
        ),
        historical_truth=receipt,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH
    assert "expected 87785099" in report.diff_reasons[0]


def test_wrong_current_observation_full_path_is_mismatch(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(full_path="evil-namespace/impostor"),
        historical_truth=receipt,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH


def test_unrelated_site_current_observation_is_mismatch(tmp_path):
    """An unrelated site URL is not the receipt's observed URL."""
    receipt, ledger_file = _genuine_receipt(tmp_path)
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(
            served_url="https://unrelated-site.gitlab.io/other/"
        ),
        historical_truth=receipt,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH


# ---------------------------------------------------------------------------
# Downgrade semantics after genuinely verified absence.
# ---------------------------------------------------------------------------


def test_actual_reappearance_downgrades_to_resurrected_not_absent(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(served_status=200, marker_observed=True),
        historical_truth=receipt,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.RESURRECTED_NOT_ABSENT
    assert report.resurrection_control == ResurrectionControlStatus.NOT_CLAIMED
    assert any("absence is REVERSED" in diff for diff in report.diff_reasons)
    assert report.freshness_state in (FreshnessState.FRESH, FreshnessState.EXPIRING)


def test_redeployment_mechanism_active_downgrades_absence(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(
            served_status=404, marker_observed=False, has_mechanism=True
        ),
        historical_truth=receipt,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.REDEPLOYMENT_MECHANISM_ACTIVE
    assert report.redeployment_risk == RedeploymentRisk.MECHANISM_PRESENT
    assert any("active CI deployment mechanism exists" in diff for diff in report.diff_reasons)


def test_stale_historical_receipt_requires_revalidation(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    stale = json.loads(json.dumps(receipt))
    # Shift the whole coherent chain 1200s into the past: eligibility was
    # established first, then the mutation requested, then absence observed.
    stale["eligibility"]["established_at"] = (NOW - timedelta(seconds=1300)).isoformat()
    stale["mutation"]["requested_at"] = (NOW - timedelta(seconds=1250)).isoformat()
    stale_at = (NOW - timedelta(seconds=1200)).isoformat()
    stale["absence"]["observation"]["observed_at"] = stale_at
    stale["observed_at"] = stale_at
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(
            served_status=404,
            marker_observed=False,
            has_mechanism=False,
            signals=(),
            pages_api_status=404,
        ),
        historical_truth=stale,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.STALE_REVALIDATION_REQUIRED
    assert report.freshness_state == FreshnessState.EXPIRED
    assert any("EXPIRED" in diff for diff in report.diff_reasons)


def test_inaccessible_provider_probe_downgrades_to_inconclusive(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(
            served_status=None,
            marker_observed=False,
            pages_api_status=403,
            has_mechanism=False,
            signals=(),
        ),
        historical_truth=receipt,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.INCONCLUSIVE_PROBE_FAILED
    assert any("inaccessible" in diff for diff in report.diff_reasons)


def test_single_404_with_403_pages_api_fails_closed(tmp_path):
    """A 404 on served URL is NOT proof of absence if Pages API is 403."""
    receipt, ledger_file = _genuine_receipt(tmp_path)
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(
            served_status=404,
            marker_observed=False,
            pages_api_status=403,
            has_mechanism=False,
            signals=(),
        ),
        historical_truth=receipt,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.INCONCLUSIVE_PROBE_FAILED
    assert report.current_truth != CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED


def test_continued_absence_legitimately_observed_across_all_surfaces(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(
            served_status=404,
            marker_observed=False,
            has_mechanism=False,
            signals=(),
            pages_api_status=404,
            pages_api_deployment_count=0,
        ),
        historical_truth=receipt,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED
    assert report.resurrection_control == ResurrectionControlStatus.NOT_CLAIMED


def test_served_200_without_verified_receipt_shows_presence_not_resurrection():
    """A current served 200 with marker demonstrates presence, but
    resurrection requires a genuinely validated previous absence."""
    current_obs = _make_obs(served_status=200, marker_observed=True)
    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=_forged_history(),
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.HISTORICAL_RECEIPT_UNVERIFIED
    assert report.current_truth != CurrentTruthStatus.RESURRECTED_NOT_ABSENT
    assert any("published and serving its marker" in d for d in report.diff_reasons)


def test_unverified_historical_receipt_reports_unverified_status():
    raw_unverified = {
        "verdict": "SAFE_TO_RETIRE",
        "observed_absence": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": (NOW - timedelta(seconds=200)).isoformat(),
    }
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(served_status=200, marker_observed=True),
        historical_truth=raw_unverified,
        now=NOW,
    )
    assert report.current_truth == CurrentTruthStatus.HISTORICAL_RECEIPT_UNVERIFIED
    assert any("Historical receipt unverified" in diff for diff in report.diff_reasons)


def test_baseline_without_history_shows_mutation_blocked():
    report = monitor_resurrection(
        TARGET, current_observation=_make_obs(served_status=200, marker_observed=True), now=NOW
    )
    assert report.current_truth == CurrentTruthStatus.TARGET_MUTATION_BLOCKED
    assert report.resurrection_control == ResurrectionControlStatus.NOT_CLAIMED


def test_protected_target_permanently_blocked():
    for pid in (87779099, 87777871, 87786164):
        tgt = TargetIdentity(pid, f"group/project-{pid}", "GITLAB_PAGES_SITE")
        obs = TargetCurrentObservation(
            project_id=pid,
            full_path=f"group/project-{pid}",
            default_branch="main",
            commit_sha=COMMIT_SHA,
            ci_config_present=True,
            redeployment_mechanism=False,
            redeployment_signals=(),
            pages_api_status=200,
            pages_api_accessible=True,
            served_url="https://example.gitlab.io/",
            served_http_status=404,
            served_marker_observed=False,
            observed_at=NOW,
        )
        report = monitor_resurrection(tgt, current_observation=obs, now=NOW)
        assert report.current_truth == CurrentTruthStatus.TARGET_MUTATION_BLOCKED
        assert any("protected" in diff for diff in report.diff_reasons)


def test_observe_target_surfaces_injectable_http_getter():
    replies = {
        ("GET", f"/projects/{TARGET.project_id}/repository/branches/main"): HttpReply(
            200, json.dumps({"commit": {"id": COMMIT_SHA}})
        ),
        (
            "GET",
            f"/projects/{TARGET.project_id}/repository/files/.gitlab-ci.yml/raw?ref={COMMIT_SHA}",
        ): HttpReply(200, "pages:\n  pages: true\n"),
        ("GET", f"/projects/{TARGET.project_id}/pages"): HttpReply(
            403, json.dumps({"error": "Forbidden"})
        ),
    }
    client = GitLabClient("dummy_token", transport=FakeTransport(replies))

    def mock_getter(url: str, timeout: float = 10.0) -> tuple[int | None, str | None, str]:
        return 200, None, "Distinctive marker present"

    obs = observe_target_surfaces(
        client,
        TARGET,
        served_url="https://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/",
        marker="marker",
        now=NOW,
        http_getter=mock_getter,
    )
    assert obs.commit_sha == COMMIT_SHA
    assert obs.redeployment_mechanism is True
    assert obs.pages_api_status == 403
    assert obs.served_http_status == 200
    assert obs.served_marker_observed is True


def test_historical_receipt_immobility(tmp_path):
    receipt, ledger_file = _genuine_receipt(tmp_path)
    orig_copy = json.loads(json.dumps(receipt))
    report = monitor_resurrection(
        TARGET,
        current_observation=_make_obs(served_status=200, marker_observed=True),
        historical_truth=receipt,
        ledger=AuthorizationLedger(ledger_file),
        now=NOW,
    )
    assert receipt == orig_copy
    assert report.historical_truth == orig_copy
    assert report.current_truth == CurrentTruthStatus.RESURRECTED_NOT_ABSENT
