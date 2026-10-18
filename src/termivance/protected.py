"""Deterministic protected-target registry.

Some targets must never be retired regardless of authorization, evidence or
model output. Protection is a deterministic constraint, not an observation, and
is therefore evaluated without any provider call.
"""

from __future__ import annotations

#: Project IDs that may never be retired. Keep this list explicit and reviewable.
PROTECTED_PROJECT_IDS: frozenset[int] = frozenset(
    {
        87779099,  # canonical Termivance repository
        87777871,  # organizer Showcase project
    }
)

_PROTECTION_REASON: dict[int, str] = {
    87779099: "canonical Termivance repository is expressly excluded from retirement",
    87777871: "organizer Showcase project is shared and must never be retired",
}


def is_protected(project_id: int) -> bool:
    """Return True if the numeric project ID is on the protected list."""
    return project_id in PROTECTED_PROJECT_IDS


def protection_reason(project_id: int) -> str | None:
    """Return the human reason a project is protected, or None."""
    return _PROTECTION_REASON.get(project_id)
