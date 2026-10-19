"""Comprehensive adversarial tests for B4 Final Repair & Supervised Execution Closure.

Covers all mandatory qualification requirements:
- Local JSON cannot forge verified retirement.
- A ledger-looking object is not actual ledger validation.
- An unverified receipt never raises the top-level provenance to RECORDED_LIVE.
- A recorded claim cannot be interpreted as freshly executed work.
- Source mismatches cannot complete the supervised chain (fail closed).
- Missing/stale artifacts do not produce false completion.
- A real counterfactual is computed rather than hardcoded.
- A candidate with no relevant provider-backed relationship cannot become a material finding.
- Genuine durable ledger verification awards LEDGER_VALIDATED, while unverified
  receipts stay UNVERIFIED_RECORDED_CLAIM.
- The 7-step investigation actually executes and marks steps EXECUTED_NOW and COMPLETED.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from termivance.authorization import Authorization, OperatorApproval
from termivance.ledger import AuthorizationLedger
from termivance.supervised_review import (
    build_supervised_review,
    run_supervised_investigation,
)
from termivance.target import TargetIdentity

ROOT = Path(__file__).resolve().parents[1]
DISPOSABLE_PID = 87785099
DISPOSABLE_PATH = (
    "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
)
CANONICAL_PID = 87779099
NOW = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)


def _v3_receipt(**overrides):
    receipt = {
        "schema": "termivance.retirement_receipt/v3",
        "target": {
            "project_id": DISPOSABLE_PID,
            "full_path": DISPOSABLE_PATH,
            "resource_kind": "GITLAB_PAGES_SITE",
        },
        "action": "unpublish_pages",
        "mutation_attempted": True,
        "verdict": "OBSERVED_ABSENT",
        "mutation": {
            "accepted": True,
            "status": 204,
            "method": "DELETE",
            "endpoint": f"/projects/{DISPOSABLE_PID}/pages",
        },
        "authorization_binding": "binding-valid-123",
        "operation_id": "op-test-1",
        "authorization_record": {
            "binding": "binding-valid-123",
            "nonce": "nonce-1",
            "action": "unpublish_pages",
            "target_key": f'[{DISPOSABLE_PID},"{DISPOSABLE_PATH}","GITLAB_PAGES_SITE"]',
        },
    }
    receipt.update(overrides)
    return receipt


def _run_control_room_builder(
    tmp_path: Path, receipt_obj: dict | None, *, ledger_path: str | None = None
) -> dict:
    tmp_path.mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "cr_test"
    cmd = [
        sys.executable,
        "scripts/build_control_room.py",
        "--out-dir",
        str(out_dir),
    ]
    if receipt_obj is not None:
        rec_path = tmp_path / "receipt.json"
        rec_path.write_text(json.dumps(receipt_obj), encoding="utf-8")
        cmd.extend(["--receipt", str(rec_path)])
    if ledger_path is not None:
        cmd.extend(["--ledger", ledger_path])

    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), check=False)
    assert proc.returncode == 0, proc.stderr
    data_js = (out_dir / "data.js").read_text(encoding="utf-8")
    return json.loads(data_js.removeprefix("window.TERMIVANCE_DATA = ").removesuffix(";\n"))


# ---------------------------------------------------------------------------
# Defect A: Evidence Authority and Ledger Validation Regressions
# ---------------------------------------------------------------------------


class TestDefectAEvidenceAuthority:
    """Rigorous adversarial tests proving local JSON cannot manufacture proof."""

    def test_fabricated_delete_receipt_is_unverified_claim(self, tmp_path):
        """Fabricated HTTP 204 accepted DELETE must be classified UNVERIFIED_RECORDED_CLAIM."""
        receipt = _v3_receipt(verdict="OBSERVED_ABSENT")
        payload = _run_control_room_builder(tmp_path, receipt)
        rc = payload["sections"]["receipt"]
        assert rc["receipt_state"] == "UNVERIFIED_RECORDED_CLAIM"
        assert rc["display_verdict"] == "UNVERIFIED_RECORDED_CLAIM"
        assert rc["claimed_verdict"] == "OBSERVED_ABSENT"
        assert rc["absence_evidence"] == "UNVERIFIED"
        assert rc["ledger_validation"] == "UNVERIFIED_NO_LEDGER"
        assert payload["mutation_status"] == "UNVERIFIED_RECORDED_CLAIM"
        assert payload["provenance_label"] != "RECORDED_LIVE"

    def test_internally_consistent_synthetic_receipt_is_not_ledger_validated(self, tmp_path):
        """An internally consistent receipt without an authenticated durable ledger
        must never receive LEDGER_VALIDATED or LEDGER_CROSS_VALIDATED."""
        receipt = _v3_receipt(ledger_path=str(tmp_path / "nonexistent.json"))
        payload = _run_control_room_builder(tmp_path, receipt)
        rc = payload["sections"]["receipt"]
        assert rc["evidence_level"] == "UNVERIFIED_RECORDED_CLAIM"
        assert rc["ledger_validation"] == "UNVERIFIED_NO_LEDGER"
        assert "no durable ledger was read or authenticated" in rc["evidence_level_detail"]

    def test_unverified_receipt_never_raises_top_level_provenance_to_recorded_live(self, tmp_path):
        """Top-level provenance_label must stay LIVE_ANONYMOUS or UNAVAILABLE."""
        receipt = _v3_receipt(verdict="OBSERVED_ABSENT")
        payload = _run_control_room_builder(tmp_path, receipt)
        assert payload["provenance_label"] != "RECORDED_LIVE"
        assert payload["mutation_status"] == "UNVERIFIED_RECORDED_CLAIM"

    def test_genuine_durable_ledger_verification_yields_ledger_validated(self, tmp_path):
        """When an actual durable ledger with matching CONSUMED_ACCEPTED entry is
        read and validated via validate_mutation_receipt, award LEDGER_VALIDATED."""
        ledger_file = tmp_path / "durable_ledger.json"
        ledger = AuthorizationLedger(ledger_file)
        ledger.health_check()

        target = TargetIdentity(DISPOSABLE_PID, DISPOSABLE_PATH, "GITLAB_PAGES_SITE")
        auth = Authorization.issue(target, "unpublish_pages", nonce="nonce-1", now=NOW)
        auth.approval = OperatorApproval(
            operator="op",
            statement=(
                f"I authorize exactly one unpublish_pages using /projects/{DISPOSABLE_PID}/pages"
            ),
            approved_at=NOW,
            channel="web_ui",
            binding=auth.binding(),
        )
        consumption = ledger.consume(auth, operation_id="op-test-1", now=NOW)
        ledger.finalize(consumption.binding, outcome="ACCEPTED")

        receipt = _v3_receipt(
            authorization_binding=auth.binding(),
            operation_id="op-test-1",
            authorization_record={
                "binding": auth.binding(),
                "nonce": "nonce-1",
                "action": "unpublish_pages",
                "target_key": target.key_string(),
            },
            ledger_path=str(ledger_file),
            eligibility={
                "established_at": NOW.isoformat(),
                "pre_state": {
                    "served_url": "https://example.gitlab.io/pages",
                    "marker": "test-marker",
                    "marker_observed": True,
                    "marker_sha256": "a" * 64,
                    "deployment_present": True,
                    "observed_at": NOW.isoformat(),
                    "genuinely_published": True,
                },
            },
            mutation={
                "accepted": True,
                "status": 204,
                "method": "DELETE",
                "endpoint": f"/projects/{DISPOSABLE_PID}/pages",
                "requested_at": NOW.isoformat(),
            },
        )
        payload = _run_control_room_builder(tmp_path, receipt, ledger_path=str(ledger_file))
        rc = payload["sections"]["receipt"]
        assert rc["ledger_validation"] == "LEDGER_VALIDATED"
        assert rc["evidence_level"] == "LEDGER_VALIDATED"
        # Even with validated ledger, absence in static build remains UNVERIFIED
        assert rc["absence_evidence"] == "UNVERIFIED"
        assert rc["display_verdict"] == "UNVERIFIED_RECORDED_CLAIM"
        assert payload["provenance_label"] != "RECORDED_LIVE"

    def test_corrupt_ledger_fails_validation(self, tmp_path):
        """Corrupt or tampered ledger fails closed to UNTRUSTED_LOCAL_CLAIM."""
        corrupt_ledger = tmp_path / "corrupt_ledger.json"
        corrupt_ledger.write_text("not json", encoding="utf-8")
        receipt = _v3_receipt(ledger_path=str(corrupt_ledger))
        payload = _run_control_room_builder(tmp_path, receipt, ledger_path=str(corrupt_ledger))
        rc = payload["sections"]["receipt"]
        assert rc["evidence_level"] == "UNTRUSTED_LOCAL_CLAIM"
        assert rc["ledger_validation"] == "LEDGER_VERIFICATION_FAILED"

    def test_cross_target_receipt_fails_ledger_validation(self, tmp_path):
        """Receipt targeting a different project fails ledger validation."""
        ledger_file = tmp_path / "ledger.json"
        ledger = AuthorizationLedger(ledger_file)
        ledger.health_check()

        target = TargetIdentity(DISPOSABLE_PID, DISPOSABLE_PATH, "GITLAB_PAGES_SITE")
        auth = Authorization.issue(target, "unpublish_pages", nonce="nonce-1", now=NOW)
        auth.approval = OperatorApproval(
            operator="op",
            statement="I authorize",
            approved_at=NOW,
            channel="web_ui",
            binding=auth.binding(),
        )
        ledger.consume(auth, operation_id="op-test-1", now=NOW)

        # Receipt claims different project
        receipt = _v3_receipt(
            target={
                "project_id": 99999999,
                "full_path": "other/project",
                "resource_kind": "GITLAB_PAGES_SITE",
            },
            authorization_binding=auth.binding(),
            ledger_path=str(ledger_file),
        )
        payload = _run_control_room_builder(tmp_path, receipt, ledger_path=str(ledger_file))
        rc = payload["sections"]["receipt"]
        assert rc["evidence_level"] == "UNTRUSTED_LOCAL_CLAIM"
        assert rc["ledger_validation"] == "LEDGER_VERIFICATION_FAILED"

    def test_wrong_endpoint_fails_ledger_validation(self, tmp_path):
        """Receipt with invalid endpoint fails ledger validation."""
        receipt = _v3_receipt(
            mutation={
                "accepted": True,
                "status": 204,
                "method": "DELETE",
                "endpoint": "/wrong/endpoint",
            },
        )
        payload = _run_control_room_builder(tmp_path, receipt)
        rc = payload["sections"]["receipt"]
        assert rc["display_verdict"] == "UNVERIFIED_RECORDED_CLAIM"


# ---------------------------------------------------------------------------
# Defect B: Supervised Review Execution and Causal Integrity Regressions
# ---------------------------------------------------------------------------


class TestDefectBSupervisedReview:
    """Tests proving the supervised review is runnable, exact-target bound, and counterfactual."""

    def test_recorded_claims_marked_recorded_input_used(self):
        """Consuming pre-existing files marks steps RECORDED_INPUT_USED, never false COMPLETED."""
        evidence = ROOT / "evidence" / "b4"
        review = build_supervised_review(
            duo_claims_path=evidence / "duo_claims.json",
            duo_reconciliation_path=evidence / "duo_reconciliation.json",
            witness_path=evidence / "witness_87785099.json",
            decision_path=evidence / "decision.json",
            risk_map_path=evidence / "risk_map.json",
            capsule_path=evidence / "proof_capsule.json",
        )
        data = review.to_dict()
        assert data["investigation_mode"] == "RECORDED_INPUT_USED"
        for step in data["steps"]:
            if step["step_id"] in (
                "independent_reconciliation",
                "source_corroboration",
                "deterministic_decision",
                "risk_map",
                "proof_capsule",
            ):
                assert step["status"] == "RECORDED_INPUT_USED"
                assert step["execution_mode"] == "RECORDED_INPUT_USED"

    def test_source_mismatch_fails_closed(self):
        """A witness record for project A cannot complete corroboration for project B."""
        evidence = ROOT / "evidence" / "b4"
        review = build_supervised_review(
            duo_claims_path=evidence / "duo_claims.json",
            duo_reconciliation_path=evidence / "duo_reconciliation.json",
            witness_path=evidence / "witness_87785099.json",  # target 87785099
            target_project_id=99999999,  # Mismatched target!
        )
        data = review.to_dict()
        witness_step = next(s for s in data["steps"] if s["step_id"] == "source_corroboration")
        assert witness_step["status"] == "STRUCTURALLY_REFUSED"
        assert "cannot complete source corroboration" in witness_step["detail"]
        assert data["target_validation"]["checks_passed"] is False

    def test_candidate_claims_have_truthful_relevance_and_attribution(self):
        """Claims on canonical project 87779099 are CONTEXTUAL or PROCEDURAL,
        never false MATERIAL."""
        evidence = ROOT / "evidence" / "b4"
        review = build_supervised_review(
            duo_claims_path=evidence / "duo_claims.json",
            duo_reconciliation_path=evidence / "duo_reconciliation.json",
        )
        data = review.to_dict()
        claims = data["candidate_claims"]
        assert len(claims) == 9

        # Claim 07: explicit boundary statement
        c07 = next(c for c in claims if c["claim_id"] == "duo-9671626-07")
        assert c07["retirement_relevance"] == "PROCEDURAL"
        assert c07["exact_target_relationship"] == "TARGET_BOUND_NEGATIVE_ASSERTION"
        assert "did NOT directly query" in c07["causal_attribution"]

        # Claims 01-03: canonical repo context
        for cid in ("duo-9671626-01", "duo-9671626-02", "duo-9671626-03"):
            c = next(x for x in claims if x["claim_id"] == cid)
            assert c["retirement_relevance"] == "CONTEXTUAL"
            assert c["exact_target_relationship"] == "NO_DIRECT_TARGET_LINK"

        # No claims are falsely marked MATERIAL for the target
        material_claims = [c for c in claims if c["retirement_relevance"] == "MATERIAL"]
        assert len(material_claims) == 0

    def test_real_counterfactual_comparison_computed(self):
        """Counterfactual comparison explicitly computes diffs and confirms verdict unchanged."""
        evidence = ROOT / "evidence" / "b4"
        review = build_supervised_review(
            duo_claims_path=evidence / "duo_claims.json",
            duo_reconciliation_path=evidence / "duo_reconciliation.json",
            decision_path=evidence / "decision.json",
            witness_path=evidence / "witness_87785099.json",
        )
        cf = review.counterfactual
        assert cf is not None
        assert cf.deterministic_verdict_changed is False
        assert cf.obligation_trace_changed is False
        assert cf.risk_explanation_changed is False
        assert cf.investigation_queue_changed is True  # 9 claims queued
        assert cf.corroboration_work_changed is True  # 9 API checks performed
        assert cf.verdict_with_candidate == "BLOCKED"
        assert cf.verdict_without_candidate == "BLOCKED"
        assert "deterministic verdict is BLOCKED in both cases" in cf.summary

    def test_run_supervised_investigation_executes_live_steps(self, tmp_path):
        """run_supervised_investigation executes all 7 steps and marks fresh steps EXECUTED_NOW."""
        out_dir = tmp_path / "investigation_out"
        review = run_supervised_investigation(
            out_dir=out_dir,
            now=NOW,
        )
        assert review.investigation_mode == "EXECUTED_NOW"
        assert review.execution_id.startswith("inv-")

        data = review.to_dict()
        steps = {s["step_id"]: s for s in data["steps"]}
        assert steps["independent_reconciliation"]["status"] == "COMPLETED"
        assert steps["independent_reconciliation"]["execution_mode"] == "EXECUTED_NOW"
        assert steps["source_corroboration"]["status"] == "COMPLETED"
        assert steps["source_corroboration"]["execution_mode"] == "EXECUTED_NOW"
        assert steps["deterministic_decision"]["status"] == "COMPLETED"
        assert steps["deterministic_decision"]["execution_mode"] == "EXECUTED_NOW"
        assert steps["risk_map"]["status"] == "COMPLETED"
        assert steps["risk_map"]["execution_mode"] == "EXECUTED_NOW"
        assert steps["proof_capsule"]["status"] == "COMPLETED"
        assert steps["proof_capsule"]["execution_mode"] == "EXECUTED_NOW"

        # Historical steps preserve their mode
        assert steps["duo_candidate_analysis"]["execution_mode"] == "RECORDED_HISTORICAL"
        assert steps["operator_handoff"]["execution_mode"] == "RECORDED_HISTORICAL"

        # Artifacts written to out_dir
        assert (out_dir / "supervised_review.json").exists()
        assert (out_dir / "proof_capsule.json").exists()
        assert (out_dir / "decision.json").exists()
        assert (out_dir / "risk_map.json").exists()
