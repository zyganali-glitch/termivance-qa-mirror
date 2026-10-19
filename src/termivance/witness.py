"""Resurrection Counterexample Witness (read-only, non-authoritative).

A bounded absence observation is never a permanent guarantee: a retired Pages
resource can *reappear* whenever a redeployment mechanism still exists — a
default-branch pipeline that publishes Pages, a pages job in the current CI
configuration, an administration-path action this identity cannot even see, or
an eventually-consistent CDN cache. This module builds the honest counter-
example record for exactly one target: it reads the target's **own**
``.gitlab-ci.yml`` at the **exact observed commit** (never the canonical
repository's template) plus the target's Pages administration surface, and
records:

* the redeployment signals actually present in the observed configuration;
* the precise phrasing of every surface this identity could *not* verify —
  a 403 here means "the observing identity cannot verify this Pages
  administration surface", never "the site is absent";
* an explicit counterexample list: everything that could still resurrect the
  resource;
* ``absence_claim: NEVER_FROM_THIS_WITNESS`` and
  ``resurrection_controlled: NOT_CLAIMED`` — this module can never award
  ``RESURRECTION_CONTROLLED``; that verdict additionally requires live
  monitoring/control evidence that a witness sweep does not provide.

There is no mutation surface: the client is GET-only by construction and this
module performs no write of any kind.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from termivance.discovery import ci_configuration_is_complete, detect_pages_mechanism
from termivance.gitlab_client import GitLabClient
from termivance.target import TargetIdentity

RESURRECTION_WITNESS_SCHEMA = "termivance.resurrection_witness/v1"
WITNESS_TTL_SECONDS = 900

ABSENCE_CLAIM_NEVER = "NEVER_FROM_THIS_WITNESS"
RESURRECTION_CONTROLLED_NOT_CLAIMED = "NOT_CLAIMED"


class ResurrectionPossibility(StrEnum):
    """What the witness can honestly say about resurrection paths."""

    MECHANISM_PRESENT_IN_OBSERVED_CONFIG = "MECHANISM_PRESENT_IN_OBSERVED_CONFIG"
    MECHANISM_NOT_FOUND_CONFIG_INCOMPLETE = "MECHANISM_NOT_FOUND_CONFIG_INCOMPLETE"
    NO_MECHANISM_IN_OBSERVED_CONFIG = "NO_MECHANISM_IN_OBSERVED_CONFIG"
    CONFIG_NOT_OBSERVED = "CONFIG_NOT_OBSERVED"


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


def _pages_admin_phrase(status: int | None) -> str:
    if status == 200:
        return (
            "the Pages administration surface is observable to this identity "
            "(HTTP 200); whether a site is served still requires the served-URL "
            "observation, and this witness claims no absence either way"
        )
    if status in (401, 403):
        return (
            f"the observing identity cannot verify this Pages administration "
            f"surface (HTTP {status}); a site may be present or absent right now "
            "and neither state is claimed from this observation"
        )
    if status == 404:
        return (
            "the Pages administration surface returned 404 to this identity; an "
            "access observation, never absence"
        )
    return (
        "the Pages administration surface was not observable in this pass; "
        "unknown is never promoted to absence"
    )


@dataclass(frozen=True, slots=True)
class ResurrectionWitness:
    """One read-only counterexample sweep for exactly one target."""

    target: TargetIdentity
    observed_at: datetime
    fresh_until: datetime
    default_branch: str | None
    commit_sha: str | None
    config: dict[str, object]
    pages_administration: dict[str, object]
    resurrection_possible: str
    counterexamples: tuple[str, ...]
    absence_claim: str = ABSENCE_CLAIM_NEVER
    resurrection_controlled: str = RESURRECTION_CONTROLLED_NOT_CLAIMED

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": RESURRECTION_WITNESS_SCHEMA,
            "authority": "NON_AUTHORITATIVE",
            "provenance": "ANONYMOUS_PUBLIC_READ",
            "target": self.target.to_dict(),
            "observed_at": _utc(self.observed_at).isoformat(),
            "fresh_until": _utc(self.fresh_until).isoformat(),
            "default_branch": self.default_branch,
            "commit_sha": self.commit_sha,
            "config": dict(self.config),
            "pages_administration": dict(self.pages_administration),
            "resurrection_possible": self.resurrection_possible,
            "counterexamples": list(self.counterexamples),
            "absence_claim": self.absence_claim,
            "resurrection_controlled": self.resurrection_controlled,
            "boundary": (
                "this witness lists resurrection counterexamples; it never "
                "claims absence and never awards RESURRECTION_CONTROLLED — "
                "that verdict additionally requires live monitoring/control "
                "evidence this read-only sweep cannot provide"
            ),
        }

    def render(self) -> str:
        lines = [
            f"RESURRECTION WITNESS — project {self.target.project_id} "
            f"({self.target.full_path}) @ {_utc(self.observed_at).isoformat()}",
            f"default branch: {self.default_branch!r}  commit: {self.commit_sha!r}",
            f"resurrection_possible: {self.resurrection_possible}",
            f"absence_claim: {self.absence_claim}  "
            f"resurrection_controlled: {self.resurrection_controlled}",
            "-" * 100,
            f"config: {self.config.get('endpoint')}",
            f"  status: {self.config.get('status')!r} ({self.config.get('error_kind')!r}); "
            f"signals: {self.config.get('signals')!r}; "
            f"complete: {self.config.get('configuration_complete')!r}",
            f"pages administration: {self.pages_administration.get('endpoint')}",
            f"  status: {self.pages_administration.get('status')!r} — "
            f"{self.pages_administration.get('phrase')}",
            "counterexamples:",
        ]
        for item in self.counterexamples:
            lines.append(f"  - {item}")
        boundary = self.to_dict()["boundary"]
        lines.append(f"boundary: {boundary}")
        return "\n".join(lines)


def build_witness(
    client: GitLabClient,
    target: TargetIdentity,
    *,
    now: datetime | None = None,
    ttl_seconds: int = WITNESS_TTL_SECONDS,
) -> ResurrectionWitness:
    """Read-only sweep: the target's own CI config at the exact commit + Pages surface."""
    observed = _utc(now)

    # 1. The target's own repository facts — never another project's template.
    project = client.get_json(f"/projects/{target.project_id}")
    default_branch: str | None = None
    if project.ok and isinstance(project.data, dict):
        branch_value = project.data.get("default_branch")
        default_branch = str(branch_value) if branch_value else None

    commit_sha: str | None = None
    if default_branch:
        commits = client.get_json(
            f"/projects/{target.project_id}/repository/commits",
            params={"ref_name": default_branch, "per_page": 1},
        )
        if commits.ok and isinstance(commits.data, list) and commits.data:
            first = commits.data[0]
            if isinstance(first, dict) and first.get("id"):
                commit_sha = str(first["id"])

    config_ref = commit_sha or default_branch or "HEAD"
    config_endpoint = (
        f"/projects/{target.project_id}/repository/files/.gitlab-ci.yml/raw"
        f"?ref={config_ref}"
    )
    config = client.get_text(
        f"/projects/{target.project_id}/repository/files/.gitlab-ci.yml/raw",
        params={"ref": config_ref},
    )
    signals: list[str] = []
    config_complete: bool | None = None
    config_digest: str | None = None
    if config.ok and isinstance(config.data, str):
        config_digest = hashlib.sha256(config.data.encode("utf-8")).hexdigest()
        _detects, signals = detect_pages_mechanism(config.data)
        config_complete = ci_configuration_is_complete(config.data)

    if not (config.ok and isinstance(config.data, str)):
        possibility = ResurrectionPossibility.CONFIG_NOT_OBSERVED
    elif signals:
        possibility = ResurrectionPossibility.MECHANISM_PRESENT_IN_OBSERVED_CONFIG
    elif config_complete:
        possibility = ResurrectionPossibility.NO_MECHANISM_IN_OBSERVED_CONFIG
    else:
        possibility = ResurrectionPossibility.MECHANISM_NOT_FOUND_CONFIG_INCOMPLETE

    # 2. The Pages administration surface of that exact target.
    pages = client.get_json(f"/projects/{target.project_id}/pages")
    pages_admin: dict[str, object] = {
        "endpoint": f"/projects/{target.project_id}/pages",
        "status": pages.status,
        "error_kind": pages.error_kind,
        "phrase": _pages_admin_phrase(pages.status),
    }

    # 3. Counterexamples — every path that could still resurrect the resource.
    counterexamples: list[str] = []
    if possibility == ResurrectionPossibility.MECHANISM_PRESENT_IN_OBSERVED_CONFIG:
        counterexamples.append(
            "the target's own default-branch CI configuration at the observed "
            f"commit {config_ref} carries Pages redeployment signal(s) {signals!r}; "
            "any pipeline executing that configuration can republish the site"
        )
    elif possibility == ResurrectionPossibility.MECHANISM_NOT_FOUND_CONFIG_INCOMPLETE:
        counterexamples.append(
            "no Pages signal was found in the observed root configuration, but it "
            "uses include:, so mechanisms may exist in external fragments this "
            "observation does not cover"
        )
    elif possibility == ResurrectionPossibility.CONFIG_NOT_OBSERVED:
        counterexamples.append(
            "the target's CI configuration was not observable; redeployment "
            "mechanisms cannot be excluded from this sweep"
        )
    counterexamples.append(
        "a pages-administration action through the provider API or UI could "
        "republish the site at any time, independent of repository content"
    )
    if not (pages.status == 200):
        counterexamples.append(
            "the Pages administration surface of this exact target is not "
            "verifiable by this observing identity right now; a site may exist "
            "and it must not be assumed away"
        )
    counterexamples.append(
        "cached or edge-replicated copies of previously served content can "
        "remain reachable after the provider state changes"
    )

    return ResurrectionWitness(
        target=target,
        observed_at=observed,
        fresh_until=observed + timedelta(seconds=ttl_seconds),
        default_branch=default_branch,
        commit_sha=commit_sha,
        config={
            "endpoint": config_endpoint,
            "ref": config_ref,
            "status": config.status,
            "error_kind": config.error_kind,
            "digest_sha256": config_digest,
            "signals": signals,
            "configuration_complete": config_complete,
        },
        pages_administration=pages_admin,
        resurrection_possible=possibility.value,
        counterexamples=tuple(counterexamples),
    )


__all__ = [
    "ABSENCE_CLAIM_NEVER",
    "RESURRECTION_CONTROLLED_NOT_CLAIMED",
    "RESURRECTION_WITNESS_SCHEMA",
    "WITNESS_TTL_SECONDS",
    "ResurrectionPossibility",
    "ResurrectionWitness",
    "build_witness",
]
