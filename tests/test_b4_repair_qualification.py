"""Independent-QA consolidated repair qualification (material defects A1-A3).

Each test proves one refused path of the remaining trust surface after B4:

* **A1** — the one consistent ledger transaction contract: real child processes
  (``spawn``) racing reservations, initializations, finalizations and readers;
  interrupted writes; legacy and in-memory tamper attempts; one-way state
  transitions. A consumed or ambiguously executed authorization can never be
  re-enabled.
* **A2** — receipts cannot promote a merely reserved operation into an accepted
  mutation, cannot disagree with the durable ledger record on nonce, action,
  operation id, binding or target key, and cannot carry a fabricated
  pre-publication state without the execution-time marker body digest.
* **A3** — an executor controlling the executor-side files can never manufacture
  its own operator consent: author identity is bound to an independent operator
  trust policy (username **and** provider-issued user ID), to an allowlisted
  approval project, to policy freshness/revocation and to the operator-held
  HMAC key; approval binding content is matched by exact, unambiguous lines;
  the approval is re-verified against the provider immediately before dispatch.

Everything here is network-free (fake transports) except multiprocessing, which
runs only on local files. Nothing is ever promoted from ``NOT_RUN`` /
``NOT_OBSERVED`` / ``BLOCKED`` into a success state.
"""

from __future__ import annotations

import json
import multiprocessing
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from _ledger_race import consume_once, finalize_then_read
from conftest import FakeTransport, ScriptedTransport, live_responses, patch_served
from test_b4_security import (
    MUTATION_OK,
    _live_ledger,
    approval_client,
    approval_record,
    healthy_delivery,
)
from test_retirement import (
    APPROVAL_IID,
    APPROVAL_KEY,
    EXECUTOR_ACCOUNT,
    EXECUTOR_USER_ID,
    MARKER,
    NOW,
    OPERATOR,
    TARGET,
    URL,
    approval_signature,
    auth,
    live_retire,
    operator_trust,
    published,
)

from termivance.authorization import Authorization, AuthorizationError
from termivance.capsule import ReceiptValidationError, validate_mutation_receipt
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.ledger import SEALED_STATE, AuthorizationLedger, LedgerError
from termivance.retirement import preflight
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict


def _race_payload(tmp_path: Path, *, operation_id: str = "op-race") -> dict[str, object]:
    issued = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    return {
        "target": TARGET.to_dict(),
        "action": "unpublish_pages",
        "nonce": "op-race-nonce-1",
        "issued_at": issued.isoformat(),
        "ttl_seconds": 600,
        "ledger": str(tmp_path / "ledger.json"),
        "operation_id": operation_id,
        "now": issued.isoformat(),
    }


def _rebuilt_authorization(payload: dict[str, object]) -> Authorization:
    """The byte-identical authorization every racing child reconstructs."""
    return Authorization.issue(
        TargetIdentity.from_dict(dict(payload["target"])),
        str(payload["action"]),
        nonce=str(payload["nonce"]),
        now=datetime.fromisoformat(str(payload["issued_at"])),
        ttl=timedelta(seconds=int(payload["ttl_seconds"])),
    )


# -- A1: the one consistent ledger transaction contract -------------------------


def test_four_concurrent_processes_yield_exactly_one_acceptance(tmp_path):
    payload = _race_payload(tmp_path)
    context = multiprocessing.get_context("spawn")
    with context.Pool(processes=4) as pool:
        verdicts = pool.map(consume_once, [payload] * 4)
    assert verdicts.count("OK") == 1, verdicts
    assert verdicts.count("REFUSED: LedgerError") == 3, verdicts
    ledger = AuthorizationLedger(tmp_path / "ledger.json")
    entries = ledger._read()
    binding = _rebuilt_authorization(payload).binding()
    assert list(entries) == [binding]
    assert entries[binding]["state"] == SEALED_STATE
    assert entries[binding]["operation_id"] == payload["operation_id"]


