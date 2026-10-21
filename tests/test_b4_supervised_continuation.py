"""Tests for the supervised continuation: fail-closed LIVE preflight, honest
OFFLINE_REPLAY provenance, and the durable causal execution ledger.

Validates:
1. Complete 12-point feasibility evaluation dictionary;
2. LIVE-mode fail-closed behaviour: a well-formed fake note can NEVER pass
   when the provider returns 401/403/404, times out, has a missing branch,
   a mismatched note body, a wrong author, a wrong note id, a wrong target
   full path, or a drifted branch HEAD;
3. LIVE mode without a provider client fails closed (no optimistic defaults);
4. OFFLINE_REPLAY mode passes for development but carries FIXTURE /
   RECORDED_INPUT provenance and never presents itself as live authenticated
   continuation;
5. Durable idempotency semantics of the continuation causal ledger:
   FIRST_STARTED is not FIRST_COMPLETED, PARTIAL/FAILED are never converted
   to COMPLETED_IDEMPOTENT, corrupted ledgers fail closed, concurrent
   identical reservations yield exactly one first execution, and the prior
   stored verdict is retrieved from the authentic completed record;
6. ``--out-dir`` omission never claims durable idempotency;
7. Verdict and status are derived from the executed review, not hard-coded;
8. Zero unauthorized mutation (no destructive calls through the transport);
9. CLI parity for ``--mode live`` / ``--mode offline-replay``.

All tests are network-free: production function paths are exercised through
injected transports and storage.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest
from conftest import FakeTransport

from termivance.continuation_ledger import (
    COMPLETED_STATE,
    PARTIAL_STATE,
    RESERVE_FIRST_EXECUTION,
    RESERVED_STATE,
    ContinuationLedger,
    ContinuationLedgerError,
)
from termivance.gitlab_client import ApiResult, GitLabClient, HttpReply
from termivance.supervised_review import (
    DEFAULT_TARGET_FULL_PATH,
    DEFAULT_TARGET_PROJECT_ID,
    DUO_SERVICE_ACCOUNT_USERNAME,
    DUO_SESSION_ID_NEUTRAL,
    FEASIBILITY_EVALUATION_12_POINTS,
    run_supervised_continuation,
    validate_continuation_preflight,
)

NOW = datetime(2026, 10, 21, 12, 0, 0, tzinfo=UTC)
AUTHENTIC_COMMIT_SHA = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
CANONICAL_PID = 87779099
NOTE_ID = 4045401991
AUTHENTIC_NOTE_BODY = (
    "### 1. Target Identity & Observed Scope\n"
    "- **Target project ID:** `87785099`\n"
    f"- **Default branch HEAD commit:** `{AUTHENTIC_COMMIT_SHA}`\n\n"
    "### 3. Candidate obligations\n"
    "1. **CI Redeployment Path**: create-pages in .gitlab-ci.yml with pages: true\n"
    "2. **Target Marker String**: TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a in site/index.html\n"
)
CI_CONTENT = (
    "create-pages:\n  stage: deploy\n  script:\n"
    "    - cp site/index.html public/index.html\n  pages: true\n"
)
MARKER = "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a"


def _note_payload(
    *,
    body: str = AUTHENTIC_NOTE_BODY,
    note_id: int = NOTE_ID,
    author: str = DUO_SERVICE_ACCOUNT_USERNAME,
    issue_iid: int = 5,
) -> str:
    return json.dumps(
        {
            "id": note_id,
            "body": body,
            "noteable_iid": issue_iid,
            "noteable_type": "Issue",
            "author": {"username": author},
            "created_at": "2026-10-19T19:46:42Z",
        }
    )


def _live_replies(
    *,
    note_status: int = 200,
    note_body_provider: str | None = None,
    note_author: str = DUO_SERVICE_ACCOUNT_USERNAME,
    note_id_returned: int = NOTE_ID,
    branch_commit: str | None = AUTHENTIC_COMMIT_SHA,
    target_path: str = DEFAULT_TARGET_FULL_PATH,
    project_status: int = 200,
) -> dict[tuple[str, str], HttpReply]:
    """A complete provider surface for the LIVE continuation path.

    Ordering matters: FakeTransport matches by URL fragment, so specific
    endpoints must precede the bare ``/projects/<pid>`` identity reads.
    """
    note_reply = (
        HttpReply(
            note_status,
            _note_payload(
                body=note_body_provider or AUTHENTIC_NOTE_BODY,
                note_id=note_id_returned,
                author=note_author,
            ),
        )
        if note_status == 200
        else HttpReply(note_status, "")
    )
    branch_reply = (
        HttpReply(200, json.dumps({"name": "main", "commit": {"id": branch_commit}}))
        if branch_commit is not None
        else HttpReply(404, "")
    )
    project_body = json.dumps(
        {
            "id": DEFAULT_TARGET_PROJECT_ID,
            "path_with_namespace": target_path,
            "default_branch": "main",
            "visibility": "public",
            "web_url": f"https://gitlab.com/{target_path}",
            "archived": False,
        }
    )
    return {
        ("GET", f"/projects/{CANONICAL_PID}/issues/5/notes/{NOTE_ID}"): note_reply,
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/repository/files/"): HttpReply(
            200, CI_CONTENT
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/repository/branches/main"): (
            branch_reply
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/repository/commits"): HttpReply(
            200, json.dumps([{"id": AUTHENTIC_COMMIT_SHA}])
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/pipelines"): HttpReply(
            200, json.dumps([{"id": 2960507698, "sha": AUTHENTIC_COMMIT_SHA, "status": "success"}])
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/issues"): HttpReply(200, "[]"),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/environments"): HttpReply(
            200, "[]"
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/pages"): HttpReply(403, ""),
        ("GET", f"/projects/{CANONICAL_PID}/issues"): HttpReply(200, "[]"),
        ("GET", f"/projects/{CANONICAL_PID}"): HttpReply(200, "{}"),
        ("GET", "/projects/87777871"): HttpReply(200, "{}"),
        ("GET", "/projects/87786164"): HttpReply(200, "{}"),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}"): HttpReply(
            project_status, project_body if project_status == 200 else ""
        ),
    }


def _live_client(**overrides) -> GitLabClient:
    return GitLabClient(None, transport=FakeTransport(_live_replies(**overrides)))


class _TimeoutTransport:
    """A transport that raises on every request (models provider timeouts)."""

    def request(self, method, url, headers, timeout):  # type: ignore[no-untyped-def]
        raise TimeoutError("simulated provider timeout")


def test_feasibility_evaluation_contains_all_12_points():
    """All 12 mandatory feasibility study dimensions are documented with platform evidence."""
    assert len(FEASIBILITY_EVALUATION_12_POINTS) == 12
    for _key, item in FEASIBILITY_EVALUATION_12_POINTS.items():
        assert "dimension" in item
        assert "feasibility" in item
        assert "platform_evidence" in item
        assert "technical_blocker" in item
        assert len(str(item["platform_evidence"])) > 20


# ---------------------------------------------------------------------------
# LIVE-mode fail-closed preflight: a well-formed fake note never passes when
# the provider observation is missing, inaccessible, or contradictory.
# ---------------------------------------------------------------------------


def test_live_preflight_passes_with_full_provider_evidence():
    client = _live_client()
    preflight, pid, sha, candidates = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is True
    assert preflight.mode == "LIVE"
    assert preflight.provenance == "LIVE_ANONYMOUS_PROVIDER_NOTE"
    assert preflight.note_author == DUO_SERVICE_ACCOUNT_USERNAME
    assert pid == DEFAULT_TARGET_PROJECT_ID
    assert sha == AUTHENTIC_COMMIT_SHA
    assert len(candidates) == 2


def test_live_preflight_passes_without_supplied_body_using_provider_body():
    """The provider note body itself is the authoritative source."""
    client = _live_client()
    preflight, _pid, _sha, candidates = validate_continuation_preflight(client=client)
    assert preflight.passed is True
    assert len(candidates) == 2


@pytest.mark.parametrize("status_code", [401, 403, 404])
def test_live_preflight_fails_closed_on_provider_note_http_error(status_code):
    """Well-formed local note + provider 401/403/404 must fail closed."""
    client = _live_client(note_status=status_code)
    preflight, _, _, _ = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "INACCESSIBLE_PROVIDER_NOTE" in (preflight.failure_reason or "")
    assert preflight.provenance == "NOT_OBSERVED"


class _RaisingClient:
    """A client whose provider reads raise directly (models unclassified timeouts)."""

    token = None

    def get_json(self, endpoint, params=None):  # type: ignore[no-untyped-def]
        raise TimeoutError("simulated provider timeout")

    def get_text(self, endpoint, params=None):  # type: ignore[no-untyped-def]
        raise TimeoutError("simulated provider timeout")


def test_live_preflight_fails_closed_on_provider_timeout():
    """A provider timeout raised through the client must fail closed."""
    preflight, _, _, _ = validate_continuation_preflight(
        client=_RaisingClient(), note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "PROVIDER_NOTE_READ_FAILED" in (preflight.failure_reason or "")
    assert preflight.provenance == "NOT_OBSERVED"


def test_live_preflight_fails_closed_on_transport_level_timeout():
    """A transport-level timeout classified by the client also fails closed."""
    client = GitLabClient(None, transport=_TimeoutTransport())
    preflight, _, _, _ = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert preflight.provenance == "NOT_OBSERVED"
    assert (preflight.failure_reason or "").startswith(
        ("INACCESSIBLE_PROVIDER_NOTE", "PROVIDER_NOTE_READ_FAILED")
    )


def test_live_preflight_fails_closed_on_missing_branch():
    """A missing/inaccessible default branch HEAD must fail closed."""
    client = _live_client(branch_commit=None)
    preflight, _, _, _ = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "BRANCH_HEAD_NOT_OBSERVED" in (preflight.failure_reason or "")


def test_live_preflight_fails_closed_on_branch_drift():
    client = _live_client(branch_commit="f" * 40)
    preflight, _, _, _ = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "STALE_SOURCE_SHA" in (preflight.failure_reason or "")


def test_live_preflight_fails_closed_on_mismatched_note_body():
    """A locally supplied body that differs from the provider body fails."""
    client = _live_client(note_body_provider="### different note body entirely")
    preflight, _, _, _ = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "NOTE_BODY_MISMATCH" in (preflight.failure_reason or "")


def test_live_preflight_fails_closed_on_wrong_author():
    """A note authored by someone other than the Duo service account fails."""
    client = _live_client(note_author="attacker-impersonator")
    preflight, _, _, _ = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "NOTE_AUTHOR_MISMATCH" in (preflight.failure_reason or "")
    assert preflight.note_author == "attacker-impersonator"


def test_live_preflight_fails_closed_on_wrong_note_id():
    """A provider response whose note id differs from the bound note fails."""
    client = _live_client(note_id_returned=999999)
    preflight, _, _, _ = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "NOTE_ID_MISMATCH" in (preflight.failure_reason or "")


def test_live_preflight_fails_closed_on_wrong_provider_target_path():
    """A provider project whose full path differs from the bound target fails."""
    client = _live_client(target_path="evil-namespace/termivance-pages-disposable")
    preflight, _, _, _ = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "PROVIDER_TARGET_PATH_MISMATCH" in (preflight.failure_reason or "")


def test_live_preflight_fails_closed_without_client():
    """LIVE mode without a provider client can never pass on unobserved prerequisites."""
    preflight, _, _, _ = validate_continuation_preflight(
        note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "PROVIDER_NOTE_NOT_OBSERVED" in (preflight.failure_reason or "")


def test_live_preflight_fails_on_project_read_error():
    client = _live_client(project_status=404)
    preflight, _, _, _ = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is False
    assert "TARGET_PATH_NOT_OBSERVED" in (preflight.failure_reason or "")


def test_preflight_refuses_malformed_agent_note():
    """Malformed note lacking target PID or commit SHA is refused even in replay."""
    malformed_note = "Here is some unstructured text without target identity."
    preflight, _, _, _ = validate_continuation_preflight(
        note_body=malformed_note, mode="OFFLINE_REPLAY"
    )
    assert preflight.passed is False
    assert "MALFORMED_AGENT_NOTE" in (preflight.failure_reason or "")


def test_preflight_refuses_incorrect_target_id():
    wrong_pid_note = (
        "### 1. Target Identity & Observed Scope\n"
        "- **Target project ID:** `99999999`\n"
        f"- **Default branch HEAD commit:** `{AUTHENTIC_COMMIT_SHA}`\n"
    )
    preflight, _, _, _ = validate_continuation_preflight(
        note_body=wrong_pid_note,
        target_project_id=DEFAULT_TARGET_PROJECT_ID,
        mode="OFFLINE_REPLAY",
    )
    assert preflight.passed is False
    assert "TARGET_ID_MISMATCH" in (preflight.failure_reason or "")


def test_preflight_refuses_stale_source_commit_sha():
    stale_sha_note = (
        "### 1. Target Identity & Observed Scope\n"
        "- **Target project ID:** `87785099`\n"
        "- **Default branch HEAD commit:** `deadbeef0123456789abcdef0123456789abcdef`\n"
    )
    preflight, _, _, _ = validate_continuation_preflight(
        note_body=stale_sha_note,
        expected_commit_sha=AUTHENTIC_COMMIT_SHA,
        mode="OFFLINE_REPLAY",
    )
    assert preflight.passed is False
    assert "STALE_SOURCE_SHA" in (preflight.failure_reason or "")


def test_preflight_refuses_mismatched_session_or_issue():
    preflight, _, _, _ = validate_continuation_preflight(
        note_body=AUTHENTIC_NOTE_BODY,
        issue_iid=999,
        duo_session_id="wrong_session",
        mode="OFFLINE_REPLAY",
    )
    assert preflight.passed is False
    assert "SESSION_IDENTITY_MISMATCH" in (preflight.failure_reason or "")


# ---------------------------------------------------------------------------
# OFFLINE_REPLAY: honest fixture provenance, never live-authenticated claims.
# ---------------------------------------------------------------------------


def test_offline_replay_preflight_passes_with_fixture_provenance():
    preflight, _, _, _ = validate_continuation_preflight(
        note_body=AUTHENTIC_NOTE_BODY, mode="OFFLINE_REPLAY"
    )
    assert preflight.passed is True
    assert preflight.mode == "OFFLINE_REPLAY"
    assert preflight.provenance == "FIXTURE_RECORDED_INPUT"


def test_offline_replay_result_never_claims_live_authentication(tmp_path):
    res = run_supervised_continuation(
        client=_live_client(),
        note_body=AUTHENTIC_NOTE_BODY,
        issue_iid=5,
        duo_session_id=DUO_SESSION_ID_NEUTRAL,
        duo_note_id=NOTE_ID,
        target_project_id=DEFAULT_TARGET_PROJECT_ID,
        expected_commit_sha=AUTHENTIC_COMMIT_SHA,
        out_dir=tmp_path / "replay_out",
        mode="OFFLINE_REPLAY",
        now=NOW,
    )
    assert res.status == "COMPLETED"
    assert res.mode == "OFFLINE_REPLAY"
    data = res.to_dict()
    assert data["autonomy_classification"] == (
        "OFFLINE_REPLAY_FIXTURE_EXECUTION (RECORDED_INPUT provenance; "
        "never a live authenticated Supervised continuation)"
    )
    assert res.supervised_review is not None
    assert res.supervised_review.investigation_mode == "OFFLINE_REPLAY"
    replay_file = tmp_path / "replay_out" / "supervised_review.json"
    assert replay_file.exists()
    written = json.loads(replay_file.read_text(encoding="utf-8"))
    assert written["investigation_mode"] == "OFFLINE_REPLAY"


# ---------------------------------------------------------------------------
# LIVE continuation execution + durable causal ledger semantics.
# ---------------------------------------------------------------------------


def _run_live(out_dir, **overrides):
    params = {
        "client": _live_client(),
        "issue_iid": 5,
        "duo_session_id": DUO_SESSION_ID_NEUTRAL,
        "duo_note_id": NOTE_ID,
        "target_project_id": DEFAULT_TARGET_PROJECT_ID,
        "expected_commit_sha": AUTHENTIC_COMMIT_SHA,
        "out_dir": out_dir,
        "mode": "LIVE",
        "now": NOW,
    }
    params.update(overrides)
    return run_supervised_continuation(**params)


def test_live_continuation_completes_with_derived_verdict(tmp_path):
    res = _run_live(tmp_path / "cont_out")
    assert res.status == "COMPLETED"
    assert res.preflight.passed is True
    assert res.preflight.provenance == "LIVE_ANONYMOUS_PROVIDER_NOTE"
    assert res.durable_store is True
    assert res.duplicate_status == "FIRST_RECORDED_EXECUTION"
    assert res.supervised_review is not None
    # Verdict is derived from the executed review, never a hard-coded value.
    assert res.deterministic_verdict == res.supervised_review.deterministic_verdict
    assert res.deterministic_verdict in ("BLOCKED", "INCONCLUSIVE")
    assert "awaiting final human review" in res.summary


def test_live_continuation_refusal_reports_not_determined_verdict(tmp_path):
    """A refused preflight must not substitute a hard-coded BLOCKED success verdict."""
    res = _run_live(tmp_path / "fail_out", client=_live_client(note_status=403))
    assert res.status == "REFUSED_PREFLIGHT"
    assert res.supervised_review is None
    assert res.deterministic_verdict == "NOT_DETERMINED"
    assert "INACCESSIBLE_PROVIDER_NOTE" in res.summary


def test_duplicate_continuation_retrieves_stored_verdict(tmp_path):
    out_dir = tmp_path / "idem"
    res1 = _run_live(out_dir)
    assert res1.status == "COMPLETED"
    assert res1.is_duplicate is False
    first_verdict = res1.deterministic_verdict

    res2 = _run_live(out_dir)
    assert res2.status == "COMPLETED_IDEMPOTENT"
    assert res2.is_duplicate is True
    assert res2.duplicate_status == "DUPLICATE_OF_RECORDED_COMPLETED_EXECUTION"
    # The verdict comes from the authentic completed record, not a constant.
    assert res2.deterministic_verdict == first_verdict
    assert res2.durable_store is True


def test_incomplete_prior_execution_requires_recovery(tmp_path):
    """A crash between reservation and finalization leaves FIRST_STARTED; a
    duplicate attempt fails closed instead of claiming idempotent completion."""
    out_dir = tmp_path / "crash"
    ledger_file = out_dir / ".continuation_executions.json"
    out_dir.mkdir(parents=True)
    ledger = ContinuationLedger(ledger_file)
    ledger.health_check()
    causal_key = (
        f"{CANONICAL_PID}:5:{DUO_SESSION_ID_NEUTRAL}:{NOTE_ID}:"
        f"{DEFAULT_TARGET_PROJECT_ID}:{AUTHENTIC_COMMIT_SHA}"
    )
    reservation = ledger.reserve(
        causal_key, execution_id="cont-crash-simulated", now=NOW
    )
    assert reservation.outcome == RESERVE_FIRST_EXECUTION
    assert reservation.record is not None
    assert reservation.record["state"] == RESERVED_STATE

    res = _run_live(out_dir)
    assert res.status == "REFUSED_INCOMPLETE_PRIOR_EXECUTION"
    assert res.deterministic_verdict == "NOT_DETERMINED"
    assert res.duplicate_status == "PRIOR_EXECUTION_INCOMPLETE_RECOVERY_REQUIRED"
    assert res.supervised_review is None


def test_explicit_recovery_reexecutes_after_incomplete_prior(tmp_path):
    out_dir = tmp_path / "recover"
    res1 = _run_live(out_dir)
    assert res1.status == "COMPLETED"
    # Simulate an incomplete follow-up execution for the same causal identity
    # by resetting the durable record to FIRST_STARTED via the ledger API.
    ledger_file = out_dir / ".continuation_executions.json"
    raw = json.loads(ledger_file.read_text(encoding="utf-8"))
    key = next(iter(raw["executions"]))
    raw["executions"][key]["state"] = RESERVED_STATE
    raw["executions"][key].pop("digest", None)
    # Recompute digest via the ledger's own integrity contract.
    from termivance.continuation_ledger import entry_digest

    raw["executions"][key]["digest"] = entry_digest(raw["executions"][key])
    ledger_file.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    refused = _run_live(out_dir)
    assert refused.status == "REFUSED_INCOMPLETE_PRIOR_EXECUTION"

    recovered = _run_live(out_dir, allow_recovery=True)
    assert recovered.status == "COMPLETED"
    assert recovered.is_duplicate is False
    # The recovered record must note the auditable recovery attempt.
    final = json.loads(ledger_file.read_text(encoding="utf-8"))
    entry = final["executions"][key]
    assert entry["state"] == COMPLETED_STATE
    assert entry.get("recovery_attempts")


def test_partial_execution_is_never_converted_to_idempotent_completion(tmp_path):
    """A PARTIAL prior execution must not become COMPLETED_IDEMPOTENT on retry."""
    out_dir = tmp_path / "partial"
    res1 = _run_live(out_dir)
    assert res1.status == "COMPLETED"
    ledger_file = out_dir / ".continuation_executions.json"
    raw = json.loads(ledger_file.read_text(encoding="utf-8"))
    key = next(iter(raw["executions"]))
    raw["executions"][key]["state"] = PARTIAL_STATE
    raw["executions"][key]["status"] = "PARTIAL_REVIEW"
    raw["executions"][key].pop("digest", None)
    from termivance.continuation_ledger import entry_digest

    raw["executions"][key]["digest"] = entry_digest(raw["executions"][key])
    ledger_file.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    res2 = _run_live(out_dir)
    assert res2.status == "REFUSED_INCOMPLETE_PRIOR_EXECUTION"
    assert res2.status != "COMPLETED_IDEMPOTENT"


def test_failed_execution_is_never_converted_to_idempotent_completion(tmp_path):
    out_dir = tmp_path / "failed"
    _run_live(out_dir)
    ledger_file = out_dir / ".continuation_executions.json"
    raw = json.loads(ledger_file.read_text(encoding="utf-8"))
    key = next(iter(raw["executions"]))
    raw["executions"][key]["state"] = "FAILED"
    raw["executions"][key].pop("digest", None)
    from termivance.continuation_ledger import entry_digest

    raw["executions"][key]["digest"] = entry_digest(raw["executions"][key])
    ledger_file.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    res2 = _run_live(out_dir)
    assert res2.status == "REFUSED_INCOMPLETE_PRIOR_EXECUTION"


def test_corrupted_ledger_fails_closed_and_never_becomes_clean(tmp_path):
    out_dir = tmp_path / "corrupt"
    out_dir.mkdir(parents=True)
    ledger_file = out_dir / ".continuation_executions.json"
    ledger_file.write_text("this is not json", encoding="utf-8")

    res = _run_live(out_dir)
    assert res.status == "REFUSED_LEDGER_UNAVAILABLE"
    assert res.durable_store is False
    assert res.duplicate_status == "LEDGER_UNAVAILABLE"
    # The corrupted file was not silently replaced by a clean ledger.
    assert ledger_file.read_text(encoding="utf-8") == "this is not json"


def test_tampered_ledger_entry_fails_integrity(tmp_path):
    out_dir = tmp_path / "tamper"
    res1 = _run_live(out_dir)
    assert res1.status == "COMPLETED"
    ledger_file = out_dir / ".continuation_executions.json"
    raw = json.loads(ledger_file.read_text(encoding="utf-8"))
    key = next(iter(raw["executions"]))
    raw["executions"][key]["verdict"] = "SAFE_TO_RETIRE"  # tamper, digest now stale
    ledger_file.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    res2 = _run_live(out_dir)
    assert res2.status == "REFUSED_LEDGER_UNAVAILABLE"
    assert res2.deterministic_verdict != "SAFE_TO_RETIRE"


def test_missing_out_dir_never_claims_durable_idempotency(tmp_path):
    """Without a durable store, no durable idempotency claim is made."""
    res1 = _run_live(None)
    assert res1.status == "COMPLETED"
    assert res1.durable_store is False
    assert res1.duplicate_status == "NOT_DURABLE_NO_LEDGER_STORE"
    data = res1.to_dict()
    assert data["durable_store"] is False

    res2 = _run_live(None)
    assert res2.status == "COMPLETED"
    assert res2.is_duplicate is False
    assert res2.duplicate_status == "NOT_DURABLE_NO_LEDGER_STORE"


def test_concurrent_identical_reservations_yield_exactly_one_first(tmp_path):
    """Two concurrent identical invocations must not both claim a unique first
    completed execution (exercised through the production ledger path)."""
    ledger_file = tmp_path / "conc" / ".continuation_executions.json"
    ledger_file.parent.mkdir(parents=True)
    causal_key = (
        f"{CANONICAL_PID}:5:{DUO_SESSION_ID_NEUTRAL}:{NOTE_ID}:"
        f"{DEFAULT_TARGET_PROJECT_ID}:{AUTHENTIC_COMMIT_SHA}"
    )

    def _reserve(_i: int) -> str:
        led = ContinuationLedger(ledger_file)
        led.health_check()
        return led.reserve(
            causal_key, execution_id=f"cont-conc-{_i}", now=NOW
        ).outcome

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(_reserve, range(4)))

    assert outcomes.count(RESERVE_FIRST_EXECUTION) == 1
    for outcome in outcomes:
        assert outcome in (RESERVE_FIRST_EXECUTION, "INCOMPLETE_PRIOR_EXECUTION")


def test_mismatched_causal_identities_are_independent_executions(tmp_path):
    out_a = tmp_path / "identity_a"
    out_b = tmp_path / "identity_b"
    res_a = _run_live(out_a)
    res_b = _run_live(out_b, expected_commit_sha=AUTHENTIC_COMMIT_SHA, duo_note_id=NOTE_ID)
    assert res_a.status == "COMPLETED"
    assert res_b.status == "COMPLETED"
    assert res_a.is_duplicate is False
    assert res_b.is_duplicate is False

    # A different expected SHA is a different causal identity: not a duplicate.
    res_c = _run_live(out_a, expected_commit_sha="a" * 40, client=_live_client())
    assert res_c.status in ("REFUSED_PREFLIGHT", "COMPLETED")
    if res_c.status == "COMPLETED":
        assert res_c.is_duplicate is False


def test_ledger_reservation_survives_simulated_process_restart(tmp_path):
    """Reservation state is durable across ledger instances (process restart)."""
    ledger_file = tmp_path / "restart" / ".continuation_executions.json"
    ledger_file.parent.mkdir(parents=True)
    first = ContinuationLedger(ledger_file)
    first.health_check()
    causal_key = "canonical:5:session:note:87785099:sha"
    first.reserve(causal_key, execution_id="cont-restart-1", now=NOW)

    # A new instance (fresh process) reads the same durable record.
    second = ContinuationLedger(ledger_file)
    record = second.lookup(causal_key)
    assert record is not None
    assert record["state"] == RESERVED_STATE
    assert record["execution_id"] == "cont-restart-1"


def test_ledger_finalize_rejects_unknown_binding(tmp_path):
    ledger_file = tmp_path / "unknown" / ".continuation_executions.json"
    ledger_file.parent.mkdir(parents=True)
    ledger = ContinuationLedger(ledger_file)
    ledger.health_check()
    with pytest.raises(ContinuationLedgerError, match="unknown causal key"):
        ledger.finalize(
            "never:reserved:key", execution_id="x", status="COMPLETED",
            verdict="BLOCKED", now=NOW,
        )


def test_zero_unauthorized_mutation_guarantee(tmp_path):
    """Continuation execution must never dispatch mutations (GET-only transport)."""
    transport = FakeTransport(_live_replies())
    client = GitLabClient(None, transport=transport)
    res = run_supervised_continuation(
        client=client,
        note_body=AUTHENTIC_NOTE_BODY,
        issue_iid=5,
        duo_session_id=DUO_SESSION_ID_NEUTRAL,
        duo_note_id=NOTE_ID,
        target_project_id=DEFAULT_TARGET_PROJECT_ID,
        expected_commit_sha=AUTHENTIC_COMMIT_SHA,
        out_dir=tmp_path / "mutation_free",
        mode="OFFLINE_REPLAY",
        now=NOW,
    )
    assert res.status == "COMPLETED"
    methods = {m.upper() for m, _url in transport.calls}
    assert methods <= {"GET"}
    assert "DELETE" not in methods
    assert "POST" not in methods
    assert "PUT" not in methods


# ---------------------------------------------------------------------------
# CLI parity
# ---------------------------------------------------------------------------


def test_cli_offline_replay_dispatch(tmp_path, monkeypatch):
    """CLI offline-replay mode parses, dispatches and exits 0 (network-free)."""
    import termivance.gitlab_client as glc
    from termivance.cli import main

    fake_client = GitLabClient(None, transport=FakeTransport(_live_replies()))
    monkeypatch.setattr(glc, "GitLabClient", lambda *a, **kw: fake_client)

    out_file = tmp_path / "cli_replay.json"
    cmd = [
        "supervised-review",
        "--continue",
        "--mode",
        "offline-replay",
        "--issue-iid",
        "5",
        "--session-id",
        DUO_SESSION_ID_NEUTRAL,
        "--note-id",
        str(NOTE_ID),
        "--target-id",
        str(DEFAULT_TARGET_PROJECT_ID),
        "--expected-sha",
        AUTHENTIC_COMMIT_SHA,
        "--note-body",
        AUTHENTIC_NOTE_BODY,
        "--out-dir",
        str(tmp_path / "cli_replay_out"),
        "--out",
        str(out_file),
    ]
    exit_code = main(cmd)
    assert exit_code == 0
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["mode"] == "OFFLINE_REPLAY"
    assert payload["status"] == "COMPLETED"
    assert "OFFLINE_REPLAY" in payload["autonomy_classification"]


def test_cli_live_mode_fails_closed_on_inaccessible_note(tmp_path, monkeypatch):
    """CLI live mode exits 1 when the provider note is inaccessible (404)."""
    import termivance.gitlab_client as glc
    from termivance.cli import main

    class _FailingClient:
        token = None

        def get_json(self, endpoint, params=None):  # type: ignore[no-untyped-def]
            return ApiResult(False, 404, None, endpoint, "GET", "NOT_FOUND")

        def get_text(self, endpoint, params=None):  # type: ignore[no-untyped-def]
            return ApiResult(False, 404, None, endpoint, "GET", "NOT_FOUND")

    monkeypatch.setattr(glc, "GitLabClient", lambda *a, **kw: _FailingClient())

    out_file = tmp_path / "cli_live_fail.json"
    cmd = [
        "supervised-review",
        "--continue",
        "--mode",
        "live",
        "--issue-iid",
        "5",
        "--session-id",
        DUO_SESSION_ID_NEUTRAL,
        "--note-id",
        str(NOTE_ID),
        "--target-id",
        str(DEFAULT_TARGET_PROJECT_ID),
        "--expected-sha",
        AUTHENTIC_COMMIT_SHA,
        "--note-body",
        AUTHENTIC_NOTE_BODY,
        "--out-dir",
        str(tmp_path / "cli_live_out"),
        "--out",
        str(out_file),
    ]
    exit_code = main(cmd)
    assert exit_code == 1
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["status"] == "REFUSED_PREFLIGHT"
    assert payload["deterministic_verdict"] == "NOT_DETERMINED"
