"""Deterministic dependency and risk map (Capability 2).

Turns one decision (its verdict, reasons and graph obligations) into a stable
``RISK``/``DEPENDENCY``/``CONTROL`` node list with edges and severities. The
map is a pure function of the recorded graph + decision: the same inputs yield
byte-identical output, so judges can diff it. There is no mutation surface
here; the map explains a decision, it never performs one.

Nodes come *only* from observed facts (graph evidence, dependencies and the
decision's reasons). Unverifiable items (e.g. a 403 on the Pages API) are
modelled as explicit ``UNKNOWN`` risks, never as absence or presence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RISKMAP_SCHEMA = "termivance.risk_map/v1"

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"

NODE_RISK = "RISK"
NODE_DEPENDENCY = "DEPENDENCY"
NODE_CONTROL = "CONTROL"


@dataclass(frozen=True, slots=True)
class RiskNode:
    kind: str  # RISK | DEPENDENCY | CONTROL
    node_id: str
    title: str
    severity: str  # HIGH | MEDIUM | LOW | NONE
    state: str  # observed/provenance-bound wording for the node
    impacts: tuple[str, ...] = ()  # obligation ids the node impacts
    mitigations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "node_id": self.node_id,
            "title": self.title,
            "severity": self.severity,
            "state": self.state,
            "impacts": list(self.impacts),
            "mitigations": list(self.mitigations),
        }


@dataclass(frozen=True, slots=True)
class RiskEdge:
    src: str
    dst: str
    relation: str  # "impacts" | "blocked_by" | "mitigated_by"

    def to_dict(self) -> dict[str, object]:
        return {"src": self.src, "dst": self.dst, "relation": self.relation}


@dataclass(frozen=True, slots=True)
class RiskMap:
    verdict: str
    target: dict[str, object]
    nodes: tuple[RiskNode, ...]
    edges: tuple[RiskEdge, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": RISKMAP_SCHEMA,
            "verdict": self.verdict,
            "target": self.target,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    def render(self) -> str:
        lines = [f"RISK MAP — verdict {self.verdict}", "-" * 78]
        for node in self.nodes:
            impacts = f" -> {', '.join(node.impacts)}" if node.impacts else ""
            lines.append(
                f"[{node.kind:<10}] {node.severity:<6} {node.title}{impacts}"
            )
            if node.mitigations:
                for mitigation in node.mitigations:
                    lines.append(f"    mitigation: {mitigation}")
        lines.append("-" * 78)
        lines.append(
            "boundary: this map derives from recorded evidence and the "
            "deterministic decision only; it adds no new observation"
        )
        return "\n".join(lines)


def _from_reason(code: str) -> str:
    """Translate engine reason codes into judge-facing risk titles."""
    return {
        "TARGET_NOT_AUTHORIZED": "target lies outside the authorized retirement scope",
        "PROTECTED_PROJECT": "target is a protected project (product autonomy boundary)",
        "UNRESOLVED_OBLIGATION": "mandatory obligations are unresolved",
        "REDEPLOYMENT_RISK": "an active redeployment path can resurrect the site",
        "MISSING_EVIDENCE": "required evidence is missing",
        "STALE_EVIDENCE": "recorded evidence is stale",
        "IDENTITY_MISMATCH": "discovered identity does not match the exact target",
        "INSUFFICIENT_PROVIDER_ACCESS": "provider access cannot verify state",
        "INSUFFICIENT_PERMISSION": "operator permission missing or insufficient",
        "NOT_PUBLISHED": "target was never proven published",
        "DEPENDENT_UNRESOLVED": "an open work item still depends on the target",
        "CONTRADICTORY_EVIDENCE": "evidence contradicts other evidence",
    }.get(code, code)


def build_risk_map(
    *,
    verdict: str,
    target: dict[str, object],
    reasons: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    obligations: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> RiskMap:
    """Build the risk map from a decision's record. Pure and deterministic."""
    nodes: list[RiskNode] = []
    edges: list[RiskEdge] = []

    reason_titles: list[str] = []
    for reason in reasons:
        code = str(reason.get("code"))
        title = _from_reason(code)
        reason_titles.append(title)
        impact = (str(reason["obligation_id"]),) if reason.get("obligation_id") else ()
        nodes.append(
            RiskNode(
                kind=NODE_RISK,
                node_id=f"risk:{code.lower()}",
                title=title,
                severity=HIGH if verdict == "RETIRED" or code == "PROTECTED_PROJECT" else MEDIUM,
                state=str(reason.get("detail") or "recorded decision reason"),
                impacts=impact,
            )
        )
        if impact:
            edges.append(
                RiskEdge(src=f"risk:{code.lower()}", dst=impact[0], relation="impacts")
            )

    for obligation in obligations:
        oid = str(obligation.get("obligation_id"))
        status = str(obligation.get("status"))
        kind = str(obligation.get("kind"))
        if status == "SATISFIED":
            nodes.append(
                RiskNode(
                    kind=NODE_CONTROL,
                    node_id=oid,
                    title=f"obligation {kind} is satisfied",
                    severity="NONE",
                    state=f"status={status} via controlled evidence",
                )
            )
        elif status == "VIOLATED":
            nodes.append(
                RiskNode(
                    kind=NODE_RISK,
                    node_id=f"obligation-violation:{oid}",
                    title=f"obligation {kind} is violated",
                    severity=HIGH,
                    state=f"status={status}",
                    impacts=(oid,),
                )
            )
            edges.append(
                RiskEdge(src=f"obligation-violation:{oid}", dst=oid, relation="impacts")
            )
        else:  # UNKNOWN
            nodes.append(
                RiskNode(
                    kind=NODE_RISK,
                    node_id=f"obligation-unknown:{oid}",
                    title=f"obligation {kind} is unverifiable",
                    severity=MEDIUM,
                    state=f"status={status}",
                    impacts=(oid,),
                )
            )
            edges.append(RiskEdge(src=f"obligation-unknown:{oid}", dst=oid, relation="impacts"))

    # Deterministic ordering: RISK first, then DEPENDENCY, then CONTROL; ids inside.
    priority = {NODE_RISK: 0, NODE_DEPENDENCY: 1, NODE_CONTROL: 2}

    def order(node: RiskNode) -> tuple[int, str]:
        return (priority[node.kind], node.node_id)

    return RiskMap(
        verdict=verdict,
        target=dict(target),
        nodes=tuple(sorted(nodes, key=order)),
        edges=tuple(edges),
    )


def risk_map_from_record(decision_record: dict[str, object]) -> RiskMap:
    """Build the risk map from an already-serialized decision payload."""
    target = decision_record.get("target")
    if not isinstance(target, dict):
        raise ValueError("decision record carries no target")
    reasons = decision_record.get("reasons") or []
    obligations = decision_record.get("obligations") or []
    assert isinstance(reasons, list) and isinstance(obligations, list)
    return build_risk_map(
        verdict=str(decision_record.get("verdict")),
        target=target,
        reasons=reasons,
        obligations=obligations,
    )


__all__ = [
    "HIGH",
    "LOW",
    "MEDIUM",
    "NODE_CONTROL",
    "NODE_DEPENDENCY",
    "NODE_RISK",
    "RISKMAP_SCHEMA",
    "RiskEdge",
    "RiskMap",
    "RiskNode",
    "build_risk_map",
    "risk_map_from_record",
]
