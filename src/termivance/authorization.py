"""Bounded, exact-target authorization with operator-approval provenance.

Authorization is never inferred from prose, a successful CI job, model text or an
earlier approval. It is bound to an immutable numeric project ID, the full path,
the exact resource kind, the exact action, an expiry, a nonce and a bounded use
count, and it is revalidated immediately before any mutation.

Two properties matter beyond "a JSON file exists":

* **Provenance** — a record may only be loaded if it carries an explicit operator
  approval block that references the *exact* endpoint and action and whose
  binding digest matches the authorization it claims to authorise. When a
  signature key is configured the record must also carry a valid HMAC.
* **Single use** — the in-memory use counter is never sufficient on its own; see
  :mod:`termivance.ledger` for the durable consumption record.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from termivance.target import TargetIdentity

#: Environment variable holding the operator-held approval signature key.
APPROVAL_KEY_ENV = "TERMIVANCE_APPROVAL_HMAC_KEY"


class AuthorizationError(RuntimeError):
    """Raised when authorization is missing, ambiguous, expired or mismatched."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _statement_digest(statement: str) -> str:
    return hashlib.sha256(statement.strip().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class OperatorApproval:
    """Verbatim operator approval provenance bound to one exact authorization."""

    operator: str
    statement: str
    approved_at: datetime
    channel: str
    binding: str
    signature: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "approved_at", _as_utc(self.approved_at))
        for name, value in (
            ("operator", self.operator),
            ("statement", self.statement),
            ("channel", self.channel),
            ("binding", self.binding),
        ):
            if not isinstance(value, str) or not value.strip():
                raise AuthorizationError(f"operator approval requires a non-empty {name}")

    @property
    def statement_sha256(self) -> str:
        return _statement_digest(self.statement)

    def verify(self, binding: str, *, key: str | None = None) -> None:
        """Verify the approval is bound to ``binding`` and, if keyed, signed."""
        if not hmac.compare_digest(self.binding, binding):
            raise AuthorizationError(
                "operator approval is bound to a different authorization than the one loaded"
            )
        if key is not None:
            expected = hmac.new(
                key.encode("utf-8"), binding.encode("utf-8"), hashlib.sha256
            ).hexdigest()
            if not self.signature or not hmac.compare_digest(expected, self.signature):
                raise AuthorizationError(
                    "operator approval signature is missing or invalid for the configured key"
                )

    def to_dict(self) -> dict[str, object]:
        return {
            "operator": self.operator,
            "statement": self.statement,
            "statement_sha256": self.statement_sha256,
            "approved_at": _as_utc(self.approved_at).isoformat(),
            "channel": self.channel,
            "binding": self.binding,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> OperatorApproval:
        try:
            approved = datetime.fromisoformat(str(data["approved_at"]))
        except (KeyError, ValueError) as exc:
            raise AuthorizationError("operator approval has an invalid approved_at") from exc
        approval = cls(
            operator=str(data.get("operator", "")),
            statement=str(data.get("statement", "")),
            approved_at=approved,
            channel=str(data.get("channel", "")),
            binding=str(data.get("binding", "")),
            signature=(str(data["signature"]) if data.get("signature") else None),
        )
        recorded = data.get("statement_sha256")
        if recorded is not None and str(recorded) != approval.statement_sha256:
            raise AuthorizationError("operator approval statement digest does not match")
        return approval


@dataclass(slots=True)
class Authorization:
    target: TargetIdentity
    action: str
    issued_at: datetime
    expires_at: datetime
    nonce: str
    max_uses: int = 1
    uses: int = 0
    approval: OperatorApproval | None = None
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

    @property
    def exact_endpoint(self) -> str:
        return f"/projects/{self._bound.project_id}/pages"

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
        """Revalidate and consume one in-memory use, or refuse."""
        if not self.is_valid(now, target, action):
            raise AuthorizationError(
                "authorization is not valid for this exact target/action/time "
                "(expired, exhausted, or target/action mismatch)"
            )
        self.uses += 1

    def verify_approval(
        self, *, key: str | None = None, require: bool = True
    ) -> OperatorApproval | None:
        """Verify operator provenance against the exact bound endpoint/action."""
        if self.approval is None:
            if require:
                raise AuthorizationError(
                    "authorization record carries no operator approval provenance and "
                    "therefore cannot authorise a mutation"
                )
            return None
        self.approval.verify(self.binding(), key=key)
        if self.exact_endpoint not in self.approval.statement:
            raise AuthorizationError(
                "operator approval statement does not reference the exact endpoint "
                f"{self.exact_endpoint}"
            )
        if self.action not in self.approval.statement:
            raise AuthorizationError(
                f"operator approval statement does not reference the action {self.action!r}"
            )
        if self.action != DEFAULT_PAGES_ACTION:
            raise AuthorizationError(
                f"only {DEFAULT_PAGES_ACTION!r} may be authorised by an approval record"
            )
        return self.approval

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
        approval: OperatorApproval | None = None,
    ) -> Authorization:
        issued = _as_utc(now or datetime.now(tz=UTC))
        return cls(
            target=target,
            action=action,
            issued_at=issued,
            expires_at=issued + ttl,
            nonce=nonce,
            max_uses=max_uses,
            approval=approval,
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
            "operator_approval": self.approval.to_dict() if self.approval else None,
        }

    def binding(self) -> str:
        """A stable digest of the exact bound target/action/expiry/nonce/uses."""
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
    def from_dict(cls, data: dict[str, object], *, require_approval: bool = True) -> Authorization:
        """Reconstruct a bound authorization from an operator approval record."""
        try:
            target = TargetIdentity.from_dict(dict(data["target"]))  # type: ignore[arg-type]
        except (KeyError, TypeError) as exc:
            raise AuthorizationError("authorization record is missing a valid target") from exc
        try:
            issued = datetime.fromisoformat(str(data["issued_at"]))
            expires = datetime.fromisoformat(str(data["expires_at"]))
        except (KeyError, ValueError) as exc:
            raise AuthorizationError("authorization record has invalid timestamps") from exc
        raw_approval = data.get("operator_approval")
        approval = None
        if isinstance(raw_approval, dict):
            approval = OperatorApproval.from_dict(dict(raw_approval))
        elif require_approval:
            raise AuthorizationError(
                "authorization record has no operator_approval block; an unsigned, "
                "provenance-free record cannot authorise a destructive operation"
            )
        record = cls(
            target=target,
            action=str(data["action"]),
            issued_at=issued,
            expires_at=expires,
            nonce=str(data["nonce"]),
            max_uses=int(data.get("max_uses", 1)),  # type: ignore[arg-type]
            uses=int(data.get("uses", 0)),  # type: ignore[arg-type]
            approval=approval,
        )
        recorded_binding = data.get("binding")
        if isinstance(recorded_binding, str) and recorded_binding != record.binding():
            raise AuthorizationError(
                "authorization binding digest does not match the recorded content"
            )
        return record


DEFAULT_PAGES_ACTION = "unpublish_pages"


def load_authorization(
    path: str | Path, *, approval_key: str | None = None, require_approval: bool = True
) -> Authorization:
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
    authorization = Authorization.from_dict(data, require_approval=require_approval)
    authorization.verify_approval(key=approval_key, require=require_approval)
    return authorization


__all__ = [
    "APPROVAL_KEY_ENV",
    "DEFAULT_PAGES_ACTION",
    "Authorization",
    "AuthorizationError",
    "OperatorApproval",
    "load_authorization",
]
