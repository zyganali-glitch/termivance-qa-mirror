import json
from datetime import UTC, datetime, timedelta

import pytest

from termivance.graph import (
    Dependency,
    DependencyKind,
    Evidence,
    EvidenceClass,
    EvidenceKind,
    Graph,
    GraphError,
    ObligationKind,
    Relation,
)
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


def make_evidence(eid: str, target: TargetIdentity, **over) -> Evidence:
    base: dict[str, object] = {
        "evidence_id": eid,
        "kind": EvidenceKind.PROJECT_IDENTITY,
        "classification": EvidenceClass.LIVE,
        "target": target,
        "method": "GET",
        "endpoint": f"/projects/{target.project_id}",
        "status": 200,
        "observed_at": NOW,
        "fresh_until": NOW + timedelta(minutes=15),
        "detail": {"project_id": target.project_id},
    }
    base.update(over)
    return Evidence(**base)  # type: ignore[arg-type]


def test_build_and_serialize_is_deterministic(pages_target):
    g = Graph()
    tnode = g.add_target(pages_target)
    oid = g.add_obligation("obl:scope", ObligationKind.TARGET_SCOPE, "scope")
    eid = g.add_evidence(make_evidence("ev:identity", pages_target))
    g.link(tnode, Relation.HAS_OBLIGATION, oid)
    g.link(oid, Relation.REQUIRES_EVIDENCE, eid)
    g.validate()
    assert g.to_json() == g.to_json()
    payload = json.loads(g.to_json())
    assert payload["schema"].startswith("termivance.retirement_obligation_graph")
    assert payload["targets"][0]["project_id"] == pages_target.project_id


def test_duplicate_obligation_id_refused(pages_target):
    g = Graph()
    g.add_target(pages_target)
    g.add_obligation("obl:x", ObligationKind.TARGET_SCOPE, "a")
    with pytest.raises(GraphError):
        g.add_obligation("obl:x", ObligationKind.TARGET_SCOPE, "b")


def test_contradictory_target_refused(pages_target):
    g = Graph()
    g.add_target(pages_target)
    other = TargetIdentity(pages_target.project_id, "different/path", pages_target.resource_kind)
    with pytest.raises(GraphError):
        g.add_target(other)


def test_edge_to_unknown_node_refused(pages_target):
    g = Graph()
    tnode = g.add_target(pages_target)
    with pytest.raises(GraphError):
        g.link(tnode, Relation.HAS_OBLIGATION, "obl:missing")


def test_non_read_only_evidence_method_refused(pages_target):
    with pytest.raises(GraphError):
        make_evidence("ev:x", pages_target, method="POST")


def test_evidence_bound_to_unknown_target_fails_validation(pages_target):
    g = Graph()
    g.add_target(pages_target)
    other = TargetIdentity(999, "other/proj", "GITLAB_PAGES_SITE")
    g.add_evidence(make_evidence("ev:y", other))
    with pytest.raises(GraphError):
        g.validate()


def test_dependency_unknown_evidence_fails_validation(pages_target):
    g = Graph()
    g.add_target(pages_target)
    g.add_dependency(
        Dependency("dep:x", DependencyKind.OPEN_WORK_ITEM, "x", True, evidence_id="ev:missing")
    )
    with pytest.raises(GraphError):
        g.validate()


def test_evidence_digest_is_stable_and_sensitive(pages_target):
    a = make_evidence("ev:z", pages_target)
    b = make_evidence("ev:z", pages_target)
    c = make_evidence("ev:z", pages_target, status=404)
    assert a.digest() == b.digest()
    assert a.digest() != c.digest()


def test_fresh_until_before_observed_refused(pages_target):
    with pytest.raises(GraphError):
        make_evidence("ev:z", pages_target, fresh_until=NOW - timedelta(seconds=1))
