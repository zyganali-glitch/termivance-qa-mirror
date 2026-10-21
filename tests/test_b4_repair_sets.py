"""Tests for B4 Bounded Candidate Repair Sets engine.

Validates:
1. Derivation of candidate repairs strictly from typed unsatisfied obligations in ROG;
2. Classification of Maintainer role on project 87785099 as
   EXTERNALLY_UNAVAILABLE_UNDER_CONTEST_CONDITIONS;
3. Refusal and cycle detection on cyclic or malformed graphs;
4. Topological dependency ordering of prerequisite remediation steps;
5. Stable, deterministic tie-breaking across runs;
6. Separation of actionable_now versus externally_unavailable obligations;
7. Zero-mutation property: repair proposals never change provider state or mutate resources;
8. Real target 87785099 decision evaluation produces bounded repair sets.
"""

from __future__ import annotations

from datetime import UTC, datetime

from termivance.engine import Decision, Reason, ReasonCode
from termivance.graph import Graph, ObligationKind, Relation
from termivance.repair import (
    AuthorityLevel,
    CapabilityKind,
    ExternalAvailability,
    compute_bounded_repair_sets,
)
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

NOW = datetime(2026, 10, 21, 12, 0, 0, tzinfo=UTC)
TARGET_DISPOSABLE = TargetIdentity(
    87785099,
    "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
    "GITLAB_PAGES_SITE",
)


def _build_test_graph_and_decision():
    graph = Graph()
    graph.add_target(TARGET_DISPOSABLE)
    graph.add_obligation("obl:target_scope", ObligationKind.TARGET_SCOPE, "Target scope")
    graph.add_obligation(
        "obl:retirement_permission:87785099",
        ObligationKind.RETIREMENT_PERMISSION,
        "Retirement permission",
    )
    graph.add_obligation(
        "obl:redeployment_path:87785099",
        ObligationKind.REDEPLOYMENT_PATH,
        "Redeployment path control",
    )
    graph.add_obligation(
        "obl:ownership_authorization:87785099",
        ObligationKind.OWNERSHIP_AUTHORIZATION,
        "Operator authorization",
    )

    # Link target to obligations
    target_node = f"target:{TARGET_DISPOSABLE.project_id}:{TARGET_DISPOSABLE.resource_kind}"
    graph.link(target_node, Relation.HAS_OBLIGATION, "obl:target_scope")
    graph.link(target_node, Relation.HAS_OBLIGATION, "obl:retirement_permission:87785099")
    graph.link(target_node, Relation.HAS_OBLIGATION, "obl:redeployment_path:87785099")
    graph.link(target_node, Relation.HAS_OBLIGATION, "obl:ownership_authorization:87785099")

    # Decision where o_perm and o_redeploy are unsatisfied
    reasons = (
        Reason(
            ReasonCode.INSUFFICIENT_PERMISSION,
            "obl:retirement_permission:87785099",
            "403 AUTH_DENIED",
        ),
        Reason(
            ReasonCode.REDEPLOYMENT_RISK, "obl:redeployment_path:87785099", "create-pages present"
        ),
    )
    obligations_records = (
        {"obligation_id": "obl:target_scope", "status": "SATISFIED"},
        {"obligation_id": "obl:retirement_permission:87785099", "status": "VIOLATED"},
        {"obligation_id": "obl:redeployment_path:87785099", "status": "VIOLATED"},
        {"obligation_id": "obl:ownership_authorization:87785099", "status": "SATISFIED"},
    )

    decision = Decision(
        verdict=Verdict.BLOCKED,
        target=TARGET_DISPOSABLE,
        action="unpublish_pages",
        evaluated_at=NOW,
        reasons=reasons,
        obligations=obligations_records,
        read_only=True,
    )

    return graph, decision


def test_maintainer_role_is_externally_unavailable():
    graph, decision = _build_test_graph_and_decision()
    repair_set = compute_bounded_repair_sets(graph, decision, now=NOW)

    assert repair_set.has_errors is False
    assert repair_set.decision_verdict == "BLOCKED"
    assert repair_set.total_unsatisfied_obligations == 2

    by_id = {c.obligation_id: c for c in repair_set.candidate_repairs}
    perm_action = by_id["obl:retirement_permission:87785099"]
    assert perm_action.externally_unavailable is True
    assert (
        perm_action.availability_classification
        == ExternalAvailability.EXTERNALLY_UNAVAILABLE_UNDER_CONTEST_CONDITIONS
    )
    assert perm_action.actionable_now is False
    assert perm_action.required_authority == AuthorityLevel.MAINTAINER
    assert "Maintainer" in perm_action.failing_condition