def test_a_health_check_racing_a_reservation_can_never_erase_the_seal(tmp_path):
    payload = _race_payload(tmp_path)
    context = multiprocessing.get_context("spawn")
    process = context.Process(target=consume_once, args=(payload,))
    process.start()
    ledger = _live_ledger(tmp_path)
    attempts = 0
    while process.is_alive() and attempts < 200:
        try:
            ledger.health_check()  # may fail closed while the winner holds the lock
        except LedgerError:
            pass  # refusal while the lock is held is the designed conservative outcome
        attempts += 1
        time.sleep(0.01)
    process.join(timeout=30)
    assert process.exitcode == 0
    binding = _rebuilt_authorization(payload).binding()
    entry = ledger._read().get(binding)
    assert entry is not None, "a concurrent health check erased a sealed reservation"
    assert entry["state"] == SEALED_STATE


def test_a_finalizer_under_a_repeated_reader_never_tears_the_ledger(tmp_path):
    payload = _race_payload(tmp_path)
    context = multiprocessing.get_context("spawn")
    process = context.Process(target=finalize_then_read, args=(payload,))
    process.start()
    ledger = _live_ledger(tmp_path)
    seen: list[str] = []
    while process.is_alive() and len(seen) < 600:
        try:
            for entry in ledger._read().values():
                seen.append(str(entry.get("state")))
        except LedgerError as exc:
            # A transient unreadable ledger is a designed conservative refusal,
            # but it must never be ambiguous JSON (that would be a torn read).
            assert "unreadable" in str(exc), exc
        time.sleep(0.01)
    process.join(timeout=60)
    assert process.exitcode == 0
    binding = _rebuilt_authorization(payload).binding()
    final = ledger._read().get(binding)
    assert final is not None and final["state"] == "CONSUMED_ACCEPTED"
    validated: list[str] = []
    for entry in ledger._read().values():
        validated.append(str(entry.get("state")))
    assert validated == ["CONSUMED_ACCEPTED"]
    assert all(state in {SEALED_STATE, "CONSUMED_ACCEPTED"} for state in seen)


def test_ambiguous_finalization_keeps_the_first_durable_outcome(tmp_path):
    ledger = _live_ledger(tmp_path)
    authorization = auth()
    ledger.consume(authorization, operation_id="op-amb", now=NOW)
    ledger.finalize(authorization.binding(), outcome="NETWORK")
    ledger.finalize(authorization.binding(), outcome="ACCEPTED")  # the conflict
    ledger.finalize(authorization.binding(), outcome="ACCEPTED")  # idempotent repeat
    record = ledger._read()[authorization.binding()]
    assert record["state"] == "CONSUMED_NETWORK"
    assert record["outcome"] == "NETWORK"
    assert record["ambiguous_outcomes"] == ["ACCEPTED"]
    with pytest.raises(LedgerError):
        ledger.consume(authorization, operation_id="op-retry", now=NOW)


def test_finalizing_an_unknown_reservation_is_an_operational_error(tmp_path):
    ledger = _live_ledger(tmp_path)
    with pytest.raises(LedgerError):
        ledger.finalize("0" * 64, outcome="ACCEPTED")


def test_interrupted_write_debris_is_swept_and_the_ledger_survives(tmp_path):
    ledger = _live_ledger(tmp_path)
    ledger.health_check()
    debris = tmp_path / ".ledger-crashed.tmp"
    debris.write_text('{"torn": ', encoding="utf-8")
    ledger.health_check()
    assert not debris.exists(), "crash debris was not swept under the lock"
    assert ledger._read() == {}


def test_a_stale_in_memory_digest_cannot_be_written(tmp_path):
    ledger = _live_ledger(tmp_path)
    authorization = auth()
    ledger.consume(authorization, operation_id="op-stale", now=NOW)
    entries = ledger._read()
    entries[authorization.binding()]["state"] = "FORGED_STATE"
    with pytest.raises(LedgerError):
        ledger._write(entries)


def test_legacy_v1_ledger_without_digests_is_refused(tmp_path):
    ledger_path = tmp_path / "legacy.json"
    ledger_path.write_text(
        json.dumps({"schema": "termivance.authorization_ledger/v1", "consumed": {}}),
        encoding="utf-8",
    )
    ledger = AuthorizationLedger(ledger_path)
    with pytest.raises(LedgerError):
        ledger._read()
    with pytest.raises(LedgerError):
        ledger.health_check()


