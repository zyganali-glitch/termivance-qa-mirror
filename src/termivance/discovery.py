"""Read-only GitLab discovery and graph construction.

Turns real, read-only GitLab API observations into a
:class:`termivance.graph.Graph`. Every observation carries provenance
(endpoint, method, status, timestamp, freshness, classification, digest).

A snapshot may be replayed from a record. Recorded observations keep the
``RECORDED_LIVE`` classification and are never presented as a new network read.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from termivance.engine import DEFAULT_ACTION
from termivance.gitlab_client import ApiResult, GitLabClient
from termivance.graph import (
    Dependency,
    DependencyKind,
    Evidence,
    EvidenceClass,
    EvidenceKind,
    Graph,
    ObligationKind,
    Relation,
)
from termivance.target import TargetIdentity

DEFAULT_TTL_SECONDS = 900

#: obligations that always apply to a retirement decision
STANDARD_OBLIGATIONS: tuple[tuple[ObligationKind, str], ...] = (
    (ObligationKind.TARGET_SCOPE, "target is in the permitted, non-protected retirement scope"),
    (
        ObligationKind.OWNERSHIP_AUTHORIZATION,
        "an exact-target authorization exists for the requested action",
    ),
    (ObligationKind.IDENTITY_BINDING, "all evidence is bound to the exact target identity"),
    (
        ObligationKind.PROVIDER_OBSERVATION,
        "a fresh provider observation of the target is available",
    ),
    (ObligationKind.UNRESOLVED_WORK, "no unresolved retirement-related work item remains"),
    (
        ObligationKind.REDEPLOYMENT_PATH,
        "no active mechanism can redeploy or recreate the target",
    ),
)

_EVIDENCE_OBLIGATIONS: dict[EvidenceKind, tuple[ObligationKind, ...]] = {
    EvidenceKind.PROJECT_IDENTITY: (
        ObligationKind.PROVIDER_OBSERVATION,
        ObligationKind.IDENTITY_BINDING,
    ),
    EvidenceKind.VISIBILITY: (ObligationKind.IDENTITY_BINDING,),
    EvidenceKind.BRANCH: (ObligationKind.IDENTITY_BINDING,),
    EvidenceKind.OPEN_ISSUES: (ObligationKind.UNRESOLVED_WORK,),
    EvidenceKind.CI_CONFIG: (ObligationKind.REDEPLOYMENT_PATH,),
}


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ObservationRecord:
    kind: EvidenceKind
    method: str
    endpoint: str
    status: int | None
    error_kind: str | None
    detail: dict[str, object]
    observed_at: datetime
    fresh_until: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "method": self.method,
            "endpoint": self.endpoint,
            "status": self.status,
            "error_kind": self.error_kind,
            "detail": self.detail,
            "observed_at": _utc(self.observed_at).isoformat(),
            "fresh_until": _utc(self.fresh_until).isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ObservationRecord:
        return cls(
            kind=EvidenceKind(data["kind"]),  # type: ignore[arg-type]
            method=str(data["method"]),
            endpoint=str(data["endpoint"]),
            status=data.get("status"),  # type: ignore[arg-type]
            error_kind=data.get("error_kind"),  # type: ignore[arg-type]
            detail=dict(data.get("detail") or {}),  # type: ignore[arg-type]
            observed_at=datetime.fromisoformat(str(data["observed_at"])),
            fresh_until=datetime.fromisoformat(str(data["fresh_until"])),
        )


@dataclass(frozen=True, slots=True)
class Snapshot:
    target: TargetIdentity
    action: str
    observed_at: datetime
    ttl_seconds: int
    classification: EvidenceClass
    records: tuple[ObservationRecord, ...] = field(default_factory=tuple)

    def record(self, kind: EvidenceKind) -> ObservationRecord | None:
        for r in self.records:
            if r.kind == kind:
                return r
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "termivance.gitlab_snapshot/v1",
            "target": self.target.to_dict(),
            "action": self.action,
            "observed_at": _utc(self.observed_at).isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "classification": self.classification.value,
            "records": [r.to_dict() for r in self.records],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Snapshot:
        return cls(
            target=TargetIdentity.from_dict(dict(data["target"])),  # type: ignore[arg-type]
            action=str(data.get("action", DEFAULT_ACTION)),
            observed_at=datetime.fromisoformat(str(data["observed_at"])),
            ttl_seconds=int(data.get("ttl_seconds", DEFAULT_TTL_SECONDS)),  # type: ignore[arg-type]
            classification=EvidenceClass(str(data.get("classification", "RECORDED_LIVE"))),
            records=tuple(
                ObservationRecord.from_dict(dict(r))  # type: ignore[arg-type]
                for r in (data.get("records") or [])  # type: ignore[union-attr]
            ),
        )


def _record(
    kind: EvidenceKind,
    result: ApiResult,
    detail: dict[str, object],
    now: datetime,
    ttl: timedelta,
) -> ObservationRecord:
    return ObservationRecord(
        kind=kind,
        method=result.method,
        endpoint=result.endpoint,
        status=result.status,
        error_kind=result.error_kind,
        detail=detail if result.ok else {"error": result.error_kind},
        observed_at=now,
        fresh_until=now + ttl,
    )


def discover_live(
    client: GitLabClient,
    target: TargetIdentity,
    *,
    now: datetime | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> Snapshot:
    """Perform read-only discovery of one exact target. Never mutates."""
    now = _utc(now or datetime.now(tz=UTC))
    ttl = timedelta(seconds=ttl_seconds)
    pid = target.project_id
    records: list[ObservationRecord] = []

    project = client.get_json(f"/projects/{pid}")
    detail: dict[str, object] = {}
    if project.ok and isinstance(project.data, dict):
        detail = {
            "project_id": project.data.get("id"),
            "path_with_namespace": project.data.get("path_with_namespace"),
            "namespace_full_path": (project.data.get("namespace") or {}).get("full_path"),
            "visibility": project.data.get("visibility"),
            "default_branch": project.data.get("default_branch"),
            "web_url": project.data.get("web_url"),
            "archived": project.data.get("archived"),
        }
    records.append(_record(EvidenceKind.PROJECT_IDENTITY, project, detail, now, ttl))

    default_branch = str(detail.get("default_branch") or "main")
    branch = client.get_json(f"/projects/{pid}/repository/branches/{default_branch}")
    records.append(
        _record(
            EvidenceKind.BRANCH,
            branch,
            {"branch": default_branch, "commit_id": (branch.data or {}).get("commit", {}).get("id")
             if branch.ok and isinstance(branch.data, dict) else None},
            now,
            ttl,
        )
    )

    ci = client.get_text(f"/projects/{pid}/repository/files/.gitlab-ci.yml/raw")
    ci_body = ci.data if (ci.ok and isinstance(ci.data, str)) else ""
    has_pages_job = bool(re.search(r"(?m)^\s*pages\s*:", ci_body))
    records.append(
        _record(
            EvidenceKind.CI_CONFIG,
            ci,
            {
                "file": ".gitlab-ci.yml",
                "present": bool(ci_body),
                "has_pages_job": has_pages_job,
                "bytes": len(ci_body),
            },
            now,
            ttl,
        )
    )

    pipelines = client.get_json(
        f"/projects/{pid}/pipelines", params={"per_page": 1, "order_by": "id", "sort": "desc"}
    )
    latest = None
    if pipelines.ok and isinstance(pipelines.data, list) and pipelines.data:
        latest = pipelines.data[0]
    records.append(
        _record(
            EvidenceKind.PIPELINE,
            pipelines,
            {
                "latest_id": (latest or {}).get("id") if isinstance(latest, dict) else None,
                "latest_status": (latest or {}).get("status") if isinstance(latest, dict) else None,
            },
            now,
            ttl,
        )
    )

    issues = client.get_json(f"/projects/{pid}/issues", params={"state": "opened", "per_page": 100})
    open_issues: list[dict[str, object]] = []
    if issues.ok and isinstance(issues.data, list):
        open_issues = [
            {"iid": i.get("iid"), "title": i.get("title")}
            for i in issues.data
            if isinstance(i, dict)
        ]
    retirement_related = [
        i for i in open_issues if "retire" in str(i.get("title", "")).lower()
    ]
    records.append(
        _record(
            EvidenceKind.OPEN_ISSUES,
            issues,
            {"open_count": len(open_issues), "retirement_related": retirement_related},
            now,
            ttl,
        )
    )

    pages = client.get_json(f"/projects/{pid}/pages")
    records.append(
        _record(
            EvidenceKind.PAGES,
            pages,
            {
                "status": pages.status,
                "present": bool(pages.ok),
                "url": (pages.data or {}).get("url") if pages.ok and isinstance(pages.data, dict)
                else None,
            },
            now,
            ttl,
        )
    )

    envs = client.get_json(f"/projects/{pid}/environments")
    records.append(
        _record(
            EvidenceKind.ENVIRONMENT,
            envs,
            {"count": len(envs.data) if envs.ok and isinstance(envs.data, list) else None},
            now,
            ttl,
        )
    )

    return Snapshot(
        target=target,
        action=DEFAULT_ACTION,
        observed_at=now,
        ttl_seconds=ttl_seconds,
        classification=EvidenceClass.LIVE,
        records=tuple(records),
    )


def graph_from_snapshot(
    snapshot: Snapshot, *, classification: EvidenceClass | None = None
) -> Graph:
    """Build a deterministic obligation graph from a snapshot."""
    classification = classification or snapshot.classification
    graph = Graph()
    target_node = graph.add_target(snapshot.target)

    obligation_ids: dict[ObligationKind, str] = {}
    for kind, description in STANDARD_OBLIGATIONS:
        oid = f"obl:{kind.value.lower()}"
        obligation_ids[kind] = graph.add_obligation(oid, kind, description)
        graph.link(target_node, Relation.HAS_OBLIGATION, oid)

    for record in snapshot.records:
        evidence = Evidence(
            evidence_id=f"ev:{record.kind.value.lower()}",
            kind=record.kind,
            classification=classification,
            target=snapshot.target,
            method=record.method if record.method in {"GET", "FIXTURE"} else "GET",
            endpoint=record.endpoint,
            status=record.status,
            observed_at=record.observed_at,
            fresh_until=record.fresh_until,
            detail=dict(record.detail),
            error_kind=record.error_kind,
        )
        eid = graph.add_evidence(evidence)
        for obl_kind in _EVIDENCE_OBLIGATIONS.get(record.kind, ()):
            graph.link(obligation_ids[obl_kind], Relation.REQUIRES_EVIDENCE, eid)

    # dependencies derived ONLY from observed facts
    issues = next((r for r in snapshot.records if r.kind == EvidenceKind.OPEN_ISSUES), None)
    if issues is not None and issues.error_kind is None:
        retirement_related = issues.detail.get("retirement_related") or []
        active = bool(retirement_related)
        dep = Dependency(
            dependency_id="dep:open_work_item",
            kind=DependencyKind.OPEN_WORK_ITEM,
            description=f"{len(retirement_related)} open retirement-related work item(s)",
            active=active,
            evidence_id="ev:open_issues",
        )
        graph.add_dependency(dep)
        graph.link(obligation_ids[ObligationKind.UNRESOLVED_WORK], Relation.BLOCKED_BY,
                   dep.dependency_id)

    ci = next((r for r in snapshot.records if r.kind == EvidenceKind.CI_CONFIG), None)
    if ci is not None and ci.error_kind is None:
        has_pages = bool(ci.detail.get("has_pages_job"))
        dep = Dependency(
            dependency_id="dep:active_redeployment",
            kind=DependencyKind.ACTIVE_REDEPLOYMENT,
            description="CI pipeline publishes/deploys a Pages site"
            if has_pages
            else "no Pages deployment job found in CI configuration",
            active=has_pages,
            evidence_id="ev:ci_config",
        )
        graph.add_dependency(dep)
        graph.link(obligation_ids[ObligationKind.REDEPLOYMENT_PATH], Relation.BLOCKED_BY,
                   dep.dependency_id)

    graph.validate()
    return graph


def save_snapshot(snapshot: Snapshot, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snapshot.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return p


def load_snapshot(path: str | Path) -> Snapshot:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Snapshot.from_dict(data)
