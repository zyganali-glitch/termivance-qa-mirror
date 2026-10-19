"""B4 P0 adversarial security tests.

Each test proves one refused path of the three closed P0 defects:

* P0-A â€” no live mutation without a valid durable single-use ledger;
* P0-B â€” no real mutation without a GitLab-authenticated operator approval
  record (provider read-back, exact identity, binding);
* P0-C â€” no ``OBSERVED_ABSENT`` receipt-forgery: claims must be bound to the
  validated mutation receipt and its durable ledger seal.

Everything here is network-free (fake transports); nothing is ever promoted
from ``NOT_RUN``/``NOT_OBSERVED``/``BLOCKED`` into a success state.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from conftest import FakeTransport, ScriptedTransport, live_responses, patch_served
from test_retirement import (
    APPROVAL_IID,
    APPROVAL_KEY,
    MARKER,
    NOW,
    OPERATOR,
    OPERATOR_USER_ID,
    TARGET,
    URL,
    allow_policy,
    approval_issue_reply,
    auth,
    control,
    live_retire,
    operator_trust,
    published,
    scripted_client,
    with_approval,
)

from termivance.authorization import AuthorizationError
from termivance.capsule import ReceiptValidationError, validate_mutation_receipt
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.ledger import SEALED_STATE, AuthorizationLedger, LedgerError
from termivance.pages import PagesMutationClient
from termivance.retirement import preflight, retire_pages
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

MUTATION_OK = {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")}


def _live_ledger(tmp_path):
    return AuthorizationLedger(tmp_path / "ledger.json")


def healthy_delivery(tmp_path, monkeypatch, **kw):
    """A fraud-free baseline: one authorized, executed, durably-sealed mutation."""
    patch_served(
        monkeypatch,
        [
            (200, f"<html>{MARKER}</html>"),
            (200, f"<html>{MARKER}</html>"),
            (404, ""),
        ],
    )
    read_client = with_approval(scripted_client(pages_sequence=[published(), published()]), auth())
    return live_retire(
        auth(),
        read_client=read_client,
        mutation_transport=FakeTransport(MUTATION_OK),
        ledger_path=tmp_path / "ledger.json",
        **kw,
    )


# -- P0-A: the durable ledger is mandatory on the live path ----------------------


def test_live_mutation_without_ledger_is_refused():
    read_client = with_approval(scripted_client(pages_sequence=[published(), published()]), auth())
    del_transport = FakeTransport(MUTATION_OK)
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport),
        read_client=read_client,
        served_url=URL,
        marker=MARKER,
        control_attestation=control(),
        approval_key=None,
        approval_project_id=TARGET.project_id,
        approval_issue_iid=APPROVAL_IID,
        now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    assert receipt.mutation_attempted is False
    assert del_transport.calls == []
    failed = [str(c["detail"]) for c in receipt.preflight.checks if not c["ok"]]
    assert any("durable" in d.lower() for d in failed)


def test_live_mutation_with_nondurable_ledger_is_refused():
    for bad_path in ("NUL", "-"):
        ledger = AuthorizationLedger(bad_path)
        pre = preflight(
            TARGET, allow_policy(), auth(), ledger=ledger, mutation_intent=True, now=NOW
        )
        checks = {c["check"]: c for c in pre.checks}
        assert checks["durable_ledger_required"]["ok"] is False, bad_path
        assert "not durable" in checks["durable_ledger_required"]["detail"]


def test_live_mutation_refuses_malformed_ledger(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.json"
    ledger = AuthorizationLedger(ledger_path)
    ledger.health_check()  # fresh creation succeeds

    ledger_path.write_text("{ this is not json", encoding="utf-8")
    with pytest.raises(LedgerError):
        ledger.health_check()

    from termivance import absence as absence_mod
    from termivance import pages as pages_mod

    def refuse(*_a, **_k):  # the served-URL probe must never fire on a refused path
        raise AssertionError("served-URL probe ran although the mutation was refused")

    monkeypatch.setattr(absence_mod, "https_get", refuse)
    monkeypatch.setattr(pages_mod, "https_get", refuse)

    read_client = with_approval(scripted_client(pages_sequence=[published(), published()]), auth())
    del_transport = FakeTransport(MUTATION_OK)
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport),
        read_client=read_client,
        served_url=URL,
        marker=MARKER,
        control_attestation=control(),
        ledger=ledger,
        approval_key=None,
        approval_project_id=TARGET.project_id,
        approval_issue_iid=APPROVAL_IID,
        now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    assert receipt.mutation_attempted is False
    assert del_transport.calls == []
    failed = [str(c["detail"]) for c in receipt.preflight.checks if not c["ok"]]
    assert any("unreadable" in d.lower() for d in failed)


def test_concurrent_reservation_attempts_are_serialized(tmp_path, monkeypatch):
    ledger = AuthorizationLedger(tmp_path / "ledger.json")
    ledger.health_check()
    authorization = auth()
    lock = tmp_path / "ledger.json.lock"
    lock.write_text("999999", encoding="utf-8")  # another process holds the lock
    with pytest.raises(LedgerError) as exc:
        ledger.consume(authorization, operation_id="op-1", now=NOW)
    assert "lock" in str(exc.value)
    # The reservation never happened while the lock was held.
    assert ledger.is_consumed(authorization.binding()) is False
    lock.unlink()
    first = ledger.consume(authorization, operation_id="op-3", now=NOW)
    assert first.state == SEALED_STATE
    with pytest.raises(LedgerError):
        ledger.consume(authorization, operation_id="op-4", now=NOW)


def test_crash_after_reservation_burns_the_authorization(tmp_path, monkeypatch):
    """A process crash between reservation and mutation is conservative."""
    ledger = AuthorizationLedger(tmp_path / "ledger.json")
    ledger.health_check()
    authorization = auth()
    ledger.consume(authorization, operation_id="op-crash", now=NOW)
    # The crash loses the in-process state; a new process reloads and still
    # must not execute.
    with pytest.raises(LedgerError):
        ledger.consume(authorization, operation_id="op-again", now=NOW)
    record = next(iter(ledger._read().values()))
    assert record["operation_id"] == "op-crash"


def test_unknown_outcome_is_recorded_conservatively_never_retried(tmp_path, monkeypatch):
    ledger = AuthorizationLedger(tmp_path / "ledger.json")
    ledger.health_check()
    authorization = auth()
    ledger.consume(authorization, operation_id="op-unk", now=NOW)
    ledger.finalize(authorization.binding(), outcome="NETWORK")
    record = ledger._read()[authorization.binding()]
    assert record["state"] == "CONSUMED_NETWORK"
    with pytest.raises(LedgerError):
        ledger.consume(authorization, operation_id="op-retry", now=NOW)


def test_tampered_record_cannot_reenable_the_authorization(tmp_path, monkeypatch):
    ledger = AuthorizationLedger(tmp_path / "ledger.json")
    ledger.health_check()
    authorization = auth()
    ledger.consume(authorization, operation_id="op-tamper", now=NOW)
    binding = authorization.binding()
    data = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    data["consumed"][binding]["state"] = "CONSUMED_ACCEPTED"
    data["consumed"][binding]["operation_id"] = "op-forged"
    (tmp_path / "ledger.json").write_text(json.dumps(data), encoding="utf-8")
    # A locally edited record no longer "reads back": the integrity digest over
    # the recorded content no longer matches, so the whole ledger refuses to be
    # consumed as evidence (fail closed) instead of serving the forged state.
    with pytest.raises(LedgerError):
        ledger.consumption_record(binding, operation_id="op-forged")
    with pytest.raises(LedgerError):
        ledger._read()
    # And no path can re-enable it: consumption refuses because it cannot
    # honestly read the durable state either.
    with pytest.raises(LedgerError):
        ledger.consume(authorization, operation_id="op-reuse", now=NOW)


# -- P0-B: GitLab-authenticated approval provenance ------------------------------


def approval_client(record, *, project_id=None, iid=APPROVAL_IID):
    pid = project_id or TARGET.project_id
    endpoint = f"/projects/{pid}/issues/{iid}"
    return GitLabClient(
        "t", transport=FakeTransport({("GET", endpoint): HttpReply(200, json.dumps(record))})
    )


def approval_record(
    authorization,
    *,
    author: str = OPERATOR,
    user_id: int = OPERATOR_USER_ID,
    state: str = "opened",
    offset=None,
):
    record = json.loads(approval_issue_reply(authorization).body)
    if author != OPERATOR:
        record["author"]["username"] = author
    if user_id != OPERATOR_USER_ID:
        record["author"]["id"] = user_id
    if state != "opened":
        record["state"] = state
    if offset is not None:
        record["created_at"] = (NOW + offset).isoformat()
    return record


def test_approval_from_a_divergent_author_is_refused():
    from termivance.approval_source import verify_approval_source

    authorization = auth()
    client = approval_client(approval_record(authorization, author="model-impersonating-op"))
    with pytest.raises(AuthorizationError):
        verify_approval_source(
            client,
            authorization,
            project_id=TARGET.project_id,
            issue_iid=APPROVAL_IID,
            trust=operator_trust(),
            approval_key=APPROVAL_KEY,
            now=NOW,
        )


def test_tampered_approval_body_is_refused():
    from termivance.approval_source import verify_approval_source

    authorization = auth()
    record = approval_record(authorization)
    record["description"] = record["description"].replace(authorization.binding(), "0" * 64)
    with pytest.raises(AuthorizationError):
        verify_approval_source(
            approval_client(record),
            authorization,
            project_id=TARGET.project_id,
            issue_iid=APPROVAL_IID,
            trust=operator_trust(),
            approval_key=APPROVAL_KEY,
            now=NOW,
        )


def test_closed_approval_issue_is_refused():
    from termivance.approval_source import verify_approval_source

    authorization = auth()
    client = approval_client(approval_record(authorization, state="closed"))
    with pytest.raises(AuthorizationError):
        verify_approval_source(
            client,
            authorization,
            project_id=TARGET.project_id,
            issue_iid=APPROVAL_IID,
            trust=operator_trust(),
            approval_key=APPROVAL_KEY,
            now=NOW,
        )


def test_missing_approval_issue_is_refused():
    from termivance.approval_source import verify_approval_source

    authorization = auth()
    client = GitLabClient("t", transport=FakeTransport({}))
    with pytest.raises(AuthorizationError):
        verify_approval_source(
            client,
            authorization,
            project_id=TARGET.project_id,
            issue_iid=APPROVAL_IID,
            trust=operator_trust(),
            approval_key=APPROVAL_KEY,
            now=NOW,
        )


def test_live_mutation_without_approval_reference_is_refused(tmp_path, monkeypatch):
    pre = preflight(
        TARGET,
        allow_policy(),
        auth(),  # channel gitlab_issue, but no issue reference supplied
        ledger=_live_ledger(tmp_path),
        mutation_intent=True,
        now=NOW,
    )
    checks = {c["check"]: c for c in pre.checks}
    assert checks["gitlab_approval_record_verified"]["ok"] is False


def test_untrusted_channel_cannot_authorize_a_real_mutation(tmp_path, monkeypatch):
    stale = auth(channel="operator-channel")
    pre = preflight(
        TARGET,
        allow_policy(),
        stale,
        ledger=_live_ledger(tmp_path),
        mutation_intent=True,
        now=NOW,
    )
    checks = {c["check"]: c for c in pre.checks}
    assert checks["approval_provenance_gitlab"]["ok"] is False


def test_early_or_late_approval_window_is_refused():
    from termivance.approval_source import verify_approval_source

    authorization = auth()
    client = approval_client(approval_record(authorization, offset=-timedelta(hours=3)))
    with pytest.raises(AuthorizationError):
        verify_approval_source(
            client,
            authorization,
            project_id=TARGET.project_id,
            issue_iid=APPROVAL_IID,
            trust=operator_trust(),
            approval_key=APPROVAL_KEY,
            now=NOW,
        )
    late = auth()
    client_late = approval_client(approval_record(late, offset=timedelta(hours=2)))
    with pytest.raises(AuthorizationError):
        verify_approval_source(
            client_late,
            late,
            project_id=TARGET.project_id,
            issue_iid=APPROVAL_IID,
            trust=operator_trust(),
            approval_key=APPROVAL_KEY,
            now=NOW,
        )


# -- P0-C: forged receipts cannot bind absence claims ----------------------------


def test_valid_round_trip_of_a_real_receipt_binds(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    binding = validate_mutation_receipt(receipt.to_dict(), TARGET, ledger=_live_ledger(tmp_path))
    assert binding.accepted is True
    assert binding.durable is True


def test_receipt_for_a_different_operation_id_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["operation_id"] = "op-forged"
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_receipt_without_a_durable_record_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    fresh_ledger = AuthorizationLedger(tmp_path / "fresh-ledger.json")
    fresh_ledger.health_check()
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(receipt.to_dict(), TARGET, ledger=fresh_ledger)


def test_receipt_marking_a_refused_mutation_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["mutation"]["accepted"] = False
    data["mutation"]["status"] = 403
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_receipt_with_swapped_target_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    other = TargetIdentity(99999999, "grp/other-pages", "GITLAB_PAGES_SITE")
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(receipt.to_dict(), other, ledger=_live_ledger(tmp_path))


def test_receipt_with_swapped_endpoint_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["mutation"]["endpoint"] = f"/projects/{TARGET.project_id}/repository"
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_receipt_with_incoherent_pre_state_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["eligibility"]["pre_state"]["marker_observed"] = False
    data["eligibility"]["pre_state"]["deployment_present"] = False
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_receipt_with_temporal_inversion_is_refused(tmp_path, monkeypatch):
    receipt = healthy_delivery(tmp_path, monkeypatch)
    data = receipt.to_dict()
    data["mutation"]["requested_at"] = (NOW - timedelta(hours=2)).isoformat()
    with pytest.raises(ReceiptValidationError):
        validate_mutation_receipt(data, TARGET, ledger=_live_ledger(tmp_path))


def test_stale_observation_cannot_be_promoted(tmp_path, monkeypatch):
    """Freshness: a valid receipt cannot award absence outside its interval."""
    from termivance.evidence import PagesObservation, bounded_absence

    receipt = healthy_delivery(tmp_path, monkeypatch)
    binding = validate_mutation_receipt(receipt.to_dict(), TARGET, ledger=_live_ledger(tmp_path))
    stale_time = NOW - timedelta(hours=24)
    observation = PagesObservation(
        target=TARGET,
        observed_scope=frozenset({"pages_api", "served_url"}),
        observation_time_utc=stale_time,
        source="stale",
        api_status=404,
        served_url=URL,
        http_status=404,
        fresh_until=stale_time + timedelta(seconds=900),
        pre_state=binding.pre_state,
        action_accepted=True,
    )
    assert bounded_absence(observation, NOW) == Verdict.INCONCLUSIVE


# -- read-only paths can never mutate --------------------------------------------


def test_read_only_discovery_dispatches_only_get():
    responses = live_responses(TARGET, pages_url=URL)
    transport = ScriptedTransport(
        responses, scripted={"/pages": [published(), published(), published(), published()]}
    )
    read_client = GitLabClient("t", transport=transport)
    from termivance.discovery import discover_live, graph_from_snapshot
    from termivance.engine import evaluate

    snapshot = discover_live(read_client, TARGET, now=NOW)
    decision = evaluate(
        graph_from_snapshot(snapshot), policy=allow_policy(), action="unpublish_pages", now=NOW
    )
    assert decision.verdict in {Verdict.INCONCLUSIVE, Verdict.BLOCKED}
    assert snapshot.records and transport.calls
    assert all(method.upper() == "GET" for method, _ in transport.calls)
