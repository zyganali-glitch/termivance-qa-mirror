"""Durable causal execution ledger for supervised continuations.

The in-memory duplicate detection previously used by
:func:`termivance.supervised_review.run_supervised_continuation` protected
nothing across processes, crashes or restarts. This module provides the same
one consistent transaction contract as :mod:`termivance.ledger`, applied to
*continuation executions* instead of authorization consumption:

* every mutating operation (``reserve``, ``finalize``, ``health_check``
  creation) runs under one exclusive cross-process lock;
* every entry carries a SHA-256 integrity digest over its canonical field
  content; an edited, torn or legacy entry is refused at read time (fail
  closed) rather than trusted — a corrupted ledger can never silently become
  a clean ledger;
* writes are atomic (:func:`os.replace` after ``fsync``), so a crash between
  reservation and finalization leaves a durable ``FIRST_STARTED`` record, never
  a lost or half-written one;
* state transitions are one-way and honest:

  - ``FIRST_STARTED`` is written *before* the review executes; it is a
    reservation, never a completed execution;
  - ``FIRST_STARTED`` may finalize to ``FIRST_COMPLETED`` (only when the
    executed review actually completed), ``PARTIAL`` or ``FAILED`` — and
    only from the execution that owns the reservation: ``finalize``
    verifies the reserved ``execution_id`` before any state transition, so
    a competing or stale execution (e.g. the original invocation after an
    explicit recovery transferred ownership) can never finalize another
    invocation's reservation;
  - ``FIRST_COMPLETED`` is never flipped by a competing finalization; a
    conflicting second outcome is appended to ``ambiguous_outcomes`` and the
    first durable state wins;
  - a duplicate invocation that finds ``FIRST_STARTED``/``PARTIAL``/``FAILED``
    does **not** become ``COMPLETED_IDEMPOTENT``: it fails closed with
    ``INCOMPLETE_PRIOR_EXECUTION`` and requires explicit, auditable recovery
    (``allow_recovery=True`` re-reserves under the same causal key and records
    the recovery attempt).

The digest layer is local tamper evidence, not cryptographic authentication:
provider provenance of a continuation remains the responsibility of the
preflight provider read-back chain in
:mod:`termivance.supervised_review`.
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

CONTINUATION_LEDGER_SCHEMA = "termivance.continuation_ledger/v1"

#: Written before the review executes. A crash after this point leaves an
#: incomplete execution that requires auditable recovery.
RESERVED_STATE = "FIRST_STARTED"
#: The only state that proves a unique first *completed* execution.
COMPLETED_STATE = "FIRST_COMPLETED"
#: Terminal states for executions that did not complete.
PARTIAL_STATE = "PARTIAL"
FAILED_STATE = "FAILED"

#: Outcomes of :meth:`ContinuationLedger.reserve`.
RESERVE_FIRST_EXECUTION = "FIRST_EXECUTION"
RESERVE_DUPLICATE_COMPLETED = "DUPLICATE_OF_COMPLETED"
RESERVE_INCOMPLETE_PRIOR = "INCOMPLETE_PRIOR_EXECUTION"

LOCK_TIMEOUT_SECONDS = 10.0
_READ_RETRIES = 5

_NON_DURABLE_PATHS: frozenset[str] = frozenset(
    {"", "-", "nul", "nul:", "/dev/null", "/dev/zero", "$null"}
)


class ContinuationLedgerError(RuntimeError):
    """Raised when the causal execution ledger cannot be trusted or written."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def entry_digest(entry: dict[str, object]) -> str:
    """The SHA-256 integrity digest over an entry *without* its digest field."""
    content = {k: v for k, v in entry.items() if k != "digest"}
    return hashlib.sha256(_canonical(content).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ReserveOutcome:
    """Result of one reservation attempt against the durable ledger."""

    outcome: str  # FIRST_EXECUTION | DUPLICATE_OF_COMPLETED | INCOMPLETE_PRIOR_EXECUTION
    record: dict[str, object] | None = None
    detail: str = ""


class ContinuationLedger:
    """A durable record of continuation executions keyed by exact causal identity."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    # -- durability classification ----------------------------------------
    def path_is_durable(self) -> bool:
        try:
            raw = str(self.path).strip()
        except Exception:  # noqa: BLE001
            return False
        if raw.lower() in _NON_DURABLE_PATHS:
            return False
        lowered = raw.lower().rstrip("/\\")
        if lowered.startswith("/dev/") or lowered.startswith("\\\\.\\"):
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
                    raise ContinuationLedgerError(
                        f"continuation ledger at {self.path} could not be read "
                        "(another process may be replacing the file)"
                    ) from None
                time.sleep(0.02)
            except (OSError, json.JSONDecodeError) as exc:
                raise ContinuationLedgerError(
                    f"continuation ledger at {self.path} is unreadable or corrupted; "
                    f"refusing to treat it as a clean ledger: {exc}"
                ) from exc
        if not isinstance(data, dict):
            raise ContinuationLedgerError(
                f"continuation ledger at {self.path} is malformed"
            )
        schema = str(data.get("schema") or "")
        if schema != CONTINUATION_LEDGER_SCHEMA:
            raise ContinuationLedgerError(
                f"continuation ledger at {self.path} reports unknown schema {schema!r}; "
                "a legacy or foreign execution store cannot back durable idempotency"
            )
        entries = data.get("executions")
        if entries is None:
            return {}
        if not isinstance(entries, dict):
            raise ContinuationLedgerError(
                f"continuation ledger at {self.path} has invalid entries"
            )
        result: dict[str, dict[str, object]] = {}
        for key, value in entries.items():
            if not isinstance(value, dict) or not bool(value.get("digest")):
                raise ContinuationLedgerError(
                    f"continuation ledger entry {key!r} at {self.path} is malformed "
                    "or lacks an integrity digest; refusing to guess"
                )
            expected = str(value["digest"])
            computed = entry_digest(dict(value))
            if computed != expected:
                raise ContinuationLedgerError(
                    f"continuation ledger entry {key!r} at {self.path} failed its "
                    "integrity digest; the record was altered or is not authentic"
                )
            result[str(key)] = dict(value)
        return result

    def _atomic_write(self, payload: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        directory = str(self.path.parent)
        fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=".contledger-", suffix=".tmp")
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
        prepared: dict[str, dict[str, object]] = {}
        for key, entry in entries.items():
            verified = dict(entry)
            expected = verified.get("digest")
            if isinstance(expected, str):
                if expected != entry_digest(verified):
                    raise ContinuationLedgerError(
                        f"refusing to persist continuation entry {key!r}: its "
                        "integrity digest no longer matches the recorded content"
                    )
            else:
                verified["digest"] = entry_digest(verified)
            prepared[key] = verified
        try:
            self._atomic_write(
                {"schema": CONTINUATION_LEDGER_SCHEMA, "executions": prepared}
            )
        except OSError as exc:
            raise ContinuationLedgerError(
                f"could not durably write the continuation ledger at {self.path}: {exc}"
            ) from exc

    def _sweep_tmp_files(self) -> None:
        try:
            for candidate in self.path.parent.glob(".contledger-*.tmp"):
                candidate.unlink(missing_ok=True)
        except OSError:
            pass  # housekeeping is best effort

    @contextlib.contextmanager
    def _exclusive(self) -> Iterator[None]:
        """Serialize ledger mutations across processes (O_CREAT|O_EXCL sentinel)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = Path(str(self.path) + ".lock")
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                if time.monotonic() > deadline:
                    raise ContinuationLedgerError(
                        f"another termivance process holds the continuation ledger "
                        f"lock ({lock_path}); refusing to guess; remove the stale "
                        "lock file once no continuation is in flight"
                    ) from None
                time.sleep(0.05)
        try:
            os.write(fd, str(os.getpid()).encode("utf-8"))
            yield
        finally:
            os.close(fd)
            with contextlib.suppress(OSError):
                lock_path.unlink(missing_ok=True)

    # -- public transaction contract ----------------------------------------
    def health_check(self) -> None:
        """Verify the ledger is durable and readable before claiming idempotency.

        Raises :class:`ContinuationLedgerError` when the store cannot be
        trusted; the caller must treat any failure as "no durable ledger" and
        refuse to claim durable idempotency.
        """
        if not self.path_is_durable():
            raise ContinuationLedgerError(
                f"continuation ledger path {self.path!s} is not durable; a durable "
                "idempotency claim requires a persistent causal execution store"
            )
        try:
            with self._exclusive():
                self._sweep_tmp_files()
                if not self.path.is_file():
                    self._write({})
                    return
                self._read()
        except ContinuationLedgerError:
            raise
        except OSError as exc:
            raise ContinuationLedgerError(
                f"continuation ledger at {self.path} failed its durability "
                f"readiness check: {exc}"
            ) from exc

    def lookup(self, causal_key: str) -> dict[str, object] | None:
        """Return the integrity-verified record for one causal key, or None."""
        entry = self._read().get(causal_key)
        return dict(entry) if entry is not None else None

    def reserve(
        self,
        causal_key: str,
        *,
        execution_id: str,
        now: datetime,
        allow_recovery: bool = False,
    ) -> ReserveOutcome:
        """Durably reserve one causal execution before the review runs.

        * no prior record → writes ``FIRST_STARTED`` and returns
          ``FIRST_EXECUTION`` (this invocation owns the unique first attempt);
        * prior ``FIRST_COMPLETED`` → returns ``DUPLICATE_OF_COMPLETED`` with
          the stored record (its verdict is the authentic completed verdict);
        * prior ``FIRST_STARTED`` / ``PARTIAL`` / ``FAILED`` → returns
          ``INCOMPLETE_PRIOR_EXECUTION`` and *refuses* unless
          ``allow_recovery`` explicitly re-reserves (recording the recovery
          attempt in the entry history).
        """
        if not causal_key or not execution_id:
            raise ContinuationLedgerError(
                "a causal reservation requires a non-empty causal key and execution id"
            )
        with self._exclusive():
            self._sweep_tmp_files()
            records = self._read()
            existing = records.get(causal_key)
            if existing is not None:
                state = str(existing.get("state") or "")
                if state == COMPLETED_STATE:
                    return ReserveOutcome(
                        outcome=RESERVE_DUPLICATE_COMPLETED,
                        record=dict(existing),
                        detail=(
                            "a first completed execution is durably recorded for "
                            "this exact causal identity"
                        ),
                    )
                if state in (RESERVED_STATE, PARTIAL_STATE, FAILED_STATE):
                    if not allow_recovery:
                        return ReserveOutcome(
                            outcome=RESERVE_INCOMPLETE_PRIOR,
                            record=dict(existing),
                            detail=(
                                f"the prior execution for this causal identity is "
                                f"{state}, not {COMPLETED_STATE}; a duplicate attempt "
                                "cannot be presented as idempotent completion and "
                                "requires verified recovery"
                            ),
                        )
                    history = list(existing.get("recovery_attempts") or [])  # type: ignore[arg-type]
                    history.append(
                        {
                            "execution_id": execution_id,
                            "recovered_at": _as_utc(now).isoformat(),
                            "prior_state": state,
                        }
                    )
                    entry = dict(existing)
                    entry.pop("digest", None)
                    entry["state"] = RESERVED_STATE
                    entry["execution_id"] = execution_id
                    entry["reserved_at"] = _as_utc(now).isoformat()
                    entry["recovery_attempts"] = history
                    records[causal_key] = entry
                    self._write(records)
                    if causal_key not in self._read():
                        raise ContinuationLedgerError(
                            "durable continuation reservation could not be verified"
                        )
                    return ReserveOutcome(
                        outcome=RESERVE_FIRST_EXECUTION,
                        record=dict(entry),
                        detail=(
                            "re-reserved after explicit auditable recovery of an "
                            f"incomplete prior execution ({state})"
                        ),
                    )
                raise ContinuationLedgerError(
                    f"continuation ledger entry {causal_key!r} carries "
                    f"untransitional state {state!r}; refusing to reserve"
                )
            entry = {
                "causal_key": causal_key,
                "execution_id": execution_id,
                "state": RESERVED_STATE,
                "reserved_at": _as_utc(now).isoformat(),
            }
            records[causal_key] = entry
            self._write(records)
            if causal_key not in self._read():
                raise ContinuationLedgerError(
                    "durable continuation reservation could not be verified"
                )
            return ReserveOutcome(
                outcome=RESERVE_FIRST_EXECUTION,
                record=dict(entry),
                detail="reserved as the unique first execution for this causal identity",
            )

    def finalize(
        self,
        causal_key: str,
        *,
        execution_id: str,
        status: str,
        verdict: str,
        now: datetime,
    ) -> dict[str, object]:
        """Record the outcome of an already-reserved causal execution.

        Transition contract (one-way, race-safe, owner-bound):

        * the record must already exist — finalizing an unknown binding is an
          operational error, not a silent no-op;
        * only the execution that owns the reservation (its ``execution_id``
          matches the caller's) may transition it — a competing or stale
          execution (e.g. the original invocation attempting to finalize
          after an explicit recovery transferred ownership to the recovering
          invocation) is refused with ``EXECUTION_OWNER_MISMATCH``;
        * ``FIRST_STARTED`` may move to ``FIRST_COMPLETED`` (only for a
          genuinely completed review), ``PARTIAL`` or ``FAILED``;
        * ``FIRST_COMPLETED`` is never flipped; a conflicting second outcome is
          appended to ``ambiguous_outcomes`` (audit-only) and reported
          verbatim — the authoritative first verdict is never modified;
        * a write failure raises but never removes the reservation;
        * after writing, the durable recorded result and its integrity digest
          are verified by an independent read-back.
        """
        if not execution_id:
            raise ContinuationLedgerError(
                "finalizing a causal execution requires a non-empty execution id"
            )
        final_state = {
            "COMPLETED": COMPLETED_STATE,
            "COMPLETED_IDEMPOTENT": COMPLETED_STATE,
            "PARTIAL_REVIEW": PARTIAL_STATE,
            "FAILED": FAILED_STATE,
        }.get(status)
        if final_state is None:
            raise ContinuationLedgerError(
                f"unknown continuation status {status!r}; refusing to finalize"
            )
        with self._exclusive():
            self._sweep_tmp_files()
            records = self._read()
            existing = records.get(causal_key)
            if existing is None:
                raise ContinuationLedgerError(
                    f"cannot finalize unknown causal key {causal_key[:24]}…; "
                    "nothing durable was ever reserved for it"
                )
            state = str(existing.get("state") or "")
            if state == COMPLETED_STATE:
                first_status = str(existing.get("status") or "")
                first_verdict = str(existing.get("verdict") or "")
                if first_status != status or first_verdict != verdict:
                    # Audit-only record of a contradictory follow-up attempt:
                    # the authoritative first verdict is preserved verbatim.
                    ambiguous = list(existing.get("ambiguous_outcomes") or [])  # type: ignore[arg-type]
                    ambiguous.append(
                        {
                            "execution_id": execution_id,
                            "status": status,
                            "verdict": verdict,
                            "reported_at": _as_utc(now).isoformat(),
                        }
                    )
                    existing.pop("digest", None)
                    existing["ambiguous_outcomes"] = ambiguous
                    records[causal_key] = existing
                    self._write(records)
                return dict(existing)
            if state != RESERVED_STATE:
                raise ContinuationLedgerError(
                    f"continuation record for {causal_key[:24]}… carries "
                    f"untransitional state {state!r}; refusing to finalize it"
                )
            reserved_owner = str(existing.get("execution_id") or "")
            if reserved_owner != execution_id:
                raise ContinuationLedgerError(
                    f"EXECUTION_OWNER_MISMATCH: the causal record for "
                    f"{causal_key[:24]}… is reserved by execution "
                    f"{reserved_owner!r}; execution {execution_id!r} cannot "
                    "finalize another invocation's reservation (a stale "
                    "pre-recovery owner is refused after explicit recovery "
                    "transferred ownership)"
                )
            entry = dict(existing)
            entry.pop("digest", None)
            entry["state"] = final_state
            entry["status"] = status
            entry["verdict"] = verdict
            entry["completed_at"] = _as_utc(now).isoformat()
            records[causal_key] = entry
            self._write(records)
            # Independent read-back: verify the durable recorded result (and,
            # through _read, its integrity digest) after finalization.
            stored = self._read().get(causal_key)
            if (
                not isinstance(stored, dict)
                or str(stored.get("state")) != final_state
                or str(stored.get("execution_id")) != execution_id
                or str(stored.get("verdict")) != verdict
            ):
                raise ContinuationLedgerError(
                    "durable continuation finalization could not be verified "
                    "by read-back after writing"
                )
            return dict(stored)


__all__ = [
    "COMPLETED_STATE",
    "CONTINUATION_LEDGER_SCHEMA",
    "ContinuationLedger",
    "ContinuationLedgerError",
    "FAILED_STATE",
    "PARTIAL_STATE",
    "RESERVE_DUPLICATE_COMPLETED",
    "RESERVE_FIRST_EXECUTION",
    "RESERVE_INCOMPLETE_PRIOR",
    "RESERVED_STATE",
    "ReserveOutcome",
    "entry_digest",
]
