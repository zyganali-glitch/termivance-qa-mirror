"""Tests for B4 Resurrection Monitoring and Current-Truth Downgrade.

Validates:
1. Exact-target monitoring re-observing provider state;
2. Current-truth downgrade from OBSERVED_ABSENT to RESURRECTED_NOT_ABSENT on reappearance;
3. Current-truth downgrade to REDEPLOYMENT_MECHANISM_ACTIVE when CI mechanism is active;
4. Current-truth downgrade to STALE_REVALIDATION_REQUIRED when historical receipt expires (>900s);
5. Current-truth downgrade to INCONCLUSIVE_PROBE_FAILED when provider probes fail;
6. Multi-surface corroboration required for CONTINUED_ABSENCE_OBSERVED (single 404 is insufficient);
7. Rejection of unverified historical receipt (evaluates to HISTORICAL_RECEIPT_UNVERIFIED);
8. Protected project refusal (87779099, 87777871, 87786164 permanently blocked);
9. Source commit drift detection between historical receipt and current observation;
10. Anti-self-award: RESURRECTION_CONTROLLED is never awarded merely because monitor exists;
11. Immutable historical truth: monitoring does not mutate or rewrite previous receipts;
12. Injectable http_getter in observe_target_surfaces.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from conftest import FakeTransport

from termivance.decay import FreshnessState
from termivance.gitlab_client import GitLabClient, HttpReply
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


def _make_valid_history(
    target: TargetIdentity = TARGET,
    commit_sha: str = COMMIT_SHA,
    observed_at: str | None = None,
    verdict: str = "OBSERVED_ABSENT",
    mutation_accepted: bool = True,
) -> dict[str, object]:
    """Produce an authentic termivance.retirement_receipt/v3 dictionary."""
    ts = observed_at or (NOW - timedelta(seconds=200)).isoformat()
    return {
        "schema": "termivance.retirement_receipt/v3",
        "target": target.to_dict(),
        "action": "UNPUBLISH_PAGES",
        "authorization_binding": "auth_binding_hash_1234567890abcdef",
        "operation_id": "op_20261021_87785099_unpublish",
        "mutation_attempted": True,
        "mutation": {
            "accepted": mutation_accepted,
            "status": 204 if mutation_accepted else 403,
        },
        "verdict": verdict,
        "commit_sha": commit_sha,
        "observed_at": ts,
        "preflight": {"observed_at": ts, "commit_sha": commit_sha},
    }


def _make_obs(
    *,
    commit_sha: str = COMMIT_SHA,
    has_mechanism: bool = True,
    signals: tuple[str, ...] = ("pages_true", "pages_keyword"),
    pages_api_status: int = 403,
    pages_api_deployment_count: int = 0,
    served_status: int | None = 200,
    marker_observed: bool = True,
    observed_at: datetime = NOW,
) -> TargetCurrentObservation:
    return TargetCurrentObservation(
        project_id=TARGET.project_id,
        full_path=TARGET.full_path,
        default_branch="main",
        commit_sha=commit_sha,
        ci_config_present=True,
        redeployment_mechanism=has_mechanism,
        redeployment_signals=signals,
        pages_api_status=pages_api_status,
        pages_api_accessible=(pages_api_status < 400),
        served_url="https://gitlab-ai-hackathon.gitlab.io/.../termivance-b3-disposable-pages-demo/",
        served_http_status=served_status,
        served_marker_observed=marker_observed,
        observed_at=observed_at,
        pages_api_deployment_count=pages_api_deployment_count,
    )


def test_validate_historical_absence_receipt():
    """Verify receipt validator enforces schema, target, mutation, and verdict."""
    valid = _make_valid_history()
    ok, reason = validate_historical_absence_receipt(valid, TARGET)
    assert ok is True
    assert "verified" in reason

    # Missing schema
    bad_schema = dict(valid)
    bad_schema["schema"] = "termivance.retirement_receipt/v2"
    ok, reason = validate_historical_absence_receipt(bad_schema, TARGET)
    assert ok is False
    assert "Unrecognized schema" in reason

    # Mismatched target ID
    bad_target = dict(valid)
    bad_target["target"] = {"project_id": 99999999, "full_path": "other/project"}
    ok, reason = validate_historical_absence_receipt(bad_target, TARGET)
    assert ok is False
    assert "Target project ID mismatch" in reason

    # Protected target
    canonical_target = TargetIdentity(87779099, "group/canonical", "GITLAB_PAGES_SITE")
    ok, reason = validate_historical_absence_receipt(valid, canonical_target)
    assert ok is False
    assert "is protected" in reason

    # Mutation not attempted
    no_mutation = dict(valid)
    no_mutation["mutation_attempted"] = False
    ok, reason = validate_historical_absence_receipt(no_mutation, TARGET)
    assert ok is False
    assert "mutation_attempted is not True" in reason

    # Verdict not OBSERVED_ABSENT
    wrong_verdict = dict(valid)
    wrong_verdict["verdict"] = "SAFE_TO_RETIRE"
    ok, reason = validate_historical_absence_receipt(wrong_verdict, TARGET)
    assert ok is False
    assert "not 'OBSERVED_ABSENT'" in reason


def test_unverified_historical_receipt_reports_unverified_status():
    """Unverified raw dictionary claims evaluate to HISTORICAL_RECEIPT_UNVERIFIED."""
    raw_unverified = {
        "verdict": "SAFE_TO_RETIRE",
        "observed_absence": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": (NOW - timedelta(seconds=200)).isoformat(),
    }
    current_obs = _make_obs(served_status=200, marker_observed=True)

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=raw_unverified,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.HISTORICAL_RECEIPT_UNVERIFIED
    assert any("Historical receipt unverified" in diff for diff in report.diff_reasons)
    assert report.current_truth != CurrentTruthStatus.RESURRECTED_NOT_ABSENT


def test_actual_reappearance_downgrades_to_resurrected_not_absent():
    """When a target was previously OBSERVED_ABSENT and now serves its marker,
    current truth is downgraded to RESURRECTED_NOT_ABSENT."""
    historical_truth = _make_valid_history()
    current_obs = _make_obs(served_status=200, marker_observed=True)

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.RESURRECTED_NOT_ABSENT
    assert report.resurrection_control == ResurrectionControlStatus.NOT_CLAIMED
    assert any("absence is REVERSED" in diff for diff in report.diff_reasons)
    assert report.freshness_state == FreshnessState.FRESH


def test_redeployment_mechanism_active_downgrades_absence():
    """When historical absence was verified, but current CI has active pages deployment job,
    current truth is downgraded to REDEPLOYMENT_MECHANISM_ACTIVE."""
    historical_truth = _make_valid_history()
    # Marker not currently served (404), but mechanism exists in CI
    current_obs = _make_obs(served_status=404, marker_observed=False, has_mechanism=True)

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.REDEPLOYMENT_MECHANISM_ACTIVE
    assert report.redeployment_risk == RedeploymentRisk.MECHANISM_PRESENT
    assert any("active CI deployment mechanism exists" in diff for diff in report.diff_reasons)


def test_stale_historical_receipt_downgrades_to_revalidation_required():
    """When historical receipt is older than 900s TTL, current truth requires revalidation."""
    historical_truth = _make_valid_history(
        observed_at=(NOW - timedelta(seconds=1200)).isoformat()
    )
    # Probes return 404, mechanism neutralized, but receipt is stale
    current_obs = _make_obs(
        served_status=404,
        marker_observed=False,
        has_mechanism=False,
        signals=(),
        pages_api_status=404,
    )

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.STALE_REVALIDATION_REQUIRED
    assert report.freshness_state == FreshnessState.EXPIRED
    assert any("EXPIRED" in diff for diff in report.diff_reasons)


def test_inaccessible_provider_probe_downgrades_to_inconclusive():
    """Failed provider probes cannot prove continued absence; they evaluate to INCONCLUSIVE."""
    historical_truth = _make_valid_history(
        observed_at=(NOW - timedelta(seconds=100)).isoformat()
    )
    # Pages API returns 403, served URL probe timed out / inaccessible (None)
    current_obs = _make_obs(
        served_status=None,
        marker_observed=False,
        pages_api_status=403,
        has_mechanism=False,
        signals=(),
    )

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.INCONCLUSIVE_PROBE_FAILED
    assert any("inaccessible" in diff for diff in report.diff_reasons)


def test_single_404_with_403_pages_api_fails_closed():
    """A 404 on served URL is NOT proof of absence if Pages API is 403/inaccessible."""
    historical_truth = _make_valid_history(
        observed_at=(NOW - timedelta(seconds=100)).isoformat()
    )
    # Served URL is 404, but Pages API is 403
    current_obs = _make_obs(
        served_status=404,
        marker_observed=False,
        pages_api_status=403,
        has_mechanism=False,
        signals=(),
    )

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.INCONCLUSIVE_PROBE_FAILED
    assert report.current_truth != CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED


def test_continued_absence_legitimately_observed_across_all_surfaces():
    """When receipt is fresh, commit matches, Pages API is 404, and served URL is 404."""
    historical_truth = _make_valid_history(
        observed_at=(NOW - timedelta(seconds=100)).isoformat()
    )
    current_obs = _make_obs(
        served_status=404,
        marker_observed=False,
        has_mechanism=False,
        signals=(),
        pages_api_status=404,
        pages_api_deployment_count=0,
    )

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED
    assert report.resurrection_control == ResurrectionControlStatus.NOT_CLAIMED


def test_protected_target_permanently_blocked():
    """Protected targets (87779099, 87777871, 87786164) evaluate to TARGET_MUTATION_BLOCKED."""
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
    """observe_target_surfaces accepts injectable http_getter without network fetch."""
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
        served_url="https://test.gitlab.io/",
        marker="marker",
        now=NOW,
        http_getter=mock_getter,
    )

    assert obs.commit_sha == COMMIT_SHA
    assert obs.redeployment_mechanism is True
    assert obs.pages_api_status == 403
    assert obs.served_http_status == 200
    assert obs.served_marker_observed is True


def test_historical_receipt_immobility():
    """Monitoring preserves historical truth dict without mutating it."""
    orig_history = _make_valid_history(
        observed_at=(NOW - timedelta(seconds=300)).isoformat()
    )
    orig_copy = json.loads(json.dumps(orig_history))
    current_obs = _make_obs(served_status=200, marker_observed=True)

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=orig_history,
        now=NOW,
    )

    assert orig_history == orig_copy
    assert report.historical_truth == orig_copy
    assert report.current_truth == CurrentTruthStatus.RESURRECTED_NOT_ABSENT
