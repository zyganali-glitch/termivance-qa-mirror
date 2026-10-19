"""Bounded-absence evidence for a real publisher→retired transition.

A negative observation is not universal absence. This module refuses to promote
unknown, error, stale, out-of-scope or un-published observations into
``OBSERVED_ABSENT``.

Crucially, two unrelated ``404`` responses are **never** sufficient. To award
``OBSERVED_ABSENT`` for one exact target the evidence must demonstrate a real
transition:

1. a genuinely published pre-state (a live Pages deployment *and* an
   independently observed distinctive marker at the exact served URL);
2. the pre-state URL is bound to the same exact target and equals the post URL;
3. a recorded, accepted authorized unpublish action;
4. an independent post-action Pages API read-back that the resource is gone;
5. an independent post-action read-back of the *same* previously served URL;
6. freshness within the stated interval.

Anything else fails closed to ``INCONCLUSIVE``; a site still served yields
``BLOCKED``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

#: The observation scopes that must all be present before a Pages site may be
#: called absent. GitLab-native state alone is never sufficient.
REQUIRED_PAGES_SCOPES: frozenset[str] = frozenset({"pages_api", "served_url"})


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class EvidenceError(ValueError):
    """Raised when an evidence receipt is malformed."""


@dataclass(frozen=True, slots=True)
class PagesPreState:
    """A genuinely published pre-retirement observation of one Pages target."""

    served_url: str
    marker: str
    marker_observed: bool
    deployment_present: bool
    observed_at: datetime
    #: SHA-256 of the served body actually observed at execution time. It binds
    #: the pre-state to *what was seen*, not merely to what a JSON file claims.
    marker_sha256: str | None = None

    @property
    def genuinely_published(self) -> bool:
        return bool(self.marker_observed and self.deployment_present and self.served_url)

    def to_dict(self) -> dict[str, object]:
        return {
            "served_url": self.served_url,
            "marker": self.marker,
            "marker_observed": self.marker_observed,
            "deployment_present": self.deployment_present,
            "marker_sha256": self.marker_sha256,
            "observed_at": _as_utc(self.observed_at).isoformat(),
            "genuinely_published": self.genuinely_published,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> PagesPreState:
        try:
            observed = datetime.fromisoformat(str(data["observed_at"]))
        except (KeyError, ValueError) as exc:
            raise EvidenceError("pre-state record has an invalid observed_at") from exc
        try:
            served_url = str(data["served_url"])
            marker = str(data["marker"])
        except KeyError as exc:
            raise EvidenceError(f"pre-state record is missing {exc}") from exc
        marker_sha256 = data.get("marker_sha256")
        if marker_sha256 is not None and not str(marker_sha256).strip():
            marker_sha256 = None
        return cls(
            served_url=served_url,
            marker=marker,
            marker_observed=bool(data.get("marker_observed")),
            deployment_present=bool(data.get("deployment_present")),
            marker_sha256=str(marker_sha256) if marker_sha256 else None,
            observed_at=observed,
        )


@dataclass(frozen=True, slots=True)
class PagesObservation:
    """One dated post-retirement observation of one exact GitLab Pages target."""

    target: TargetIdentity
    observed_scope: frozenset[str]
    observation_time_utc: datetime
    source: str
    api_status: int | None
    served_url: str | None
    http_status: int | None
    fresh_until: datetime
    pre_state: PagesPreState | None = None
    action_accepted: bool = False
    action_endpoint: str | None = None

    def __post_init__(self) -> None:
        if self.target.resource_kind != "GITLAB_PAGES_SITE":
            raise EvidenceError("PagesObservation target must be a GITLAB_PAGES_SITE")
        if not isinstance(self.observed_scope, frozenset):
            raise EvidenceError("observed_scope must be a frozenset")
        if not isinstance(self.source, str) or not self.source.strip():
            raise EvidenceError("source describing the observation identity is required")

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": "GITLAB_PAGES",
            "target": self.target.to_dict(),
            "observed_scope": sorted(self.observed_scope),
            "observation_time_utc": _as_utc(self.observation_time_utc).isoformat(),
            "source": self.source,
            "api_status": self.api_status,
            "served_url": self.served_url,
            "http_status": self.http_status,
            "fresh_until": _as_utc(self.fresh_until).isoformat(),
            "action_accepted": self.action_accepted,
            "action_endpoint": self.action_endpoint,
            "pre_state": self.pre_state.to_dict() if self.pre_state else None,
        }


def bounded_absence(observation: PagesObservation, now: datetime) -> Verdict:
    """Return the strongest verdict this observation can justify, failing closed.

    ``OBSERVED_ABSENT`` requires the full transition described in the module
    docstring. A missing or unproven pre-state, a mismatched URL, an unaccepted
    action, an error/timeout/challenge, or stale evidence all yield
    ``INCONCLUSIVE``.
    """
    now = _as_utc(now)
    if now > _as_utc(observation.fresh_until):
        return Verdict.INCONCLUSIVE
    if observation.api_status == 200:
        return Verdict.BLOCKED
    if not REQUIRED_PAGES_SCOPES.issubset(observation.observed_scope):
        return Verdict.INCONCLUSIVE

    pre = observation.pre_state
    if pre is None or not pre.genuinely_published:
        # No proof the site was ever genuinely published: absence cannot be claimed.
        return Verdict.INCONCLUSIVE
    if not observation.served_url or pre.served_url != observation.served_url:
        return Verdict.INCONCLUSIVE
    if not observation.action_accepted:
        return Verdict.INCONCLUSIVE
    if observation.api_status in (404, 410) and observation.http_status in (404, 410):
        return Verdict.OBSERVED_ABSENT
    return Verdict.INCONCLUSIVE


def receipt(
    observation: PagesObservation, now: datetime, *, authorization_binding: str | None = None
) -> Mapping[str, object]:
    """Build a minimal bounded-absence receipt for the observation."""
    data: dict[str, object] = dict(observation.to_dict())
    data["verdict"] = bounded_absence(observation, now).value
    data["authorization_binding"] = authorization_binding
    return data
