"""Affirmative, operator-supplied redeployment-control attestation.

An observed CI file without a Pages mechanism is **not** proof that no
redeployment path exists (a scheduled pipeline, a webhook, an external deploy, or
a future commit can always recreate a Pages site). Termivance therefore never
infers negative control: it requires an explicit, attributed, dated operator
attestation bound to the exact target.

This is deliberately *not* a model or executor judgement. The record is supplied
out of band by the operator, and, when a signature key is configured, must carry
a valid HMAC over the exact target binding.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from termivance.discovery import ObservationRecord
from termivance.graph import EvidenceKind
from termivance.target import TargetIdentity


class AttestationError(RuntimeError):
    """Raised when a control attestation is missing, malformed or mismatched."""


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def target_key_for(target: TargetIdentity) -> str:
    """A stable, canonical string form of the exact bound target."""
    return f"{target.project_id}:{target.full_path}:{target.resource_kind}"


@dataclass(frozen=True, slots=True)
class ControlAttestation:
    """An explicit operator statement that redeployment is technically controlled."""

    operator: str
    statement: str
    asserted_at: datetime
    target_key: str
    signature: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "asserted_at", _utc(self.asserted_at))
        for name, value in (
            ("operator", self.operator),
            ("statement", self.statement),
            ("target_key", self.target_key),
        ):
            if not isinstance(value, str) or not value.strip():
                raise AttestationError(f"control attestation requires a non-empty {name}")

    def verify(self, target: TargetIdentity, *, key: str | None = None) -> None:
        if self.target_key != target_key_for(target):
            raise AttestationError(
                "control attestation is bound to a different target than the one to be retired"
            )
        if key is not None:
            expected = hmac.new(
                key.encode("utf-8"), self.target_key.encode("utf-8"), hashlib.sha256
            ).hexdigest()
            if not self.signature or not hmac.compare_digest(expected, self.signature):
                raise AttestationError(
                    "control attestation signature is missing or invalid for the configured key"
                )

    def to_record(self, *, now: datetime, ttl: timedelta) -> ObservationRecord:
        observed = _utc(now)
        return ObservationRecord(
            kind=EvidenceKind.REDEPLOYMENT_CONTROL,
            method="ATTESTATION",
            endpoint="operator://redeployment-control",
            status=None,
            error_kind=None,
            detail={
                "control": self.statement,
                "operator": self.operator,
                "asserted_at": self.asserted_at.isoformat(),
                "target_key": self.target_key,
            },
            observed_at=observed,
            fresh_until=observed + ttl,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "termivance.control_attestation/v1",
            "operator": self.operator,
            "statement": self.statement,
            "asserted_at": self.asserted_at.isoformat(),
            "target_key": self.target_key,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ControlAttestation:
        try:
            asserted = datetime.fromisoformat(str(data["asserted_at"]))
        except (KeyError, ValueError) as exc:
            raise AttestationError("control attestation has an invalid asserted_at") from exc
        return cls(
            operator=str(data.get("operator", "")),
            statement=str(data.get("statement", "")),
            asserted_at=asserted,
            target_key=str(data.get("target_key", "")),
            signature=(str(data["signature"]) if data.get("signature") else None),
        )


__all__ = ["AttestationError", "ControlAttestation", "target_key_for"]
