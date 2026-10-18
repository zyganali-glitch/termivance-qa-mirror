"""Retirement Obligation Graph.

A small, typed, machine-evaluable graph of *retirement obligations* and the
conditions that permit or prevent a retirement transition. It is deliberately
not a general knowledge graph: nodes are exact GitLab-bound targets,
obligations, evidence observations and dependencies.

Guarantees enforced here:

* stable, explicit node and edge types;
* no contradictory duplicate identities;
* every edge references existing nodes;
* evidence is bound to one exact target and carries provenance;
* deterministic JSON serialization.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from termivance.target import TargetIdentity


class GraphError(ValueError):
    """Raised when the graph is malformed or contradictory."""


class NodeKind(StrEnum):
    TARGET = "TARGET"
    OBLIGATION = "OBLIGATION"
    EVIDENCE = "EVIDENCE"
    DEPENDENCY = "DEPENDENCY"


class Relation(StrEnum):
    HAS_OBLIGATION = "HAS_OBLIGATION"
    REQUIRES_EVIDENCE = "REQUIRES_EVIDENCE"
    BLOCKED_BY = "BLOCKED_BY"
    SATISFIED_BY = "SATISFIED_BY"


class ObligationKind(StrEnum):
    TARGET_SCOPE = "TARGET_SCOPE"
    OWNERSHIP_AUTHORIZATION = "OWNERSHIP_AUTHORIZATION"
    RETIREMENT_PERMISSION = "RETIREMENT_PERMISSION"
    PAGES_PUBLISHED = "PAGES_PUBLISHED"
    PROVIDER_OBSERVATION = "PROVIDER_OBSERVATION"
    IDENTITY_BINDING = "IDENTITY_BINDING"
    DEPENDENT_CONSUMERS = "DEPENDENT_CONSUMERS"
    REDEPLOYMENT_PATH = "REDEPLOYMENT_PATH"
    UNRESOLVED_WORK = "UNRESOLVED_WORK"


class EvidenceClass(StrEnum):
    """Provenance classification.

    A fixture is never LIVE, and a record is never a fresh network read. Only
    ``LIVE`` may satisfy a mandatory live provider-evidence requirement.
    """

    LIVE = "LIVE"
    RECORDED_LIVE = "RECORDED_LIVE"
    FIXTURE = "FIXTURE"
    OPERATOR_CONFIRMED = "OPERATOR_CONFIRMED"


class EvidenceKind(StrEnum):
    PROJECT_IDENTITY = "PROJECT_IDENTITY"
    VISIBILITY = "VISIBILITY"
    BRANCH = "BRANCH"
    CI_CONFIG = "CI_CONFIG"
    PIPELINE = "PIPELINE"
    OPEN_ISSUES = "OPEN_ISSUES"
    PAGES = "PAGES"
    ENVIRONMENT = "ENVIRONMENT"
    #: The acting identity's effective ability to administer Pages on the target.
    EFFECTIVE_PERMISSION = "EFFECTIVE_PERMISSION"
    #: Evidence that the target is genuinely published (deployment + served marker).
    PAGES_DEPLOYMENT = "PAGES_DEPLOYMENT"
    #: An affirmative, operator-supplied control attestation (not provider state).
    REDEPLOYMENT_CONTROL = "REDEPLOYMENT_CONTROL"


class DependencyKind(StrEnum):
    OPEN_WORK_ITEM = "OPEN_WORK_ITEM"
    ACTIVE_REDEPLOYMENT = "ACTIVE_REDEPLOYMENT"
    CONSUMER = "CONSUMER"
    SHARED_RESOURCE = "SHARED_RESOURCE"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class Evidence:
    """One dated provider (or fixture) observation bound to an exact target."""

    evidence_id: str
    kind: EvidenceKind
    classification: EvidenceClass
    target: TargetIdentity
    method: str
    endpoint: str
    status: int | None
    observed_at: datetime
    fresh_until: datetime
    detail: dict[str, object]
    error_kind: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise GraphError("evidence_id must be non-empty")
        if self.method not in {"GET", "FIXTURE", "ATTESTATION"}:
            raise GraphError(f"evidence method must be read-only, got {self.method!r}")
        if not isinstance(self.detail, dict):
            raise GraphError("evidence detail must be a mapping")
        if _as_utc(self.fresh_until) < _as_utc(self.observed_at):
            raise GraphError("fresh_until must not precede observed_at")

    def is_fresh(self, now: datetime) -> bool:
        return _as_utc(now) <= _as_utc(self.fresh_until)

    def digest(self) -> str:
        payload = {
            "evidence_id": self.evidence_id,
            "kind": self.kind.value,
            "classification": self.classification.value,
            "target": self.target.to_dict(),
            "method": self.method,
            "endpoint": self.endpoint,
            "status": self.status,
            "observed_at": _as_utc(self.observed_at).isoformat(),
            "detail": self.detail,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "kind": self.kind.value,
            "classification": self.classification.value,
            "target": self.target.to_dict(),
            "method": self.method,
            "endpoint": self.endpoint,
            "status": self.status,
            "error_kind": self.error_kind,
            "observed_at": _as_utc(self.observed_at).isoformat(),
            "fresh_until": _as_utc(self.fresh_until).isoformat(),
            "digest": self.digest(),
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class Obligation:
    obligation_id: str
    kind: ObligationKind
    description: str
    mandatory: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "obligation_id": self.obligation_id,
            "kind": self.kind.value,
            "description": self.description,
            "mandatory": self.mandatory,
        }


@dataclass(frozen=True, slots=True)
class Dependency:
    dependency_id: str
    kind: DependencyKind
    description: str
    active: bool
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "dependency_id": self.dependency_id,
            "kind": self.kind.value,
            "description": self.description,
            "active": self.active,
            "evidence_id": self.evidence_id,
        }


@dataclass(frozen=True, slots=True)
class Edge:
    src: str
    relation: Relation
    dst: str

    def to_dict(self) -> dict[str, str]:
        return {"from": self.src, "relation": self.relation.value, "to": self.dst}


class Graph:
    """A mutable builder for one target's retirement obligation graph."""

    def __init__(self) -> None:
        self._targets: dict[str, TargetIdentity] = {}
        self._obligations: dict[str, Obligation] = {}
        self._evidence: dict[str, Evidence] = {}
        self._dependencies: dict[str, Dependency] = {}
        self._edges: list[Edge] = []
        self._node_ids: set[str] = set()

    # -- builders ---------------------------------------------------------
    def add_target(self, target: TargetIdentity) -> str:
        node_id = f"target:{target.project_id}:{target.resource_kind}"
        existing = self._targets.get(node_id)
        if existing is not None and existing.key() != target.key():
            raise GraphError(f"contradictory duplicate target identity for {node_id}")
        self._targets[node_id] = target
        self._node_ids.add(node_id)
        return node_id

    def add_obligation(
        self,
        obligation_id: str,
        kind: ObligationKind,
        description: str,
        *,
        mandatory: bool = True,
    ) -> str:
        self._register(obligation_id)
        self._obligations[obligation_id] = Obligation(obligation_id, kind, description, mandatory)
        return obligation_id

    def add_evidence(self, evidence: Evidence) -> str:
        self._register(evidence.evidence_id)
        self._evidence[evidence.evidence_id] = evidence
        return evidence.evidence_id

    def add_dependency(self, dependency: Dependency) -> str:
        self._register(dependency.dependency_id)
        self._dependencies[dependency.dependency_id] = dependency
        return dependency.dependency_id

    def link(self, src: str, relation: Relation, dst: str) -> None:
        if src not in self._node_ids:
            raise GraphError(f"edge source {src!r} is not a known node")
        if dst not in self._node_ids:
            raise GraphError(f"edge target {dst!r} is not a known node")
        edge = Edge(src, relation, dst)
        if edge not in self._edges:
            self._edges.append(edge)

    def _register(self, node_id: str) -> None:
        if not isinstance(node_id, str) or not node_id.strip():
            raise GraphError("node id must be a non-empty string")
        if node_id in self._node_ids and (
            node_id in self._obligations
            or node_id in self._evidence
            or node_id in self._dependencies
        ):
            raise GraphError(f"duplicate node id {node_id!r}")
        self._node_ids.add(node_id)

    # -- validation -------------------------------------------------------
    def validate(self) -> None:
        for evidence in self._evidence.values():
            if evidence.target.key() not in {t.key() for t in self._targets.values()}:
                raise GraphError(f"evidence {evidence.evidence_id!r} references an unknown target")
        for dependency in self._dependencies.values():
            ev = dependency.evidence_id
            if ev is not None and ev not in self._evidence:
                raise GraphError(
                    f"dependency {dependency.dependency_id!r} references unknown evidence {ev!r}"
                )
        for edge in self._edges:
            if edge.src not in self._node_ids or edge.dst not in self._node_ids:
                raise GraphError(f"edge references an unknown node: {edge.to_dict()}")

    # -- accessors --------------------------------------------------------
    @property
    def targets(self) -> dict[str, TargetIdentity]:
        return dict(self._targets)

    @property
    def obligations(self) -> dict[str, Obligation]:
        return dict(self._obligations)

    @property
    def evidence(self) -> dict[str, Evidence]:
        return dict(self._evidence)

    @property
    def dependencies(self) -> dict[str, Dependency]:
        return dict(self._dependencies)

    @property
    def edges(self) -> tuple[Edge, ...]:
        return tuple(self._edges)

    def evidence_for(self, obligation_id: str) -> list[Evidence]:
        ids = [
            e.dst
            for e in self._edges
            if e.src == obligation_id
            and e.relation in (Relation.REQUIRES_EVIDENCE, Relation.SATISFIED_BY)
        ]
        return [self._evidence[i] for i in ids if i in self._evidence]

    def dependencies_for(self, obligation_id: str) -> list[Dependency]:
        ids = [
            e.dst
            for e in self._edges
            if e.src == obligation_id and e.relation == Relation.BLOCKED_BY
        ]
        return [self._dependencies[i] for i in ids if i in self._dependencies]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "termivance.retirement_obligation_graph/v1",
            "targets": [t.to_dict() for _, t in sorted(self._targets.items())],
            "obligations": [o.to_dict() for _, o in sorted(self._obligations.items())],
            "dependencies": [d.to_dict() for _, d in sorted(self._dependencies.items())],
            "evidence": [e.to_dict() for _, e in sorted(self._evidence.items())],
            "edges": [e.to_dict() for e in self._edges],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
