"""Shared cross-resource dependency semantics (Capability glue since B4-repair).

One module owns the mapping from *observed portfolio evidence* to everything
downstream — so the Portfolio, Risk Map and Simulation always operate on the
very same resource records, never on three different re-derivations:

* every OBSERVED resource record of a retirement-relevant kind becomes a
  ``DEPENDENCY`` node whose state text carries the provenance label and
  freshness window of the actual observation;
* every INFERRED portfolio relation becomes an explicitly ``INFERRED`` edge —
  inferred edges are context, never obligations, and can never satisfy a
  mandatory obligation in the decision engine;
* every NOT_OBSERVED resource kind becomes an explicit ``UNKNOWN`` risk node:
  the provider fact is inaccessible, and that gate stays open — a 401/403/404 is
  never promoted to absence or presence.

There is no mutation surface here: this module builds views over already
recorded observations and can authorize nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from termivance.portfolio import (
    KIND_CI_REDEPLOY,
    KIND_PAGES,
    PORTFOLIO_TTL_SECONDS,
    SUPPORT_INFERRED,
    SUPPORT_NOT_OBSERVED,
    SUPPORT_OBSERVED,
    PortfolioRelation,
    PortfolioSnapshot,
    ResourceRecord,
)

DEPENDENCIES_SCHEMA = "termivance.cross_dependencies/v1"

#: Resource kinds that can resurrect or obstruct a Pages retirement directly.
REDEPLOYMENT_KINDS = (KIND_CI_REDEPLOY,)


@dataclass(frozen=True, slots=True)
class CrossResourceView:
    """Resource records and relations derived once, reused by risk map + simulation."""

    nodes: tuple[ResourceRecord, ...]
    relations: tuple[PortfolioRelation, ...]
    not_observed_kinds: tuple[str, ...]
    derived_at: datetime

    @property
    def inferred_relations(self) -> int:
        return sum(1 for rel in self.relations if rel.support == SUPPORT_INFERRED)

    @property
    def observed_relations(self) -> int:
        return sum(1 for rel in self.relations if rel.support == SUPPORT_OBSERVED)

    @property
    def redeploy_signal_present(self) -> bool:
        return any(
            r.kind == KIND_CI_REDEPLOY
            and r.support == SUPPORT_OBSERVED
            and r.state == "PAGES_REDEPLOYMENT_SIGNAL_PRESENT"
            for r in self.nodes
        )

    @property
    def pages_observed_somewhere(self) -> bool:
        return any(
            r.kind == KIND_PAGES and r.support == SUPPORT_OBSERVED for r in self.nodes
        )

    def as_risk_nodes(self, target: dict[str, object]) -> tuple[dict[str, object], ...]:
        """Judge-facing dependency/risk node dicts with full provenance.

        OBSERVED resources are DEPENDENCY nodes; NOT_OBSERVED kinds are RISK
        nodes whose state explicitly records the access limitation.
        """
        node_list: list[dict[str, object]] = []
        for record in self.nodes:
            fresh_until = record.fresh_until.isoformat()
            if record.support == SUPPORT_OBSERVED:
                node_list.append(
                    {
                        "kind": "DEPENDENCY",
                        "node_id": f"resource:{record.ref}",
                        "title": f"{record.kind} {record.state}",
                        "severity": (
                            "HIGH"
                            if record.kind in REDEPLOYMENT_KINDS
                            and record.state == "PAGES_REDEPLOYMENT_SIGNAL_PRESENT"
                            else "LOW"
                        ),
                        "state": (
                            f"{record.state} via GET {record.endpoint} "
                            f"[{record.provenance}, fresh until {fresh_until}]"
                        ),
                        "impacts": (),
                        "mitigations": (
                            "observation only; mutation_capability=NOT_AUTHORIZING",
                        ),
                        "support": record.support,
                        "resource": record.to_dict(),
                        "target": target,
                    }
                )
            else:
                node_list.append(
                    {
                        "kind": "RISK",
                        "node_id": f"not-observed:{record.ref}",
                        "title": f"{record.kind} was NOT_OBSERVED at the provider",
                        "severity": "MEDIUM",
                        "state": (
                            f"{record.state} via GET {record.endpoint} "
                            f"[{record.provenance}]; a 401/403/404 is never absence"
                        ),
                        "impacts": (),
                        "mitigations": (
                            "re-check via an authorized read when credentials permit",
                        ),
                        "support": record.support,
                        "resource": record.to_dict(),
                        "target": target,
                    }
                )
        return tuple(node_list)

    def as_risk_edges(self) -> tuple[dict[str, object], ...]:
        """Portfolio relations as risk-map edges, support-labelled.

        Both endpoints are resolved against the view's own recorded node refs;
        a relation pointing anywhere else is a structural bug, not context.
        """
        ref_to_node = {
            record.ref: (
                f"resource:{record.ref}"
                if record.support == SUPPORT_OBSERVED
                else f"not-observed:{record.ref}"
            )
            for record in self.nodes
        }
        edges: list[dict[str, object]] = []
        for relation in self.relations:
            try:
                src = ref_to_node[relation.src]
                dst = ref_to_node[relation.dst]
            except KeyError as exc:
                raise ValueError(
                    "portfolio relation points outside the observed records: "
                    f"{relation!r} (missing ref {exc})"
                ) from exc
            edges.append(
                {
                    "src": src,
                    "dst": dst,
                    "relation": relation.kind,
                    "support": relation.support,
                }
            )
        return tuple(edges)

    def as_simulation_factors(self) -> tuple[dict[str, object], ...]:
        """Resource-level projection factors for the hypothetical analysis.

        A pages unpublish acts on the Pages publication only. The projection for
        every *other* observed resource kind is: no known action path from that
        endpoint — and that is a projection, never an observation.
        """
        factors: list[dict[str, object]] = []
        for record in self.nodes:
            if record.kind == KIND_PAGES or record.support != SUPPORT_OBSERVED:
                continue
            factors.append(
                {
                    "resource": record.ref,
                    "kind": record.kind,
                    "observed_state": record.state,
                    "support": record.support,
                    "observed_at": record.observed_at.isoformat(),
                    "fresh_until": record.fresh_until.isoformat(),
                    "projection": (
                        f"an authorized DELETE of the Pages publication acts on the "
                        f"Pages resource only; {record.kind} observed here is NOT "
                        "acted on by that endpoint — any post-retirement change "
                        "would have to be re-observed independently"
                    ),
                    "state": "PROJECTED_NOT_OBSERVED",
                }
            )
        if self.redeploy_signal_present:
            factors.append(
                {
                    "resource": "cross-resource:redeployment",
                    "kind": KIND_CI_REDEPLOY,
                    "observed_state": "PAGES_REDEPLOYMENT_SIGNAL_PRESENT",
                    "support": "INFERRED_CAPABILITY",
                    "projection": (
                        "the recorded CI mechanism could redeploy the site after "
                        "retirement (INFERRED from configuration text); "
                        "resurrection is a live risk, never a verdict"
                    ),
                    "state": "PROJECTED_NOT_OBSERVED",
                }
            )
        return tuple(factors)


def cross_resource_view(snapshot: PortfolioSnapshot) -> CrossResourceView:
    """Derive the shared cross-resource view from one portfolio snapshot.

    The view carries exactly the resource evidence the snapshot recorded — the
    Risk Map and Simulation consume *this* view rather than re-probing or
    re-inventing resource facts.
    """
    nodes: list[ResourceRecord] = []
    not_observed: list[str] = []
    for asset in snapshot.assets:
        for record in asset.resources:
            nodes.append(record)
            if record.support == SUPPORT_NOT_OBSERVED and record.kind not in not_observed:
                not_observed.append(record.kind)
    return CrossResourceView(
        nodes=tuple(sorted(nodes, key=lambda r: r.ref)),
        relations=tuple(snapshot.relations),
        not_observed_kinds=tuple(sorted(not_observed)),
        derived_at=snapshot.observed_at,
    )


def freshness_note(now: datetime) -> dict[str, object]:
    """The standard TTL statement attached to any cross-resource view usage."""
    return {
        "ttl_seconds": PORTFOLIO_TTL_SECONDS,
        "statement": (
            "portfolio resource records are bounded observations; after their "
            "freshness window they expire and are never extended by inference"
        ),
        "derived_at": now.isoformat(),
    }


__all__ = [
    "DEPENDENCIES_SCHEMA",
    "REDEPLOYMENT_KINDS",
    "CrossResourceView",
    "cross_resource_view",
    "freshness_note",
]
