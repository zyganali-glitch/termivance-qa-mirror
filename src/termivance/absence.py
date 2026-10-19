"""Live bounded-absence observation of a *real* publication → retirement transition.

Two independent channels are combined for one exact Pages target:

* the GitLab Pages API (``GET /projects/:id/pages``), and
* a separate, unauthenticated HTTP request to the exact previously-served URL.

A negative observation is never universal absence. In particular two unrelated
``404`` responses prove nothing: to award ``OBSERVED_ABSENT`` the evidence must
show that the *same exact* resource was genuinely live before the authorized
unpublish and is gone after it:

1. genuine pre-retirement publication (live Pages deployment **and** an
   independently observed distinctive marker at the exact served URL);
2. the pre-state URL bound to the same target and equal to the post-action URL;
3. a recorded, accepted, authorized unpublish action **bound to a validated
   mutation receipt** (P0-C: a caller-supplied claim can never substitute for
   it — the receipt must prove the exact target, endpoint, operation and its
   durable ledger seal);
4. an independent post-action Pages API read-back;
5. an independent post-action read-back of that same previously served URL;
6. freshness within the stated interval.

Everything else — a never-published site, an unaccepted action, an inaccessible
or challenged URL, a redirect, ambiguity, staleness or URL mismatch — fails
closed to ``INCONCLUSIVE``. A site still served yields ``BLOCKED``. Without a
validated mutation receipt the strongest possible verdict is ``INCONCLUSIVE``,
no matter what the probes return.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from termivance.capsule import MutationBinding, ReceiptValidationError, exact_pages_endpoint
from termivance.evidence import PagesObservation, PagesPreState, bounded_absence
from termivance.gitlab_client import GitLabClient
from termivance.pages import PublicationProbe, https_get, read_pages_state
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

DEFAULT_TTL_SECONDS = 900


def _utc(now: datetime | None) -> datetime:
    value = now or datetime.now(tz=UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def publication_pre_state(probe: PublicationProbe) -> PagesPreState:
    """Convert a live publication probe into the bound pre-retirement state."""
    return PagesPreState(
        served_url=probe.served_url,
        marker=probe.marker,
        marker_observed=probe.marker_observed,
        deployment_present=probe.deployment_present,
        observed_at=probe.observed_at,
    )


@dataclass(frozen=True, slots=True)
class AbsenceProbe:
    """One combined, independently sourced observation of a Pages target."""

    observation: PagesObservation
    pages_api_status: int | None
    pages_api_error: str | None
    served_http_status: int | None
    served_error: str | None
    verdict: Verdict
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict.value,
            "pages_api": {"status": self.pages_api_status, "error": self.pages_api_error},
            "served_url": {
                "http_status": self.served_http_status,
                "error": self.served_error,
            },
            "notes": list(self.notes),
            "observation": self.observation.to_dict(),
        }


def observe_absence(
    client: GitLabClient,
    target: TargetIdentity,
    served_url: str,
    *,
    pre_state: PagesPreState | None = None,
    mutation_receipt: MutationBinding | None = None,
    now: datetime | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> AbsenceProbe:
    """Perform both independent post-action probes and compute the bounded verdict.

    ``mutation_receipt`` (P0-C) is the only bridge to a claimable absence: it
    must be bound to exactly this target, the exact allowed Pages endpoint and
    a durably sealed operation. A caller-supplied ``pre_state`` alone is
    context, never a claim.

    Raises :class:`ReceiptValidationError` when a receipt is structurally
    foreign (different target or endpoint); evidence-level weaknesses instead
    fail closed to ``INCONCLUSIVE``.
    """
    observed = _utc(now)
    state = read_pages_state(client, target, now=observed)
    http_status, http_error, _body = https_get(served_url)

    notes: list[str] = []
    action_accepted = False
    action_endpoint: str | None = None
    effective_pre_state = pre_state

    if mutation_receipt is not None:
        if mutation_receipt.target.key() != target.key():
            raise ReceiptValidationError(
                f"the mutation receipt is bound to target "
                f"{mutation_receipt.target.project_id} ({mutation_receipt.target.full_path}) "
                f"but the observation targets {target.project_id} ({target.full_path}); "
                "cross-target receipts are refused"
            )
        expected_endpoint = exact_pages_endpoint(target)
        if mutation_receipt.endpoint != expected_endpoint:
            raise ReceiptValidationError(
                f"the mutation receipt endpoint {mutation_receipt.endpoint!r} is not the "
                f"exact allowed endpoint {expected_endpoint!r}"
            )
        if not mutation_receipt.accepted:
            notes.append("the bound mutation was not accepted; nothing is proven removed")
        elif not mutation_receipt.durable:
            notes.append(
                "the bound mutation is not durably sealed; no absence may be claimed "
                "from an unsealed action"
            )
        if mutation_receipt.accepted and mutation_receipt.durable:
            action_accepted = True
            action_endpoint = mutation_receipt.endpoint
        if pre_state is None:
            effective_pre_state = mutation_receipt.pre_state
        elif pre_state.to_dict() != mutation_receipt.pre_state.to_dict():
            raise ReceiptValidationError(
                "the supplied pre-state does not match the receipt-bound pre-state; "
                "injected pre-state evidence is refused"
            )
    else:
        notes.append(
            "no validated mutation receipt was supplied: the strongest possible "
            "verdict is INCONCLUSIVE regardless of what the probes return"
        )
        if pre_state is not None:
            notes.append(
                "a caller-supplied pre-state is retained as context only; it can never "
                "prove the authorized mutation"
            )

    if effective_pre_state is None:
        notes.append("no proven pre-retirement publication exists: absence cannot be claimed")
    elif effective_pre_state.served_url != served_url:
        notes.append(
            f"pre-retirement URL {effective_pre_state.served_url!r} does not match the "
            f"observed URL {served_url!r}"
        )
    elif not effective_pre_state.genuinely_published:
        notes.append("the pre-retirement observation did not prove genuine publication")

    observation = PagesObservation(
        target=target,
        observed_scope=frozenset({"pages_api", "served_url"}),
        observation_time_utc=observed,
        source=f"GET {state.endpoint} + GET {served_url}",
        api_status=state.status,
        served_url=served_url,
        http_status=http_status,
        fresh_until=observed + timedelta(seconds=ttl_seconds),
        pre_state=effective_pre_state,
        action_accepted=action_accepted,
        action_endpoint=action_endpoint,
    )
    verdict = bounded_absence(observation, observed)
    return AbsenceProbe(
        observation=observation,
        pages_api_status=state.status,
        pages_api_error=state.error_kind,
        served_http_status=http_status,
        served_error=http_error,
        verdict=verdict,
        notes=tuple(notes),
    )


__all__ = [
    "AbsenceProbe",
    "DEFAULT_TTL_SECONDS",
    "observe_absence",
    "publication_pre_state",
]
