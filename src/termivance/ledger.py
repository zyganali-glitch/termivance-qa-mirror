"""Durable, failure-safe single-use consumption ledger for authorization.

The in-memory ``uses`` counter on :class:`termivance.authorization.Authorization`
protects one process. It does nothing against the realistic failure modes this
module exists for:

* reloading the same authorization JSON file in a *new* CLI invocation and
  executing a second destructive operation;
* two processes attempting the same mutation concurrently;
* a crash between reservation and mutation.

The ledger is a small local JSON file. Consumption is *sealed* (durable record
with state ``RESERVED_BEFORE_MUTATION``) **before** the mutation is attempted,
written atomically (temp file + ``os.replace`` + ``fsync``), so:

* a crash after the seal burns the authorization (conservative: an unused but
  burnt authorization is always preferable to a reused one);
* a repeated invocation with the same bound authorization is refused, no matter
  which process got there first;
* no database, network call or paid service is involved.

Since B4 the durable ledger is **mandatory** on the live ``retire_pages``
execution path (P0-A). A live mutation is refused unless
:meth:`AuthorizationLedger.health_check` proves the ledger is a real, writable,
readable persistence point and :meth:`AuthorizationLedger.consume` has sealed
this exact authorization durably.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from termivance.authorization import Authorization

LEDGER_SCHEMA = "termivance.authorization_ledger/v1"

#: The only initial state a consumption record can ever carry. It is written
#: before the mutation is dispatched; a crash after this point burns the
#: authorization.
SEALED_STATE = "RESERVED_BEFORE_MUTATION"

#: Maximum time to wait for the ledger lock before refusing (conservative:
#: a stale lock from a crashed process must never be silently stolen).
LOCK_TIMEOUT_SECONDS = 10.0

#: Paths that can never durably persist consumption state. A ledger written to
#: one of these would silently lose every reservation.
_NON_DURABLE_PATHS: frozenset[str] = frozenset(
    {"", "-", "nul", "nul:", "/dev/null", "/dev/zero", "/dev/lockable", "$null"}
)


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

    # -- durability classification ----------------------------------------
    def path_is_durable(self) -> bool:
        """False for destinations that cannot persist consumption records.

        Covers terminal/wastebin-style targets (``nul``, ``/dev/null``, ``-``)
        and bare directories. Everything else is provisionally durable; the
        real proof is :meth:`health_check`, which actually writes and re-reads.
        """
        try:
            raw = str(self.path).strip()
        except Exception:  # noqa: BLE001 - a path object must exist to be durable
            return False
        if raw.lower() in _NON_DURABLE_PATHS:
            return False
        lowered = raw.lower().rstrip("/\\")
        if lowered.startswith("/dev/") or lowered.startswith("\\\\.\\"):
            return False
        if lowered == "nul":
            return False
        try:
            if self.path.is_dir():
                return False
        except OSError:
            return False
        return True

    # -- durable read/write -------------------------------------------------
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
        result: dict[str, dict[str, object]] = {}
        for key, value in entries.items():
            if not isinstance(value, dict):
                # A malformed entry must never be silently forgotten: it may be
                # the only durable record that an authorization was spent.
                raise LedgerError(
                    f"authorization ledger entry {key!r} at {self.path} is malformed"
                )
            result[str(key)] = dict(value)
        return result

    def _atomic_write(self, payload: dict[str, object]) -> None:
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

    def _write(self, entries: dict[str, dict[str, object]]) -> None:
        try:
            self._atomic_write({"schema": LEDGER_SCHEMA, "consumed": entries})
        except OSError as exc:
            raise LedgerError(
                f"could not durably write the authorization ledger at {self.path}: {exc}"
            ) from exc

    @contextlib.contextmanager
    def _exclusive(self) -> Iterator[None]:
        """Serialize ledger mutations across processes with a lock file.

        The lock is a ``O_CREAT|O_EXCL`` sentinel next to the ledger itself.
        On timeout the operation *refuses* (a stale lock from a crashed process
        must never be silently stolen — the extra authorization then simply
        does not execute). The stale lock can be removed by the operator.
        """
        lock_path = Path(str(self.path) + ".lock")
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                if time.monotonic() > deadline:
                    raise LedgerError(
                        f"another termivance process holds the authorization ledger "
                        f"lock ({lock_path}); refusing to guess; remove the stale "
                        "lock file once no mutation is in flight"
                    ) from None
                time.sleep(0.05)
        try:
            os.write(fd, str(os.getpid()).encode("utf-8"))
            yield
        finally:
            os.close(fd)
            with contextlib.suppress(OSError):
                lock_path.unlink(missing_ok=True)

    def health_check(self) -> None:
        """Verify the ledger is actually durable and readable before a mutation.

        Creates and re-reads an empty durable record for a fresh path; validates
        a pre-existing one (prior consumption records are valid content).
        Raises :class:`LedgerError` when the ledger cannot be trusted; the
        caller must treat any failure as "no durable ledger" and refuse the
        live mutation. Never silently proceeds.
        """
        if not self.path_is_durable():
            raise LedgerError(
                f"authorization ledger path {self.path!s} is not durable; a real "
                "mutation requires a persistent single-use ledger"
            )
        try:
            if not self.path.is_file():
                self._write({})
            else:
                self._read()
        except LedgerError:
            raise
        except OSError as exc:
            raise LedgerError(
                f"authorization ledger at {self.path} failed its durability readiness "
                f"check: {exc}"
            ) from exc

    def is_consumed(self, binding: str) -> bool:
        return binding in self._read()

    def record(self, entry: Consumption) -> None:
        entries = self._read()
        existing = entries.get(entry.binding)
        if (
            existing is not None
            and str(existing.get("state", "")) == SEALED_STATE
            and existing != entry.to_dict()
        ):
            # A sealed reservation already exists for this exact binding and it
            # is not byte-identical to the new one: refuse the overwrite so a
            # rewrite can never manufacture a matching record.
            raise LedgerError(
                f"authorization {entry.binding[:16]}… is already durably reserved by "
                "a different record; refusing to overwrite it"
            )
        entries[entry.binding] = entry.to_dict()
        self._write(entries)

    def consume(
        self,
        authorization: Authorization,
        *,
        operation_id: str,
        now: datetime,
        target_key: str | None = None,
    ) -> Consumption:
        """Durably spend one exact authorization, or refuse.

        Raises :class:`LedgerError` when the same bound authorization was
        already consumed — including by an earlier, separate process invocation
        (replay across processes) or by a concurrent racer (the atomic
        write-then-verify ensures exactly one caller observes its own seal).
        """
        binding = authorization.binding()
        with self._exclusive():
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
                state=SEALED_STATE,
            )
            if entry.state != SEALED_STATE:  # defensive: frozen dataclass cannot drift
                raise LedgerError("consumption record lost its sealed state before reservation")
            self.record(entry)
            if not self.is_consumed(binding):  # verify the write really landed
                raise LedgerError("durable authorization consumption could not be verified")
            return entry

    def finalize(self, binding: str, *, outcome: str) -> None:
        """Record the observed outcome of the operation (best effort).

        The reservation is already durable: failing to annotate the outcome
        must never silently re-enable the authorization, so write failures are
        swallowed on purpose. An ambiguous or interrupted outcome is recorded
        verbatim (e.g. ``CONSUMED_NETWORK``) and never retried automatically.
        """
        entries = self._read()
        existing = entries.get(binding)
        if existing is None:
            return
        existing["state"] = f"CONSUMED_{outcome}"
        entries[binding] = existing
        try:
            self._write(entries)
        except OSError:
            # The reservation is already durable; failing to annotate it must
            # not silently re-enable the authorization.
            return

    # -- auditable receipt metadata -----------------------------------------
    def consumption_record(self, binding: str, *, operation_id: str) -> dict[str, object] | None:
        """Return the durable record of one operation, when present.

        This proves the caller *attempted* a durable reservation at a specific
        time. It is never promoted into evidence that the mutation succeeded,
        that absence was observed, or that resurrection is controlled.
        """
        entry = self._read().get(binding)
        if entry is None or entry.get("operation_id") != operation_id:
            return None
        return dict(entry)


__all__ = [
    "AuthorizationLedger",
    "Consumption",
    "LEDGER_SCHEMA",
    "LOCK_TIMEOUT_SECONDS",
    "LedgerError",
    "SEALED_STATE",
]
