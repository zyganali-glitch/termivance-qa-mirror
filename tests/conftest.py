"""Shared pytest fixtures and helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from termivance.discovery import (
    ObservationRecord,
    Snapshot,
    graph_from_snapshot,
)
from termivance.gitlab_client import HttpReply
from termivance.graph import EvidenceClass, EvidenceKind
from termivance.policy import Policy
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


@pytest.fixture()
def pages_target() -> TargetIdentity:
    return TargetIdentity(
        project_id=12345678,
        full_path="example-group/example-disposable-pages",
        resource_kind="GITLAB_PAGES_SITE",
    )


@pytest.fixture()
def canonical_target() -> TargetIdentity:
    return TargetIdentity(
        project_id=87779099,
        full_path="gitlab-ai-hackathon/transcend-october-2026/39306908/termivance",
        resource_kind="GITLAB_PAGES_SITE",
    )


@pytest.fixture()
def allow_policy(pages_target: TargetIdentity) -> Policy:
    """A synthetic policy that permits the disposable example target only."""
    return Policy(
        schema_version=1,
        mode="OPERATOR_APPROVED",
        mutation_enabled=False,
        provider="GITLAB_PAGES",
        allowed_target_project_ids=(pages_target.project_id,),
        allowed_target_full_paths=(pages_target.full_path,),
        allowed_actions=("unpublish_pages",),
        authorization_required=True,
    )


class FakeTransport:
    """Deterministic transport keyed on (method, url fragment)."""

    def __init__(self, responses: dict[tuple[str, str], HttpReply]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    def request(self, method: str, url: str, headers, timeout):  # type: ignore[no-untyped-def]
        self.calls.append((method, url))
        for (m, fragment), reply in self.responses.items():
            if m.upper() == method.upper() and fragment in url:
                return reply
        return HttpReply(status=404, body="", error="HTTP 404")


def make_snapshot(
    target: TargetIdentity,
    *,
    classification: EvidenceClass = EvidenceClass.LIVE,
    observed_at: datetime = NOW,
    open_retirement_issues: int = 0,
    open_generic_issues: int = 0,
    pages_mechanism: bool = False,
    includes_present: bool = False,
    operator_control: bool = False,
    pages_error: str | None = None,
    project_id_override: int | None = None,
    include_ci_config: bool = True,
    include_identity: bool = True,
) -> Snapshot:
    """Build a synthetic snapshot for deterministic engine/discovery tests."""
    ttl = timedelta(seconds=900)
    fresh = observed_at + ttl
    records: list[ObservationRecord] = []
    if include_identity:
        records.append(
            ObservationRecord(
                kind=EvidenceKind.PROJECT_IDENTITY,
                method="GET",
                endpoint=f"/projects/{target.project_id}",
                status=200,
                error_kind=None,
                detail={
                    "project_id": project_id_override
                    if project_id_override is not None
                    else target.project_id,
                    "path_with_namespace": target.full_path,
                    "visibility": "public",
                    "default_branch": "main",
                },
                observed_at=observed_at,
                fresh_until=fresh,
            )
        )
    records.append(
        ObservationRecord(
            kind=EvidenceKind.BRANCH,
            method="GET",
            endpoint=f"/projects/{target.project_id}/repository/branches/main",
            status=200,
            error_kind=None,
            detail={"branch": "main", "commit_id": "0" * 40},
            observed_at=observed_at,
            fresh_until=fresh,
        )
    )
    if include_ci_config:
        records.append(
            ObservationRecord(
                kind=EvidenceKind.CI_CONFIG,
                method="GET",
                endpoint=f"/projects/{target.project_id}/repository/files/.gitlab-ci.yml/raw",
                status=200,
                error_kind=None,
                detail={
                    "file": ".gitlab-ci.yml",
                    "present": True,
                    "pages_mechanism": pages_mechanism,
                    "pages_signals": ["pages_job_key"] if pages_mechanism else [],
                    "includes_present": includes_present,
                },
                observed_at=observed_at,
                fresh_until=fresh,
            )
        )
    if operator_control:
        records.append(
            ObservationRecord(
                kind=EvidenceKind.REDEPLOYMENT_CONTROL,
                method="ATTESTATION",
                endpoint="operator://redeployment-control",
                status=None,
                error_kind=None,
                detail={"control": "operator confirmed no redeployment path for this target"},
                observed_at=observed_at,
                fresh_until=fresh,
            )
        )
    issues = [
        {"iid": 1, "title": "retire this", "labels": ["retirement"]}
        for _ in range(open_retirement_issues)
    ]
    issues += [
        {"iid": 100 + n, "title": "fix a normal bug", "labels": ["bug"]}
        for n in range(open_generic_issues)
    ]
    records.append(
        ObservationRecord(
            kind=EvidenceKind.OPEN_ISSUES,
            method="GET",
            endpoint=f"/projects/{target.project_id}/issues",
            status=200,
            error_kind=None,
            detail={
                "open_count": len(issues),
                "retirement_related": issues[:open_retirement_issues],
            },
            observed_at=observed_at,
            fresh_until=fresh,
        )
    )
    records.append(
        ObservationRecord(
            kind=EvidenceKind.PAGES,
            method="GET",
            endpoint=f"/projects/{target.project_id}/pages",
            status=200 if pages_error is None else 403,
            error_kind=pages_error,
            detail={} if pages_error is None else {"error": pages_error},
            observed_at=observed_at,
            fresh_until=fresh,
        )
    )
    return Snapshot(
        target=target,
        action="unpublish_pages",
        observed_at=observed_at,
        ttl_seconds=900,
        classification=classification,
        records=tuple(records),
    )


def build_graph(snapshot: Snapshot):  # type: ignore[no-untyped-def]
    return graph_from_snapshot(snapshot)
