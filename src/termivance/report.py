"""Judge-readable rendering of a deterministic decision.

Pure formatting only: no network, no mutation. Kept separate from the read-only
evaluator so rendering can never trigger an API call.
"""

from __future__ import annotations

from termivance.discovery import Snapshot
from termivance.engine import Decision
from termivance.graph import Evidence
from termivance.verdicts import Verdict


def _evidence_table(graph_evidence: list[Evidence]) -> str:
    rows = ["| evidence | kind | class | status | observed_at | digest |",
            "|---|---|---|---|---|---|"]
    for ev in sorted(graph_evidence, key=lambda e: e.evidence_id):
        rows.append(
            f"| `{ev.evidence_id}` | {ev.kind.value} | {ev.classification.value} | "
            f"{ev.status} | {ev.observed_at.isoformat()} | `{ev.digest()[:12]}` |"
        )
    return "\n".join(rows)


def render_decision_report(
    decision: Decision, snapshot: Snapshot, graph_evidence: list[Evidence]
) -> str:
    """Render a sanitized, non-authoritative markdown report of a decision."""
    target = decision.target
    obs_time = snapshot.observed_at.isoformat()
    lines = [
        "## Termivance B2 — Deterministic Retirement Decision (READ-ONLY)",
        "",
        "### What is being retired?",
        f"- Target: project `{target.project_id}` `{target.full_path}` "
        f"({target.resource_kind}), action `{decision.action}`.",
        "- Provider: GitLab (read-only observations only).",
        "",
        "### Deterministic result",
        f"- **Verdict: `{decision.verdict.value}`** (computed by deterministic code).",
        f"- Evaluated at: {decision.evaluated_at.isoformat()}",
        f"- Observation time: {obs_time}",
        f"- Classification: `{snapshot.classification.value}`",
        "- Destructive API operations performed: **0** (read-only client).",
        "",
        "### Blocking obligations and reasons",
    ]
    if decision.reasons:
        lines.append("| reason | obligation | detail | evidence |")
        lines.append("|---|---|---|---|")
        for r in decision.reasons:
            lines.append(
                f"| `{r.code.value}` | `{r.obligation_id or '-'}` | {r.detail} | "
                f"`{r.evidence_id or '-'}` |"
            )
    else:
        lines.append("_No blocking reasons._")

    lines += [
        "",
        "### Obligation status",
        "| obligation | kind | mandatory | status |",
        "|---|---|---|---|",
    ]
    for o in decision.obligations:
        lines.append(f"| `{o['obligation_id']}` | {o['kind']} | {o['mandatory']} | {o['status']} |")

    lines += ["", "### Evidence provenance", _evidence_table(graph_evidence)]

    lines += ["", "### What would resolve the block"]
    conds = decision.safe_conditions()
    if conds:
        lines += [f"- {c}" for c in conds]
    else:
        lines.append("- Nothing; obligations are satisfied under the checked scope.")

    lines += [
        "",
        "### Authority boundary",
        "- This verdict is produced by deterministic Python over typed facts.",
        "- A GitLab Duo agent may *explain* this result but cannot compute or override it.",
        "- `SAFE_TO_RETIRE` would mean eligibility under the checked protocol scope only; "
        "it is not evidence of removal. `OBSERVED_ABSENT` / "
        "`RESURRECTION_CONTROLLED` are out of B2 scope.",
        "",
        f"_Termivance deterministic status: {decision.verdict.value}._",
    ]
    if decision.verdict == Verdict.BLOCKED:
        lines.append(
            "No destructive operation was attempted. This is a dry-run eligibility evaluation."
        )
    return "\n".join(lines)
