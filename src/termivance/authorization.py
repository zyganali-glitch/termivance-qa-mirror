"""Bounded, exact-target authorization.

Authorization is never inferred from prose, a successful CI job, or an earlier
approval. It is bound to an immutable numeric project ID, the full path, the
exact resource kind, the exact action, an expiry and a bounded use count, and it
is revalidated immediately before any mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from termivance.target import TargetIdentity


class AuthorizationError(RuntimeError):
    """Raised when authorization is missing, ambiguous, expired or mismatched."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(slots=True)
class Authorization:
    target: TargetIdentity
    action: str
    issued_at: datetime
    expires_at: datetime
    nonce: str
    max_uses: int = 1
    uses: int = 0
    _bound: TargetIdentity = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.target, TargetIdentity):
            raise AuthorizationError("target must be a validated TargetIdentity")
        self.issued_at = _as_utc(self.issued_at)
        self.expires_at = _as_utc(self.expires_at)
        if self.expires_at <= self.issued_at:
            raise AuthorizationError("expires_at must be after issued_at")
        if not isinstance(self.action, str) or not self.action.strip():
            raise AuthorizationError("action must be a non-empty string")
        if not isinstance(self.nonce, str) or not self.nonce.strip():
            raise AuthorizationError("nonce must be a non-empty single-use identifier")
        if not isinstance(self.max_uses, int) or self.max_uses < 1:
            raise AuthorizationError("max_uses must be an integer >= 1")
        # Freeze the exact bound target so later mutation of inputs cannot shift it.
        self._bound = TargetIdentity(
            project_id=self.target.project_id,
            full_path=self.target.full_path,
            resource_kind=self.target.resource_kind,
        )

    def is_valid(self, now: datetime, target: TargetIdentity, action: str) -> bool:
        """Return True only for the exact bound target/action within bounds."""
        now = _as_utc(now)
        if self.uses >= self.max_uses:
            return False
        if now < self.issued_at or now > self.expires_at:
            return False
        if action != self.action:
            return False
        return target.key() == self._bound.key()

    def consume(self, now: datetime, target: TargetIdentity, action: str) -> None:
        """Revalidate and consume one use, or refuse."""
        if not self.is_valid(now, target, action):
            raise AuthorizationError(
                "authorization is not valid for this exact target/action/time "
                "(expired, exhausted, or target/action mismatch)"
            )
        self.uses += 1

    @classmethod
    def issue(
        cls,
        target: TargetIdentity,
        action: str,
        *,
        nonce: str,
        now: datetime | None = None,
        ttl: timedelta = timedelta(minutes=10),
        max_uses: int = 1,
    ) -> Authorization:
        issued = _as_utc(now or datetime.now(tz=UTC))
        return cls(
            target=target,
            action=action,
            issued_at=issued,
            expires_at=issued + ttl,
            nonce=nonce,
            max_uses=max_uses,
        )

    @classmethod
    def from_prose(cls, *_args: object, **_kwargs: object) -> Authorization:
        """Always refuse: authorization may not be inferred from prose."""
        raise AuthorizationError("authorization cannot be inferred from prose or model text")
