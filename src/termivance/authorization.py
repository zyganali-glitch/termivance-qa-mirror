"""Bounded, exact-target authorization.

Authorization is never inferred from prose, a successful CI job, or an earlier
approval. It is bound to an immutable numeric project ID, the full path, the
exact resource kind, the exact action, an expiry and a bounded use count, and it
is revalidated immediately before any mutation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

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

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "termivance.authorization/v1",
            "target": self.target.to_dict(),
            "action": self.action,
            "issued_at": _as_utc(self.issued_at).isoformat(),
            "expires_at": _as_utc(self.expires_at).isoformat(),
            "nonce": self.nonce,
            "max_uses": self.max_uses,
            "uses": self.uses,
            "binding": self.binding(),
        }

    def binding(self) -> str:
        """A stable digest of the exact bound target/action/expiry/uses.

        Printed in the receipt so an operator approval can be compared to the
        exact authorization that was consumed.
        """
        payload = json.dumps(
            {
                "target": self._bound.to_dict(),
                "action": self.action,
                "issued_at": _as_utc(self.issued_at).isoformat(),
                "expires_at": _as_utc(self.expires_at).isoformat(),
                "nonce": self.nonce,
                "max_uses": self.max_uses,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Authorization:
        """Reconstruct a bound authorization from a signed operator approval record."""
        try:
            target = TargetIdentity.from_dict(dict(data["target"]))  # type: ignore[arg-type]
        except (KeyError, TypeError) as exc:
            raise AuthorizationError("authorization record is missing a valid target") from exc
        try:
            issued = datetime.fromisoformat(str(data["issued_at"]))
            expires = datetime.fromisoformat(str(data["expires_at"]))
        except (KeyError, ValueError) as exc:
            raise AuthorizationError("authorization record has invalid timestamps") from exc
        return cls(
            target=target,
            action=str(data["action"]),
            issued_at=issued,
            expires_at=expires,
            nonce=str(data["nonce"]),
            max_uses=int(data.get("max_uses", 1)),  # type: ignore[arg-type]
            uses=int(data.get("uses", 0)),  # type: ignore[arg-type]
        )


def load_authorization(path: str | Path) -> Authorization:
    """Load an explicit, operator-issued authorization record. Fails closed."""
    p = Path(path)
    if not p.is_file():
        raise AuthorizationError(f"authorization file not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthorizationError(f"invalid authorization JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AuthorizationError("authorization record must be a JSON object")
    return Authorization.from_dict(data)
