"""Retirement simulation — "What if we retire this?" (Capability 3).

A *hypothetical* consequence analysis built from the current recorded graph.
The module contains no mutation surface at all — it never even imports one —
and every projected effect is labelled ``PROJECTED_NOT_OBSERVED``: a simulation
can describe what a provider *should* do after an action, but it can never
claim that the provider did it, nor mint a verdict about absence.

The deterministic engine is run once on the current graph to state what the
executor would decide *today*; the remaining projection is a pure rule table
over the same obligations. No equipment is added by the simulation, no
obligation is simulated to ``SATISFIED``, and eligibility can never be created
here that did not already exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from termivance.engine import evaluate
from termivance.graph import Graph
from termivance.policy import Policy
from termivance.verdicts import Verdict

SIMULATION_SCHEMA = "termivance.retirement_simulation/v1"
HYPOTHETICAL_BANNER = (
    "HYPOTHETICAL SIMULATION — no request was sent, nothing was mutated, no verdict was earned"
)


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ObligationProjection:
    obligation_id: str
    obligation_kind: str
    current_status: str
    projected_status: str
    consequence: str
    flips_eligible: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "obligation_id": self.obligation_id,
            "obligation_kind": self.obligation_kind,
            "current_status": self.current_status,
            "projected_status": self.projected_status,
            "consequence": self.consequence,
            "flips_eligible": self.flips_eligible,
        }


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """One hypothetical analysis. Every effect stays ``PROJECTED_NOT_OBSERVED``."""

    evaluable: bool
    decision_record: dict[str, object]
    projections: tuple[ObligationProjection, ...]
    projected_provider_effects: tuple[dict[str, object], ...]
    redeployment_risk: str
    hypothetical: bool = True
    #: Resource-level projection factors derived from the *same*, observed
    #: portfolio snapshot the Portfolio and Risk Map surfaced (never re-derived,
    #: never invented inside the simulation).
    cross_resource_factors: tuple[dict[str, object], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": SIMULATION_SCHEMA,
            "hypothetical": self.hypothetical,
            "banner": HYPOTHETICAL_BANNER,
            "evaluable": self.evaluable,
            "decision": self.decision_record,
            "obligation_projections": [p.to_dict() for p in self.projections],
            "projected_provider_effects": list(self.projected_provider_effects),
            "redeployment_risk": self.redeployment_risk,
            "cross_resource_factors": list(self.cross_resource_factors),
        }

    def render(self) -> str:
        lines = [
            HYPOTHETICAL_BANNER,
            "=" * 78,
            "Current deterministic decision (this is real, not projected):",
            f"  verdict: {self.decision_record.get('verdict')}",
            "If an authorized `unpublish_pages` DID execute, providers are projected to:",
        ]
        for effect in self.projected_provider_effects:
            lines.append(f"  - {effect['effect']} [{effect['state']}]")
        lines.append("Obligation-level projection (nothing simulated to SATISFIED):")
        for projection in self.projections:
            lines.append(
                f"  [{projection.obligation_kind:<26}] {projection.current_status:<9} -> "
                f"{projection.projected_status:<24} {projection.consequence}"
            )
        lines.append(f"redeployment risk: {self.redeployment_risk}")
        if self.cross_resource_factors:
            lines.append("Cross-resource projection (same observed portfolio evidence):")
            for factor in self.cross_resource_factors:
                lines.append(
                    f"  [{factor.get('kind'):<26}] {str(factor.get('resource')):<40} "
                    f"[{factor.get('state')}]"
                )
        lines.append("-" * 78)
        lines.append(
            "boundary: every 'projected' item is a rule-based expectation; only a "
            "fresh, independent provider observation after a real, authorized "
            "mutation can ever upgrade it"
        )
        return "\n".join(lines)


def _projection_for(obligation: dict[str, Any]) -> ObligationProjection:
    kind = str(obligation.get("kind"))
    oid = str(obligation.get("obligation_id"))
    status = str(obligation.get("status"))
    flips = False
    if kind == "PAGES_PUBLISHED":
        if status == "SATISFIED":
            projected = "PRESUMED_UNKNOWN_AFTER_UNPUBLISH"
            consequence = (
                "publication proof would lose its live meaning; a fresh provider "
                "observation would be required (absence is never inferred)"
            )
        else:
            projected = status
            consequence = "still not proven published; a simulation cannot create evidence"
    elif kind == "REDEPLOYMENT_PATH":
        projected = status
        consequence = (
            "an active redeployment mechanism would still be able to resurrect "
            "the site; it is consumed by retirement, not removed by it"
        )
    elif kind == "UNRESOLVED_WORK":
        projected = status
        flips = status == "VIOLATED"
        consequence = (
            "still blocks retirement until the recorded work item resolves"
            if status == "VIOLATED"
            else "no recorded open work item"
        )
    elif kind == "PROVIDER_OBSERVATION":
        projected = status
        consequence = (
            "provider observations stay historical; they expire and are never "
            "extended by the action itself"
        )
    else:
        projected = status
        consequence = "unchanged by this hypothetical action"
    return ObligationProjection(
        obligation_id=oid,
        obligation_kind=kind,
        current_status=status,
        projected_status=projected,
        consequence=consequence,
        flips_eligible=flips,
    )


def simulate_retirement(
    graph: Graph,
    *,
    policy: Policy,
    action: str = "unpublish_pages",
    now: datetime | None = None,
    authorization: object | None = None,
    cross: object | None = None,
) -> SimulationResult:
    """Project the consequences of an authorized retirement. Purely hypothetical.

    ``cross`` is the shared :class:`termivance.dependencies.CrossResourceView`
    derived from the same observed portfolio snapshot; its factors are appended
    verbatim and are projective context — they never create eligibility, never
    satisfy an obligation and never mint a verdict.
    """
    observed = _utc(now)
    from termivance.authorization import Authorization

    decision = evaluate(
        graph,
        policy=policy,
        action=action,
        now=observed,
        authorization=authorization if isinstance(authorization, Authorization) else None,
    )
    record = decision.to_dict(graph=graph)
    projections = tuple(_projection_for(o) for o in record.get("obligations", ()))

    effects: list[dict[str, object]] = []
    target = decision.target
    endpoint = f"/projects/{target.project_id}/pages"
    effects.append(
        {
            "effect": (
                f"authorized DELETE {endpoint} on project {target.project_id} would be "
                "expected to return 2xx"
            ),
            "state": "PROJECTED_NOT_OBSERVED",
        }
    )
    effects.append(
        {
            "effect": (
                f"GET {endpoint} would be expected to no longer report a deployment — "
                "this must be re-observed independently, never assumed"
            ),
            "state": "PROJECTED_NOT_OBSERVED",
        }
    )
    effects.append(
        {
            "effect": (
                "the previously served URL may return 404 — or keep serving stale "
                "content: CDN convergence has unknown delay and errors are never "
                "promoted to verified absence"
            ),
            "state": "PROJECTED_NOT_OBSERVED",
        }
    )
    redeployment = any(
        str(o.get("kind")) == "REDEPLOYMENT_PATH" and str(o.get("status")) != "SATISFIED"
        for o in record.get("obligations", ())
    )
    redeployment_risk = (
        "HIGH: the recorded CI/Pages mechanism can redeploy the site after "
        "retirement; resurrection is a live risk unless that path is "
        "demonstrably inert — and that is a risk, never a verdict."
        if redeployment
        else "No active redeployment mechanism proven from evidence; this is NOT "
        "evidence that none exists — a later redeployment is always possible"
    )
    cross_factors: tuple[dict[str, object], ...] = ()
    if cross is not None and hasattr(cross, "as_simulation_factors"):
        cross_factors = tuple(dict(f) for f in cross.as_simulation_factors())
    return SimulationResult(
        evaluable=decision.verdict in {Verdict.SAFE_TO_RETIRE, Verdict.BLOCKED},
        decision_record=record,
        projections=projections,
        projected_provider_effects=tuple(effects),
        redeployment_risk=redeployment_risk,
        cross_resource_factors=cross_factors,
    )


__all__ = [
    "HYPOTHETICAL_BANNER",
    "SIMULATION_SCHEMA",
    "ObligationProjection",
    "SimulationResult",
    "simulate_retirement",
]
