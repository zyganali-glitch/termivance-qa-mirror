"""Spawn-safe multiprocessing workers for ledger concurrency tests.

These functions are executed in *real child processes* (Windows ``spawn``
re-imports this module), which is why they deliberately import nothing from
``conftest`` — only stdlib and ``termivance``.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any


def _rebuild_authorization(payload: dict[str, Any]) -> Any:
    """Reconstruct the byte-identical authorization the parent process built.

    Binding digests derive from the target, action, timestamps, nonce and use
    bound, all of which are provided deterministically — so every racing child
    computes the exact same authentication binding.
    """
    from termivance.authorization import Authorization
    from termivance.target import TargetIdentity

    issued = datetime.fromisoformat(payload["issued_at"])
    target = TargetIdentity.from_dict(payload["target"])
    return Authorization.issue(
        target,
        payload["action"],
        nonce=payload["nonce"],
        now=issued,
        ttl=timedelta(seconds=payload["ttl_seconds"]),
        max_uses=1,
    )


def consume_once(payload: dict[str, Any]) -> str:
    """Try to durably spend the shared authorization exactly once."""
    from termivance.ledger import AuthorizationLedger

    authorization = _rebuild_authorization(payload)
    ledger = AuthorizationLedger(payload["ledger"])
    try:
        ledger.consume(
            authorization,
            operation_id=payload["operation_id"],
            now=datetime.fromisoformat(payload["now"]),
        )
    except Exception as exc:  # noqa: BLE001 - the verdict string is what the test asserts on
        return f"REFUSED: {type(exc).__name__}"
    return "OK"


def finalize_then_read(payload: dict[str, Any]) -> list[str]:
    """Finalize a sealed reservation while readers hammer the ledger file.

    Exercises the interleaving the transaction contract must survive: a
    finalizing writer under the exclusive lock and repeated plain readers that
    must always observe a complete, digest-consistent file.
    """
    from termivance.ledger import AuthorizationLedger, LedgerError

    authorization = _rebuild_authorization(payload)
    ledger = AuthorizationLedger(payload["ledger"])
    ledger.consume(
        authorization,
        operation_id=payload["operation_id"],
        now=datetime.fromisoformat(payload["now"]),
    )
    observations: list[str] = []
    sleep_slot = 0.0
    while sleep_slot < 60:
        try:
            entry = ledger._read().get(authorization.binding())
            if entry is not None:
                observations.append(str(entry.get("state")))
        except LedgerError as exc:
            observations.append(f"ERROR:{exc}")
        time.sleep(0.012)
        sleep_slot += 1
    try:
        ledger.finalize(authorization.binding(), outcome="ACCEPTED")
        observations.append("FINALIZED")
    except LedgerError as exc:  # pragma: no cover - a finalized race must never fail
        observations.append(f"FINALIZE_ERROR:{exc}")
    return observations


def health_check_while_reserving(payload: dict[str, Any]) -> str:
    """Run the ledger's readiness/creation self-check while another process seals.

    The initializing health check must never race a concurrent reservation into
    an empty file; it must observe the other process's seal (or fail closed).
    """
    from termivance.ledger import AuthorizationLedger

    ledger = AuthorizationLedger(payload["ledger"])
    for _ in range(6):
        try:
            ledger.health_check()
        except Exception as exc:  # noqa: BLE001 - refusal is a legal outcome
            return f"HEALTH_REFUSED: {type(exc).__name__}"
        time.sleep(0.03)
    return "HEALTH_OK"


__all__ = ["consume_once", "finalize_then_read", "health_check_while_reserving"]
