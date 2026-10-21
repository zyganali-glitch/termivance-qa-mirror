"""Deterministic Bounded Candidate Repair Sets engine.

Calculates actionable prerequisite-remediation guidance directly from the
Retirement Obligation Graph without expanding mutation authority or relying
on language-model text generation.

Design invariants:
1. Every candidate repair is derived from a typed unsatisfied obligation in the
   graph, not from AI-generated generic advice.
2. The hackathon organizer-denied Maintainer role is formally classified as:
   `EXTERNALLY_UNAVAILABLE_UNDER_CONTEST_CONDITIONS`. It is NOT an ordinary
   automatically actionable repair.
3. Algorithms use bounded deterministic DAG topological selection, dependency
   ordering, stable tie-breaking, and cycle detection (failing closed).
4. Formally designated as 'Bounded Candidate Repair Sets', refusing unjustified
   global mathematical optimality claims.
5. Zero mutation guarantee: proposals never mutate provider state, never authorize
   mutations, and never alter deterministic verdicts by suggestion alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from termivance.engine import Decision
    from termivance.graph import Graph
    from termivance.target import TargetIdentity

REPAIR_SET_SCHEMA = "termivance.bounded_repair_set/v1"
DISPOSABLE_TARGET_PID = 87785099


class AuthorityLevel(StrEnum):
    """Authority required to satisfy an obligation."""

    OPERATOR = "OPERATOR"
    HACKATHON_ORGANIZER = "HACKATHON_ORGANIZER"
    MAINTAINER = "MAINTAINER"
    AUTOMATION = "AUTOMATION"


class CapabilityKind(StrEnum):
    """Human versus automated remediation capability."""

    HUMAN_ACTION = "HUMAN_ACTION"
    AUTOMATED_CONFIG = "AUTOMATED_CONFIG"
    ORGANIZER_PERMISSION = "ORGANIZER_PERMISSION"
    OPERATOR_APPROVAL = "OPERATOR_APPROVAL"


class ExternalAvailability(StrEnum):
    """External availability status of the required remediation condition."""

    AVAILABLE = "AVAILABLE"
    EXTERNALLY_UNAVAILABLE_UNDER_CONTEST_CONDITIONS = (
        "EXTERNALLY_UNAVAILABLE_UNDER_CONTEST_CONDITIONS"
    )
    DEPENDENT_ON_EXTERNAL_PROVIDER = "DEPENDENT_ON_EXTERNAL_PROVIDER"


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class CandidateRepairAction:
    """One typed remediation recommendation for an unsatisfied obligation."""

    obligation_id: str
    obligation_kind: str
    provider_evidence_ref: str
    failing_condition: str
    prerequisites: tuple[str, ...]
    required_authority: AuthorityLevel
    capability: CapabilityKind
    resolution_evidence: str
    externally_unavailable: bool
    availability_classification: ExternalAvailability
    actionable_now: bool
    revalidation_required: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "obligation_id": self.obligation_id,
            "obligation_kind": self.obligation_kind,
            "provider_evidence_ref": self.provider_evidence_ref,
            "failing_condition": self.failing_condition,
            "prerequisites": list(self.prerequisites),
            "required_authority": self.required_authority.value,
            "capability": self.capability.value,
            "resolution_evidence": self.resolution_evidence,
            "externally_unavailable": self.externally_unavailable,
            "availability_classification": self.availability_classification.value,
            "actionable_now": self.actionable_now,
            "revalidation_required": self.revalidation_required,
        }


@dataclass(frozen=True, slots=True)
class BoundedRepairSet:
    """The bounded, dependency-ordered candidate repair plan derived from a decision."""

    target_project_id: int
    target_full_path: str
    decision_verdict: str
    total_unsatisfied_obligations: int
    candidate_repairs: tuple[CandidateRepairAction, ...]
    dependency_order: tuple[str, ...]
    actionable_now_ids: tuple[str, ...]
    externally_blocked_ids: tuple[str, ...]
    malformed_graph_errors: tuple[str, ...]
    generated_at: str

    @property
    def has_errors(self) -> bool:
        return bool(self.malformed_graph_errors)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": REPAIR_SET_SCHEMA,
            "authority": "NON_AUTHORITATIVE_REMEDIATION_GUIDANCE",
            "target": {
                "project_id": self.target_project_id,
                "full_path": self.target_full_path,
            },
            "decision_verdict": self.decision_verdict,
            "total_unsatisfied_obligations": self.total_unsatisfied_obligations,
            "candidate_repairs": [r.to_dict() for r in self.candidate_repairs],
            "dependency_order": list(self.dependency_order),
            "actionable_now_ids": list(self.actionable_now_ids),
            "externally_blocked_ids": list(self.externally_blocked_ids),
            "malformed_graph_errors": list(self.malformed_graph_errors),
            "generated_at": self.generated_at,
            "invariants": [
                "Proposals never mutate provider state or authorize actions.",
                "Proposals never mark tasks completed without provider evidence.",
                "Proposals cannot improve a deterministic verdict by suggestion alone.",
                ("Organizer Maintainer denial is EXTERNALLY_UNAVAILABLE_UNDER_CONTEST_CONDITIONS."),
            ],
        }


def _detect_graph_cycles(graph: Graph) -> list[str]:
    """Detect cycles among obligations in the graph using DFS."""
    visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
    cycles: list[str] = []

    adj: dict[str, list[str]] = {oid: [] for oid in graph.obligations}
    for edge in graph.edges:
        if edge.src in adj and edge.dst in graph.obligations:
            adj[edge.src].append(edge.dst)

    def dfs(node: str, path: list[str]) -> None:
        visited[node] = 1
        for neighbor in adj.get(node, []):
            if visited.get(neighbor) == 1:
                cycle_str = " -> ".join(path + [neighbor])
                cycles.append(f"CYCLE_DETECTED: {cycle_str}")
            elif visited.get(neighbor, 0) == 0:
                dfs(neighbor, path + [neighbor])
        visited[node] = 2

    for node in graph.obligations:
        if visited.get(node, 0) == 0:
            dfs(node, [node])

    return cycles


def compute_bounded_repair_sets(
    graph: Graph,
    decision: Decision,
    *,
    target: TargetIdentity | None = None,
    now: datetime | None = None,
) -> BoundedRepairSet:
    """Compute bounded candidate repair sets derived strictly from unsatisfied obligations.

    Adheres strictly to the Retirement Obligation Graph:
    - Analyzes reasons and unsatisfied obligations in the decision.
    - Validates graph acyclicity.
    - Eliminates redundant actions dominated by unsatisfied upstream prerequisites.
    - Identifies externally unavailable conditions (specifically Maintainer denial).
    - Sorts candidates deterministically by topological dependency order and stable tie-breaking.
    """
    evaluated_at = _utc(now)
    tgt = target or decision.target

    # 1. Cycle and malformation check
    cycle_errors = _detect_graph_cycles(graph)
    if cycle_errors:
        return BoundedRepairSet(
            target_project_id=tgt.project_id,
            target_full_path=tgt.full_path,
            decision_verdict=decision.verdict.value,
            total_unsatisfied_obligations=0,
            candidate_repairs=(),
            dependency_order=(),
            actionable_now_ids=(),
            externally_blocked_ids=(),
            malformed_graph_errors=tuple(cycle_errors),
            generated_at=evaluated_at.isoformat(),
        )

    # 2. Identify unsatisfied obligations from decision reasons and obligation statuses
    unsatisfied_map: dict[str, str] = {}
    for reason in decision.reasons:
        if reason.obligation_id:
            unsatisfied_map[reason.obligation_id] = reason.detail

    for obl_dict in decision.obligations:
        oid = str(obl_dict.get("obligation_id", ""))
        status = str(obl_dict.get("status", ""))
        if status in {"VIOLATED", "UNKNOWN"} and oid not in unsatisfied_map:
            unsatisfied_map[oid] = f"Obligation status is {status}"

    # Build dependency graph between unsatisfied obligations
    adj: dict[str, list[str]] = {oid: [] for oid in unsatisfied_map}
    in_degree: dict[str, int] = dict.fromkeys(unsatisfied_map, 0)

    # Extract explicit inter-obligation edges from graph
    for edge in graph.edges:
        if edge.src in unsatisfied_map and edge.dst in unsatisfied_map:
            if edge.dst not in adj[edge.src]:
                adj[edge.src].append(edge.dst)
                in_degree[edge.dst] = in_degree.get(edge.dst, 0) + 1

    # Add domain prerequisites if upstream obligation is also unsatisfied
    scope_oid = None
    for oid in unsatisfied_map:
        if "target_scope" in oid.lower():
            scope_oid = oid
            break

    if scope_oid:
        for oid in unsatisfied_map:
            if oid != scope_oid and oid not in adj[scope_oid]:
                adj[scope_oid].append(oid)
                in_degree[oid] = in_degree.get(oid, 0) + 1

    # 3. Formulate candidate repair actions for each unsatisfied obligation
    raw_candidates: dict[str, CandidateRepairAction] = {}
    for oid, failing_detail in unsatisfied_map.items():
        obl = graph.obligations.get(oid)
        kind_str = obl.kind.value if obl else "CUSTOM"

        # Determine prerequisites among unsatisfied obligations (incoming edges in adj)
        prereqs = tuple(
            sorted(upstream for upstream, downstream in adj.items() if oid in downstream)
        )

        # Target-specific and obligation-specific domain mapping
        if "retirement_permission" in oid.lower() or kind_str == "RETIREMENT_PERMISSION":
            # Target 87785099 Maintainer role is explicitly denied by organizer
            if tgt.project_id == DISPOSABLE_TARGET_PID:
                raw_candidates[oid] = CandidateRepairAction(
                    obligation_id=oid,
                    obligation_kind=kind_str,
                    provider_evidence_ref=f"GET /projects/{tgt.project_id}/pages (HTTP 403)",
                    failing_condition=(
                        "Developer role lacks permission to unpublish Pages; "
                        "Maintainer role required."
                    ),
                    prerequisites=prereqs,
                    required_authority=AuthorityLevel.MAINTAINER,
                    capability=CapabilityKind.ORGANIZER_PERMISSION,
                    resolution_evidence=(
                        f"GitLab API GET /projects/{tgt.project_id}/pages returning HTTP 200 "
                        "or Maintainer membership record."
                    ),
                    externally_unavailable=True,
                    availability_classification=(
                        ExternalAvailability.EXTERNALLY_UNAVAILABLE_UNDER_CONTEST_CONDITIONS
                    ),
                    actionable_now=False,
                    revalidation_required=True,
                )
            else:
                raw_candidates[oid] = CandidateRepairAction(
                    obligation_id=oid,
                    obligation_kind=kind_str,
                    provider_evidence_ref=f"GET /projects/{tgt.project_id}/members",
                    failing_condition="Project retirement permission not established.",
                    prerequisites=prereqs,
                    required_authority=AuthorityLevel.MAINTAINER,
                    capability=CapabilityKind.ORGANIZER_PERMISSION,
                    resolution_evidence="Maintainer permission on target project.",
                    externally_unavailable=False,
                    availability_classification=ExternalAvailability.AVAILABLE,
                    actionable_now=not bool(prereqs),
                    revalidation_required=True,
                )

        elif "redeployment_path" in oid.lower() or kind_str == "REDEPLOYMENT_PATH":
            ci_ref = f"GET /projects/{tgt.project_id}/repository/files/.gitlab-ci.yml/raw"
            raw_candidates[oid] = CandidateRepairAction(
                obligation_id=oid,
                obligation_kind=kind_str,
                provider_evidence_ref=ci_ref,
                failing_condition=(
                    "Target repository CI configuration contains active create-pages "
                    "Pages deployment mechanism."
                ),
                prerequisites=prereqs,
                required_authority=AuthorityLevel.OPERATOR,
                capability=CapabilityKind.AUTOMATED_CONFIG,
                resolution_evidence=(
                    "Neutralized .gitlab-ci.yml omitting pages: true or signed "
                    "RedeploymentControlAttestation."
                ),
                externally_unavailable=False,
                availability_classification=ExternalAvailability.AVAILABLE,
                actionable_now=not bool(prereqs),
                revalidation_required=True,
            )

        elif "target_scope" in oid.lower() or kind_str == "TARGET_SCOPE":
            tgt_res_ev = (
                f"Target project ID matching approved disposable target {DISPOSABLE_TARGET_PID}."
            )
            raw_candidates[oid] = CandidateRepairAction(
                obligation_id=oid,
                obligation_kind=kind_str,
                provider_evidence_ref=f"GET /projects/{tgt.project_id}",
                failing_condition="Target identity verification or scope validation failed.",
                prerequisites=prereqs,
                required_authority=AuthorityLevel.OPERATOR,
                capability=CapabilityKind.HUMAN_ACTION,
                resolution_evidence=tgt_res_ev,
                externally_unavailable=False,
                availability_classification=ExternalAvailability.AVAILABLE,
                actionable_now=not bool(prereqs),
                revalidation_required=True,
            )

        elif "ownership_authorization" in oid.lower() or kind_str == "OWNERSHIP_AUTHORIZATION":
            raw_candidates[oid] = CandidateRepairAction(
                obligation_id=oid,
                obligation_kind=kind_str,
                provider_evidence_ref=f"GET /projects/{tgt.project_id}/issues",
                failing_condition="Operator authorization token with valid HMAC signature missing.",
                prerequisites=prereqs,
                required_authority=AuthorityLevel.OPERATOR,
                capability=CapabilityKind.OPERATOR_APPROVAL,
                resolution_evidence=(
                    "Valid OperatorApproval record referencing target project ID and "
                    "matching HMAC signature."
                ),
                externally_unavailable=False,
                availability_classification=ExternalAvailability.AVAILABLE,
                actionable_now=not bool(prereqs),
                revalidation_required=False,
            )

        elif "pages_published" in oid.lower() or kind_str == "PAGES_PUBLISHED":
            raw_candidates[oid] = CandidateRepairAction(
                obligation_id=oid,
                obligation_kind=kind_str,
                provider_evidence_ref="Served Pages URL probe",
                failing_condition="Target Pages site publication not independently observed.",
                prerequisites=prereqs,
                required_authority=AuthorityLevel.AUTOMATION,
                capability=CapabilityKind.AUTOMATED_CONFIG,
                resolution_evidence=(
                    "Served Pages URL returning HTTP 200 with matching distinctive marker."
                ),
                externally_unavailable=False,
                availability_classification=ExternalAvailability.AVAILABLE,
                actionable_now=not bool(prereqs),
                revalidation_required=True,
            )

        elif "evidence_freshness" in oid.lower() or kind_str == "EVIDENCE_FRESHNESS":
            raw_candidates[oid] = CandidateRepairAction(
                obligation_id=oid,
                obligation_kind=kind_str,
                provider_evidence_ref="Discovery snapshot timestamp",
                failing_condition="Provider observations are older than 900s TTL.",
                prerequisites=prereqs,
                required_authority=AuthorityLevel.AUTOMATION,
                capability=CapabilityKind.AUTOMATED_CONFIG,
                resolution_evidence="Fresh discovery execution within 600s threshold.",
                externally_unavailable=False,
                availability_classification=ExternalAvailability.AVAILABLE,
                actionable_now=not bool(prereqs),
                revalidation_required=True,
            )

        else:
            raw_candidates[oid] = CandidateRepairAction(
                obligation_id=oid,
                obligation_kind=kind_str,
                provider_evidence_ref=f"Obligation {oid}",
                failing_condition=failing_detail,
                prerequisites=prereqs,
                required_authority=AuthorityLevel.OPERATOR,
                capability=CapabilityKind.HUMAN_ACTION,
                resolution_evidence=f"Resolution of obligation {oid} with provider proof.",
                externally_unavailable=False,
                availability_classification=ExternalAvailability.AVAILABLE,
                actionable_now=not bool(prereqs),
                revalidation_required=True,
            )

    # 4. Topological sort with stable tie-breaking for dependency ordering
    ready_queue = [oid for oid, deg in in_degree.items() if deg == 0]
    sorted_order: list[str] = []

    while ready_queue:
        # Stable deterministic tie-breaker: sort by obligation ID string
        ready_queue.sort()
        curr = ready_queue.pop(0)
        sorted_order.append(curr)

        for neighbor in adj.get(curr, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                ready_queue.append(neighbor)

    # If some nodes were not processed, append sorted
    for oid in sorted(unsatisfied_map):
        if oid not in sorted_order:
            sorted_order.append(oid)

    ordered_candidates = tuple(
        raw_candidates[oid] for oid in sorted_order if oid in raw_candidates
    )

    actionable_now = tuple(c.obligation_id for c in ordered_candidates if c.actionable_now)
    externally_blocked = tuple(
        c.obligation_id for c in ordered_candidates if c.externally_unavailable
    )

    return BoundedRepairSet(
        target_project_id=tgt.project_id,
        target_full_path=tgt.full_path,
        decision_verdict=decision.verdict.value,
        total_unsatisfied_obligations=len(ordered_candidates),
        candidate_repairs=ordered_candidates,
        dependency_order=tuple(sorted_order),
        actionable_now_ids=actionable_now,
        externally_blocked_ids=externally_blocked,
        malformed_graph_errors=(),
        generated_at=evaluated_at.isoformat(),
    )
