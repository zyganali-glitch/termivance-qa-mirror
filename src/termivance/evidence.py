"""Bounded-absence evidence.

A negative observation is not universal absence. This module computes a verdict
from one observation of one exact target and refuses to promote unknown, error,
stale or out-of-scope observations into ``OBSERVED_ABSENT``.
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
class PagesObservation:
    """One dated observation of one exact GitLab Pages target."""

    target: TargetIdentity
    observed_scope: frozenset[str]
    observation_time_utc: datetime
    source: str
    api_status: int | None
    served_url: str | None
    http_status: int | None
    fresh_until: datetime

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
        }


def bounded_absence(observation: PagesObservation, now: datetime) -> Verdict:
    """Return the strongest verdict this single observation can justify.

    ``OBSERVED_ABSENT`` requires the API to report the Pages site missing *and*
    the served URL to be independently gone, within scope and within freshness.
    Anything else fails closed to ``INCONCLUSIVE``; a site still served yields
    ``BLOCKED``.
    """
    now = _as_utc(now)
    if now > _as_utc(observation.fresh_until):
        return Verdict.INCONCLUSIVE
    if not REQUIRED_PAGES_SCOPES.issubset(observation.observed_scope):
        return Verdict.INCONCLUSIVE
    if observation.api_status == 200:
        return Verdict.BLOCKED
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
