"""Resurrection tripwire (P2).

Compares two *recorded* observation passes of the same exact target and reports
whether observed publication state changed between them. The tripwire never
mutates anything, never awards absence and never claims control:

* publication observed earlier and gone later → an absence *observation*
  (bounded, per its own rules) worth recording;
* absence observed earlier and publication observed later → **resurrection** —
  the retirement is no longer controlled. This module only *reports* that
  state; re-control requires a fresh authorized operation, never a report.

Both passes must be bound to the same exact target and to compatible evidence.
Anything else (cross-target, missing evidence, stale intervals, contradictions)
stays ``INCONCLUSIVE``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from termivance.evidence import PagesPreState
from termivance.target import TargetIdentity

TRIPWIRE_SCHEMA = "termivance.tripwire/v1"

RESURRECTION_NOT_CONTROLLED = "RESURRECTION_NOT_CONTROLLED"
ABSENCE_OBSERVED_NOT_CONTROLLED = "ABSENCE_OBSERVED_NOT_CONTROLLED"
STABLE_PRESENT = "STABLE_PRESENT"
STABLE_ABSENT_NOT_CONTROLLED = "STABLE_ABSENT_NOT_CONTROLLED"
INCONCLUSIVE = "INCONCLUSIVE"


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class TripwireReading:
    """One recorded observation pass feeding the tripwire."""

    target: TargetIdentity
    served_url: str
    publication_observed: bool  # deployment present (API-level) at reading time
    observed_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target.to_dict(),
            "served_url": self.served_url,
            "publication_observed": self.publication_observed,
            "observed_at": _utc(self.observed_at).isoformat(),
        }


@dataclass(frozen=True, slots=True)
class TripwireReport:
    earlier: TripwireReading
    later: TripwireReading
    state: str
    explanation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": TRIPWIRE_SCHEMA,
            "state": self.state,
            "explanation": self.explanation,
            "earlier": self.earlier.to_dict(),
            "later": self.later.to_dict(),
        }

    def render(self) -> str:
        return "\n".join(
            [
                f"TRIPWIRE: {self.state}",
                f"earlier: publication_observed={self.earlier.publication_observed} "
                f"@ {self.earlier.observed_at.isoformat()}",
                f"later:   publication_observed={self.later.publication_observed} "
                f"@ {self.later.observed_at.isoformat()}",
                self.explanation,
            ]
        )


def check_tripwire(
    earlier: TripwireReading, later: TripwireReading, *, now: datetime | None = None
) -> TripwireReport:
    """Compare two recorded passes of the same target. Fail-closed on anything unclear.

    Args ``now``/``observed`` exist for deterministic interfaces; the comparison
    itself uses only the recorded reading times.
    """
    if earlier.target.key() != later.target.key():
        return TripwireReport(
            earlier, later, INCONCLUSIVE,
            "the two passes are bound to different targets; nothing is claimed",
        )
    if later.observed_at < earlier.observed_at:
        return TripwireReport(
            earlier, later, INCONCLUSIVE,
            "the later pass predates the earlier one; order is unprovable",
        )
    if earlier.publication_observed and not later.publication_observed:
        return TripwireReport(
            earlier, later, ABSENCE_OBSERVED_NOT_CONTROLLED,
            "publication was observed earlier and not observed later: an absence "
            "observation — the absence verdict itself comes only from the bounded "
            "absence rules, and resurrection remains possible",
        )
    if not earlier.publication_observed and later.publication_observed:
        return TripwireReport(
            earlier, later, RESURRECTION_NOT_CONTROLLED,
            "an earlier absent observation is followed by a live deployment: the "
            "site resurfaced. Only a fresh authorized operation can re-establish "
            "control; this report is not that control",
        )
    if earlier.publication_observed and later.publication_observed:
        return TripwireReport(
            earlier, later, STABLE_PRESENT,
            "publication observed on both passes; nothing retired so far",
        )
    return TripwireReport(
        earlier, later, STABLE_ABSENT_NOT_CONTROLLED,
        "no deployment observed on either pass; stable absence is uncontrolled "
        "against redeployment (CDN lag and later redeploys keep this open)"
    )


def reading_from_pre_state(target: TargetIdentity, pre: PagesPreState) -> TripwireReading:
    """Adapt a bounded-absence pre-state (or observation) into a tripwire reading."""
    return TripwireReading(
        target=target,
        served_url=pre.served_url,
        publication_observed=pre.genuinely_published,
        observed_at=pre.observed_at,
    )


__all__ = [
    "TRIPWIRE_SCHEMA",
    "ABSENCE_OBSERVED_NOT_CONTROLLED",
    "INCONCLUSIVE",
    "RESURRECTION_NOT_CONTROLLED",
    "STABLE_ABSENT_NOT_CONTROLLED",
    "STABLE_PRESENT",
    "TripwireReading",
    "TripwireReport",
    "check_tripwire",
    "reading_from_pre_state",
]
