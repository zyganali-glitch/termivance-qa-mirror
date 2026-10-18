from datetime import timedelta

import pytest
from conftest import NOW, build_graph, make_snapshot

from termivance.authorization import Authorization, AuthorizationError
from termivance.engine import ReasonCode, evaluate
from termivance.graph import Graph, ObligationKind, Relation
from termivance.policy import Policy
from termivance.target import TargetIdentity
from termivance.verdicts import ModelClaimRejected, Verdict, reject_model_awarded_verdict


def auth_for(target, *, action="unpublish_pages", ttl=timedelta(minutes=10), now=NOW):
    return Authorization.issue(target, action, nonce="n1", now=now, ttl=ttl)


def decide(snapshot, policy, *, now=NOW, authorization=None):
    return evaluate(build_graph(snapshot), policy=policy, action=snapshot.action, now=now,
                    authorization=authorization)


def test_synthetic_safe_case(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, operator_control=True)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.SAFE_TO_RETIRE
    assert decision.read_only is True


def test_complete_ci_without_affirmative_control_is_not_safe(pages_target, allow_policy):
    # CI present, no Pages mechanism, but no affirmative control: NOT SAFE.
    snapshot = make_snapshot(pages_target)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.INCONCLUSIVE
    assert ReasonCode.MISSING_EVIDENCE in {r.code for r in decision.reasons}


def test_includes_make_redeployment_unknown(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, includes_present=True)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.INCONCLUSIVE
    assert ReasonCode.MISSING_EVIDENCE in {r.code for r in decision.reasons}


def test_operator_control_satisfies_redeployment(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, operator_control=True)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.SAFE_TO_RETIRE


def test_protected_target_is_blocked_even_with_authorization(canonical_target):
    policy = Policy(1, "OPERATOR_APPROVED", False, "GITLAB_PAGES",
                    (canonical_target.project_id,), (canonical_target.full_path,),
                    ("unpublish_pages",), True)
    snapshot = make_snapshot(canonical_target)
    decision = decide(snapshot, policy, authorization=auth_for(canonical_target))
    assert decision.verdict == Verdict.BLOCKED
    codes = {r.code for r in decision.reasons}
    assert ReasonCode.PROTECTED_PROJECT in codes


def test_canonical_demo_has_multiple_real_reasons(canonical_target, allow_policy):
    snapshot = make_snapshot(canonical_target, open_retirement_issues=1)
    decision = decide(snapshot, allow_policy)
    assert decision.verdict == Verdict.BLOCKED
    codes = {r.code for r in decision.reasons}
    assert {ReasonCode.PROTECTED_PROJECT, ReasonCode.TARGET_NOT_AUTHORIZED,
            ReasonCode.UNRESOLVED_OBLIGATION}.issubset(codes)


def test_target_not_in_scope_is_blocked(pages_target):
    policy = Policy(
        1, "OPERATOR_APPROVED", False, "GITLAB_PAGES", (), (), ("unpublish_pages",), True
    )
    decision = decide(make_snapshot(pages_target), policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.BLOCKED
    assert ReasonCode.TARGET_NOT_AUTHORIZED in {r.code for r in decision.reasons}


def test_missing_authorization_is_blocked(pages_target, allow_policy):
    decision = decide(make_snapshot(pages_target), allow_policy, authorization=None)
    assert decision.verdict == Verdict.BLOCKED
    assert ReasonCode.TARGET_NOT_AUTHORIZED in {r.code for r in decision.reasons}


def test_expired_authorization_is_blocked(pages_target, allow_policy):
    auth = auth_for(pages_target, ttl=timedelta(seconds=1))
    decision = decide(make_snapshot(pages_target), allow_policy, authorization=auth,
                      now=NOW + timedelta(minutes=5))
    assert decision.verdict == Verdict.BLOCKED


def test_wrong_action_authorization_is_blocked(pages_target, allow_policy):
    auth = auth_for(pages_target, action="delete_project")
    decision = decide(make_snapshot(pages_target), allow_policy, authorization=auth)
    assert decision.verdict == Verdict.BLOCKED


def test_wrong_target_authorization_is_blocked(pages_target, allow_policy):
    other = TargetIdentity(pages_target.project_id, "other/path", pages_target.resource_kind)
    auth = auth_for(other)
    decision = decide(make_snapshot(pages_target), allow_policy, authorization=auth)
    assert decision.verdict == Verdict.BLOCKED


def test_missing_provider_observation_is_inconclusive(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, include_identity=False)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.INCONCLUSIVE
    assert ReasonCode.MISSING_EVIDENCE in {r.code for r in decision.reasons}


def test_stale_observation_is_inconclusive(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target)
    later = NOW + timedelta(minutes=30)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target, now=later),
                      now=later)
    assert decision.verdict == Verdict.INCONCLUSIVE
    assert ReasonCode.STALE_EVIDENCE in {r.code for r in decision.reasons}


