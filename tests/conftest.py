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


class ScriptedTransport(FakeTransport):
    """A FakeTransport whose chosen endpoints return successive replies.

    Used to model a genuine publication → retirement transition where the pre
    and post state of the same endpoint differ.
    """

    def __init__(
        self,
        responses: dict[tuple[str, str], HttpReply],
        scripted: dict[str, list[HttpReply]] | None = None,
    ) -> None:
        super().__init__(responses)
        self.scripted = {k: list(v) for k, v in (scripted or {}).items()}
        self._index = dict.fromkeys(self.scripted, 0)

    def request(self, method: str, url: str, headers, timeout):  # type: ignore[no-untyped-def]
        self.calls.append((method, url))
        for fragment, replies in self.scripted.items():
            if fragment in url and replies:
                i = min(self._index[fragment], len(replies) - 1)
                self._index[fragment] += 1
                return replies[i]
        for (m, fragment), reply in self.responses.items():
            if m.upper() == method.upper() and fragment in url:
                return reply
        return HttpReply(status=404, body="", error="HTTP 404")


def project_payload(target, *, access_level: int = 40) -> dict[str, object]:
    return {
        "id": target.project_id,
        "path_with_namespace": target.full_path,
        "namespace": {"full_path": target.full_path.rsplit("/", 1)[0]},
        "visibility": "public",
        "default_branch": "main",
        "web_url": f"https://gitlab.com/{target.full_path}",
        "archived": False,
        "permissions": {
            "project_access": {"access_level": access_level},
            "group_access": None,
        },
    }


def live_responses(
    target,
    *,
    access_level: int = 40,
    pages_status: int = 200,
    deployments: int = 1,
    pages_url: str | None = None,
    ci_has_pages: bool = False,
    ci_includes: bool = False,
    open_retirement_issues: int = 0,
) -> dict[tuple[str, str], HttpReply]:
    """A complete read-only GitLab surface for one healthy target project."""
    import json as _json

    pid = target.project_id
    ci = "stages:\n  - deploy\n"
    if ci_includes:
        ci = f"include:\n  - local: /other.yml\n{ci}"
    if ci_has_pages:
        ci += "pages:\n  script:\n    - echo hi\n"
    pages_body = _json.dumps(
        {
            "url": pages_url or f"https://{target.full_path.split('/')[-1]}.pages.example/",
            "deployments": [{"id": n + 1} for n in range(deployments)],
        }
    )
    issues = [
        {"iid": n + 1, "title": "retire this", "labels": ["retirement"]}
        for n in range(open_retirement_issues)
    ]
    return {
        ("GET", f"/projects/{pid}/repository/files/"): HttpReply(200, ci),
        ("GET", f"/projects/{pid}/repository/branches/"): HttpReply(
            200, _json.dumps({"name": "main", "commit": {"id": "a" * 40}})
        ),
        ("GET", f"/projects/{pid}/pipelines"): HttpReply(
            200, _json.dumps([{"id": 999, "status": "success"}])
        ),
        ("GET", f"/projects/{pid}/issues"): HttpReply(200, _json.dumps(issues)),
        ("GET", f"/projects/{pid}/pages"): (
            HttpReply(pages_status, pages_body if pages_status == 200 else "")
        ),
        ("GET", f"/projects/{pid}/environments"): HttpReply(200, _json.dumps([])),
        ("GET", f"/projects/{pid}"): HttpReply(
            200, _json.dumps(project_payload(target, access_level=access_level))
        ),
    }


def patch_served(monkeypatch, sequence, _unused=None):  # type: ignore[no-untyped-def]
    """Patch both independent served-URL probes (publication + absence).

    ``sequence`` is one ``(status, body)`` pair or a list of them, consumed in
    call order with the last pair repeating. Both modules share one counter so a
    publication → retirement transition can be modelled faithfully.
    """
    from termivance import absence as absence_mod
    from termivance import pages as pages_mod

    if isinstance(sequence, tuple) and len(sequence) == 2 and isinstance(sequence[0], int):
        sequence = [sequence]
    state = {"i": 0}

    def _next(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        index = min(state["i"], len(sequence) - 1)
        state["i"] += 1
        status, body = sequence[index]
        return status, None, body

    monkeypatch.setattr(pages_mod, "https_get", _next)
    monkeypatch.setattr(absence_mod, "https_get", _next)


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
    include_permission: bool = True,
    can_manage_pages: bool = True,
    include_publication: bool = True,
    published: bool = True,
    served_url: str | None = None,
    marker: str = "TERMIVANCE-B3-DISPOSABLE-MARKER",
) -> Snapshot:
    """Build a synthetic snapshot for deterministic engine/discovery tests."""
    ttl = timedelta(seconds=900)
    fresh = observed_at + ttl
    resolved_url = served_url or f"https://{target.full_path.split('/')[-1]}.pages.example/"
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
    if include_permission:
        level = 40 if can_manage_pages else 30
        records.append(
            ObservationRecord(
                kind=EvidenceKind.EFFECTIVE_PERMISSION,
                method="GET",
                endpoint=f"/projects/{target.project_id}",
                status=200,
                error_kind=None,
                detail={
                    "effective_access_level": level,
                    "pages_api_status": 200 if pages_error is None else 403,
                    "pages_api_error": pages_error,
                    "can_manage_pages": can_manage_pages,
                },
                observed_at=observed_at,
                fresh_until=fresh,
            )
        )
    if include_publication:
        records.append(
            ObservationRecord(
                kind=EvidenceKind.PAGES_DEPLOYMENT,
                method="GET",
                endpoint=resolved_url,
                status=200 if published else 404,
                error_kind=None,
                detail={
                    "source": "gitlab_pages_api+served_url_probe",
                    "deployment_present": published,
                    "deployment_count": 1 if published else 0,
                    "served_url": resolved_url,
                    "marker": marker,
                    "marker_observed": published,
                },
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
