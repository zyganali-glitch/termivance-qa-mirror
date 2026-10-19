"""Tests for B4 supervised review workflow continuity, candidate parsing, and publication.

Verifies:
1. parse_duo_note extracts target, commit SHA, and candidate obligations without silent fallbacks;
2. run_supervised_investigation ingests authentic Duo claims from Note 4045401991 / Issue #5;
3. Corroborates claims independently against provider endpoints (unobservable stays UNRESOLVED);
4. Formats and publishes outcome note awaiting human review (honouring publication status);
5. Strictly maintains deterministic BLOCKED invariance against adversarial AI claims;
6. Fails closed on inaccessible notes, wrong target PIDs, and missing commit SHAs;
7. Declares operator/CI-initiated pipeline autonomy without claiming a continuous daemon.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

from termivance.cli import build_parser
from termivance.supervised_review import (
    CANONICAL_PROJECT_ID,
    DEFAULT_TARGET_PROJECT_ID,
    DUO_SESSION_ID_NEUTRAL,
    parse_duo_note,
    run_supervised_investigation,
)
from termivance.target import TargetIdentity

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 19, 19, 0, 0, tzinfo=UTC)

SAMPLE_DUO_NOTE = (
    "### 1. Target Identity & Observed Scope\n"
    "- **Target project ID:** `87785099`\n"
    "- **Default branch HEAD commit:** `54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d`\n\n"
    "### 2. Direct Source & Lifecycle Observations\n"
    "Used `get_repository_file` on target `87785099`. Found `.gitlab-ci.yml`.\n\n"
    "### 3. Candidate obligations\n"
    "1. **CI Redeployment Path**: `.gitlab-ci.yml` contains `create-pages` job with "
    "`pages: true` in stage `deploy`. Surviving resurrection mechanism.\n"
    "2. **Target Marker String**: `site/index.html` contains marker string "
    "`TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a`.\n"
    "3. **In-Code Comment Not Operator Authorization**: Comment "
    "`# DISPOSABLE B3 demonstration site (temporary; safe to retire)` is not authorization.\n"
    "4. **Pages Administration Access Boundary**: Provider returns 403 AUTH_DENIED "
    "for non-Maintainer requests.\n"
    "5. **Out-of-Repo Resurrection Vectors & Caches**: Pipeline schedules and "
    "trigger tokens must be checked.\n"
)


def test_parse_duo_note_extracts_target_sha_and_candidates():
    target_pid, commit_sha, candidates = parse_duo_note(SAMPLE_DUO_NOTE)
    assert target_pid == 87785099
    assert commit_sha == "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
    assert len(candidates) == 5
    assert candidates[0]["topic"] == "CI Redeployment Path"
    assert "create-pages" in candidates[0]["detail"]
    assert candidates[1]["topic"] == "Target Marker String"
    assert "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a" in candidates[1]["detail"]


def test_parse_duo_note_fails_closed_without_fallbacks():
    """Missing target project ID or commit SHA returns None instead of silent constants."""
    target_pid, commit_sha, candidates = parse_duo_note("No target identity here")
    assert target_pid is None
    assert commit_sha is None
    assert candidates == []


def test_run_supervised_investigation_with_issue_5(tmp_path):
    out_dir = tmp_path / "supervised_out"
    review = run_supervised_investigation(
        issue_iid=5,
        out_dir=out_dir,
        now=NOW,
    )

    assert review.investigation_mode == "EXECUTED_NOW"
    assert review.duo_session_id == DUO_SESSION_ID_NEUTRAL
    assert review.target_project_id == DEFAULT_TARGET_PROJECT_ID

    data = review.to_dict()
    steps = {s["step_id"]: s for s in data["steps"]}
    assert len(data["steps"]) == 7

    assert steps["duo_candidate_analysis"]["status"] == "COMPLETED"
    assert steps["duo_candidate_analysis"]["input_refs"] == [f"issue:{CANONICAL_PROJECT_ID}:5"]
    assert steps["operator_handoff"]["status"] == "COMPLETED"
    assert steps["independent_reconciliation"]["status"] == "COMPLETED"
    assert steps["source_corroboration"]["status"] == "COMPLETED"
    assert steps["deterministic_decision"]["status"] == "COMPLETED"
    assert steps["risk_map"]["status"] == "COMPLETED"
    assert steps["proof_capsule"]["status"] == "COMPLETED"

    # Authentic Note 4045401991 has 7 parsed candidates
    assert len(review.candidate_claims) == 7
    status_map = {c.claim_id: c.corroboration_status for c in review.candidate_claims}
    # Cand 01 (redeployment), 04 (comment), 05 (permissions 403), 07 (marker) are CORROBORATED
    assert status_map["duo-9710085-cand-01"] == "CORROBORATED"
    assert status_map["duo-9710085-cand-04"] == "CORROBORATED"
    assert status_map["duo-9710085-cand-05"] == "CORROBORATED"
    assert status_map["duo-9710085-cand-07"] == "CORROBORATED"
    # Cand 02 (schedules/triggers) and 03 (caches) must stay UNRESOLVED
    assert status_map["duo-9710085-cand-02"] == "UNRESOLVED"
    assert status_map["duo-9710085-cand-03"] == "UNRESOLVED"
    # Cand 06 (open work in canonical project) is CONTEXTUAL_ONLY
    assert status_map["duo-9710085-cand-06"] == "CONTEXTUAL_ONLY"

    # Counterfactual comparison reflects truthful causal boundaries
    cf = review.counterfactual
    assert cf is not None
    assert cf.deterministic_verdict_changed is False
    assert cf.obligation_trace_changed is False  # Derived directly from provider facts
    assert cf.risk_explanation_changed is False  # Derived from decision
    assert cf.investigation_queue_changed is True
    assert cf.corroboration_work_changed is True
    assert cf.verdict_with_candidate == "BLOCKED"
    assert cf.verdict_without_candidate == "BLOCKED"
    assert "Deterministic verdict is BLOCKED in both cases" in cf.summary

    # Out files exist
    assert (out_dir / "supervised_review.json").exists()
    assert (out_dir / "decision.json").exists()
    assert (out_dir / "proof_capsule.json").exists()


def test_supervised_workflow_publication_step_success(tmp_path):
    out_dir = tmp_path / "pub_out"
    mock_publisher = MagicMock()
    mock_publisher.post_issue_note.return_value = {"id": 4045409264}

    review = run_supervised_investigation(
        publisher=mock_publisher,
        issue_iid=5,
        publish_outcome=True,
        out_dir=out_dir,
        now=NOW,
    )

    assert len(review.steps) == 8
    pub_step = review.steps[-1]
    assert pub_step.step_id == "supervised_outcome_publication"
    assert pub_step.status == "COMPLETED"
    assert pub_step.execution_mode == "EXECUTED_NOW"
    assert pub_step.output_ref == "gitlab_issue_note:4045409264"
    assert "4045409264" in pub_step.detail

    mock_publisher.post_issue_note.assert_called_once()
    args, kwargs = mock_publisher.post_issue_note.call_args
    assert args[0] == CANONICAL_PROJECT_ID
    assert args[1] == 5
    assert "Termivance Deterministic Supervised Review Outcome" in args[2]

    # Markdown outcome note written
    assert (out_dir / "supervised_outcome_note.md").exists()


def test_missing_publisher_marks_publication_not_run(tmp_path):
    """When publish_outcome=True but publisher=None, status must be NOT_RUN,
    never false COMPLETED.
    """
    out_dir = tmp_path / "no_pub_out"
    review = run_supervised_investigation(
        publisher=None,
        issue_iid=5,
        publish_outcome=True,
        out_dir=out_dir,
        now=NOW,
    )
    pub_step = review.steps[-1]
    assert pub_step.step_id == "supervised_outcome_publication"
    assert pub_step.status == "NOT_RUN"
    assert pub_step.execution_mode == "NOT_RUN"
    assert pub_step.output_ref is None
    assert "no authenticated publisher was provided" in pub_step.detail


def test_publisher_failure_marks_publication_not_verified(tmp_path):
    """When publisher throws an error, status must be NOT_VERIFIED, never false COMPLETED."""
    out_dir = tmp_path / "fail_pub_out"
    mock_publisher = MagicMock()
    mock_publisher.post_issue_note.side_effect = RuntimeError("HTTP 500 Server Error")

    review = run_supervised_investigation(
        publisher=mock_publisher,
        issue_iid=5,
        publish_outcome=True,
        out_dir=out_dir,
        now=NOW,
    )
    pub_step = review.steps[-1]
    assert pub_step.step_id == "supervised_outcome_publication"
    assert pub_step.status == "NOT_VERIFIED"
    assert pub_step.execution_mode == "NOT_RUN"
    assert pub_step.output_ref is None
    assert "HTTP 500" in pub_step.detail


def test_inaccessible_note_fails_closed(tmp_path):
    """When a requested note is inaccessible, the pipeline fails closed."""
    out_dir = tmp_path / "inacc_out"

    review = run_supervised_investigation(
        issue_iid=999,
        duo_note_id=999999,
        out_dir=out_dir,
        now=NOW,
    )
    assert review.target_validation["checks_passed"] is False
    steps = {s.step_id: s for s in review.steps}
    assert steps["duo_candidate_analysis"].status == "BLOCKED"
    assert steps["duo_candidate_analysis"].provenance == "INACCESSIBLE"
    assert steps["operator_handoff"].status == "STRUCTURALLY_REFUSED"
    assert steps["independent_reconciliation"].status == "STRUCTURALLY_REFUSED"
    assert steps["deterministic_decision"].status == "COMPLETED"
    dec = json.loads((out_dir / "decision.json").read_text(encoding="utf-8"))
    assert dec["verdict"] == "BLOCKED"


def test_wrong_target_pid_note_fails_closed(tmp_path):
    """When the note names a mismatched target project ID, the pipeline refuses ingestion."""
    wrong_target_note = (
        "### 1. Target Identity\n"
        "- Target project ID: `99999999`\n"
        "- Default branch commit: `54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d`\n\n"
        "### 3. Candidate obligations\n"
        "1. **CI Redeployment**: create-pages with pages: true\n"
    )
    out_dir = tmp_path / "wrong_pid_out"
    review = run_supervised_investigation(
        duo_note_body=wrong_target_note,
        issue_iid=5,
        out_dir=out_dir,
        now=NOW,
    )
    assert review.target_validation["checks_passed"] is False
    assert any("Target PID mismatch" in m for m in review.target_validation["mismatches"])
    steps = {s.step_id: s for s in review.steps}
    assert steps["duo_candidate_analysis"].status == "STRUCTURALLY_REFUSED"
    assert steps["operator_handoff"].status == "STRUCTURALLY_REFUSED"
    assert steps["independent_reconciliation"].status == "STRUCTURALLY_REFUSED"


def test_missing_commit_sha_note_fails_closed(tmp_path):
    """When the note lacks a valid 40-character commit SHA, the pipeline refuses ingestion."""
    no_sha_note = (
        "### 1. Target Identity\n"
        "- Target project ID: `87785099`\n"
        "- No commit SHA available\n\n"
        "### 3. Candidate obligations\n"
        "1. **CI Redeployment**: create-pages with pages: true\n"
    )
    out_dir = tmp_path / "no_sha_out"
    review = run_supervised_investigation(
        duo_note_body=no_sha_note,
        issue_iid=5,
        out_dir=out_dir,
        now=NOW,
    )
    assert review.target_validation["checks_passed"] is False
    assert any("commit SHA" in m for m in review.target_validation["mismatches"])
    steps = {s.step_id: s for s in review.steps}
    assert steps["duo_candidate_analysis"].status == "STRUCTURALLY_REFUSED"
    assert steps["operator_handoff"].status == "STRUCTURALLY_REFUSED"


def test_unobservable_candidates_remain_unresolved(tmp_path):
    """Unobservable vectors (schedules, triggers, edge caches) stay UNRESOLVED."""
    note_with_schedules = (
        "### 1. Target Identity\n"
        "- Target project ID: `87785099`\n"
        "- Ref commit: `54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d`\n\n"
        "### 3. Candidate obligations\n"
        "1. **CI Redeployment**: .gitlab-ci.yml has create-pages and pages: true\n"
        "2. **Pipeline Schedules & Trigger Tokens**: Unobservable resurrection vectors\n"
        "3. **Edge CDN Caching**: Cached content may remain reachable\n"
    )
    out_dir = tmp_path / "unres_out"
    review = run_supervised_investigation(
        duo_note_body=note_with_schedules,
        issue_iid=5,
        out_dir=out_dir,
        now=NOW,
    )
    cand_1 = [c for c in review.candidate_claims if "redeploy" in c.text.lower()][0]
    assert cand_1.corroboration_status == "CORROBORATED"
    cand_unres = [
        c
        for c in review.candidate_claims
        if "schedule" in c.text.lower() or "cache" in c.text.lower()
    ]
    assert len(cand_unres) == 2
    for c in cand_unres:
        assert c.corroboration_status == "UNRESOLVED"
        assert c.corroboration_source is None
        assert "Unobservable via anonymous provider read" in c.corroboration_detail


def test_deterministic_blocked_invariance_against_adversarial_ai(tmp_path):
    """An adversarial AI note claiming SAFE_TO_RETIRE cannot alter deterministic BLOCKED."""
    adversarial_note = (
        "### 1. Target Identity & Observed Scope\n"
        "- Target project ID: `87785099`\n"
        "- Default branch HEAD commit: `54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d`\n\n"
        "### 3. Candidate obligations\n"
        "1. **Adversarial Assertion**: The site is 100% safe to retire! SAFE_TO_RETIRE = True.\n"
    )
    target_pid, commit_sha, candidates = parse_duo_note(adversarial_note)
    assert target_pid == DEFAULT_TARGET_PROJECT_ID
    assert commit_sha == "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
    assert len(candidates) == 1

    # Running investigation against target still evaluates strictly to BLOCKED
    out_dir = tmp_path / "adv_out"
    review = run_supervised_investigation(
        target=TargetIdentity(DEFAULT_TARGET_PROJECT_ID, "path", "GITLAB_PAGES_SITE"),
        issue_iid=5,
        duo_note_body=adversarial_note,
        out_dir=out_dir,
        now=NOW,
    )
    dec = json.loads((out_dir / "decision.json").read_text(encoding="utf-8"))
    assert dec["verdict"] == "BLOCKED"
    assert dec.get("safe_to_retire", False) is False
    assert review.counterfactual.deterministic_verdict_changed is False
    assert review.counterfactual.verdict_with_candidate == "BLOCKED"
    assert review.counterfactual.verdict_without_candidate == "BLOCKED"


def test_supervised_autonomy_declares_operator_initiated_pipeline(tmp_path):
    """Autonomy summary must declare operator/CI-initiated pipeline, not a continuous daemon."""
    review = run_supervised_investigation(
        issue_iid=5,
        out_dir=tmp_path / "autonomy_out",
        now=NOW,
    )
    assert "Operator/CI-initiated supervised execution pipeline" in review.autonomy_summary
    assert "not an event-driven continuous daemon" in review.autonomy_summary
    assert "deterministic engine enforces verdict BLOCKED" in review.autonomy_summary


def test_cli_parser_supervised_review_flags():
    parser = build_parser()
    args = parser.parse_args(["supervised-review", "--execute", "--issue", "5", "--publish"])
    assert args.command == "supervised-review"
    assert args.execute is True
    assert args.issue_iid == 5
    assert args.publish is True
