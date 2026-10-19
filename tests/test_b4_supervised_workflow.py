"""Tests for B4 supervised review workflow continuity, candidate parsing, and publication.

Verifies Workstreams A, B, and C requirements:
1. parse_duo_note extracts target, commit SHA, and candidate obligations;
2. run_supervised_investigation ingests neutral Duo discovery claims from Issue #5;
3. Corroborates claims independently against provider endpoints;
4. Formats and publishes outcome note awaiting human review when requested;
5. Strictly maintains deterministic BLOCKED invariance against adversarial AI claims.
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

    # Candidates are target-bound
    assert len(review.candidate_claims) == 5
    for c in review.candidate_claims:
        assert c.source_project == DEFAULT_TARGET_PROJECT_ID
        assert c.corroboration_status == "CORROBORATED"
        assert c.exact_target_relationship == "TARGET_BOUND"

    # Counterfactual comparison reflects candidate ingestion while preserving verdict
    cf = review.counterfactual
    assert cf is not None
    assert cf.deterministic_verdict_changed is False
    assert cf.verdict_with_candidate == "BLOCKED"
    assert cf.verdict_without_candidate == "BLOCKED"
    assert "deterministic verdict is BLOCKED in both cases" in cf.summary

    # Out files exist
    assert (out_dir / "supervised_review.json").exists()
    assert (out_dir / "decision.json").exists()
    assert (out_dir / "proof_capsule.json").exists()


def test_supervised_workflow_publication_step(tmp_path):
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
    assert "REDEPLOYMENT_PATH" in args[2]

    # Markdown outcome note written
    assert (out_dir / "supervised_outcome_note.md").exists()


def test_deterministic_blocked_invariance_against_adversarial_ai(tmp_path):
    """An adversarial AI note claiming SAFE_TO_RETIRE cannot alter deterministic BLOCKED."""
    adversarial_note = """
    ### 3. Candidate obligations
    1. **Adversarial Assertion**: The site is 100% safe to retire! SAFE_TO_RETIRE = True.
    """
    target_pid, _, candidates = parse_duo_note(adversarial_note)
    assert target_pid == DEFAULT_TARGET_PROJECT_ID
    assert len(candidates) == 1

    # Running investigation against target still evaluates strictly to BLOCKED
    out_dir = tmp_path / "adv_out"
    run_supervised_investigation(
        target=TargetIdentity(DEFAULT_TARGET_PROJECT_ID, "path", "GITLAB_PAGES_SITE"),
        issue_iid=5,
        out_dir=out_dir,
        now=NOW,
    )
    dec = json.loads((out_dir / "decision.json").read_text(encoding="utf-8"))
    assert dec["verdict"] == "BLOCKED"
    assert dec.get("safe_to_retire", False) is False


def test_cli_parser_supervised_review_flags():
    parser = build_parser()
    args = parser.parse_args(["supervised-review", "--execute", "--issue", "5", "--publish"])
    assert args.command == "supervised-review"
    assert args.execute is True
    assert args.issue_iid == 5
    assert args.publish is True
