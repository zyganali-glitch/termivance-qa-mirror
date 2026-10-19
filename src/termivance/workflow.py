"""Single-flow retirement workflow orchestration (Capability 6).

Wraps the ONE real executor path (:func:`termivance.retirement.retire_pages`)
into an explicit, auditable stage plan. The workflow module itself never
mutates: it *plans* the ordered steps, checks which artifacts already exist,
and reports each stage as ``COMPLETE``/``BLOCKED``/``NOT_RUN`` based only on
recorded files. The actual destructive step remains exactly the single
``retire-pages --execute`` invocation — there is no second mutation code path
here, in keeping with the one-real-flow architecture.

Stage order (each depends on the previous artifact):

1.  ``snapshot``        — read-only discovery record (``discover`` command)
2.  ``decision``        — deterministic engine decision on that snapshot
3.  ``authorization``   — operator authorization JSON + approval template
4.  ``approval_issue``  — operator-issued GitLab issue (GUI, outside the agent)
5.  ``execute``         — the single authorized flow (eligibility, revalidation,
    durable ledger reservation, one DELETE, independent read-back)
6.  ``absence``         — receipt-bound independent observation
7.  ``capsule``         — proof capsule assembled from the recorded artifacts

``plan()`` renders the exact commands. ``assess()`` takes artifact paths and
classifies every stage without inventing any state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

WORKFLOW_SCHEMA = "termivance.workflow/v1"

COMPLETE = "COMPLETE"
BLOCKED = "BLOCKED"
NOT_RUN = "NOT_RUN"

STAGES = (
    "snapshot",
    "decision",
    "authorization",
    "approval_issue",
    "execute",
    "absence",
    "capsule",
)


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class StagePlan:
    stage: str
    command: str
    produces: str
    depends_on: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "command": self.command,
            "produces": self.produces,
            "depends_on": list(self.depends_on),
        }


@dataclass(frozen=True, slots=True)
class WorkflowPlan:
    target_project_id: int
    target_full_path: str
    stages: tuple[StagePlan, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": WORKFLOW_SCHEMA,
            "mode": "SINGLE_DUO_FLOW",
            "target": {
                "project_id": self.target_project_id,
                "full_path": self.target_full_path,
            },
            "stages": [s.to_dict() for s in self.stages],
        }

    def render(self) -> str:
        lines = [
            "TERMIVANCE SINGLE-FLOW RETIREMENT PLAN",
            f"target: project {self.target_project_id} ({self.target_full_path})",
            "",
        ]
        for index, stage in enumerate(self.stages, start=1):
            lines.append(f"{index}. {stage.stage}")
            lines.append(f"   run:     {stage.command}")
            lines.append(f"   produces: {stage.produces}")
            if stage.depends_on:
                lines.append(f"   needs:    {', '.join(stage.depends_on)}")
        lines.append("")
        lines.append(
            "The destructive step is stage 5 only, and only ever through the "
            "one real GitLab Duo Custom Flow executor path "
            "(retire-pages --execute with ledger + GitLab approval record)."
        )
        return "\n".join(lines)


def plan(*, project_id: int, full_path: str, out_dir: str | Path) -> WorkflowPlan:
    """The canonical stage plan for one exact target (real, runnable commands)."""
    out = Path(out_dir)
    pid = str(project_id)
    return WorkflowPlan(
        target_project_id=project_id,
        target_full_path=full_path,
        stages=(
            StagePlan(
                "snapshot",
                f"termivance discover --project-id {pid} --save {out / 'snapshot.json'}",
                "read-only discovery record (RECORDED_LIVE)",
                (),
            ),
            StagePlan(
                "decision",
                f"termivance evaluate --from-record {out / 'snapshot.json'} "
                f"--policy <policy.json> --json > {out / 'decision.json'}",
                "deterministic engine decision",
                ("snapshot",),
            ),
            StagePlan(
                "authorization",
                "termivance approval-template --authorization config/authorization.json",
                "operator paste-ready approval statement",
                ("snapshot",),
            ),
            StagePlan(
                "approval_issue",
                "(operator, in the GitLab web UI) open one issue in project "
                f"{project_id}, paste the statement as its description and keep "
                "it OPEN",
                "GitLab-authenticated approval record (issue iid)",
                ("authorization",),
            ),
            StagePlan(
                "execute",
                f"termivance retire-pages --project-id {pid} --url <served-url> "
                "--marker <marker> --policy <policy.json> --authorization "
                "<auth.json> --ledger evidence/ledger.json --approval-project-id "
                f"{pid} --approval-issue-iid <iid> --execute --json > "
                f"{out / 'receipt.json'}",
                "retirement receipt from the ONE real authorized flow",
                ("snapshot", "decision", "authorization", "approval_issue"),
            ),
            StagePlan(
                "absence",
                f"termivance observe-absence --project-id {pid} --url <served-url> "
                f"--receipt {out / 'receipt.json'} --ledger evidence/ledger.json",
                "receipt-bound bounded absence probe",
                ("execute",),
            ),
            StagePlan(
                "capsule",
                f"termivance capsule-build --receipt {out / 'receipt.json'} "
                f"--out {out / 'proof_capsule.json'}",
                "tamper-evident proof capsule (integrity-verifiable)",
                ("execute",),
            ),
        ),
    )


@dataclass(frozen=True, slots=True)
class StageStatus:
    stage: str
    state: str
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"stage": self.stage, "state": self.state, "detail": self.detail}


def _stage_from_files(stage: str, artifacts: dict[str, Path]) -> StageStatus:
    artifact = artifacts.get(stage)
    if artifact is None or not artifact.is_file():
        return StageStatus(stage, NOT_RUN, f"no artifact supplied for stage {stage!r}")
    try:
        data = json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return StageStatus(stage, BLOCKED, f"artifact {artifact} is unreadable: {exc}")
    if not isinstance(data, dict):
        return StageStatus(stage, BLOCKED, f"artifact {artifact} is not a JSON object")

    if stage == "snapshot":
        classification = str(data.get("classification"))
        state = COMPLETE if classification else BLOCKED
        detail = f"snapshot classification={classification or 'missing'}"
        return StageStatus(stage, state, detail)
    if stage == "decision":
        verdict = str(data.get("verdict"))
        state = COMPLETE if verdict else BLOCKED
        return StageStatus(stage, state, f"decision verdict={verdict or 'missing'}")
    if stage == "authorization":
        state = COMPLETE if data.get("operator_approval") else BLOCKED
        detail = (
            "operator approval block present"
            if state == COMPLETE
            else "no operator approval block"
        )
        return StageStatus(stage, state, detail)
    if stage == "approval_issue":
        iid = data.get("issue_iid") or data.get("iid")
        state = COMPLETE if iid else NOT_RUN
        return StageStatus(stage, state, f"approval issue iid={iid or 'missing'}")
    if stage == "execute":
        attempted = data.get("mutation_attempted") is True
        verdict = str(data.get("verdict") or "")
        if attempted and verdict in {"RETIRED", "OBSERVED_ABSENT", "INCONCLUSIVE"}:
            return StageStatus(
                stage, COMPLETE, f"one mutation attempted, receipt verdict={verdict}"
            )
        if verdict == "BLOCKED":
            return StageStatus(stage, BLOCKED, "the executor refused the mutation (BLOCKED)")
        return StageStatus(stage, NOT_RUN, f"receipt state={verdict or 'missing'}")
    if stage == "absence":
        verdict = str(data.get("verdict") or "")
        state = COMPLETE if verdict else NOT_RUN
        return StageStatus(stage, state, f"absence verdict={verdict or 'missing'}")
    if stage == "capsule":
        manifest = data.get("manifest_digest")
        state = COMPLETE if manifest else BLOCKED
        digest = str(manifest)[:16] + "…" if manifest else "missing"
        return StageStatus(stage, state, f"manifest digest sha256 {digest}")
    return StageStatus(stage, NOT_RUN, "unknown stage")


def assess(artifacts: dict[str, Path], plan_: WorkflowPlan) -> dict[str, object]:
    """Classify every planned stage from recorded artifacts. Invents nothing."""
    stage_map = {stage.stage: stage for stage in plan_.stages}
    statuses = [_stage_from_files(stage, artifacts) for stage in stage_map]
    return {
        "schema": WORKFLOW_SCHEMA,
        "mode": "ARTIFACT_ASSESSMENT",
        "target": {
            "project_id": plan_.target_project_id,
            "full_path": plan_.target_full_path,
        },
        "stages": [s.to_dict() for s in statuses],
        "summary": {
            stage: status.state for stage, status in zip(stage_map, statuses, strict=True)
        },
        "observed_at": _utc().isoformat(),
    }


def render_assessment(assessment: dict[str, object]) -> str:
    lines = ["WORKFLOW ASSESSMENT", "-" * 64]
    for stage in assessment.get("stages", ()):  # type: ignore[union-attr]
        assert isinstance(stage, dict)
        lines.append(f"[{stage['state']:<8}] {stage['stage']:<15} {stage['detail']}")
    lines.append("-" * 64)
    lines.append("states are read from recorded artifacts only; nothing is inferred")
    return "\n".join(lines)


__all__ = [
    "BLOCKED",
    "COMPLETE",
    "NOT_RUN",
    "STAGES",
    "StagePlan",
    "StageStatus",
    "WorkflowPlan",
    "WORKFLOW_SCHEMA",
    "assess",
    "plan",
    "render_assessment",
]
