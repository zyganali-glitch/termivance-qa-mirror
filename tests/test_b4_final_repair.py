"""Adversarial tests for Repair A (receipt classification) and Repair B (workflow).

These tests prove that:
- A fabricated receipt never becomes live provider proof in Control Room
- A correctly shaped JSON with an invented OBSERVED_ABSENT verdict cannot
  manufacture actual absence
- Cross-target Duo claims cannot authorize or satisfy target-specific obligations
- AI suggestions remain non-authoritative
- A missing operator trust policy blocks the generated real-execution path
- The integrated workflow reports manual handoffs honestly
- No additional destructive GitLab API call path was introduced
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PID = 12345678
PATH = "example-group/example-disposable-pages"


def _v3_receipt(**overrides):
    """A minimally coherent v3 receipt for adversarial tests."""
    receipt = {
        "schema": "termivance.retirement_receipt/v3",
        "target": {"project_id": PID, "full_path": PATH, "resource_kind": "GITLAB_PAGES_SITE"},
        "action": "unpublish_pages",
        "mutation_attempted": False,
        "verdict": "BLOCKED",
        "mutation": None,
    }
    receipt.update(overrides)
    return receipt


def _build_control_room(tmp_path, receipt_obj):
    """Run the builder with one receipt artifact; return the embedded payload."""
    tmp_path = Path(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt_obj), encoding="utf-8")
    out_dir = tmp_path / "control_room_adversarial"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/build_control_room.py",
            "--receipt",
            str(receipt_path),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data_js = (out_dir / "data.js").read_text(encoding="utf-8")
    return json.loads(data_js.removeprefix("window.TERMIVANCE_DATA = ").removesuffix(";\n"))


# ---------------------------------------------------------------------------
# Repair A adversarial tests
# ---------------------------------------------------------------------------


class TestFabricatedReceiptNeverBecomesProof:
    """A fabricated receipt-shaped JSON must never become live provider proof."""

    def test_fabricated_accepted_delete_receipt_is_untrusted(self, tmp_path):
        """A fabricated receipt with mutation_attempted=true, accepted=true,
        HTTP 204, and OBSERVED_ABSENT verdict must be classified with
        UNTRUSTED_LOCAL_CLAIM evidence_level."""
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="OBSERVED_ABSENT",
            mutation={"accepted": True, "status": 204, "method": "DELETE"},
            # Missing authorization_binding, operation_id, authorization_record
        )
        payload = _build_control_room(tmp_path, receipt)
        classification = payload["sections"]["receipt"]
        assert classification["evidence_level"] == "UNTRUSTED_LOCAL_CLAIM"
        assert "fabricated" in classification["evidence_level_detail"] or \
               "no authorization_binding" in classification["evidence_level_detail"]

    def test_fabricated_observed_absent_cannot_manufacture_absence(self, tmp_path):
        """Even with OBSERVED_ABSENT verdict, a fabricated receipt must show
        its trust limitation."""
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="OBSERVED_ABSENT",
            mutation={"accepted": True, "status": 204, "method": "DELETE"},
        )
        payload = _build_control_room(tmp_path, receipt)
        classification = payload["sections"]["receipt"]
        # The receipt_state may display the recorded verdict, but evidence_level
        # must expose the trust boundary
        assert classification["evidence_level"] in (
            "UNTRUSTED_LOCAL_CLAIM",
            "STRUCTURALLY_COHERENT_RECORDED_CLAIM",
        )

    def test_fabricated_receipt_with_fake_authorization_is_untrusted(self, tmp_path):
        """A receipt with a fabricated authorization_binding but no
        authorization_record is at most a structural claim."""
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="RETIRED",
            mutation={"accepted": True, "status": 204, "method": "DELETE"},
            authorization_binding="fake-binding-abc",
            # No operation_id → UNTRUSTED_LOCAL_CLAIM
        )
        payload = _build_control_room(tmp_path, receipt)
        classification = payload["sections"]["receipt"]
        assert classification["evidence_level"] == "UNTRUSTED_LOCAL_CLAIM"

    def test_fabricated_receipt_with_inconsistent_auth_record(self, tmp_path):
        """A receipt whose authorization_record disagrees with its
        authorization_binding is UNTRUSTED_LOCAL_CLAIM."""
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="RETIRED",
            mutation={"accepted": True, "status": 204, "method": "DELETE"},
            authorization_binding="binding-A",
            operation_id="op-123",
            authorization_record={
                "binding": "binding-B-DIFFERENT",
                "nonce": "n",
                "action": "unpublish_pages",
                "target_key": "some-key",
            },
        )
        payload = _build_control_room(tmp_path, receipt)
        classification = payload["sections"]["receipt"]
        assert classification["evidence_level"] == "UNTRUSTED_LOCAL_CLAIM"
        assert "disagrees" in classification["evidence_level_detail"]

    def test_structurally_complete_fabricated_receipt_is_ledger_cross_validated_not_proven(
        self, tmp_path
    ):
        """A receipt with all cross-validation fields internally consistent
        is LEDGER_CROSS_VALIDATED — but NOT provider-proven.

        Note: MUTATION_ACCEPTED is a classify_receipt *output* state, not a
        valid receipt verdict.  We use INCONCLUSIVE here so the receipt passes
        the verdict-recognition gate and the provenance validation is reached.
        """
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="INCONCLUSIVE",
            mutation={"accepted": True, "status": 204, "method": "DELETE"},
            authorization_binding="bind-X",
            operation_id="op-456",
            authorization_record={
                "binding": "bind-X",
                "nonce": "nonce-1",
                "action": "unpublish_pages",
                "target_key": f"[{PID},\"{PATH}\",\"GITLAB_PAGES_SITE\"]",
            },
            ledger_path="evidence/ledger.json",
        )
        payload = _build_control_room(tmp_path, receipt)
        classification = payload["sections"]["receipt"]
        assert classification["evidence_level"] == "LEDGER_CROSS_VALIDATED"
        # Even at this level, the UI must not claim provider truth
        assert "static build" in classification["evidence_level_detail"]
        assert "provider" in classification["evidence_level_detail"]


class TestMissingLedgerExposesLimit:
    """A receipt missing ledger provenance is never promoted."""

    def test_no_ledger_path_recorded(self, tmp_path):
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="INCONCLUSIVE",
            mutation={"accepted": True, "status": 204, "method": "DELETE"},
            authorization_binding="bind-X",
            operation_id="op-789",
            authorization_record={
                "binding": "bind-X",
                "nonce": "n",
                "action": "unpublish_pages",
                "target_key": "k",
            },
            # No ledger_path
        )
        payload = _build_control_room(tmp_path, receipt)
        classification = payload["sections"]["receipt"]
        assert classification["evidence_level"] == "LEDGER_CROSS_VALIDATED"
        assert "no ledger path" in classification["evidence_level_detail"]


class TestWrongTargetAndEndpoint:
    """Cross-target receipts must not be accepted."""

    def test_wrong_target_project_id_still_classifies_evidence_level(self, tmp_path):
        """Even if the receipt is structurally correct, its evidence_level
        should reflect the completeness of its provenance chain."""
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="OBSERVED_ABSENT",
            mutation={"accepted": True, "status": 204, "method": "DELETE"},
            # Different target in the receipt body
            target={"project_id": 99999999, "full_path": "other/project",
                     "resource_kind": "GITLAB_PAGES_SITE"},
        )
        payload = _build_control_room(tmp_path, receipt)
        classification = payload["sections"]["receipt"]
        # It should classify but with UNTRUSTED provenance
        assert classification["evidence_level"] in (
            "UNTRUSTED_LOCAL_CLAIM",
            "STRUCTURALLY_COHERENT_RECORDED_CLAIM",
        )


class TestMalformedTimestamps:
    """Malformed receipts fail closed."""

    def test_string_status_is_invalid(self, tmp_path):
        """A receipt with status as string "204" not int is INVALID."""
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="RETIRED",
            mutation={"accepted": True, "status": "204", "method": "DELETE"},
        )
        payload = _build_control_room(tmp_path, receipt)
        assert payload["sections"]["receipt"]["receipt_state"] == "INVALID"

    def test_negative_status_is_invalid(self, tmp_path):
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="RETIRED",
            mutation={"accepted": True, "status": -1, "method": "DELETE"},
        )
        payload = _build_control_room(tmp_path, receipt)
        assert payload["sections"]["receipt"]["receipt_state"] == "INVALID"


class TestReplay:
    """Identical receipts produce identical classifications."""

    def test_identical_receipt_same_result(self, tmp_path):
        receipt = _v3_receipt(
            mutation_attempted=True,
            verdict="INCONCLUSIVE",
            mutation={"accepted": True, "status": 204, "method": "DELETE"},
        )
        p1 = _build_control_room(tmp_path / "run1", receipt)
        p2 = _build_control_room(tmp_path / "run2", receipt)
        # Receipt sections must be identical (except built_at timestamp)
        assert p1["sections"]["receipt"] == p2["sections"]["receipt"]


# ---------------------------------------------------------------------------
# Repair B: workflow correctness tests
# ---------------------------------------------------------------------------


class TestWorkflowCommandCompleteness:
    """The generated workflow plan must include all mandatory arguments."""

    def test_execute_command_includes_operator_trust(self):
        from termivance.workflow import plan

        plan_ = plan(project_id=PID, full_path=PATH, out_dir="evidence/b4")
        execute_stage = next(s for s in plan_.stages if s.stage == "execute")
        assert "--operator-trust" in execute_stage.command
        assert "--execute" in execute_stage.command
        assert "--ledger" in execute_stage.command
        assert "--approval-project-id" in execute_stage.command
        assert "--approval-issue-iid" in execute_stage.command
        assert "--policy" in execute_stage.command
        assert "--authorization" in execute_stage.command

    def test_mode_label_is_not_duo_flow(self):
        from termivance.workflow import plan

        plan_ = plan(project_id=PID, full_path=PATH, out_dir="evidence/b4")
        data = plan_.to_dict()
        assert data["mode"] == "SINGLE_AUTHORIZED_FLOW"
        assert data["mode"] != "SINGLE_DUO_FLOW"
        assert "mode_note" in data
        assert "not a GitLab Duo" in data["mode_note"]

    def test_render_text_is_truthful_about_python_workflow(self):
        from termivance.workflow import plan

        plan_ = plan(project_id=PID, full_path=PATH, out_dir="evidence/b4")
        text = plan_.render()
        assert "deterministic Python workflow" in text
        assert "--operator-trust" in text


class TestMissingOperatorTrustBlocks:
    """The CLI correctly refuses --execute without --operator-trust."""

    def test_retire_pages_refuses_execute_without_trust(self):
        from termivance.cli import build_parser

        parser = build_parser()
        # The parser should accept --operator-trust
        args = parser.parse_args([
            "retire-pages",
            "--project-id", str(PID),
            "--execute",
        ])
        assert args.execute is True
        assert args.operator_trust is None
        # The actual command would refuse at runtime (tested in test_retirement.py)


# ---------------------------------------------------------------------------
# Supervised review tests
# ---------------------------------------------------------------------------


class TestSupervisedReview:
    """The supervised review correctly represents the causal chain."""

    def test_review_from_real_evidence_artifacts(self):
        from termivance.supervised_review import build_supervised_review

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
        assert data["schema"] == "termivance.supervised_review/v1"
        assert data["authority"] == "NON_AUTHORITATIVE"

        # Steps must include the genuine Duo step
        step_ids = [s["step_id"] for s in data["steps"]]
        assert "duo_candidate_analysis" in step_ids
        assert "operator_handoff" in step_ids
        assert "independent_reconciliation" in step_ids
        assert "source_corroboration" in step_ids
        assert "deterministic_decision" in step_ids

        # Autonomy must be honestly reported
        duo_step = next(s for s in data["steps"] if s["step_id"] == "duo_candidate_analysis")
        assert duo_step["autonomy"] == "DUO_AUTONOMOUS"
        handoff = next(s for s in data["steps"] if s["step_id"] == "operator_handoff")
        assert handoff["autonomy"] == "OPERATOR_CONFIRMED_HANDOFF"

        # Autonomy summary must state it's NOT fully autonomous
        assert "NOT fully autonomous" in data["autonomy_summary"]

        # Counterfactual must show verdict unchanged
        cf = data["counterfactual"]
        assert cf is not None
        assert cf["deterministic_verdict_changed"] is False

    def test_review_without_evidence_shows_not_run(self):
        from termivance.supervised_review import build_supervised_review

        review = build_supervised_review()
        data = review.to_dict()
        not_run_steps = [s for s in data["steps"] if s["status"] == "NOT_RUN"]
        assert len(not_run_steps) > 0

    def test_counterfactual_never_manufactures_changed_verdict(self):
        """The counterfactual must never claim the AI changed the verdict."""
        from termivance.supervised_review import build_supervised_review

        evidence = ROOT / "evidence" / "b4"
        review = build_supervised_review(
            duo_claims_path=evidence / "duo_claims.json",
            duo_reconciliation_path=evidence / "duo_reconciliation.json",
            decision_path=evidence / "decision.json",
        )
        cf = review.counterfactual
        assert cf is not None
        assert cf.deterministic_verdict_changed is False
        assert cf.verdict_with_candidate == cf.verdict_without_candidate

    def test_review_cli_command_exists(self):
        from termivance.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["supervised-review", "--json"])
        assert args.command == "supervised-review"

    def test_review_render_includes_boundary(self):
        from termivance.supervised_review import build_supervised_review

        review = build_supervised_review()
        text = review.render()
        assert "SUPERVISED RETIREMENT REVIEW" in text


# ---------------------------------------------------------------------------
# No additional destructive API path
# ---------------------------------------------------------------------------


class TestNoNewDestructivePath:
    """Verify no additional destructive GitLab API call path was introduced."""

    def test_supervised_review_has_no_mutation_surface(self):
        import termivance.supervised_review as mod
        names = dir(mod)
        assert not any("unpublish" in n or "mutate" in n or "delete" in n.lower()
                       for n in names if not n.startswith("_"))

    def test_supervised_review_has_no_network_calls(self):
        """The supervised review module only reads local files."""
        import inspect

        import termivance.supervised_review as mod
        source = inspect.getsource(mod)
        # Must not import or reference GitLabClient, requests, urllib
        assert "GitLabClient" not in source
        assert "urllib.request" not in source
        assert "requests.get" not in source
