"""Retirement verdicts and the deterministic authority boundary.

Only deterministic code in this package may award an *authoritative* verdict.
Model/agent text is never allowed to assert one. This module encodes that rule
so it can be enforced and tested, not merely documented.
"""

from __future__ import annotations

from enum import StrEnum


class Verdict(StrEnum):
    """The complete set of Termivance verdicts.

    Ordered from most conservative to least; ``combine`` relies on this order.
    """

    NOT_RUN = "NOT_RUN"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"
    SAFE_TO_RETIRE = "SAFE_TO_RETIRE"
    RETIRED = "RETIRED"
    OBSERVED_ABSENT = "OBSERVED_ABSENT"
    RESURRECTION_CONTROLLED = "RESURRECTION_CONTROLLED"


# Verdicts that assert a proven, evidence-backed retirement outcome. These may
# only ever be produced by deterministic evaluation code.
AUTHORITATIVE: frozenset[Verdict] = frozenset(
    {
        Verdict.SAFE_TO_RETIRE,
        Verdict.RETIRED,
        Verdict.OBSERVED_ABSENT,
        Verdict.RESURRECTION_CONTROLLED,
    }
)

_ORDER: tuple[Verdict, ...] = tuple(Verdict)


class ModelClaimRejected(RuntimeError):
    """Raised when model-generated text attempts to award an authoritative verdict."""


def reject_model_awarded_verdict(verdict: Verdict | str) -> None:
    """Refuse an attempt by model prose to assert an authoritative verdict.

    Non-authoritative verdicts (for example ``BLOCKED`` or ``INCONCLUSIVE``) are
    permitted from any source because they fail closed.
    """
    resolved = Verdict(verdict)
    if resolved in AUTHORITATIVE:
        raise ModelClaimRejected(
            f"model/agent text may not award authoritative verdict {resolved.value!r}; "
            "only deterministic evaluation may do so"
        )


def combine(*verdicts: Verdict | str) -> Verdict:
    """Return the most conservative verdict in a fail-closed way.

    Any ``NOT_RUN``/``BLOCKED``/``INCONCLUSIVE`` dominates, so uncertainty can
    never be silently upgraded into a proven retirement outcome.
    """
    if not verdicts:
        return Verdict.NOT_RUN
    resolved = [Verdict(v) for v in verdicts]
    return min(resolved, key=_ORDER.index)