def test_identity_mismatch_is_blocked(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, project_id_override=99999999)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.BLOCKED
    assert ReasonCode.IDENTITY_MISMATCH in {r.code for r in decision.reasons}


def test_active_redeployment_is_blocked(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, pages_mechanism=True)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.BLOCKED
    assert ReasonCode.REDEPLOYMENT_RISK in {r.code for r in decision.reasons}


def test_generic_open_issue_does_not_block(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, open_generic_issues=1, operator_control=True)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.SAFE_TO_RETIRE


def test_retirement_open_issue_blocks(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, open_retirement_issues=1, operator_control=True)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.BLOCKED
    assert ReasonCode.UNRESOLVED_OBLIGATION in {r.code for r in decision.reasons}


def test_fresh_recorded_snapshot_cannot_satisfy_live_requirement(pages_target, allow_policy):
    from termivance.graph import EvidenceClass

    snapshot = make_snapshot(
        pages_target, classification=EvidenceClass.RECORDED_LIVE, operator_control=True
    )
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.INCONCLUSIVE
    assert ReasonCode.MISSING_EVIDENCE in {r.code for r in decision.reasons}


def test_missing_ci_config_is_inconclusive(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, include_ci_config=False)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.INCONCLUSIVE
    assert ReasonCode.MISSING_EVIDENCE in {r.code for r in decision.reasons}


def test_no_mandatory_obligations_is_inconclusive(pages_target, allow_policy):
    graph = Graph()
    graph.add_target(pages_target)
    decision = evaluate(graph, policy=allow_policy, now=NOW, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.INCONCLUSIVE


def test_two_targets_is_inconclusive(pages_target, allow_policy):
    graph = Graph()
    graph.add_target(pages_target)
    graph.add_target(TargetIdentity(2, "a/b", "GITLAB_PAGES_SITE"))
    decision = evaluate(graph, policy=allow_policy, now=NOW)
    assert decision.verdict == Verdict.INCONCLUSIVE
    assert ReasonCode.IDENTITY_MISMATCH in {r.code for r in decision.reasons}


def test_fixture_only_evidence_cannot_satisfy_provider_observation(pages_target, allow_policy):
    from termivance.graph import EvidenceClass

    snapshot = make_snapshot(pages_target, classification=EvidenceClass.FIXTURE)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    assert decision.verdict == Verdict.INCONCLUSIVE


def test_replayed_record_is_not_live_and_stale_fails_closed(pages_target, allow_policy):
    from termivance.graph import EvidenceClass

    snapshot = make_snapshot(pages_target, classification=EvidenceClass.RECORDED_LIVE)
    later = NOW + timedelta(minutes=30)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target, now=later),
                      now=later)
    assert decision.verdict == Verdict.INCONCLUSIVE


def test_model_cannot_award_authoritative_verdict():
    reject_model_awarded_verdict(Verdict.BLOCKED)
    reject_model_awarded_verdict(Verdict.INCONCLUSIVE)
    with pytest.raises(ModelClaimRejected):
        reject_model_awarded_verdict(Verdict.SAFE_TO_RETIRE)
    with pytest.raises(ModelClaimRejected):
        reject_model_awarded_verdict(Verdict.OBSERVED_ABSENT)


def test_authorization_from_prose_refused(pages_target):
    with pytest.raises(AuthorizationError):
        Authorization.from_prose("please retire it")


def test_decision_serialization_has_boundaries(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, operator_control=True)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    payload = decision.to_dict()
    assert payload["verdict"] == "SAFE_TO_RETIRE"
    assert payload["read_only"] is True
    assert payload["authoritative"] is True
    assert payload["schema"] == "termivance.retirement_decision/v1"


def test_obligation_summary_present(pages_target, allow_policy):
    snapshot = make_snapshot(pages_target, operator_control=True)
    decision = decide(snapshot, allow_policy, authorization=auth_for(pages_target))
    kinds = {o["kind"] for o in decision.obligations}
    assert ObligationKind.TARGET_SCOPE.value in kinds
    assert ObligationKind.PROVIDER_OBSERVATION.value in kinds


def test_graph_links_cover_target(pages_target):
    graph = build_graph(make_snapshot(pages_target))
    rel = {e.relation for e in graph.edges}
    assert Relation.HAS_OBLIGATION in rel
