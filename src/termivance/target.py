"""Exact target identity.

A retirement operation is only ever meaningful against one exact, immutable
target. This module makes the target explicit and validated so that ambiguous or
free-text targets cannot be constructed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

RESOURCE_KINDS: frozenset[str] = frozenset(
    {
        "GITLAB_PROJECT",
        "GITLAB_PAGES_SITE",
        "GITLAB_ENVIRONMENT",
    }
)


class TargetError(ValueError):
    """Raised when a target identity is invalid or ambiguous."""


@dataclass(frozen=True, slots=True)
class TargetIdentity:
    """An immutable identity for a single GitLab-hosted resource.

    ``project_id`` is the numeric, immutable GitLab project ID; the human
    ``full_path`` may be renamed but the numeric ID may not change.
    """

    project_id: int
    full_path: str
    resource_kind: str

    def __post_init__(self) -> None:
        if isinstance(self.project_id, bool) or not isinstance(self.project_id, int):
            raise TargetError("project_id must be an integer (immutable numeric GitLab ID)")
        if self.project_id <= 0:
            raise TargetError("project_id must be a positive numeric ID")
        if not isinstance(self.full_path, str) or not self.full_path.strip():
            raise TargetError("full_path must be a non-empty namespace/project path")
        if self.full_path != self.full_path.strip():
            raise TargetError("full_path must not contain surrounding whitespace")
        if self.full_path.startswith("/") or self.full_path.endswith("/"):
            raise TargetError("full_path must be normalized without leading/trailing '/'")
        if self.resource_kind not in RESOURCE_KINDS:
            raise TargetError(f"unknown resource_kind: {self.resource_kind!r}")

    def key(self) -> tuple[int, str, str]:
        """Return the exact-identity tuple used for equality-sensitive checks."""
        return (self.project_id, self.full_path, self.resource_kind)

    def key_string(self) -> str:
        """A canonical *string* form of :meth:`key` for durable cross-process use.

        Tuples do not survive a JSON round trip (they become arrays), so any
        record that must compare equal after being saved and reloaded — ledger
        entries, execution-time authorization records — uses this canonical
        string instead of the raw tuple.
        """
        return json.dumps(list(self.key()), separators=(",", ":"), ensure_ascii=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "full_path": self.full_path,
            "resource_kind": self.resource_kind,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TargetIdentity:
        try:
            return cls(
                project_id=data["project_id"],  # type: ignore[arg-type]
                full_path=data["full_path"],  # type: ignore[arg-type]
                resource_kind=data["resource_kind"],  # type: ignore[arg-type]
            )
        except KeyError as exc:
            raise TargetError(f"target is missing required field: {exc.args[0]!r}") from exc
