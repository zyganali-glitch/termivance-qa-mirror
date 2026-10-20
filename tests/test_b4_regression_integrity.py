"""Independent QA regression tests for B4 repair closure:

1. Real publisher interface contract & transport-level integration
2. Response identity validation & read-back distinction
3. Missing publisher, publisher error & interface mismatch
4. Evidence-driven candidate corroboration (rejecting keyword-only matching)
5. Adversarial AI claims contradiction (absent pages: true, absent marker, wrong status)
6. Source commit binding & content mismatch
7. Historical agent execution vs live note read provenance truth
8. Mixed candidate status outcome note formatting
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from conftest import FakeTransport

from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.publish import GitLabPublisher
from termivance.supervised_review import (
    CANONICAL_PROJECT_ID,
    DEFAULT_TARGET_PROJECT_ID,
    ProviderObservations,
    _corroborate_single_candidate,
    _format_supervised_outcome_note,
    run_supervised_investigation,
)
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 20, 8, 30, tzinfo=UTC)
TARGET_PID = DEFAULT_TARGET_PROJECT_ID
TARGET_PATH = (
    "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
)
TARGET = TargetIdentity(TARGET_PID, TARGET_PATH, "GITLAB_PAGES_SITE")
COMMIT_SHA = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"


def mock_target_responses() -> dict[tuple[str, str], HttpReply]:
    return {
        ("GET", f"/projects/{TARGET_PID}/repository/commits"): HttpReply(
            200, json.dumps([{"id": COMMIT_SHA}])
        ),
        ("GET", f"/projects/{TARGET_PID}/repository/files/.gitlab-ci.yml/raw"): HttpReply(
            200,
            "# DISPOSABLE B3 demonstration site (temporary; safe to retire)\n"
            "create-pages:\n"
            "  stage: deploy\n"
            "  image: alpine:3.20\n"
            "  pages: true\n",
        ),
        ("GET", f"/projects/{TARGET_PID}/repository/files/site%2Fmarker.txt/raw"): HttpReply(
            200, "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a\n"
        ),
        ("GET", f"/projects/{TARGET_PID}/pages"): HttpReply(403, ""),
        ("GET", f"/projects/{TARGET_PID}/pipelines"): HttpReply(200, "[]"),
        ("GET", f"/projects/{TARGET_PID}/environments"): HttpReply(200, "[]"),
        ("GET", f"/projects/{TARGET_PID}/issues"): HttpReply(200, "[]"),
        ("GET", f"/projects/{CANONICAL_PROJECT_ID}/issues"): HttpReply(200, "[]"),
        ("GET", f"/projects/{TARGET_PID}"): HttpReply(
            200,
            json.dumps(
                {
                    "id": TARGET_PID,
                    "path_with_namespace": TARGET_PATH,
                    "default_branch": "main",
                    "permissions": {
                        "project_access": {"access_level": 30},
                        "group_access": None,
                    },
                }
            ),
        ),
        ("GET", f"/projects/{CANONICAL_PROJECT_ID}"): HttpReply(
            200,
            json.dumps(
                {
                    "id": CANONICAL_PROJECT_ID,
                    "path_with_namespace": "gitlab-ai-hackathon/termivance",
                    "default_branch": "main",
                    "permissions": {
                        "project_access": {"access_level": 30},
                        "group_access": None,
                    },
                }
            ),
        ),
    }


# ---------------------------------------------------------------------------
# DEFECT 1: REAL PUBLISHER INTERFACE CONTRACT & RESPONSE IDENTITY
# ---------------------------------------------------------------------------


def test_successful_provider_acknowledged_issue_note_publication(tmp_path):
    """Use the real GitLabPublisher interface with a mocked HTTP transport."""
    pub_transport = FakeTransport(
        {
            ("POST", f"/projects/{CANONICAL_PROJECT_ID}/issues/5/notes"): HttpReply(
                201, json.dumps({"id": 4045409264, "body": "outcome note content"})
            )
        }
    )
    publisher = GitLabPublisher("mock-token", transport=pub_transport)

    # Client providing independent read-back confirmation
    client_responses = {
        ("GET", f"/projects/{CANONICAL_PROJECT_ID}/issues/5/notes/4045409264"): HttpReply(
            200, json.dumps({"id": 4045409264, "body": "outcome note content"})
        ),
        **mock_target_responses(),
    }
    client = GitLabClient(None, transport=FakeTransport(client_responses))

    out_dir = tmp_path / "pub_success"
    review = run_supervised_investigation(
        client=client,
        publisher=publisher,
        target=TARGET,
        issue_iid=5,
        publish_outcome=True,
        out_dir=out_dir,
        now=NOW,
    )

    pub_step = next(s for s in review.steps if s.step_id == "supervised_outcome_publication")
    assert pub_step.status == "COMPLETED"
    assert pub_step.execution_mode == "EXECUTED_NOW"
    assert pub_step.output_ref == "gitlab_issue_note:4045409264"
    assert "API acknowledged HTTP 201" in pub_step.detail
    assert "independent read-back verified note 4045409264" in pub_step.detail
    assert (out_dir / "supervised_outcome_note.md").exists()


def test_missing_publisher_produces_honest_not_run(tmp_path):
    """When publish requested but publisher=None, status must be NOT_RUN."""
    review = run_supervised_investigation(
        publisher=None,
        target=TARGET,
        issue_iid=5,
        publish_outcome=True,
        out_dir=tmp_path / "no_pub",
        now=NOW,
    )
    pub_step = next(s for s in review.steps if s.step_id == "supervised_outcome_publication")
    assert pub_step.status == "NOT_RUN"
    assert pub_step.execution_mode == "NOT_RUN"
    assert pub_step.output_ref is None
    assert "no authenticated publisher was provided" in pub_step.detail


def test_publisher_error_produces_honest_not_verified(tmp_path):
    """When publisher encounters transport HTTP error, produce honest NOT_VERIFIED."""
    err_transport = FakeTransport(
        {
            ("POST", f"/projects/{CANONICAL_PROJECT_ID}/issues/5/notes"): HttpReply(
                500, "Internal Server Error", error="HTTP 500"
            )
        }
    )
    publisher = GitLabPublisher("mock-token", transport=err_transport)

    review = run_supervised_investigation(
        publisher=publisher,
        target=TARGET,
        issue_iid=5,
        publish_outcome=True,
        out_dir=tmp_path / "err_pub",
        now=NOW,
    )
    pub_step = next(s for s in review.steps if s.step_id == "supervised_outcome_publication")
    assert pub_step.status == "NOT_VERIFIED"
    assert pub_step.execution_mode == "NOT_RUN"
    assert "status=500" in pub_step.detail or "500" in pub_step.detail


def test_publisher_interface_mismatch_aborts_with_not_verified(tmp_path):
    """An object lacking create_issue_note produces NOT_VERIFIED with mismatch detail."""

    class IncompatiblePublisher:
        pass

    review = run_supervised_investigation(
        publisher=IncompatiblePublisher(),
        target=TARGET,
        issue_iid=5,
        publish_outcome=True,
        out_dir=tmp_path / "mismatch_pub",
        now=NOW,
    )
    pub_step = next(s for s in review.steps if s.step_id == "supervised_outcome_publication")
    assert pub_step.status == "NOT_VERIFIED"
    assert pub_step.execution_mode == "NOT_RUN"
    assert "Publisher interface mismatch" in pub_step.detail
    assert "create_issue_note" in pub_step.detail


def test_incorrect_missing_or_contradictory_note_response_identity(tmp_path):
    """When publisher returns 201 but lacks valid note id, refuse COMPLETED."""
    non_identifying_transport = FakeTransport(
        {
            ("POST", f"/projects/{CANONICAL_PROJECT_ID}/issues/5/notes"): HttpReply(
                201, json.dumps({"status": "created", "note": "missing id"})
            )
        }
    )
    publisher = GitLabPublisher("mock-token", transport=non_identifying_transport)

    review = run_supervised_investigation(
        publisher=publisher,
        target=TARGET,
        issue_iid=5,
        publish_outcome=True,
        out_dir=tmp_path / "non_id_pub",
        now=NOW,
    )
    pub_step = next(s for s in review.steps if s.step_id == "supervised_outcome_publication")
    assert pub_step.status == "NOT_VERIFIED"
    assert pub_step.execution_mode == "NOT_RUN"
    assert pub_step.output_ref is None


# ---------------------------------------------------------------------------
# DEFECT 2: EVIDENCE-DRIVEN CANDIDATE CORROBORATION (NO KEYWORD INFERENCE)
# ---------------------------------------------------------------------------


def test_adversarial_ai_falsely_claiming_absent_pages_true_is_contradicted():
    """An AI claim alleging create-pages with pages: true must be CONTRADICTED

    if the actual observed .gitlab-ci.yml does NOT contain this configuration.
    """
    clean_ci_text = "stages:\n  - test\ntest_job:\n  stage: test\n  script: echo clean\n"
    obs = ProviderObservations(
        target_project_id=TARGET_PID,
        observed_commit_sha=COMMIT_SHA,
        ci_config_text=clean_ci_text,
        ci_signals=(),
        ci_status=200,
        ci_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        marker_text="marker",
        marker_status=200,
        pages_status=403,
        pages_error_kind="AUTH_DENIED",
        policy=None,
        canonical_issues=None,
    )

    ai_cand = {
        "num": 1,
        "topic": "CI Redeployment",
        "detail": "Target .gitlab-ci.yml has create-pages and pages: true",
    }
    result = _corroborate_single_candidate(ai_cand, TARGET_PID, COMMIT_SHA, "9710085", obs=obs)

    assert result.corroboration_status == "CONTRADICTED"
    assert "does NOT contain this job or signal" in result.corroboration_detail
    assert "CONTRADICTED_AI_CLAIM" in result.causal_attribution


def test_source_commit_mismatch_returns_unresolved():
    """When a candidate is bound to commit A but target HEAD is commit B, return UNRESOLVED."""
    obs = ProviderObservations(
        target_project_id=TARGET_PID,
        observed_commit_sha="9999999999999999999999999999999999999999",  # Different commit
        ci_config_text="pages:\n  pages: true\n",
        ci_signals=("pages_true",),
        ci_status=200,
        ci_digest="abc",
        marker_text="marker",
        marker_status=200,
        pages_status=403,
        pages_error_kind="AUTH_DENIED",
        policy=None,
        canonical_issues=None,
    )

    ai_cand = {
        "num": 1,
        "topic": "CI Redeployment",
        "detail": "create-pages with pages: true",
    }
    result = _corroborate_single_candidate(ai_cand, TARGET_PID, COMMIT_SHA, "9710085", obs=obs)

    assert result.corroboration_status == "UNRESOLVED"
    assert "Source commit mismatch" in result.corroboration_detail


def test_absent_or_changed_marker_is_contradicted():
    """When AI claims marker 7f3c9a but observed file returns 404 or different text, contradict."""
    obs_404 = ProviderObservations(
        target_project_id=TARGET_PID,
        observed_commit_sha=COMMIT_SHA,
        ci_config_text="pages: true",
        ci_signals=("pages_true",),
        ci_status=200,
        ci_digest="abc",
        marker_text=None,
        marker_status=404,  # Absent!
        pages_status=403,
        pages_error_kind="AUTH_DENIED",
        policy=None,
        canonical_issues=None,
    )

    ai_cand = {
        "num": 7,
        "topic": "Marker",
        "detail": "Marker TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a verified",
    }
    res_404 = _corroborate_single_candidate(ai_cand, TARGET_PID, COMMIT_SHA, "9710085", obs=obs_404)
    assert res_404.corroboration_status == "CONTRADICTED"
    assert "marker absent" in res_404.corroboration_detail.lower()

    # Mismatched marker content
    obs_mismatch = ProviderObservations(
        target_project_id=TARGET_PID,
        observed_commit_sha=COMMIT_SHA,
        ci_config_text="pages: true",
        ci_signals=("pages_true",),
        ci_status=200,
        ci_digest="abc",
        marker_text="UNRELATED_DIFFERENT_CONTENT",
        marker_status=200,
        pages_status=403,
        pages_error_kind="AUTH_DENIED",
        policy=None,
        canonical_issues=None,
    )
    res_mismatch = _corroborate_single_candidate(
        ai_cand, TARGET_PID, COMMIT_SHA, "9710085", obs=obs_mismatch
    )
    assert res_mismatch.corroboration_status == "CONTRADICTED"
    assert "does NOT contain this marker" in res_mismatch.corroboration_detail


def test_pages_permission_endpoint_unexpected_status_is_contradicted():
    """When AI claims 403 AUTH_DENIED but actual probe returned HTTP 200, contradict."""
    obs = ProviderObservations(
        target_project_id=TARGET_PID,
        observed_commit_sha=COMMIT_SHA,
        ci_config_text="pages: true",
        ci_signals=("pages_true",),
        ci_status=200,
        ci_digest="abc",
        marker_text="7f3c9a",
        marker_status=200,
        pages_status=200,  # Unexpected 200!
        pages_error_kind=None,
        policy=None,
        canonical_issues=None,
    )

    ai_cand = {
        "num": 5,
        "topic": "Permissions",
        "detail": "Pages administration endpoint returned 403 AUTH_DENIED",
    }
    result = _corroborate_single_candidate(ai_cand, TARGET_PID, COMMIT_SHA, "9710085", obs=obs)

    assert result.corroboration_status == "CONTRADICTED"
    assert "actual provider observation returned HTTP 200" in result.corroboration_detail


def test_historical_duo_note_read_vs_historical_agent_execution(tmp_path):
    """Reading a note live via REST API keeps duo_candidate_analysis RECORDED_HISTORICAL."""
    # Live note read simulation
    note_payload = {
        "id": 4045401991,
        "body": (
            "### 1. Target Identity\n"
            f"- Target project ID: `{TARGET_PID}`\n"
            f"- Ref commit: `{COMMIT_SHA}`\n\n"
            "### 3. Candidate obligations\n"
            "1. **CI Redeployment**: create-pages with pages: true\n"
        ),
        "author": {"username": "duo_agent"},
        "created_at": "2026-10-19T19:46:42Z",
    }
    note_responses = {
        ("GET", f"/projects/{CANONICAL_PROJECT_ID}/issues/5/notes/4045401991"): HttpReply(
            200, json.dumps(note_payload)
        ),
        **mock_target_responses(),
    }
    client = GitLabClient(None, transport=FakeTransport(note_responses))

    review = run_supervised_investigation(
        client=client,
        target=TARGET,
        issue_iid=5,
        out_dir=tmp_path / "hist_out",
        now=NOW,
    )

    steps = {s.step_id: s for s in review.steps}
    # Step 1: Agent step MUST remain RECORDED_HISTORICAL
    assert steps["duo_candidate_analysis"].execution_mode == "RECORDED_HISTORICAL"
    assert steps["duo_candidate_analysis"].status == "COMPLETED"

    # Step 2: Supervised handoff ingestion is EXECUTED_NOW
    assert steps["operator_handoff"].execution_mode == "EXECUTED_NOW"
    assert steps["operator_handoff"].status == "COMPLETED"


def test_mixed_candidate_status_outcome_note_truth():
    """Outcome note copy must not claim all candidates verified when some are unresolved."""
    summary = [
        {
            "topic": "cand-01",
            "status": "CORROBORATED",
            "obligation": "REDEPLOYMENT_PATH",
            "detail": "CI ok",
        },
        {
            "topic": "cand-02",
            "status": "UNRESOLVED",
            "obligation": "NONE (UNOBSERVABLE)",
            "detail": "schedules",
        },
        {
            "topic": "cand-03",
            "status": "UNRESOLVED",
            "obligation": "NONE (UNOBSERVABLE)",
            "detail": "caches",
        },
        {
            "topic": "cand-04",
            "status": "CORROBORATED",
            "obligation": "OWNERSHIP_AUTHORIZATION",
            "detail": "policy",
        },
        {
            "topic": "cand-05",
            "status": "CORROBORATED",
            "obligation": "RETIREMENT_PERMISSION",
            "detail": "403",
        },
        {
            "topic": "cand-06",
            "status": "CONTEXTUAL_ONLY",
            "obligation": "COORDINATION_CONTEXT",
            "detail": "issues",
        },
        {
            "topic": "cand-07",
            "status": "CORROBORATED",
            "obligation": "PAGES_PUBLISHED",
            "detail": "marker",
        },
    ]
    note = _format_supervised_outcome_note(
        exec_id="inv-test-1",
        target_project_id=TARGET_PID,
        target_path=TARGET_PATH,
        commit_sha=COMMIT_SHA,
        duo_session_id="9710085",
        duo_note_id=4045401991,
        candidate_summary=summary,
        verdict="BLOCKED",
    )

    # Must NOT say 'All candidate obligations ... were independently verified'
    assert (
        "All candidate obligations proposed by GitLab Duo were independently verified"
        not in note
    )
    # Must report truthful breakdown
    assert "4 corroborated, 2 unresolved, 1 contextual" in note
    assert "REDEPLOYMENT_PATH" in note
    assert "COORDINATION_CONTEXT" in note
    assert "OWNERSHIP_AUTHORIZATION" in note
