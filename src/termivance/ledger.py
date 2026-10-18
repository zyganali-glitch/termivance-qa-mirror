"""Durable, failure-safe single-use consumption ledger for authorization.

The in-memory ``uses`` counter on :class:`termivance.authorization.Authorization`
protects one process. It does nothing against the realistic failure mode this
module exists for: reloading the same authorization JSON file in a *new* CLI
invocation and executing a second destructive operation.

The ledger is a small local JSON file. Consumption is recorded **before** the
mutation is attempted and written atomically (temp file + ``os.replace``), so:

* a crash after the reservation burns the authorization (conservative: an
  unused but burnt authorization is always preferable to a reused one);
* a repeated invocation with the same bound authorization is refused;
* no database, network call or paid service is involved.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from termivance.authorization import Authorization


class LedgerError(RuntimeError):
    """Raised when a consumption record cannot be written or already exists."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class Consumption:
    """One durable record that an exact authorization was spent."""

    binding: str
    nonce: str
    action: str
    target_key: str
    operation_id: str
    consumed_at: datetime
    state: str

    def to_dict(self) -> dict[str, object]:
        return {
            "binding": self.binding,
            "nonce": self.nonce,
            "action": self.action,
            "target_key": self.target_key,
            "operation_id": self.operation_id,
            "consumed_at": _as_utc(self.consumed_at).isoformat(),
            "state": self.state,
        }


class AuthorizationLedger:
    """A minimal durable record of spent authorizations."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _read(self) -> dict[str, dict[str, object]]:
        if not self.path.is_file():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LedgerError(
                f"authorization ledger at {self.path} is unreadable; refusing to guess: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise LedgerError(f"authorization ledger at {self.path} is malformed")
        entries = data.get("consumed")
        if entries is None:
            return {}
        if not isinstance(entries, dict):
            raise LedgerError(f"authorization ledger at {self.path} has invalid entries")
        return {str(k): dict(v) for k, v in entries.items() if isinstance(v, dict)}

    def _write(self, entries: dict[str, dict[str, object]]) -> None:
        payload = {
            "schema": "termivance.authorization_ledger/v1",
            "consumed": entries,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        directory = str(self.path.parent)
        fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=".ledger-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise

    def is_consumed(self, binding: str) -> bool:
        return binding in self._read()

    def record(self, entry: Consumption) -> None:
        entries = self._read()
        entries[entry.binding] = entry.to_dict()
        try:
            self._write(entries)
        except OSError as exc:
            raise LedgerError(
                f"could not durably record authorization consumption at {self.path}: {exc}"
            ) from exc

    def consume(
        self,
        authorization: Authorization,
        *,
        operation_id: str,
        now: datetime,
        target_key: str | None = None,
    ) -> Consumption:
        """Durably spend one exact authorization, or refuse.

        Raises :class:`LedgerError` when the same bound authorization was already
        consumed — including by an earlier, separate process invocation.
        """
        binding = authorization.binding()
        if self.is_consumed(binding):
            raise LedgerError(
                f"authorization {binding[:16]}… was already consumed; a reloaded "
                "authorization file can never execute a second destructive operation"
            )
        entry = Consumption(
            binding=binding,
            nonce=authorization.nonce,
            action=authorization.action,
            target_key=target_key or authorization.target.key(),
            operation_id=operation_id,
            consumed_at=_as_utc(now),
            state="RESERVED_BEFORE_MUTATION",
        )
        self.record(entry)
        if not self.is_consumed(binding):  # verify the write really landed
            raise LedgerError("durable authorization consumption could not be verified")
        return entry

    def finalize(self, binding: str, *, outcome: str) -> None:
        """Record the observed outcome of the operation (best effort)."""
        entries = self._read()
        existing = entries.get(binding)
        if existing is None:
            return
        existing["state"] = f"CONSUMED_{outcome}"
        entries[binding] = existing
        try:
            self._write(entries)
        except OSError:
            # The reservation is already durable; failing to annotate it must not
            # silently re-enable the authorization.
            return


__all__ = ["AuthorizationLedger", "Consumption", "LedgerError"]