# -- A2: receipts cannot promote reservations or fabricate pre-states -----------


def test_a_merely_reserved_operation_cannot_be_promoted_by_a_saved_receipt(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch, operation_id="op-reserved-1")
    reserved_path = tmp_path / "reserved-ledger.json"
    reserved = AuthorizationLedger(reserved_path)
    reserved.health_check()
    reserved.consume(auth(), operation_id="op-reserved-1", now=NOW)
    with pytest.raises(ReceiptValidationError) as excinfo:
        validate_mutation_receipt(receipt.to_dict(), TARGET, ledger=reserved)
    assert "reserved" in str(excinfo.value)


def test_the_receipt_nonce_must_match_the_durable_record(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["authorization_record"]["nonce"] = "op-forged-nonce"
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_the_receipt_target_key_must_match_the_durable_record(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["authorization_record"]["target_key"] = TargetIdentity(
        99999999, "grp/other-pages", "GITLAB_PAGES_SITE"
    ).key_string()
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_a_pre_state_without_the_execution_time_marker_digest_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["eligibility"]["pre_state"].pop("marker_sha256")
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_a_non_hex_marker_digest_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["eligibility"]["pre_state"]["marker_sha256"] = "not-a-hex-digest"
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_a_receipt_with_a_swapped_binding_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["authorization_record"]["binding"] = "b" * 64
    data["authorization_binding"] = "b" * 64
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_an_older_v2_receipt_shape_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["schema"] = "termivance.retirement_receipt/v2"
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


# -- A3: an executor can never manufacture its own operator consent --------------


def _verify(record, authorization, *, trust=None, approval_key=APPROVAL_KEY):
    """Standard strict verification of a provider-read-back approval record."""
    from termivance.approval_source import verify_approval_source

    return verify_approval_source(
        approval_client(record),
        authorization,
        project_id=TARGET.project_id,
        issue_iid=APPROVAL_IID,
        trust=trust if trust is not None else operator_trust(),
        approval_key=approval_key,
        now=NOW,
    )


def test_an_executor_issued_self_approval_is_refused():
    authorization = auth()
    record = approval_record(authorization, author=EXECUTOR_ACCOUNT, user_id=EXECUTOR_USER_ID)
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(record, authorization)
    assert "trusted operator" in str(excinfo.value)


def test_a_spoofed_username_with_a_foreign_provider_id_is_refused():
    authorization = auth()
    record = approval_record(authorization, user_id=EXECUTOR_USER_ID)
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(record, authorization)
    assert "user ID" in str(excinfo.value)


def test_an_approval_signed_with_a_forged_key_is_refused():
    authorization = auth()
    forged = approval_signature(authorization, key="attacker-controlled-key")
    authorization.approval = replace(authorization.approval, signature=forged)
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(approval_record(authorization), authorization)
    assert "signature" in str(excinfo.value)


def test_a_verification_without_the_operator_held_key_never_becomes_a_mutation():
    authorization = auth()
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(approval_record(authorization), authorization, approval_key=None)
    assert "signature key" in str(excinfo.value)


def test_an_unsigned_approval_required_to_be_signed_is_refused():
    authorization = auth(signature=None)
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(approval_record(authorization), authorization)
    assert "signature" in str(excinfo.value)


def test_a_revoked_operator_cannot_approve_anymore():
    authorization = auth()
    trust = operator_trust(revoked=((OPERATOR, NOW - timedelta(seconds=1)),))
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(approval_record(authorization), authorization, trust=trust)
    assert "revoked" in str(excinfo.value)


def test_an_approval_beyond_the_policy_freshness_window_is_refused():
    authorization = auth()
    stale = approval_record(authorization, offset=-timedelta(hours=30))
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(stale, authorization)
    assert "stale" in str(excinfo.value)


def test_a_duplicated_binding_line_is_ambiguous_and_therefore_refused():
    authorization = auth()
    record = approval_record(authorization)
    record["description"] += f"\nnonce: {authorization.nonce}\n"
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(record, authorization)
    assert "ambiguous" in str(excinfo.value)


def test_an_edited_binding_digest_line_is_refused():
    authorization = auth()
    record = approval_record(authorization)
    record["description"] = record["description"].replace(authorization.binding(), "e" * 64)
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(record, authorization)
    assert "exactly as required" in str(excinfo.value)


def test_an_approval_issue_in_an_unallowlisted_project_is_refused():
    authorization = auth()
    trust = operator_trust(approval_projects=(999_000_79,))
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(approval_record(authorization), authorization, trust=trust)
    assert "approval project" in str(excinfo.value)


def test_an_issue_without_a_provider_issued_author_id_is_refused():
    authorization = auth()
    record = approval_record(authorization)
    record["author"].pop("id")
    with pytest.raises(AuthorizationError) as excinfo:
        _verify(record, authorization)
    assert "user ID" in str(excinfo.value)


def test_malformed_or_degenerate_trust_policy_files_are_refused(tmp_path):
    from termivance.approval_source import TrustPolicyError, load_operator_trust

    no_operators = tmp_path / "no-operators.json"
    no_operators.write_text(
        json.dumps(
            {
                "schema": "termivance.operator_trust/v1",
                "trusted_operators": [],
                "approval_project_ids": [12345678],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(TrustPolicyError):
        load_operator_trust(no_operators)

    wrong_schema = tmp_path / "wrong-schema.json"
    wrong_schema.write_text(json.dumps({"schema": "untrusted/v0"}), encoding="utf-8")
    with pytest.raises(TrustPolicyError):
        load_operator_trust(wrong_schema)

    bad_id = tmp_path / "bad-id.json"
    bad_id.write_text(
        json.dumps(
            {
                "schema": "termivance.operator_trust/v1",
                "trusted_operators": [{"username": OPERATOR, "user_id": -1}],
                "approval_project_ids": [12345678],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(TrustPolicyError):
        load_operator_trust(bad_id)

    unreadable = tmp_path / "unreadable.json"
    unreadable.write_text("{ not json", encoding="utf-8")
    with pytest.raises(TrustPolicyError):
        load_operator_trust(unreadable)


def test_a_real_mutation_without_a_trust_policy_is_refused_at_preflight(tmp_path):
    pre = preflight(
        TARGET,
        allow_policy_fixture(),
        auth(),
        ledger=_live_ledger(tmp_path),
        mutation_intent=True,
        approval_client=GitLabClient("t", transport=FakeTransport({})),
        approval_project_id=TARGET.project_id,
        approval_issue_iid=APPROVAL_IID,
        now=NOW,
    )
    checks = {c["check"]: c for c in pre.checks}
    assert checks["operator_trust_policy_verified"]["ok"] is False
    assert pre.ok is False


def allow_policy_fixture():
    from test_retirement import allow_policy

    return allow_policy()


# -- dispatch-time re-verification (consent must still hold at execution time) ---


def test_dispatch_reverification_refuses_an_issue_closed_in_the_meantime(tmp_path, monkeypatch):
    patch_served(
        monkeypatch, [(200, f"<html>{MARKER}</html>"), (200, f"<html>{MARKER}</html>"), (404, "")]
    )
    del_transport = FakeTransport(MUTATION_OK)
    open_record = approval_record(auth())
    closed_record = dict(open_record)
    closed_record["state"] = "closed"
    transport = ScriptedTransport(
        live_responses(TARGET, pages_url=URL),
        scripted={
            "/pages": [published(), published(), published()],
            f"issues/{APPROVAL_IID}": [
                HttpReply(200, json.dumps(open_record)),
                HttpReply(200, json.dumps(closed_record)),
            ],
        },
    )
    read_client = GitLabClient("t", transport=transport)
    receipt = live_retire(
        auth(),
        read_client=read_client,
        mutation_transport=del_transport,
        ledger_path=tmp_path / "ledger.json",
    )
    assert del_transport.calls == [], "a revoked-in-flight approval must stop the dispatch"
    assert receipt.verdict == Verdict.BLOCKED
    assert receipt.mutation_attempted is False
    assert any("re-verification" in note for note in receipt.notes)
    # Conservative burn: the reservation was sealed, then the dispatch refused.
    reservation = AuthorizationLedger(tmp_path / "ledger.json")._read()
    assert any(entry.get("state") == SEALED_STATE for entry in reservation.values())
