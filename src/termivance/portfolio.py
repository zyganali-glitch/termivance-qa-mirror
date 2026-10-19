"""Read-only portfolio overview of GitLab projects (Capability 1).

Answers, from *observed* provider facts only: which projects exist, which are
pages sites, what their deployment state is, and whether they fall in the
approved retirement scope. There is **no mutation surface** anywhere in this
module: it only ever accepts a GET-only :class:`GitLabClient`.

Anonymous reads (``GitLabClient(None)``) are supported and are always labelled
``ANONYMOUS_PUBLIC_READ``: a 403 on ``/pages`` is recorded as
``PAGES_UNVERIFIABLE_403`` — never promoted to "site present" or "site gone".
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from termivance.gitlab_client import GitLabClient
from termivance.policy import Policy, load_policy
from termivance.protected import is_protected, protection_reason

PORTFOLIO_SCHEMA = "termivance.portfolio/v1"

PAGES_PRESENT = "DEPLOYMENT_PRESENT"
PAGES_UNVERIFIABLE = "PAGES_UNVERIFIABLE_403"
PAGES_ABSENT = "NO_PAGES"
PAGES_UNKNOWN = "UNKNOWN"


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class AssetObservation:
    """One GitLab project as observed through read-only endpoints."""

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
    """Observe one project with two GETs (project + pages). Never mutates."""
    observed = _utc(now)
    anonymous = client.token is None
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
        )
    data = project.data
    path = str(data.get("path_with_namespace") or "")
    pages = client.get_json(f"/projects/{project_id}/pages")
    if pages.ok and isinstance(pages.data, dict):
        pages_state = PAGES_PRESENT if pages.data.get("url") else PAGES_UNKNOWN
    elif pages.error_kind == "AUTH_DENIED":
        # A 403 cannot distinguish site-present from site-gone; say so.
        pages_state = PAGES_UNVERIFIABLE
    elif pages.error_kind == "NOT_FOUND":
        pages_state = PAGES_ABSENT
    else:
        pages_state = PAGES_UNKNOWN
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
        error_kind=pages.error_kind if pages_state in (PAGES_UNVERIFIABLE, PAGES_UNKNOWN) else None,
        anonymous=anonymous,
        observed_at=observed,
    )


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """One read-only observation pass over a set of projects."""

    assets: tuple[AssetObservation, ...]
    observed_at: datetime
    anonymous: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": PORTFOLIO_SCHEMA,
            "provenance": "ANONYMOUS_PUBLIC_READ" if self.anonymous else "AUTHENTICATED_READ",
            "observed_at": _utc(self.observed_at).isoformat(),
            "assets": [a.to_dict() for a in self.assets],
            "totals": {
                "assets": len(self.assets),
                "pages_sites": sum(1 for a in self.assets if a.pages_state == PAGES_PRESENT),
                "pages_unverifiable": sum(
                    1 for a in self.assets if a.pages_state == PAGES_UNVERIFIABLE
                ),
                "approved_targets": sum(1 for a in self.assets if a.approved_target),
                "protected": sum(1 for a in self.assets if a.role.startswith("PROTECTED")),
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
        totals = self.to_dict()["totals"]
        assert isinstance(totals, dict)
        lines.append("-" * 100)
        lines.append(
            f"totals: {totals['assets']} assets, {totals['pages_sites']} pages sites, "
            f"{totals['pages_unverifiable']} unverifiable(403), "
            f"{totals['approved_targets']} approved targets, {totals['protected']} protected"
        )
        # Honest limitation: a 403 is not evidence of presence or absence.
        lines.append(
            "boundary: PAGES_UNVERIFIABLE_403 is an access observation, "
            "never a deployment claim"
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
    return PortfolioSnapshot(
        assets=tuple(assets), observed_at=observed, anonymous=client.token is None
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
        )
        for a in (data.get("assets") or ())  # type: ignore[union-attr]
    )
    return PortfolioSnapshot(
        assets=assets,
        observed_at=datetime.fromisoformat(str(data.get("observed_at"))),
        anonymous=str(data.get("provenance")) == "ANONYMOUS_PUBLIC_READ",
    )


__all__ = [
    "PORTFOLIO_SCHEMA",
    "AssetObservation",
    "PortfolioSnapshot",
    "default_policy",
    "observe_asset",
    "observe_portfolio",
    "portfolio_from_data",
]
