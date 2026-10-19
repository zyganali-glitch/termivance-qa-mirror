"""Read-only portfolio overview of GitLab projects (Capability 1, v2).

Answers, from *observed* provider facts only: which projects exist, which are
pages sites, what their deployment state is, and — since the multi-resource
contract — which **retirement-relevant resource kinds** each project carries:
environments, deployments, releases, package-registry records, CI/CD
redeployment mechanisms, retirement-relevant issues and the Pages publication
state. Every resource preserves its exact provider/project/resource ID, type,
observed state, source endpoint, observation timestamp, freshness, provenance
and explicit ``NOT_OBSERVED`` for inaccessible provider facts. Inferred
relationships are always marked ``INFERRED``.

There is **no mutation surface** anywhere in this module: it only ever accepts a
GET-only :class:`GitLabClient`, every resource record carries
``mutation_capability: NOT_AUTHORIZING``, and a mere observation can never
authorize mutation of that resource.

Anonymous reads (``GitLabClient(None)``) are supported and are always labelled
``ANONYMOUS_PUBLIC_READ``: a 403 on an endpoint is recorded ``NOT_OBSERVED`` and
is never promoted to "present" or "gone".
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from termivance.discovery import (
    ci_configuration_is_complete,
    detect_pages_mechanism,
    is_retirement_related,
)
from termivance.gitlab_client import GitLabClient
from termivance.policy import Policy, load_policy
from termivance.protected import is_protected, protection_reason

PORTFOLIO_SCHEMA = "termivance.portfolio/v2"
PORTFOLIO_SCHEMA_V1 = "termivance.portfolio/v1"
#: Every portfolio observation stays fresh for this long after acquisition.
PORTFOLIO_TTL_SECONDS = 900

PAGES_PRESENT = "DEPLOYMENT_PRESENT"
PAGES_UNVERIFIABLE = "PAGES_UNVERIFIABLE_403"
#: QA-FIX C: a standalone Pages-endpoint 404 is an *unavailable observation*,
#: never verified absence. Whether the endpoint is invisible because no site was
#: ever published, because the site exists but the endpoint is hidden, or
#: because the inbound identity lacks visibility cannot be decided from one
#: read-only probe. Only the separate authorized-transition evidence protocol
#: (proven pre-publication state + accepted unpublish + independent read-back)
#: may ever produce PAGES_ABSENT.
PAGES_NOT_OBSERVED_404 = "PAGES_NOT_OBSERVED_404"
PAGES_ABSENT = "NO_PAGES"
PAGES_UNKNOWN = "UNKNOWN"

#: Discovery is *never* an authorization to mutate any resource.
NOT_AUTHORIZING = "NOT_AUTHORIZING"
SUPPORT_OBSERVED = "OBSERVED"
SUPPORT_NOT_OBSERVED = "NOT_OBSERVED"
SUPPORT_INFERRED = "INFERRED"

KIND_ENVIRONMENT = "ENVIRONMENT"
KIND_DEPLOYMENT = "DEPLOYMENT"
KIND_RELEASE = "RELEASE"
KIND_PACKAGE = "PACKAGE"
KIND_ISSUE = "OPEN_ISSUE"
KIND_PAGES = "PAGES_SITE"
KIND_CI_REDEPLOY = "CI_REDEPLOYMENT_MECHANISM"

DARK_RESOURCE_KINDS: frozenset[str] = frozenset(
    {
        KIND_ENVIRONMENT,
        KIND_DEPLOYMENT,
        KIND_RELEASE,
        KIND_PACKAGE,
        KIND_ISSUE,
        KIND_PAGES,
        KIND_CI_REDEPLOY,
    }
)


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ResourceRecord:
    """One observed (or explicitly unobservable) provider resource of one kind."""

    kind: str
    ref: str  # exact provider/project/resource address, example 'environment:123:7'
    state: str  # provider-observed state, or a NOT_OBSERVED access observation
    endpoint: str
    observed_at: datetime
    fresh_until: datetime
    provenance: str
    support: str = SUPPORT_OBSERVED  # OBSERVED | NOT_OBSERVED
    detail: dict[str, object] = field(default_factory=dict)
    operation_supported: str = "READ_ONLY_OBSERVATION"
    mutation_capability: str = NOT_AUTHORIZING

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "ref": self.ref,
            "state": self.state,
            "endpoint": self.endpoint,
            "observed_at": _utc(self.observed_at).isoformat(),
            "fresh_until": _utc(self.fresh_until).isoformat(),
            "provenance": self.provenance,
            "support": self.support,
            "detail": dict(self.detail),
            "operation_supported": self.operation_supported,
            "mutation_capability": self.mutation_capability,
        }

    @classmethod
    def not_observed(
        cls,
        *,
        kind: str,
        project_id: int,
        endpoint: str,
        error_kind: str | None,
        observed_at: datetime,
        provenance: str,
    ) -> ResourceRecord:
        """An explicitly unobservable provider fact (401/403/404 is never absence)."""
        raw = str(project_id)
        return cls(
            kind=kind,
            ref=f"{kind.lower()}:{raw}:not_observed",
            state=f"NOT_OBSERVED ({error_kind or 'no provider response'})",
            endpoint=endpoint,
            observed_at=observed_at,
            fresh_until=observed_at + timedelta(seconds=PORTFOLIO_TTL_SECONDS),
            provenance=provenance,
            support=SUPPORT_NOT_OBSERVED,
            operation_supported="READ_ONLY_OBSERVATION",
            detail={"project_id": project_id},
            mutation_capability=NOT_AUTHORIZING,
        )


def _records(
    client: GitLabClient,
    *,
    project_id: int,
    endpoint: str,
    kind: str,
    observed_at: datetime,
    provenance: str,
    build: Callable[[list[dict[str, object]]], list[ResourceRecord]],
) -> tuple[ResourceRecord, ...]:
    """Shared GET+classify wrapper for one project endpoint family."""
    result = client.get_json(endpoint)
    if result.ok and isinstance(result.data, list):
        return tuple(build(result.data))
    return (
        ResourceRecord.not_observed(
            kind=kind,
            project_id=project_id,
            endpoint=endpoint,
            error_kind=result.error_kind or (None if result.ok else "BAD_RESPONSE"),
            observed_at=observed_at,
            provenance=provenance,
        ),
    )


def _generic_records(
    kind: str,
    endpoint: str,
    observed_at: datetime,
    provenance: str,
    project_id: int,
    data: list[dict[str, object]],
    *,
    detail_keys: tuple[str, ...],
    id_key: str,
    state_key: str,
    nested: dict[str, tuple[str, str]] | None = None,
) -> list[ResourceRecord]:
    """Build resource records from one provider list endpoint.

    ``nested`` maps a detail key to ``(entry_key, nested_key)`` for provider
    payloads that nest the fact (a deployment's environment lives at
    ``entry['environment']['name']``, not a flat ``environment_name``).
    """
    records: list[ResourceRecord] = []
    nested = nested or {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        provider_id = entry.get(id_key)
        if provider_id is None:
            continue
        detail: dict[str, object] = {"project_id": project_id}
        for key in detail_keys:
            if key in nested:
                entry_key, nested_key = nested[key]
                container = entry.get(entry_key)
                value = container.get(nested_key) if isinstance(container, dict) else None
            else:
                value = entry.get(key)
            if value is None:
                continue
            detail[key] = value if isinstance(value, (str, int, bool, list)) else str(value)
        records.append(
            ResourceRecord(
                kind=kind,
                ref=f"{kind.lower()}:{project_id}:{provider_id}",
                state=str(entry.get(state_key) or "UNKNOWN_STATE"),
                endpoint=endpoint,
                observed_at=observed_at,
                fresh_until=observed_at + timedelta(seconds=PORTFOLIO_TTL_SECONDS),
                provenance=provenance,
                detail=dict(detail),
            )
        )
    return records


def _issue_records(
    data: list[dict[str, object]],
    *,
    project_id: int,
    endpoint: str,
    observed_at: datetime,
    provenance: str,
) -> list[ResourceRecord]:
    records: list[ResourceRecord] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        iid = entry.get("iid")
        if not isinstance(iid, int):
            continue
        labels = [str(x) for x in (entry.get("labels") or []) if isinstance(x, str)]
        records.append(
            ResourceRecord(
                kind=KIND_ISSUE,
                ref=f"issue:{project_id}:{iid}",
                state=str(entry.get("state") or "unknown"),
                endpoint=endpoint,
                observed_at=observed_at,
                fresh_until=observed_at + timedelta(seconds=PORTFOLIO_TTL_SECONDS),
                provenance=provenance,
                detail={
                    "project_id": project_id,
                    "iid": iid,
                    "title": str(entry.get("title") or ""),
                    "labels": labels,
                    "retirement_related": is_retirement_related(entry),
                },
            )
        )
    return records


def _ci_records(
    ci_body: str,
    *,
    project_id: int,
    endpoint: str,
    observed_at: datetime,
    provenance: str,
) -> ResourceRecord:
    detects, signals = detect_pages_mechanism(ci_body)
    return ResourceRecord(
        kind=KIND_CI_REDEPLOY,
        ref=f"ci_redeployment:{project_id}",
        state=(
            "PAGES_REDEPLOYMENT_SIGNAL_PRESENT"
            if detects
            else "NO_PAGES_SIGNAL_IN_DEFAULT_BRANCH_CONFIG"
        ),
        endpoint=endpoint,
        observed_at=observed_at,
        fresh_until=observed_at + timedelta(seconds=PORTFOLIO_TTL_SECONDS),
        provenance=provenance,
        detail={
            "project_id": project_id,
            "signals": signals,
            "configuration_complete": ci_configuration_is_complete(ci_body),
        },
        # The mechanism text is an observation; whether it would redeploy is INFERRED.
        operation_supported="READ_ONLY_OBSERVATION",
    )


def _pages_record(
    pages_state: str,
    *,
    project_id: int,
    endpoint: str,
    served_url: str,
    observed_at: datetime,
    provenance: str,
    error_kind: str | None,
) -> ResourceRecord:
    return (
        ResourceRecord(
            kind=KIND_PAGES,
            ref=f"pages:{project_id}",
            state=pages_state,
            endpoint=endpoint,
            observed_at=observed_at,
            fresh_until=observed_at + timedelta(seconds=PORTFOLIO_TTL_SECONDS),
            provenance=provenance,
            detail={"project_id": project_id, "served_url": served_url},
            operation_supported="UNPUBLISH_PAGES (authorized path only)",
            mutation_capability=NOT_AUTHORIZING,
        )
        if _pages_support(pages_state)
        else ResourceRecord.not_observed(
            kind=KIND_PAGES,
            project_id=project_id,
            endpoint=endpoint,
            error_kind=error_kind,
            observed_at=observed_at,
            provenance=provenance,
        )
    )


def _pages_support(pages_state: str) -> bool:
    """True only for an *observed* Pages record.

    QA-FIX C: only a positive provider read (a served URL from the Pages API)
    is an OBSERVED fact. ``PAGES_ABSENT`` is intentionally excluded — bounded
    retirement absence is established by the authorized-transition evidence
    protocol (receipt-bound bounded absence), never by a standalone read-only
    404, 403 or 401.
    """
    return pages_state == PAGES_PRESENT


@dataclass(frozen=True, slots=True)
class AssetObservation:
    """One GitLab project as observed through read-only, resource-kind-aware probes."""

    project_id: int
    full_path: str
    name: str
    web_url: str
    visibility: str
    archived: bool | None
    description: str
    role: str
    pages_state: str
    ok: bool
    error_kind: str | None
    anonymous: bool
    observed_at: datetime
    resources: tuple[ResourceRecord, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "full_path": self.full_path,
            "name": self.name,
            "web_url": self.web_url,
            "visibility": self.visibility,
            "archived": self.archived,
            "description": self.description,
            "role": self.role,
            "pages_state": self.pages_state,
            "ok": self.ok,
            "error_kind": self.error_kind,
            "provenance": "ANONYMOUS_PUBLIC_READ" if self.anonymous else "AUTHENTICATED_READ",
            "observed_at": _utc(self.observed_at).isoformat(),
            "resources": [r.to_dict() for r in self.resources],
        }

    @property
    def approved_target(self) -> bool:
        return self.role == "APPROVED_RETIREMENT_TARGET"


def _role_for(project_id: int, policy: Policy | None) -> str:
    if is_protected(project_id):
        reason = protection_reason(project_id)
        return f"PROTECTED ({reason})" if reason else "PROTECTED"
    if policy is not None:
        if project_id in policy.allowed_target_project_ids:
            return "APPROVED_RETIREMENT_TARGET"
        if policy.mode == "EXAMPLE_ONLY_NOT_AUTHORIZATION" or not policy.allowed_target_project_ids:
            # An example-mode policy authorizes nothing; call it out as such.
            return "NON_TARGET (policy authorizes nothing)"
    return "NON_TARGET"


def observe_asset(
    client: GitLabClient,
    *,
    project_id: int,
    full_path: str | None = None,
    policy: Policy | None = None,
    now: datetime | None = None,
) -> AssetObservation:
    """Observe one project: identity + pages + every supported resource kind.

    Never mutates. 401/403/404/5xx provider responses are recorded as explicit
    ``NOT_OBSERVED`` resource records — never as absence, presence or 403-driven
    claims. Discovering a resource never authorizes mutating it.
    """
    observed = _utc(now)
    anonymous = client.token is None
    provenance = "ANONYMOUS_PUBLIC_READ" if anonymous else "AUTHENTICATED_READ"
    project = client.get_json(f"/projects/{project_id}")
    if not project.ok or not isinstance(project.data, dict):
        return AssetObservation(
            project_id=project_id,
            full_path=full_path or f"projects/{project_id}",
            name="(unreadable)",
            web_url="",
            visibility="unknown",
            archived=None,
            description="",
            role=_role_for(project_id, policy),
            pages_state=PAGES_UNKNOWN,
            ok=False,
            error_kind=project.error_kind,
            anonymous=anonymous,
            observed_at=observed,
            resources=(
                ResourceRecord.not_observed(
                    kind=KIND_PAGES,
                    project_id=project_id,
                    endpoint=f"/projects/{project_id}/pages",
                    error_kind=project.error_kind,
                    observed_at=observed,
                    provenance=provenance,
                ),
            ),
        )
    data = project.data
    path = str(data.get("path_with_namespace") or "")

    pages_endpoint = f"/projects/{project_id}/pages"
    pages = client.get_json(pages_endpoint)
    served_url = ""
    if pages.ok and isinstance(pages.data, dict):
        served_url = str(pages.data.get("url") or "")
        pages_state = PAGES_PRESENT if served_url else PAGES_UNKNOWN
        pages_error = None
    elif pages.error_kind == "AUTH_DENIED":
        # A 401/403 cannot distinguish site-present from site-gone; say so.
        pages_state = PAGES_UNVERIFIABLE
        pages_error = pages.error_kind
    elif pages.error_kind == "NOT_FOUND":
        # QA-FIX C: a standalone 404 is an access/visibility observation, not
        # proof that a previously published site became absent.
        pages_state = PAGES_NOT_OBSERVED_404
        pages_error = pages.error_kind
    else:
        pages_state = PAGES_UNKNOWN
        pages_error = pages.error_kind
    pages_record = _pages_record(
        pages_state,
        project_id=project_id,
        endpoint=pages_endpoint,
        served_url=served_url,
        observed_at=observed,
        provenance=provenance,
        error_kind=pages_error,
    )

    env_endpoint = f"/projects/{project_id}/environments"
    environments = _records(
        client,
        project_id=project_id,
        endpoint=env_endpoint,
        kind=KIND_ENVIRONMENT,
        observed_at=observed,
        provenance=provenance,
        build=lambda items: _generic_records(
            KIND_ENVIRONMENT,
            env_endpoint,
            observed,
            provenance,
            project_id,
            items,
            detail_keys=("name", "external_url"),
            id_key="id",
            state_key="state",
        ),
    )
    deployments = _records(
        client,
        project_id=project_id,
        endpoint=f"/projects/{project_id}/deployments",
        kind=KIND_DEPLOYMENT,
        observed_at=observed,
        provenance=provenance,
        build=lambda items: _generic_records(
            KIND_DEPLOYMENT,
            f"/projects/{project_id}/deployments",
            observed,
            provenance,
            project_id,
            items,
            detail_keys=("ref", "environment_name"),
            nested={"environment_name": ("environment", "name")},
            id_key="id",
            state_key="status",
        ),
    )
    releases = _records(
        client,
        project_id=project_id,
        endpoint=f"/projects/{project_id}/releases",
        kind=KIND_RELEASE,
        observed_at=observed,
        provenance=provenance,
        build=lambda items: _generic_records(
            KIND_RELEASE,
            f"/projects/{project_id}/releases",
            observed,
            provenance,
            project_id,
            items,
            detail_keys=("name", "tag_name"),
            id_key="tag_name",
            state_key="tag_name",
        ),
    )
    packages = _records(
        client,
        project_id=project_id,
        endpoint=f"/projects/{project_id}/packages",
        kind=KIND_PACKAGE,
        observed_at=observed,
        provenance=provenance,
        build=lambda items: _generic_records(
            KIND_PACKAGE,
            f"/projects/{project_id}/packages",
            observed,
            provenance,
            project_id,
            items,
            detail_keys=("name", "version", "package_type"),
            id_key="id",
            state_key="package_type",
        ),
    )
    issues_endpoint = f"/projects/{project_id}/issues"
    issues = _records(
        client,
        project_id=project_id,
        endpoint=f"{issues_endpoint}?state=opened&per_page=50",
        kind=KIND_ISSUE,
        observed_at=observed,
        provenance=provenance,
        build=lambda items: _issue_records(
            items,
            project_id=project_id,
            endpoint=f"{issues_endpoint}?state=opened",
            observed_at=observed,
            provenance=provenance,
        ),
    )
    ci_endpoint = f"/projects/{project_id}/repository/files/.gitlab-ci.yml/raw"
    ci_body = client.get_text(ci_endpoint)
    if ci_body.ok and isinstance(ci_body.data, str):
        ci = (
            _ci_records(
                ci_body.data,
                project_id=project_id,
                endpoint=ci_endpoint,
                observed_at=observed,
                provenance=provenance,
            ),
        )
    else:
        ci = (
            ResourceRecord.not_observed(
                kind=KIND_CI_REDEPLOY,
                project_id=project_id,
                endpoint=ci_endpoint,
                error_kind=ci_body.error_kind,
                observed_at=observed,
                provenance=provenance,
            ),
        )
    return AssetObservation(
        project_id=project_id,
        full_path=path or full_path or f"projects/{project_id}",
        name=str(data.get("name") or ""),
        web_url=str(data.get("web_url") or ""),
        visibility=str(data.get("visibility") or "unknown"),
        archived=data.get("archived") if isinstance(data.get("archived"), bool) else None,
        description=str(data.get("description") or ""),
        role=_role_for(project_id, policy),
        pages_state=pages_state,
        ok=True,
        error_kind=pages.error_kind
        if pages_state in (PAGES_UNVERIFIABLE, PAGES_NOT_OBSERVED_404, PAGES_UNKNOWN)
        else None,
        anonymous=anonymous,
        observed_at=observed,
        resources=(
            pages_record,
            *ci,
            *environments,
            *deployments,
            *releases,
            *packages,
            *issues,
        ),
    )


@dataclass(frozen=True, slots=True)
class PortfolioRelation:
    """One cross-resource edge derived from portfolio evidence."""

    src: str
    dst: str
    kind: str  # deployed_to | recreates | obligates
    support: str  # OBSERVED | INFERRED — never claims an authorization

    def to_dict(self) -> dict[str, object]:
        return {
            "src": self.src,
            "dst": self.dst,
            "kind": self.kind,
            "support": self.support,
        }


def _pages_ref(asset: AssetObservation) -> str | None:
    """The asset's recorded Pages record ref — observed or NOT_OBSERVED.

    Relations must anchor to recorded resources only; when no Pages record was
    recorded at all the relation is withheld rather than synthesized.
    """
    for record in asset.resources:
        if record.kind == KIND_PAGES:
            return record.ref
    return None


def relations_for(asset: AssetObservation) -> tuple[PortfolioRelation, ...]:
    """Derive the cross-resource relationships one asset's evidence supports.

    Deployments to environments that actually exist are observed provider facts.
    CI mechananisms that *could* redeploy Pages are ``INFERRED``: the config text
    implies a capability, not an observed redeployment. Retirement-relevant
    issues are obligations *derived from issue text* — again ``INFERRED``. None
    of these edges authorize any mutation.
    """
    edges: list[PortfolioRelation] = []

    def env_refs_by_name() -> dict[str, str]:
        """Resolve exact environment record refs by name, so relations point at
        recorded resources instead of synthesized pseudo-refs."""
        mapping: dict[str, str] = {}
        for r in asset.resources:
            if r.kind == KIND_ENVIRONMENT and r.support == SUPPORT_OBSERVED:
                name = str((r.detail or {}).get("name") or "")
                if name:
                    mapping[name] = r.ref
        return mapping

    env_refs = env_refs_by_name()
    environments = set(env_refs)
    for record in asset.resources:
        if record.kind != KIND_DEPLOYMENT or record.support != SUPPORT_OBSERVED:
            continue
        env_name = str((record.detail or {}).get("environment_name") or "")
        if env_name and env_name in environments:
            edges.append(
                PortfolioRelation(
                    src=record.ref,
                    dst=env_refs[env_name],
                    kind="deployed_to",
                    support=SUPPORT_OBSERVED,
                )
            )
    ci_records = [
        r
        for r in asset.resources
        if r.kind == KIND_CI_REDEPLOY
        and r.support == SUPPORT_OBSERVED
        and r.state == "PAGES_REDEPLOYMENT_SIGNAL_PRESENT"
    ]
    pages_ref = _pages_ref(asset)
    if ci_records and pages_ref and asset.pages_state in {PAGES_PRESENT, PAGES_UNVERIFIABLE}:
        for record in ci_records:
            edges.append(
                PortfolioRelation(
                    src=record.ref,
                    dst=pages_ref,
                    kind="recreates",
                    support=SUPPORT_INFERRED,
                )
            )
    for record in asset.resources:
        if record.kind != KIND_ISSUE or record.support != SUPPORT_OBSERVED:
            continue
        if (record.detail or {}).get("retirement_related") is True:
            if pages_ref:
                edges.append(
                    PortfolioRelation(
                        src=record.ref,
                        dst=pages_ref,
                        kind="obligates",
                        support=SUPPORT_INFERRED,
                    )
                )
    return tuple(edges)


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """One read-only observation pass over a set of projects."""

    assets: tuple[AssetObservation, ...]
    observed_at: datetime
    anonymous: bool
    relations: tuple[PortfolioRelation, ...] = ()

    def to_dict(self) -> dict[str, object]:
        counts_by_kind: dict[str, int] = {}
        observed_counts: dict[str, int] = {}
        for record in [r for a in self.assets for r in a.resources]:
            counts_by_kind[record.kind] = counts_by_kind.get(record.kind, 0) + 1
            if record.support == SUPPORT_OBSERVED:
                observed_counts[record.kind] = observed_counts.get(record.kind, 0) + 1
        return {
            "schema": PORTFOLIO_SCHEMA,
            "provenance": "ANONYMOUS_PUBLIC_READ" if self.anonymous else "AUTHENTICATED_READ",
            "observed_at": _utc(self.observed_at).isoformat(),
            "assets": [a.to_dict() for a in self.assets],
            "relations": [rel.to_dict() for rel in self.relations],
            "totals": {
                "assets": len(self.assets),
                "pages_sites": sum(1 for a in self.assets if a.pages_state == PAGES_PRESENT),
                "pages_unverifiable": sum(
                    1 for a in self.assets if a.pages_state == PAGES_UNVERIFIABLE
                ),
                "pages_not_observed": sum(
                    1 for a in self.assets if a.pages_state == PAGES_NOT_OBSERVED_404
                ),
                "approved_targets": sum(1 for a in self.assets if a.approved_target),
                "protected": sum(1 for a in self.assets if a.role.startswith("PROTECTED")),
                "resources_observed": sum(observed_counts.values()),
                "resources_not_observed": sum(
                    1
                    for r in [r for a in self.assets for r in a.resources]
                    if r.support == SUPPORT_NOT_OBSERVED
                ),
                "resource_kinds_observed": dict(
                    sorted(observed_counts.items(), key=lambda kv: -kv[1])
                ),
                "inferred_relations": sum(
                    1 for rel in self.relations if rel.support == SUPPORT_INFERRED
                ),
                "observed_relations": sum(
                    1 for rel in self.relations if rel.support == SUPPORT_OBSERVED
                ),
            },
        }

    def render(self) -> str:
        lines = [
            f"PORTFOLIO ({'ANONYMOUS_PUBLIC_READ' if self.anonymous else 'AUTHENTICATED_READ'}) "
            f"@ {_utc(self.observed_at).isoformat()}",
            f"{'ID':>12}  {'ROLE':<38} {'PAGES':<24} PATH",
            "-" * 100,
        ]
        for asset in self.assets:
            lines.append(
                f"{asset.project_id:>12}  {asset.role:<38} {asset.pages_state:<24} "
                f"{asset.full_path}"
            )
            observed = [
                r
                for r in asset.resources
                if r.support == SUPPORT_OBSERVED and r.kind in DARK_RESOURCE_KINDS
            ]
            if observed:
                kinds = sorted({r.kind for r in observed})
                lines.append(f"{'':>12}  resources observed: {', '.join(kinds)}")
            unobserved = sorted(
                {r.kind for r in asset.resources if r.support == SUPPORT_NOT_OBSERVED}
            )
            if unobserved:
                lines.append(
                    f"{'':>12}  resources NOT_OBSERVED (401/403/404 never absence): "
                    f"{', '.join(unobserved)}"
                )
        totals = self.to_dict()["totals"]
        assert isinstance(totals, dict)
        lines.append("-" * 100)
        lines.append(
            f"totals: {totals['assets']} assets, {totals['pages_sites']} pages sites, "
            f"{totals['pages_unverifiable']} unverifiable(401/403), "
            f"{totals['pages_not_observed']} pages endpoint NOT_OBSERVED(404 — never absence), "
            f"{totals['approved_targets']} approved targets, {totals['protected']} protected; "
            f"observed resources {totals['resources_observed']} "
            f"(not observed {totals['resources_not_observed']}); "
            f"relations observed {totals['observed_relations']} "
            f"/ inferred {totals['inferred_relations']}"
        )
        # Honest limitation: access failures are not evidence of presence or
        # absence, a 404 on the Pages endpoint is not a verified retirement, and
        # a discovery pass authorizes nothing.
        lines.append(
            "boundary: NOT_OBSERVED records are access observations, never "
            "deployment claims; verified Pages absence exists only inside the "
            "authorized-transition evidence protocol, never from a read-only "
            "probe; every resource carries mutation_capability="
            "NOT_AUTHORIZING — discovering a resource never authorizes mutating it"
        )
        return "\n".join(lines)


def observe_portfolio(
    client: GitLabClient,
    project_ids: Iterable[int],
    *,
    full_paths: dict[int, str] | None = None,
    policy: Policy | None = None,
    now: datetime | None = None,
) -> PortfolioSnapshot:
    """Read-only pass over the given project ids (any order, stable output)."""
    observed = _utc(now)
    assets: list[AssetObservation] = []
    for pid in sorted(set(project_ids)):
        assets.append(
            observe_asset(
                client,
                project_id=pid,
                full_path=(full_paths or {}).get(pid),
                policy=policy,
                now=observed,
            )
        )
    snapshot_relations: list[PortfolioRelation] = []
    for asset in assets:
        snapshot_relations.extend(relations_for(asset))
    return PortfolioSnapshot(
        assets=tuple(assets),
        observed_at=observed,
        anonymous=client.token is None,
        relations=tuple(snapshot_relations),
    )


def default_policy(path: str | None = None) -> Policy:
    """The shipped B3 disposable policy, used only to label approved targets."""
    return load_policy(path or "config/retirement_policy.b3_disposable.json")


def portfolio_from_data(data: dict[str, object]) -> PortfolioSnapshot:
    """Rebuild a snapshot from its recorded JSON (for evidence replays/UI)."""
    assets = tuple(
        AssetObservation(
            project_id=int(a["project_id"]),
            full_path=str(a["full_path"]),
            name=str(a["name"]),
            web_url=str(a["web_url"]),
            visibility=str(a["visibility"]),
            archived=a["archived"] if isinstance(a["archived"], bool) else None,
            description=str(a["description"]),
            role=str(a["role"]),
            pages_state=str(a["pages_state"]),
            ok=bool(a["ok"]),
            error_kind=str(a["error_kind"]) if a.get("error_kind") else None,
            anonymous=str(a.get("provenance")) == "ANONYMOUS_PUBLIC_READ",
            observed_at=datetime.fromisoformat(str(a["observed_at"])),
            resources=tuple(
                ResourceRecord(
                    kind=str(r["kind"]),
                    ref=str(r["ref"]),
                    state=str(r["state"]),
                    endpoint=str(r["endpoint"]),
                    observed_at=datetime.fromisoformat(str(r["observed_at"])),
                    fresh_until=datetime.fromisoformat(str(r["fresh_until"])),
                    provenance=str(r.get("provenance") or "RECORDED"),
                    support=str(r.get("support") or SUPPORT_OBSERVED),
                    detail=dict(r.get("detail") or {}),
                    operation_supported=str(r.get("operation_supported") or ""),
                    mutation_capability=str(r.get("mutation_capability") or NOT_AUTHORIZING),
                )
                for r in (a.get("resources") or ())
                if isinstance(r, dict)
            ),
        )
        for a in (data.get("assets") or ())  # type: ignore[union-attr]
    )
    relations = tuple(
        PortfolioRelation(
            src=str(rel["src"]),
            dst=str(rel["dst"]),
            kind=str(rel["kind"]),
            support=str(rel["support"]),
        )
        for rel in (data.get("relations") or ())  # type: ignore[union-attr]
        if isinstance(rel, dict)
    )
    return PortfolioSnapshot(
        assets=assets,
        observed_at=datetime.fromisoformat(str(data.get("observed_at"))),
        anonymous=str(data.get("provenance")) == "ANONYMOUS_PUBLIC_READ",
        relations=relations,
    )


__all__ = [
    "DARK_RESOURCE_KINDS",
    "KIND_CI_REDEPLOY",
    "KIND_DEPLOYMENT",
    "KIND_ENVIRONMENT",
    "KIND_ISSUE",
    "KIND_PACKAGE",
    "KIND_PAGES",
    "KIND_RELEASE",
    "NOT_AUTHORIZING",
    "PORTFOLIO_SCHEMA",
    "PORTFOLIO_SCHEMA_V1",
    "PORTFOLIO_TTL_SECONDS",
    "PAGES_ABSENT",
    "PAGES_NOT_OBSERVED_404",
    "PAGES_PRESENT",
    "PAGES_UNVERIFIABLE",
    "PAGES_UNKNOWN",
    "SUPPORT_INFERRED",
    "SUPPORT_NOT_OBSERVED",
    "SUPPORT_OBSERVED",
    "AssetObservation",
    "PortfolioRelation",
    "PortfolioSnapshot",
    "ResourceRecord",
    "default_policy",
    "observe_asset",
    "observe_portfolio",
    "portfolio_from_data",
    "relations_for",
]
