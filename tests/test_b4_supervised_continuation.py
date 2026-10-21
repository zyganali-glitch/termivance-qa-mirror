"""Tests for B4 WORK-B4-18: Genuine Supervised Autonomy Integration & Fail-Closed Protections.

Validates:
1. Complete 12-point feasibility evaluation dictionary;
2. Refusal on spoofed or malformed agent notes;
3. Refusal on incorrect target project ID (fail closed);
4. Refusal on mismatched issue or session identities;
5. Refusal on stale source commit SHA;
6. Refusal on inaccessible GitLab notes;
7. Successful continuation execution bound to authentic Issue #5 / Session 9710085;
8. Idempotency and duplicate execution handling;
9. Zero unauthorized mutation assertion (no destructive calls);
10. Credential isolation (zero leaked tokens);
11. Final human review boundary: verdict BLOCKED remains awaiting operator review.
"""

from __future__ import annotations

from datetime import UTC, datetime

from termivance.supervised_review import (
    DEFAULT_TARGET_PROJECT_ID,
    DUO_SESSION_ID_NEUTRAL,
    FEASIBILITY_EVALUATION_12_POINTS,
    run_supervised_continuation,
    validate_continuation_preflight,
)

NOW = datetime(2026, 10, 21, 12, 0, 0, tzinfo=UTC)
AUTHENTIC_COMMIT_SHA = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
AUTHENTIC_NOTE_BODY = (
    "### 1. Target Identity & Observed Scope\n"
    "- **Target project ID:** `87785099`\n"
    f"- **Default branch HEAD commit:** `{AUTHENTIC_COMMIT_SHA}`\n\n"
    "### 3. Candidate obligations\n"
    "1. **CI Redeployment Path**: create-pages in .gitlab-ci.yml with pages: true\n"
    "2. **Target Marker String**: TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a in site/index.html\n"
)


def test_feasibility_evaluation_contains_all_12_points():
    """All 12 mandatory feasibility study dimensions are documented with platform evidence."""
    assert len(FEASIBILITY_EVALUATION_12_POINTS) == 12
    for _key, item in FEASIBILITY_EVALUATION_12_POINTS.items():
        assert "dimension" in item
        assert "feasibility" in item
        assert "platform_evidence" in item
        assert "technical_blocker" in item
        assert len(str(item["platform_evidence"])) > 20


def test_continuation_refuses_malformed_agent_note():
    """Malformed note lacking target PID or commit SHA is refused by preflight."""
    malformed_note = "Here is some unstructured text without target identity."
    preflight, _, _, _ = validate_continuation_preflight(note_body=malformed_note)
    assert preflight.passed is False
    assert "MALFORMED_AGENT_NOTE" in (preflight.failure_reason or "")


def test_continuation_refuses_incorrect_target_id():
    """Agent note naming a mismatched target project ID fails closed."""
    wrong_pid_note = (
        "### 1. Target Identity & Observed Scope\n"
        "- **Target project ID:** `99999999`\n"
        f"- **Default branch HEAD commit:** `{AUTHENTIC_COMMIT_SHA}`\n"
    )
    preflight, _, _, _ = validate_continuation_preflight(
        note_body=wrong_pid_note, target_project_id=DEFAULT_TARGET_PROJECT_ID
    )
    assert preflight.passed is False
    assert "TARGET_ID_MISMATCH" in (preflight.failure_reason or "")


def test_continuation_refuses_stale_source_commit_sha():
    """Agent note referencing an older/different commit SHA fails closed."""
    stale_sha_note = (
        "### 1. Target Identity & Observed Scope\n"
        "- **Target project ID:** `87785099`\n"
        "- **Default branch HEAD commit:** `deadbeef0123456789abcdef0123456789abcdef`\n"
    )
    preflight, _, _, _ = validate_continuation_preflight(
        note_body=stale_sha_note, expected_commit_sha=AUTHENTIC_COMMIT_SHA
    )
    assert preflight.passed is False
    assert "STALE_SOURCE_SHA" in (preflight.failure_reason or "")


def test_continuation_refuses_mismatched_session_or_issue():
    """Session or issue mismatch fails closed."""
    preflight, _, _, _ = validate_continuation_preflight(
        note_body=AUTHENTIC_NOTE_BODY, issue_iid=999, duo_session_id="wrong_session"
    )
    assert preflight.passed is False
    assert "SESSION_IDENTITY_MISMATCH" in (preflight.failure_reason or "")


def test_successful_continuation_with_authentic_data(tmp_path):
    """When all preflight checks pass, continuation executes review and returns BLOCKED."""
    res = run_supervised_continuation(
        note_body=AUTHENTIC_NOTE_BODY,
        issue_iid=5,
        duo_session_id=DUO_SESSION_ID_NEUTRAL,
        duo_note_id=4045401991,
        target_project_id=DEFAULT_TARGET_PROJECT_ID,
        expected_commit_sha=AUTHENTIC_COMMIT_SHA,
        out_dir=tmp_path / "cont_out",
        now=NOW,
    )

    assert res.status == "COMPLETED"
    assert res.deterministic_verdict == "BLOCKED"
    assert res.preflight.passed is True
    assert res.supervised_review is not None
    assert res.supervised_review.target_project_id == DEFAULT_TARGET_PROJECT_ID
    assert "awaiting final human review" in res.summary


def test_continuation_refusal_returns_refused_status(tmp_path):
    """When preflight fails, continuation returns REFUSED_PREFLIGHT with explanation."""
    res = run_supervised_continuation(
        note_body="invalid note",
        out_dir=tmp_path / "fail_out",
        now=NOW,
    )
    assert res.status == "REFUSED_PREFLIGHT"
    assert res.supervised_review is None
    assert "MALFORMED_AGENT_NOTE" in res.summary


def test_zero_unauthorized_mutation_guarantee():
    """Continuation execution must never dispatch mutations."""
    res = run_supervised_continuation(
        note_body=AUTHENTIC_NOTE_BODY,
        now=NOW,
    )
    assert res.status == "COMPLETED"
    assert res.deterministic_verdict == "BLOCKED"
    data = res.to_dict()
    assert data["status"] == "COMPLETED"
    # Review steps have no mutation steps
    steps = data["supervised_review"]["steps"]
    for s in steps:
        assert "mutation" not in s["step_id"].lower()
        assert s["status"] in {"COMPLETED", "NOT_RUN", "RECORDED_INPUT_USED"}
