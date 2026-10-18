"""Deterministic retirement decision engine.

Evaluates a :class:`termivance.graph.Graph` into a bounded retirement verdict.
This is the only place an authoritative verdict is produced. Model/agent text
can describe the result but can never compute it.

The engine is deliberately separate from execution:

* retirement *eligibility* - this engine;
* *authorization to execute* - :class:`termivance.authorization.Authorization`;
* *execution status* and *post-execution observation* - B3, out of scope here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from termivance.authorization import Authorization
from termivance.graph import (
    DependencyKind,
    Evidence,
    EvidenceClass,
    EvidenceKind,
    Graph,
    Obligation,
    ObligationKind,
)
from termivance.policy import EXAMPLE_MODE, Policy
from termivance.protected import is_protected, protection_reason
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

DEFAULT_ACTION = "unpublish_pages"

SATISFIED = "SATISFIED"
VIOLATED = "VIOLATED"
UNKNOWN = "UNKNOWN"


class ReasonCode(StrEnum):
    TARGET_NOT_AUTHORIZED = "TARGET_NOT_AUTHORIZED"
    PROTECTED_PROJECT = "PROTECTED_PROJECT"
    UNRESOLVED_OBLIGATION = "UNRESOLVED_OBLIGATION"
    REDEPLOYMENT_RISK = "REDEPLOYMENT_RISK"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    INSUFFICIENT_PROVIDER_ACCESS = "INSUFFICIENT_PROVIDER_ACCESS"
    INSUFFICIENT_PERMISSION = "INSUFFICIENT_PERMISSION"
    NOT_PUBLISHED = "NOT_PUBLISHED"
    DEPENDENT_UNRESOLVED = "DEPENDENT_UNRESOLVED"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"


@dataclass(frozen=True, slots=True)
class Reason:
    code: ReasonCode
    obligation_id: str | None
    detail: str
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "obligation_id": self.obligation_id,
            "detail": self.detail,
            "evidence_id": self.evidence_id,
        }


@dataclass(frozen=True, slots=True)
class Decision:
    verdict: Verdict
    target: TargetIdentity
    action: str
    evaluated_at: datetime
    reasons: tuple[Reason, ...]
    obligations: tuple[dict[str, object], ...]
    read_only: bool = True

    @property
    def blocking_reasons(self) -> tuple[Reason, ...]:
        return self.reasons

    def safe_conditions(self) -> tuple[str, ...]:
        conditions: list[str] = []
        for reason in self.reasons:
            conditions.append(f"resolve {reason.code.value}: {reason.detail}")
        return tuple(conditions)

    def to_dict(self, *, graph: Graph | None = None) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": "termivance.retirement_decision/v1",
            "verdict": self.verdict.value,
            "target": self.target.to_dict(),
            "action": self.action,
            "evaluated_at": self.evaluated_at.astimezone(UTC).isoformat(),
            "read_only": self.read_only,
            "authoritative": self.verdict in {Verdict.SAFE_TO_RETIRE},
            "reasons": [r.to_dict() for r in self.reasons],
            "obligations": list(self.obligations),
            "missing_conditions": list(self.safe_conditions()),
        }
        if graph is not None:
            payload["graph"] = graph.to_dict()
        return payload


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _latest(graph: Graph, kind: EvidenceKind) -> Evidence | None:
    matches = [e for e in graph.evidence.values() if e.kind == kind]
    if not matches:
        return None
    return max(matches, key=lambda e: _utc(e.observed_at))


def _obligation_id(graph: Graph, kind: ObligationKind) -> str | None:
    for oid, obl in graph.obligations.items():
        if obl.kind == kind:
            return oid
    return None


def _evaluate_obligation(
    obligation: Obligation,
    graph: Graph,
    target: TargetIdentity,
    policy: Policy,
    action: str,
    authorization: Authorization | None,
    now: datetime,
) -> tuple[str, list[Reason]]:
    kind = obligation.kind
    oid = obligation.obligation_id

    if kind == ObligationKind.TARGET_SCOPE:
        if is_protected(target.project_id):
            return VIOLATED, [
                Reason(
                    ReasonCode.PROTECTED_PROJECT,
                    oid,
                    protection_reason(target.project_id)
                    or f"project {target.project_id} is protected",
                )
            ]
        in_permitted_scope = target.project_id in policy.allowed_target_project_ids
        if policy.mode == EXAMPLE_MODE or not in_permitted_scope:
            return VIOLATED, [
                Reason(
                    ReasonCode.TARGET_NOT_AUTHORIZED,
                    oid,
                    f"project {target.project_id} is not in the permitted retirement scope",
                )
            ]
        if target.full_path not in policy.allowed_target_full_paths:
            return VIOLATED, [
                Reason(
                    ReasonCode.TARGET_NOT_AUTHORIZED,
                    oid,
                    f"full path {target.full_path!r} is not in the permitted retirement scope",
                )
            ]
        return SATISFIED, []

    if kind == ObligationKind.OWNERSHIP_AUTHORIZATION:
        if authorization is None:
            return VIOLATED, [
                Reason(ReasonCode.TARGET_NOT_AUTHORIZED, oid, "no bound authorization supplied")
            ]
        if not authorization.is_valid(now, target, action):
            return VIOLATED, [
                Reason(
                    ReasonCode.TARGET_NOT_AUTHORIZED,
                    oid,
                    "authorization is missing, expired, exhausted, or bound to a different "
                    "target/action",
                )
            ]
        return SATISFIED, []

    if kind == ObligationKind.RETIREMENT_PERMISSION:
        perm = _latest(graph, EvidenceKind.EFFECTIVE_PERMISSION)
        if perm is None:
            return UNKNOWN, [
                Reason(
                    ReasonCode.MISSING_EVIDENCE,
                    oid,
                    "effective Pages administration permission was not observed",
                )
            ]
        if perm.classification != EvidenceClass.LIVE:
            return UNKNOWN, [
                Reason(
                    ReasonCode.MISSING_EVIDENCE,
                    oid,
                    f"permission evidence is {perm.classification.value}, not a live observation",
                    perm.evidence_id,
                )
            ]
        if perm.error_kind is not None:
            return UNKNOWN, [
                Reason(
                    ReasonCode.INSUFFICIENT_PROVIDER_ACCESS,
                    oid,
                    f"permission could not be observed ({perm.error_kind})",
                    perm.evidence_id,
                )
            ]
        if not perm.is_fresh(now):
            return UNKNOWN, [
                Reason(
                    ReasonCode.STALE_EVIDENCE, oid, "permission evidence is stale", perm.evidence_id
                )
            ]
        if bool(perm.detail.get("can_manage_pages")):
            return SATISFIED, []
        return VIOLATED, [
            Reason(
                ReasonCode.INSUFFICIENT_PERMISSION,
                oid,
                "the acting identity lacks Maintainer/Owner Pages administration on the target",
                perm.evidence_id,
            )
        ]

    if kind == ObligationKind.PAGES_PUBLISHED:
        pub = _latest(graph, EvidenceKind.PAGES_DEPLOYMENT)
        if pub is None:
            return UNKNOWN, [
                Reason(
                    ReasonCode.MISSING_EVIDENCE,
                    oid,
                    "no live Pages publication evidence for the target",
                )
            ]
        if pub.classification != EvidenceClass.LIVE:
            return UNKNOWN, [
                Reason(
                    ReasonCode.MISSING_EVIDENCE,
                    oid,
                    f"publication evidence is {pub.classification.value}, not live",
                    pub.evidence_id,
                )
            ]
        if pub.error_kind is not None:
            return UNKNOWN, [
                Reason(
                    ReasonCode.INSUFFICIENT_PROVIDER_ACCESS,
                    oid,
                    f"publication could not be observed ({pub.error_kind})",
                    pub.evidence_id,
                )
            ]
        if not pub.is_fresh(now):
            return UNKNOWN, [
                Reason(
                    ReasonCode.STALE_EVIDENCE, oid, "publication evidence is stale", pub.evidence_id
                )
            ]
        deployment = bool(pub.detail.get("deployment_present"))
        marker = bool(pub.detail.get("marker_observed"))
        url = pub.detail.get("served_url")
        if deployment and marker and isinstance(url, str) and url:
            return SATISFIED, []
        return VIOLATED, [
            Reason(
                ReasonCode.NOT_PUBLISHED,
                oid,
                "the target is not a genuinely published Pages site "
                f"(deployment_present={deployment}, marker_observed={marker})",
                pub.evidence_id,
            )
        ]

    if kind == ObligationKind.IDENTITY_BINDING:
        reasons: list[Reason] = []
        for ev in graph.evidence.values():
            if ev.target.key() != target.key():
                reasons.append(
                    Reason(
                        ReasonCode.IDENTITY_MISMATCH,
                        oid,
                        f"evidence {ev.evidence_id} is bound to a different target",
                        ev.evidence_id,
                    )
                )
        identity = _latest(graph, EvidenceKind.PROJECT_IDENTITY)
        if identity is not None:
            observed_id = identity.detail.get("project_id")
            if observed_id is not None and observed_id != target.project_id:
                reasons.append(
                    Reason(
                        ReasonCode.IDENTITY_MISMATCH,
                        oid,
                        f"observed project id {observed_id} does not match target "
                        f"{target.project_id}",
                        identity.evidence_id,
                    )
                )
            observed_path = identity.detail.get("path_with_namespace")
            if (
                isinstance(observed_path, str)
                and observed_path
                and observed_path != target.full_path
            ):
                reasons.append(
                    Reason(
                        ReasonCode.IDENTITY_MISMATCH,
                        oid,
                        f"observed full path {observed_path!r} does not match the authorised "
                        f"path {target.full_path!r}",
                        identity.evidence_id,
                    )
                )
        return (VIOLATED, reasons) if reasons else (SATISFIED, [])

    if kind == ObligationKind.PROVIDER_OBSERVATION:
        identity = _latest(graph, EvidenceKind.PROJECT_IDENTITY)
        if identity is None:
            return UNKNOWN, [
                Reason(ReasonCode.MISSING_EVIDENCE, oid, "no provider identity observation")
            ]
        if identity.classification != EvidenceClass.LIVE:
            return UNKNOWN, [
                Reason(
                    ReasonCode.MISSING_EVIDENCE,
                    oid,
                    f"provider evidence is {identity.classification.value}, not a live "
                    "observation; fixtures and records cannot satisfy a live requirement",
                    identity.evidence_id,
                )
            ]
        if identity.error_kind is not None:
            code = (
                ReasonCode.INSUFFICIENT_PROVIDER_ACCESS
                if identity.error_kind in {"AUTH_DENIED", "NOT_FOUND"}
                else ReasonCode.MISSING_EVIDENCE
            )
            return UNKNOWN, [
                Reason(
                    code,
                    oid,
                    f"provider observation failed: {identity.error_kind}",
                    identity.evidence_id,
                )
            ]
        if not identity.is_fresh(now):
            return UNKNOWN, [
                Reason(
                    ReasonCode.STALE_EVIDENCE,
                    oid,
                    "provider identity observation is stale",
                    identity.evidence_id,
                )
            ]
        return SATISFIED, []

    if kind == ObligationKind.UNRESOLVED_WORK:
        deps = graph.dependencies_for(oid)
        active = [d for d in deps if d.active]
        if active:
            return VIOLATED, [
                Reason(
                    ReasonCode.UNRESOLVED_OBLIGATION,
                    oid,
                    f"{len(active)} active unresolved retirement work item(s)",
                    active[0].evidence_id,
                )
            ]
        if _latest(graph, EvidenceKind.OPEN_ISSUES) is None:
            return UNKNOWN, [
                Reason(
                    ReasonCode.MISSING_EVIDENCE,
                    oid,
                    "open work items were not observed",
                )
            ]
        return SATISFIED, []

    if kind == ObligationKind.REDEPLOYMENT_PATH:
        deps = graph.dependencies_for(oid)
        active = [d for d in deps if d.active]
        if active:
            return VIOLATED, [
                Reason(
                    ReasonCode.REDEPLOYMENT_RISK,
                    oid,
                    f"{len(active)} observed redeployment/recreation mechanism(s)",
                    active[0].evidence_id,
                )
            ]
        control = _latest(graph, EvidenceKind.REDEPLOYMENT_CONTROL)
        if (
            control is not None
            and control.classification == EvidenceClass.OPERATOR_CONFIRMED
            and control.error_kind is None
            and control.is_fresh(now)
        ):
            return SATISFIED, []
        ci = _latest(graph, EvidenceKind.CI_CONFIG)
        if ci is None:
            return UNKNOWN, [
                Reason(
                    ReasonCode.MISSING_EVIDENCE,
                    oid,
                    "CI configuration was not observed, so redeployment risk is unknown",
                )
            ]
        if ci.error_kind is not None:
            return UNKNOWN, [
                Reason(
                    ReasonCode.INSUFFICIENT_PROVIDER_ACCESS,
                    oid,
                    f"CI configuration could not be read ({ci.error_kind}); completeness unknown",
                    ci.evidence_id,
                )
            ]
        if bool(ci.detail.get("includes_present")):
            return UNKNOWN, [
                Reason(
                    ReasonCode.MISSING_EVIDENCE,
                    oid,
                    "CI configuration includes external configuration; global completeness is "
                    "not established",
                    ci.evidence_id,
                )
            ]
        return UNKNOWN, [
            Reason(
                ReasonCode.MISSING_EVIDENCE,
                oid,
                "no operator-confirmed control that redeployment is prevented; absence of a "
                "discovered mechanism is not proof of absence",
                ci.evidence_id,
            )
        ]

    if kind == ObligationKind.DEPENDENT_CONSUMERS:
        deps = graph.dependencies_for(oid)
        active = [d for d in deps if d.kind == DependencyKind.CONSUMER and d.active]
        if active:
            return VIOLATED, [
                Reason(
                    ReasonCode.DEPENDENT_UNRESOLVED,
                    oid,
                    f"{len(active)} active dependent consumer(s)",
                    active[0].evidence_id,
                )
            ]
        return SATISFIED, []

    # Unknown obligation kind: fail closed.
    return UNKNOWN, [
        Reason(
            ReasonCode.MISSING_EVIDENCE,
            oid,
            f"unsupported obligation kind {kind!r} cannot be evaluated",
        )
    ]


def evaluate(
    graph: Graph,
    *,
    policy: Policy,
    action: str = DEFAULT_ACTION,
    now: datetime | None = None,
    authorization: Authorization | None = None,
) -> Decision:
    """Deterministically evaluate a retirement obligation graph."""
    now = _utc(now or datetime.now(tz=UTC))
    graph.validate()
    targets = list(graph.targets.values())
    if len(targets) != 1:
        target = targets[0] if targets else TargetIdentity(1, "unknown/unknown", "GITLAB_PROJECT")
        return Decision(
            verdict=Verdict.INCONCLUSIVE,
            target=target,
            action=action,
            evaluated_at=now,
            reasons=(
                Reason(
                    ReasonCode.IDENTITY_MISMATCH,
                    None,
                    f"exactly one target is required, found {len(targets)}",
                ),
            ),
            obligations=(),
        )
    target = targets[0]

    statuses: dict[str, str] = {}
    reasons: list[Reason] = []
    obligation_summaries: list[dict[str, object]] = []
    for oid, obligation in sorted(graph.obligations.items()):
        status, rs = _evaluate_obligation(
            obligation, graph, target, policy, action, authorization, now
        )
        statuses[oid] = status
        reasons.extend(rs)
        obligation_summaries.append(
            {
                "obligation_id": oid,
                "kind": obligation.kind.value,
                "status": status,
                "mandatory": obligation.mandatory,
            }
        )

    mandatory = [o for o in graph.obligations.values() if o.mandatory]
    if not mandatory:
        verdict = Verdict.INCONCLUSIVE
        reasons.append(
            Reason(ReasonCode.MISSING_EVIDENCE, None, "no mandatory obligations were defined")
        )
    elif any(statuses[o.obligation_id] == VIOLATED for o in mandatory):
        verdict = Verdict.BLOCKED
    elif any(statuses[o.obligation_id] == UNKNOWN for o in mandatory):
        verdict = Verdict.INCONCLUSIVE
    else:
        verdict = Verdict.SAFE_TO_RETIRE

    return Decision(
        verdict=verdict,
        target=target,
        action=action,
        evaluated_at=now,
        reasons=tuple(reasons),
        obligations=tuple(obligation_summaries),
    )