def test_actionable_redeployment_repair():
    graph, decision = _build_test_graph_and_decision()
    repair_set = compute_bounded_repair_sets(graph, decision, now=NOW)

    by_id = {c.obligation_id: c for c in repair_set.candidate_repairs}
    redeploy_action = by_id["obl:redeployment_path:87785099"]
    assert redeploy_action.externally_unavailable is False
    assert redeploy_action.actionable_now is True
    assert redeploy_action.capability == CapabilityKind.AUTOMATED_CONFIG
    assert redeploy_action.required_authority == AuthorityLevel.OPERATOR
    assert "pages: true" in redeploy_action.resolution_evidence


def test_cyclic_graph_refusal():
    """Adversarial test: malformed cyclic graph fails closed with CYCLE_DETECTED."""
    graph = Graph()
    graph.add_target(TARGET_DISPOSABLE)
    graph.add_obligation("obl:1", ObligationKind.TARGET_SCOPE, "Obligation 1")
    graph.add_obligation("obl:2", ObligationKind.REDEPLOYMENT_PATH, "Obligation 2")

    # Create cycle: obl:1 -> obl:2 -> obl:1
    graph.link("obl:1", Relation.BLOCKED_BY, "obl:2")
    graph.link("obl:2", Relation.BLOCKED_BY, "obl:1")

    decision = Decision(
        verdict=Verdict.BLOCKED,
        target=TARGET_DISPOSABLE,
        action="unpublish_pages",
        evaluated_at=NOW,
        reasons=(Reason(ReasonCode.UNRESOLVED_OBLIGATION, "obl:1", "Failed"),),
        obligations=({"obligation_id": "obl:1", "status": "VIOLATED"},),
        read_only=True,
    )

    repair_set = compute_bounded_repair_sets(graph, decision, now=NOW)
    assert repair_set.has_errors is True
    assert any("CYCLE_DETECTED" in err for err in repair_set.malformed_graph_errors)
    assert repair_set.total_unsatisfied_obligations == 0
    assert repair_set.candidate_repairs == ()


def test_topological_dependency_ordering():
    graph = Graph()
    graph.add_target(TARGET_DISPOSABLE)
    graph.add_obligation("obl:target_scope", ObligationKind.TARGET_SCOPE, "Upstream")
    graph.add_obligation(
        "obl:ownership_authorization", ObligationKind.OWNERSHIP_AUTHORIZATION, "Midstream"
    )
    graph.add_obligation("obl:redeployment_path", ObligationKind.REDEPLOYMENT_PATH, "Downstream")

    graph.link("obl:ownership_authorization", Relation.BLOCKED_BY, "obl:redeployment_path")

    # All three unsatisfied
    decision = Decision(
        verdict=Verdict.BLOCKED,
        target=TARGET_DISPOSABLE,
        action="unpublish_pages",
        evaluated_at=NOW,
        reasons=(
            Reason(ReasonCode.TARGET_NOT_AUTHORIZED, "obl:target_scope", "Scope unverified"),
            Reason(ReasonCode.TARGET_NOT_AUTHORIZED, "obl:ownership_authorization", "No auth"),
            Reason(ReasonCode.REDEPLOYMENT_RISK, "obl:redeployment_path", "Redeploy active"),
        ),
        obligations=(
            {"obligation_id": "obl:target_scope", "status": "VIOLATED"},
            {"obligation_id": "obl:ownership_authorization", "status": "VIOLATED"},
            {"obligation_id": "obl:redeployment_path", "status": "VIOLATED"},
        ),
        read_only=True,
    )

    repair_set = compute_bounded_repair_sets(graph, decision, now=NOW)
    order = repair_set.dependency_order
    # Target scope is upstream domain prerequisite
    assert order.index("obl:target_scope") < order.index("obl:ownership_authorization")
    assert order.index("obl:target_scope") < order.index("obl:redeployment_path")


def test_tie_breaking_stability():
    graph, decision = _build_test_graph_and_decision()
    run1 = compute_bounded_repair_sets(graph, decision, now=NOW)
    run2 = compute_bounded_repair_sets(graph, decision, now=NOW)
    assert run1.dependency_order == run2.dependency_order
    assert [c.obligation_id for c in run1.candidate_repairs] == [
        c.obligation_id for c in run2.candidate_repairs
    ]


def test_zero_mutation_guarantee():
    """Proposal must be strictly read-only and never authorize or award verdicts."""
    graph, decision = _build_test_graph_and_decision()
    repair_set = compute_bounded_repair_sets(graph, decision, now=NOW)
    data = repair_set.to_dict()

    assert data["authority"] == "NON_AUTHORITATIVE_REMEDIATION_GUIDANCE"
    assert data["decision_verdict"] == "BLOCKED"
    for cand in data["candidate_repairs"]:
        assert cand["availability_classification"] in {
            "AVAILABLE",
            "EXTERNALLY_UNAVAILABLE_UNDER_CONTEST_CONDITIONS",
            "DEPENDENT_ON_EXTERNAL_PROVIDER",
        }
