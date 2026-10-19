"""Durable, failure-safe single-use consumption ledger for authorization.

The in-memory ``uses`` counter on :class:`termivance.authorization.Authorization`
protects one process. It does nothing against the realistic failure modes this
module exists for:

* reloading the same authorization JSON file in a *new* CLI invocation and
  executing a second destructive operation;
* two processes attempting the same mutation concurrently;
* a crash between reservation and mutation.

The ledger is a small local JSON file governed by **one consistent transaction
contract**:

* *mutating or initializing* operations (``record``, ``consume``, ``finalize``,
  ``health_check`` creation) all run under the same exclusive cross-process
  lock; readers never take it and rely on atomic :func:`os.replace` to observe
  a complete previous-or-new file;
* every entry carries a SHA-256 *integrity digest* over its canonical field
  content; an edited, legacy or torn entry is refused at read time (fail
  closed) rather than trusted;
* state transitions are one-way: ``RESERVED_BEFORE_MUTATION`` can only become
  ``CONSUMED_<outcome>``; an already-finalized record is never flipped by a
  competing finalization — a conflicting second outcome is appended to the
  entry's ``ambiguous_outcomes`` and the first (durable) state wins;
* no existing consumption identity is ever silently overwritten, and a
  consumed or ambiguously executed authorization can never be re-enabled.

The digest layer detects accidental or inconsistent local edits; it is plain
local integrity, **not** cryptographically authenticated evidence — provider
provenance of a mutation stays the responsibility of the independent read-back
chain in :mod:`termivance.absence` / :mod:`termivance.approval_source`.

Since B4 the durable ledger is **mandatory** on the live ``retire_pages``
execution path (P0-A).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from termivance.authorization import Authorization

LEDGER_SCHEMA = "termivance.authorization_ledger/v2"
LEDGER_SCHEMA_LEGACY = "termivance.authorization_ledger/v1"

#: The only initial state a consumption record can ever carry. It is written
#: before the mutation is dispatched; a crash after this point burns the
#: authorization.
SEALED_STATE = "RESERVED_BEFORE_MUTATION"

#: Maximum time to wait for the ledger lock before refusing (conservative:
#: a stale lock from a crashed process must never be silently stolen).
LOCK_TIMEOUT_SECONDS = 10.0

#: Transient read retries when another process swaps the ledger file under us.
_READ_RETRIES = 5

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


def _canonical(value: Any) -> str:
    """Deterministic serialization for entry integrity digests."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def entry_digest(entry: dict[str, object]) -> str:
    """The SHA-256 integrity digest over an entry *without* its digest field."""
    content = {k: v for k, v in entry.items() if k != "digest"}
    return hashlib.sha256(_canonical(content).encode("utf-8")).hexdigest()


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
    outcome: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "binding": self.binding,
            "nonce": self.nonce,
            "action": self.action,
            "target_key": self.target_key,
            "operation_id": self.operation_id,
            "consumed_at": _as_utc(self.consumed_at).isoformat(),
            "state": self.state,
            "outcome": self.outcome,
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
        """Read and integrity-verify the ledger. Fails closed on anything odd."""
        data: object = None
        for attempt in range(_READ_RETRIES):
            try:
                if not self.path.is_file():
                    return {}
                data = json.loads(self.path.read_text(encoding="utf-8"))
                break
            except FileNotFoundError:
                return {}
            except PermissionError:
                if attempt == _READ_RETRIES - 1:
                    raise LedgerError(
                        f"authorization ledger at {self.path} could not be read "
                        "(another process may be replacing the file)"
                    ) from None
                time.sleep(0.02)
            except (OSError, json.JSONDecodeError) as exc:
                raise LedgerError(
                    f"authorization ledger at {self.path} is unreadable; refusing to guess: {exc}"
                ) from exc
        if not isinstance(data, dict):
            raise LedgerError(f"authorization ledger at {self.path} is malformed")
        schema = str(data.get("schema") or "")
        if schema == LEDGER_SCHEMA_LEGACY:
            raise LedgerError(
                f"authorization ledger at {self.path} uses the legacy v1 format "
                "without per-entry integrity digests; supply a fresh ledger path "
                "instead of trusting a legacy record"
            )
        if schema != LEDGER_SCHEMA:
            raise LedgerError(
                f"authorization ledger at {self.path} reports unknown schema {schema!r}"
            )
        entries = data.get("consumed")
        if entries is None:
            return {}
        if not isinstance(entries, dict):
            raise LedgerError(f"authorization ledger at {self.path} has invalid entries")
        result: dict[str, dict[str, object]] = {}
        for key, value in entries.items():
            if not isinstance(value, dict) or not bool(value.get("digest")):
                # A malformed or undigestable entry must never be silently
                # forgotten: it may be the only durable record that an
                # authorization was spent — or the fingerprint of tampering.
                raise LedgerError(
                    f"authorization ledger entry {key!r} at {self.path} is malformed "
                    "or lacks an integrity digest"
                )
            expected = str(value["digest"])
            computed = entry_digest(dict(value))
            if computed != expected:
                raise LedgerError(
                    f"authorization ledger entry {key!r} at {self.path} failed its "
                    "integrity digest; the record was altered or is not authentic"
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
        """Write entries, embedding per-entry integrity digests.

        Refuses to persist any entry whose recorded digest does not match its
        content (defense in depth against in-memory drift).
        """
        prepared: dict[str, dict[str, object]] = {}
        for key, entry in entries.items():
            verified = dict(entry)
            expected = verified.get("digest")
            if isinstance(expected, str):
                if expected != entry_digest(verified):
                    raise LedgerError(
                        f"refusing to persist ledger entry {key!r}: its integrity "
                        "digest no longer matches the recorded content"
                    )
            else:
                verified["digest"] = entry_digest(verified)
            prepared[key] = verified
        try:
            self._atomic_write({"schema": LEDGER_SCHEMA, "consumed": prepared})
        except OSError as exc:
            raise LedgerError(
                f"could not durably write the authorization ledger at {self.path}: {exc}"
            ) from exc

    def _sweep_tmp_files(self) -> None:
        """Housekeeping: remove abandoned temp files from interrupted writes.

        Called only while holding the lock, so a concurrent writer cannot have
        an in-flight temp file at this instant; leftover temp files can only
        be crash debris from a dead process.
        """
        try:
            for candidate in self.path.parent.glob(".ledger-*.tmp"):
                candidate.unlink(missing_ok=True)
        except OSError:
            pass  # housekeeping is best effort; durability never depends on it

    @contextlib.contextmanager
    def _exclusive(self) -> Iterator[None]:
        """Serialize ledger mutations and initialization across processes.

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
        a pre-existing one (prior consumption records are valid content). The
        creation branch re-checks existence **under the lock**, so an
        initializing health check racing a concurrent reservation observes the
        other process's entry instead of erasing it.
        Raises :class:`LedgerError` when the ledger cannot be trusted; the
        caller must treat any failure as "no durable ledger" and refuse the
        live mutation.
        """
        if not self.path_is_durable():
            raise LedgerError(
                f"authorization ledger path {self.path!s} is not durable; a real "
                "mutation requires a persistent single-use ledger"
            )
        try:
            with self._exclusive():
                self._sweep_tmp_files()  # crash debris from any earlier process
                if not self.path.is_file():
                    self._write({})
                    return
                self._read()
        except LedgerError:
            raise
        except OSError as exc:
            raise LedgerError(
                f"authorization ledger at {self.path} failed its durability readiness check: {exc}"
            ) from exc

    def is_consumed(self, binding: str) -> bool:
        return binding in self._read()

    def record(self, entry: Consumption) -> None:
        """Durably add one consumption record (takes the exclusive lock).

        A sealed record already present for this exact binding is never
        silently overwritten: the existing durable identity wins, and a
        different candidate is refused.
        """
        with self._exclusive():
            entries = self._read()
            existing = entries.get(entry.binding)
            if (
                existing is not None
                and existing != {**entry.to_dict(), "digest": existing.get("digest")}
                and existing != entry.to_dict()
            ):
                raise LedgerError(
                    f"authorization {entry.binding[:16]}… is already durably recorded by "
                    "a different entry; refusing to overwrite it"
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
        write-then-verify under the exclusive lock ensures exactly one caller
        observes its own seal).
        """
        binding = authorization.binding()
        with self._exclusive():
            self._sweep_tmp_files()
            records = self._read()
            if binding in records:
                raise LedgerError(
                    f"authorization {binding[:16]}… was already consumed; a reloaded "
                    "authorization file can never execute a second destructive operation"
                )
            entry = Consumption(
                binding=binding,
                nonce=authorization.nonce,
                action=authorization.action,
                target_key=target_key or authorization.target.key_string(),
                operation_id=operation_id,
                consumed_at=_as_utc(now),
                state=SEALED_STATE,
            )
            if entry.state != SEALED_STATE:  # defensive: frozen dataclass cannot drift
                raise LedgerError("consumption record lost its sealed state before reservation")
            records[binding] = entry.to_dict()
            self._write(records)
            if binding not in self._read():  # verify the write really landed
                raise LedgerError("durable authorization consumption could not be verified")
            return entry

    def finalize(self, binding: str, *, outcome: str) -> None:
        """Record the observed outcome of an already-sealed reservation.

        Transition contract (one-way, race-safe):

        * the record must already exist — finalizing an unknown binding is an
          operational error, not a silent no-op;
        * ``RESERVED_BEFORE_MUTATION`` may move to ``CONSUMED_<outcome>``;
        * an already-``CONSUMED_*`` record is never flipped: the durable state
          stays, and a *conflicting* second outcome is appended to
          ``ambiguous_outcomes`` and reported verbatim (e.g. an ACCEPTED
          report arriving after a NETWORK outcome is a genuine ambiguity);
        * a write failure raises, but never removes the reservation: the
          sealed state was already durable before this call.
        """
        with self._exclusive():
            entries = self._read()
            existing = entries.get(binding)
            if existing is None:
                raise LedgerError(
                    f"cannot finalize unknown authorization binding "
                    f"{binding[:16]}…; nothing durable was ever reserved for it"
                )
            state = str(existing.get("state") or "")
            if state == SEALED_STATE:
                if str(existing.get("outcome") or "") == str(outcome):
                    # Same outcome seen twice under the sealed state (a retried
                    # finalize racing the first one): make it durable once.
                    pass
                else:
                    existing.pop("digest", None)  # content changes; _write re-seals
                    existing["state"] = f"CONSUMED_{outcome}"
                    existing["outcome"] = str(outcome)
                    entries[binding] = existing
                    self._write(entries)
            elif state.startswith("CONSUMED_"):
                first = str(existing.get("outcome") or "")
                ambiguous = list(existing.get("ambiguous_outcomes") or [])  # type: ignore[arg-type]
                if str(outcome) not in {first, *ambiguous}:
                    existing.pop("digest", None)  # content changes; _write re-seals
                    ambiguous.append(str(outcome))
                    existing["ambiguous_outcomes"] = ambiguous
                    entries[binding] = existing
                    self._write(entries)
            else:
                raise LedgerError(
                    f"ledger record for {binding[:16]}… carries untransitional "
                    f"state {state!r}; refusing to finalize it"
                )

    # -- auditable receipt metadata -----------------------------------------
    def consumption_record(self, binding: str, *, operation_id: str) -> dict[str, object] | None:
        """Return the durable, integrity-verified record of one operation.

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
    "entry_digest",
]
