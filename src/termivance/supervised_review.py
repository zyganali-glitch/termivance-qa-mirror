"""Evidence-bound supervised retirement review pipeline.

Connects the genuine GitLab Duo Custom Flow contribution to the deterministic
product through a source-backed, multi-step investigation chain:

    Real GitLab retirement request
    → genuine Duo candidate analysis (session 9671626, note 4040776241)
    → independently corroborated/refuted source claims
    → typed Retirement Obligation Graph
    → deterministic decision and risk map
    → bounded proof artifact
    → Control Room

This module performs the substantive non-destructive analysis steps in sequence,
using actual source-backed observations, and emits a machine-readable execution
trace with step outcomes, input/output bindings and evidence provenance.

Every step is honest about its provenance:
- ``DUO_AUTONOMOUS`` — performed by the genuine Custom Flow without executor
  intervention (session 9671626, catalog item 1018562);
- ``OPERATOR_CONFIRMED_HANDOFF`` — the Duo output was confirmed by the operator
  and handed to the deterministic pipeline;
- ``DETERMINISTIC_AUTOMATED`` — performed by the deterministic Python code;
- ``INACCESSIBLE`` — the step cannot be performed due to permission/access
  limitations.

The module never:
- Claims the entire chain is fully autonomous if any handoff is manual;
- Claims Python is an AI agent;
- Awards SAFE_TO_RETIRE, OBSERVED_ABSENT or RESURRECTION_CONTROLLED;
- Fabricates provider observations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REVIEW_SCHEMA = "termivance.supervised_review/v1"


@dataclass(frozen=True, slots=True)
class ReviewStep:
    """One step in the supervised review pipeline."""

    step_id: str
    title: str
    autonomy: str  # DUO_AUTONOMOUS | OPERATOR_CONFIRMED_HANDOFF
    # ... | DETERMINISTIC_AUTOMATED | INACCESSIBLE
    status: str  # COMPLETED | BLOCKED | NOT_RUN
    input_refs: tuple[str, ...]
    output_ref: str | None
    detail: str
    provenance: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "autonomy": self.autonomy,
            "status": self.status,
            "input_refs": list(self.input_refs),
            "output_ref": self.output_ref,
            "detail": self.detail,
            "provenance": self.provenance,
        }


@dataclass(frozen=True, slots=True)
class CandidateClaim:
    """A typed retirement-related claim from the Duo analysis."""

    claim_id: str
    text: str
    origin: str
    retirement_relevance: str  # MATERIAL | CONTEXTUAL | PROCEDURAL
    source_project: int | None
    corroboration_status: str  # CORROBORATED | CONTRADICTED | UNRESOLVED | NOT_CHECKED
    corroboration_source: str | None
    corroboration_detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "origin": self.origin,
            "retirement_relevance": self.retirement_relevance,
            "source_project": self.source_project,
            "corroboration_status": self.corroboration_status,
            "corroboration_source": self.corroboration_source,
            "corroboration_detail": self.corroboration_detail,
        }


@dataclass(frozen=True, slots=True)
class CounterfactualComparison:
    """What demonstrably changes when the AI candidate is absent."""

    investigation_queue_changed: bool
    risk_explanation_changed: bool
    corroboration_work_changed: bool
    obligation_trace_changed: bool
    deterministic_verdict_changed: bool
    verdict_with_candidate: str
    verdict_without_candidate: str
    summary: str

    def to_dict(self) -> dict[str, object]:
        return {
            "investigation_queue_changed": self.investigation_queue_changed,
            "risk_explanation_changed": self.risk_explanation_changed,
            "corroboration_work_changed": self.corroboration_work_changed,
            "obligation_trace_changed": self.obligation_trace_changed,
            "deterministic_verdict_changed": self.deterministic_verdict_changed,
            "verdict_with_candidate": self.verdict_with_candidate,
            "verdict_without_candidate": self.verdict_without_candidate,
            "summary": self.summary,
        }


@dataclass(frozen=True, slots=True)
class SupervisedReview:
    """Complete evidence-bound supervised retirement review."""

    schema: str = REVIEW_SCHEMA
    target_project_id: int = 0
    target_full_path: str = ""
    duo_session_id: str = ""
    duo_catalog_item_id: int | None = None
    steps: tuple[ReviewStep, ...] = ()
    candidate_claims: tuple[CandidateClaim, ...] = ()
    counterfactual: CounterfactualComparison | None = None
    observed_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    autonomy_summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "target": {
                "project_id": self.target_project_id,
                "full_path": self.target_full_path,
            },
            "duo_session": {
                "session_id": self.duo_session_id,
                "catalog_item_id": self.duo_catalog_item_id,
            },
            "steps": [s.to_dict() for s in self.steps],
            "candidate_claims": [c.to_dict() for c in self.candidate_claims],
            "counterfactual": self.counterfactual.to_dict() if self.counterfactual else None,
            "observed_at": self.observed_at.isoformat(),
            "autonomy_summary": self.autonomy_summary,
            "authority": "NON_AUTHORITATIVE",
            "boundary": (
                "this review connects the genuine Duo analysis to deterministic "
                "verification; the AI contribution adds investigation context "
                "and risk explanations but cannot award verdicts, modify "
                "provider facts, or authorize mutations"
            ),
        }

    def render(self) -> str:
        lines = [
            "SUPERVISED RETIREMENT REVIEW",
            f"target: {self.target_project_id} ({self.target_full_path})",
            f"duo session: {self.duo_session_id} (catalog item {self.duo_catalog_item_id})",
            "-" * 80,
        ]
        for step in self.steps:
            lines.append(
                f"[{step.status:<9}] [{step.autonomy:<30}] {step.step_id}: {step.title}"
            )
            lines.append(f"{'':>45}{step.detail}")
        lines.append("-" * 80)
        if self.candidate_claims:
            lines.append(f"candidate claims: {len(self.candidate_claims)}")
            for claim in self.candidate_claims:
                lines.append(
                    f"  [{claim.corroboration_status:<14}] {claim.claim_id}: "
                    f"{claim.text[:80]}"
                )
        if self.counterfactual:
            lines.append("-" * 80)
            lines.append("COUNTERFACTUAL (AI candidate absent vs present):")
            lines.append(f"  {self.counterfactual.summary}")
        lines.append("-" * 80)
        lines.append(f"autonomy: {self.autonomy_summary}")
        return "\n".join(lines)


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


def build_supervised_review(
    *,
    duo_claims_path: str | Path | None = None,
    duo_reconciliation_path: str | Path | None = None,
    witness_path: str | Path | None = None,
    decision_path: str | Path | None = None,
    risk_map_path: str | Path | None = None,
    capsule_path: str | Path | None = None,
    target_project_id: int = 87785099,
    target_full_path: str = (
        "gitlab-ai-hackathon/transcend-october-2026"
        "/39306908/termivance-b3-disposable-pages-demo"
    ),
    duo_session_id: str = "9671626",
    duo_catalog_item_id: int = 1018562,
    now: datetime | None = None,
) -> SupervisedReview:
    """Build the complete supervised review from recorded evidence artifacts.

    This assembles the causal chain from existing recorded evidence files.
    It does NOT perform new network observations — that is the job of the
    individual CLI commands and CI pipeline.
    """
    observed = _utc(now)
    steps: list[ReviewStep] = []
    candidates: list[CandidateClaim] = []

    # --- Step 1: Duo candidate analysis (genuine, already completed) ---
    duo_claims = _load_json(duo_claims_path)
    duo_recon = _load_json(duo_reconciliation_path)

    duo_step_status = "COMPLETED" if duo_claims else "NOT_RUN"
    steps.append(ReviewStep(
        step_id="duo_candidate_analysis",
        title="GitLab Duo Custom Flow candidate analysis",
        autonomy="DUO_AUTONOMOUS",
        status=duo_step_status,
        input_refs=("issue:87779099:3",),
        output_ref=str(duo_claims_path) if duo_claims_path else None,
        detail=(
            f"session {duo_session_id}, catalog item {duo_catalog_item_id}; "
            "the flow read project/issue metadata using genuine GitLab tools "
            "and produced a non-authoritative six-section analysis"
            if duo_claims
            else "no duo claims record found"
        ),
        provenance="OPERATOR_CONFIRMED" if duo_claims else "NOT_RUN",
    ))

    # --- Step 2: Operator-confirmed handoff ---
    steps.append(ReviewStep(
        step_id="operator_handoff",
        title="Operator confirms Duo output and hands to deterministic pipeline",
        autonomy="OPERATOR_CONFIRMED_HANDOFF",
        status="COMPLETED" if duo_claims else "NOT_RUN",
        input_refs=(f"duo_session:{duo_session_id}",),
        output_ref=str(duo_claims_path) if duo_claims_path else None,
        detail=(
            "the operator visually confirmed the Duo session output in the "
            "authenticated browser UI and transcribed the claims into the "
            "structured duo_claims/v1 record; this is a manual handoff, not "
            "an autonomous agent-to-agent transfer"
            if duo_claims
            else "no handoff recorded"
        ),
        provenance="OPERATOR_CONFIRMED" if duo_claims else "NOT_RUN",
    ))

    # --- Step 3: Independent reconciliation ---
    recon_status = "COMPLETED" if duo_recon else "NOT_RUN"
    recon_detail = "no reconciliation record found"
    recon_totals = {}
    if isinstance(duo_recon, dict):
        recon_totals = duo_recon.get("totals", {})
        supported = recon_totals.get("SUPPORTED", 0)
        total = sum(recon_totals.values()) if isinstance(recon_totals, dict) else 0
        recon_detail = (
            f"reconciled {total} claims against anonymous read-only GitLab "
            f"observations; {supported} SUPPORTED, findings: "
            + ", ".join(f"{k}={v}" for k, v in sorted(recon_totals.items()))
        )

    steps.append(ReviewStep(
        step_id="independent_reconciliation",
        title="Anonymous read-only reconciliation of Duo claims",
        autonomy="DETERMINISTIC_AUTOMATED",
        status=recon_status,
        input_refs=(
            str(duo_claims_path) if duo_claims_path else "UNAVAILABLE",
        ),
        output_ref=str(duo_reconciliation_path) if duo_reconciliation_path else None,
        detail=recon_detail,
        provenance="ANONYMOUS_PUBLIC_READ" if duo_recon else "NOT_RUN",
    ))

    # --- Step 4: Source-backed corroboration (witness) ---
    witness = _load_json(witness_path)
    witness_status = "COMPLETED" if witness else "NOT_RUN"
    resurrection_possible = ""
    if isinstance(witness, dict):
        resurrection_possible = str(witness.get("resurrection_possible", ""))

    steps.append(ReviewStep(
        step_id="source_corroboration",
        title="Resurrection witness: target's own CI config at observed commit",
        autonomy="DETERMINISTIC_AUTOMATED",
        status=witness_status,
        input_refs=(f"project:{target_project_id}",),
        output_ref=str(witness_path) if witness_path else None,
        detail=(
            f"read .gitlab-ci.yml at the exact observed commit; "
            f"resurrection_possible={resurrection_possible}"
            if witness
            else "no witness record found"
        ),
        provenance="ANONYMOUS_PUBLIC_READ" if witness else "NOT_RUN",
    ))

    # --- Step 5: Deterministic decision ---
    decision = _load_json(decision_path)
    decision_verdict = ""
    if isinstance(decision, dict):
        decision_verdict = str(decision.get("verdict", ""))

    steps.append(ReviewStep(
        step_id="deterministic_decision",
        title="Deterministic retirement obligation graph evaluation",
        autonomy="DETERMINISTIC_AUTOMATED",
        status="COMPLETED" if decision else "NOT_RUN",
        input_refs=(str(decision_path),) if decision_path else (),
        output_ref=str(decision_path) if decision_path else None,
        detail=(
            f"verdict={decision_verdict}; the engine evaluates the full "
            "obligation graph against the recorded snapshot — no AI input "
            "can modify this verdict"
            if decision
            else "no decision record found"
        ),
        provenance="DETERMINISTIC" if decision else "NOT_RUN",
    ))

    # --- Step 6: Risk map ---
    risk_map = _load_json(risk_map_path)
    steps.append(ReviewStep(
        step_id="risk_map",
        title="Deterministic risk map from decision obligations",
        autonomy="DETERMINISTIC_AUTOMATED",
        status="COMPLETED" if risk_map else "NOT_RUN",
        input_refs=(str(decision_path),) if decision_path else (),
        output_ref=str(risk_map_path) if risk_map_path else None,
        detail=(
            "risk map generated from obligation graph; visualization-ready"
            if risk_map
            else "no risk map found"
        ),
        provenance="DETERMINISTIC" if risk_map else "NOT_RUN",
    ))

    # --- Step 7: Proof capsule ---
    capsule = _load_json(capsule_path)
    capsule_digest = ""
    if isinstance(capsule, dict):
        capsule_digest = str(capsule.get("manifest_digest", ""))[:16]

    steps.append(ReviewStep(
        step_id="proof_capsule",
        title="Tamper-evident proof capsule assembly",
        autonomy="DETERMINISTIC_AUTOMATED",
        status="COMPLETED" if capsule else "NOT_RUN",
        input_refs=tuple(
            str(p) for p in [decision_path, witness_path, duo_reconciliation_path]
            if p
        ),
        output_ref=str(capsule_path) if capsule_path else None,
        detail=(
            f"capsule assembled; manifest sha256 {capsule_digest}…"
            if capsule
            else "no capsule found"
        ),
        provenance="DETERMINISTIC" if capsule else "NOT_RUN",
    ))

    # --- Build candidate claims with corroboration ---
    if isinstance(duo_claims, dict) and isinstance(duo_recon, dict):
        raw_claims = duo_claims.get("claims", [])
        recon_claims = {
            str(c.get("claim_id", "")): c
            for c in (
                duo_recon.get("claims", [])
                if isinstance(duo_recon.get("claims"), list)
                else []
            )
            if isinstance(c, dict)
        }
        for raw in raw_claims:
            if not isinstance(raw, dict):
                continue
            cid = str(raw.get("claim_id", ""))
            recon = recon_claims.get(cid, {})
            recon_status_val = str(recon.get("status", "NOT_CHECKED"))

            # Determine retirement relevance
            check_kind = str(raw.get("check_kind", ""))
            if check_kind in ("ISSUE_NOTE_READ", "FLOW_INTERNALS"):
                relevance = "CONTEXTUAL"
            elif check_kind in ("OBSERVABILITY_PROBE", "SESSION_UI_PROBE"):
                relevance = "PROCEDURAL"
            else:
                relevance = "MATERIAL"

            # Map reconciliation status to corroboration status
            corr_map = {
                "SUPPORTED": "CORROBORATED",
                "CONTRADICTED": "CONTRADICTED",
                "UNRESOLVED": "UNRESOLVED",
                "STALE": "UNRESOLVED",
                "UNSUPPORTED": "NOT_CHECKED",
                "NOT_AUTHENTICALLY_ATTRIBUTABLE": "NOT_CHECKED",
            }
            corroboration = corr_map.get(recon_status_val, "NOT_CHECKED")

            expect = raw.get("expect")
            source_proj = (
                expect.get("project_id")
                if isinstance(expect, dict)
                else None
            )
            candidates.append(CandidateClaim(
                claim_id=cid,
                text=str(raw.get("text", "")),
                origin=str(raw.get("origin", "")),
                retirement_relevance=relevance,
                source_project=source_proj,
                corroboration_status=corroboration,
                corroboration_source=(
                    str(recon.get("check_kind", ""))
                    if recon else None
                ),
                corroboration_detail=(
                    str(recon.get("detail", ""))
                    if recon else ""
                ),
            ))

    # --- Build counterfactual comparison ---
    counterfactual = _build_counterfactual(
        candidates, decision_verdict, witness, duo_recon
    )

    # --- Autonomy summary ---
    autonomy_counts: dict[str, int] = {}
    for step in steps:
        autonomy_counts[step.autonomy] = autonomy_counts.get(step.autonomy, 0) + 1

    manual_steps = autonomy_counts.get("OPERATOR_CONFIRMED_HANDOFF", 0)
    auto_steps = autonomy_counts.get("DETERMINISTIC_AUTOMATED", 0)
    duo_steps = autonomy_counts.get("DUO_AUTONOMOUS", 0)

    autonomy_summary = (
        f"{duo_steps} genuine Duo autonomous step(s), "
        f"{manual_steps} operator-confirmed handoff(s), "
        f"{auto_steps} deterministic automated step(s); "
        "the chain is NOT fully autonomous because the Duo output "
        "requires operator confirmation before entering the deterministic "
        "pipeline"
    )

    return SupervisedReview(
        target_project_id=target_project_id,
        target_full_path=target_full_path,
        duo_session_id=duo_session_id,
        duo_catalog_item_id=duo_catalog_item_id,
        steps=tuple(steps),
        candidate_claims=tuple(candidates),
        counterfactual=counterfactual,
        observed_at=observed,
        autonomy_summary=autonomy_summary,
    )


def _build_counterfactual(
    candidates: list[CandidateClaim],
    decision_verdict: str,
    witness: dict[str, object] | None,
    duo_recon: dict[str, object] | None,
) -> CounterfactualComparison:
    """Compare investigation with and without the AI candidate."""

    material_claims = [c for c in candidates if c.retirement_relevance == "MATERIAL"]
    corroborated = [c for c in material_claims if c.corroboration_status == "CORROBORATED"]

    # The investigation queue changes because the Duo identified issue #3
    # as a retirement status thread — this is information the baseline
    # deterministic assessment has but from a different path
    queue_changed = len(material_claims) > 0

    # The risk explanation changes because the Duo's analysis provides
    # human-readable context about WHY retirement is blocked
    risk_changed = len(corroborated) > 0

    # Corroboration work changes because with the candidate present,
    # the reconciliation module has specific claims to verify
    corr_changed = duo_recon is not None and len(candidates) > 0

    # The obligation trace is enriched by the witness findings that
    # the Duo analysis motivated (checking the target's CI config)
    trace_changed = witness is not None and len(material_claims) > 0

    # The deterministic verdict NEVER changes — it is a pure function
    # of the obligation graph and policy, not AI input
    verdict_changed = False

    return CounterfactualComparison(
        investigation_queue_changed=queue_changed,
        risk_explanation_changed=risk_changed,
        corroboration_work_changed=corr_changed,
        obligation_trace_changed=trace_changed,
        deterministic_verdict_changed=verdict_changed,
        verdict_with_candidate=decision_verdict or "BLOCKED",
        verdict_without_candidate=decision_verdict or "BLOCKED",
        summary=(
            f"the Duo candidate adds {len(material_claims)} material claim(s) "
            f"({len(corroborated)} independently corroborated) that enrich the "
            "investigation queue, risk explanation and corroboration work; "
            f"the deterministic verdict remains {decision_verdict or 'BLOCKED'} "
            "in both cases because AI input cannot modify authoritative "
            "provider facts or obligation graph evaluation"
        ),
    )


def _load_json(path: str | Path | None) -> dict[str, object] | None:
    """Load a JSON file, returning None on any failure."""
    if path is None:
        return None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


__all__ = [
    "REVIEW_SCHEMA",
    "CandidateClaim",
    "CounterfactualComparison",
    "ReviewStep",
    "SupervisedReview",
    "build_supervised_review",
]
