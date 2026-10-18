"""Live bounded-absence observation.

Combines two independent evidence channels for one exact Pages target:

* the GitLab Pages API (``GET /projects/:id/pages``), and
* a separate, unauthenticated HTTP request to the exact previously-served URL.

The two are never conflated. The strongest claim this can support is
``OBSERVED_ABSENT`` for the *exact tested resource and surfaces within the
observation interval*. A 403, a timeout, a redirect to a login page, or an
inaccessible URL is never promoted to absence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from termivance.evidence import PagesObservation, bounded_absence
from termivance.gitlab_client import GitLabClient
from termivance.pages import https_get_status, read_pages_state
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

DEFAULT_TTL_SECONDS = 900


@dataclass(frozen=True, slots=True)
class AbsenceProbe:
    """One combined, independently sourced observation of a Pages target."""

    observation: PagesObservation
    pages_api_status: int | None
    pages_api_error: str | None
    served_http_status: int | None
    served_error: str | None
    verdict: Verdict

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict.value,
            "pages_api": {"status": self.pages_api_status, "error": self.pages_api_error},
            "served_url": {
                "http_status": self.served_http_status,
                "error": self.served_error,
            },
            "observation": self.observation.to_dict(),
        }


def observe_absence(
    client: GitLabClient,
    target: TargetIdentity,
    served_url: str,
    *,
    now: datetime | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> AbsenceProbe:
    """Perform both independent probes and compute the bounded verdict."""
    observed = now or datetime.now(tz=UTC)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)
    observed = observed.astimezone(UTC)

    state = read_pages_state(client, target, now=observed)
    http_status, http_error = https_get_status(served_url)

    observation = PagesObservation(
        target=target,
        observed_scope=frozenset({"pages_api", "served_url"}),
        observation_time_utc=observed,
        source=f"GET {state.endpoint} + GET {served_url}",
        api_status=state.status,
        served_url=served_url,
        http_status=http_status,
        fresh_until=observed + timedelta(seconds=ttl_seconds),
    )
    verdict = bounded_absence(observation, observed)
    return AbsenceProbe(
        observation=observation,
        pages_api_status=state.status,
        pages_api_error=state.error_kind,
        served_http_status=http_status,
        served_error=http_error,
        verdict=verdict,
    )
