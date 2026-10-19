"""Tests for the deterministic, authorized retirement executor and preflight."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from conftest import (
    FakeTransport,
    ScriptedTransport,
    live_responses,
    make_snapshot,
    patch_served,
    project_payload,
)

from termivance.attestation import AttestationError, ControlAttestation, target_key_for
from termivance.authorization import (
    APPROVAL_KEY_ENV,
    Authorization,
    AuthorizationError,
    OperatorApproval,
    load_authorization,
)
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.ledger import AuthorizationLedger, LedgerError
from termivance.pages import PagesMutationClient
from termivance.policy import Policy
from termivance.retirement import preflight, retire_pages
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
TARGET = TargetIdentity(12345678, "grp/disposable-pages", "GITLAB_PAGES_SITE")
URL = "https://disposable-pages.pages.example/"
MARKER = "TERMIVANCE-B3-DISPOSABLE-MARKER"
ACTION = "unpublish_pages"
APPROVAL_IID = 77
OPERATOR = "termivance-operator"


def allow_policy() -> Policy:
    return Policy(
        schema_version=1,
        mode="OPERATOR_APPROVED",
        mutation_enabled=True,
        provider="GITLAB_PAGES",
        allowed_target_project_ids=(TARGET.project_id,),
        allowed_target_full_paths=(TARGET.full_path,),
        allowed_actions=(ACTION,),
        authorization_required=True,
    )


def example_policy() -> Policy:
    return Policy(
        schema_version=1,
        mode="EXAMPLE_ONLY_NOT_AUTHORIZATION",
        mutation_enabled=False,
        provider="GITLAB_PAGES",
        allowed_target_project_ids=(),
        allowed_target_full_paths=(),
        allowed_actions=(),
        authorization_required=True,
    )


def auth(
    *,
    ttl: timedelta = timedelta(minutes=10),
    max_uses: int = 1,
    target: TargetIdentity = TARGET,
    action: str = ACTION,
    now: datetime = NOW,
    approve: bool = True,
    signature: str | None = None,
    channel: str = "gitlab_issue",
) -> Authorization:
    authorization = Authorization.issue(
        target, action, nonce="op-approval-1", now=now, ttl=ttl, max_uses=max_uses
    )
    if approve:
        authorization.approval = OperatorApproval(
            operator=OPERATOR,
            statement=(
                f"I authorize exactly one {action} operation using "
                f"{authorization.exact_endpoint} for project {target.project_id}"
            ),
            approved_at=now,
            channel=channel,
            binding=authorization.binding(),
            signature=signature,
        )
    return authorization


def approval_issue_reply(authorization: Authorization, *, author=OPERATOR, state="opened"):
    """A scripted GitLab approval issue the provider read-back can verify."""
    body = (
        "Operator approval — Termivance retirement mutation\n"
        f"endpoint: {authorization.exact_endpoint}\n"
        f"action: {authorization.action}\n"
        f"target: {authorization.target.full_path} (project "
        f"{authorization.target.project_id}, kind "
        f"{authorization.target.resource_kind})\n"
        f"nonce: {authorization.nonce}\n"
        f"binding: {authorization.binding()}\n"
        "I authorize exactly one unpublish_pages operation as stated above."
    )
    return HttpReply(
        200,
        json.dumps(
            {
                "iid": APPROVAL_IID,
                "state": state,
                "created_at": (NOW - timedelta(seconds=30)).isoformat(),
                "author": {"username": author},
                "description": body,
            }
        ),
    )


def with_approval(client: GitLabClient, authorization: Authorization, **kw) -> GitLabClient:
    """Attach the operator approval issue to an existing read-only transport.

    The approval pair is inserted FIRST because FakeTransport matches by
    insertion order and the generic ``/issues`` fragment would otherwise win
    over the specific ``/issues/77`` one.
    """
    inner = client._transport
    approval_pair = (
        "GET",
        f"/projects/{TARGET.project_id}/issues/{APPROVAL_IID}",
    )
    reordered = {approval_pair: approval_issue_reply(authorization, **kw)}
    for key, value in inner.responses.items():  # type: ignore[attr-defined]
        if key != approval_pair:
            reordered[key] = value
    inner.responses = reordered
    return client


def live_retire(
    authorization, *, read_client, mutation_transport, ledger_path, **kw
):
    """Standard live-mutation invocation with the P0 gates wired in."""
    from termivance.ledger import AuthorizationLedger

    return retire_pages(
        TARGET,
        allow_policy(),
        authorization,
        mutation_client=PagesMutationClient("t", transport=mutation_transport),
        read_client=read_client,
        served_url=URL,
        marker=MARKER,
        control_attestation=control(),
        ledger=AuthorizationLedger(ledger_path),
        approval_key=None,
        approval_project_id=TARGET.project_id,
        approval_issue_iid=APPROVAL_IID,
        now=NOW,
        **kw,
    )


def control() -> ControlAttestation:
    return ControlAttestation(
        operator="termivance-operator",
        statement="no redeployment path remains for this disposable target",
        asserted_at=NOW,
        target_key=target_key_for(TARGET),
    )


def scripted_client(*, pages_sequence, **kw) -> GitLabClient:
    responses = live_responses(TARGET, pages_url=URL, **kw)
    return GitLabClient(
        "t", transport=ScriptedTransport(responses, scripted={"/pages": pages_sequence})
    )


def published() -> HttpReply:
    return HttpReply(200, json.dumps({"url": URL, "deployments": [{"id": 1}]}))


def gone() -> HttpReply:
    return HttpReply(404, "", "HTTP 404")


# -- preflight -----------------------------------------------------------------


def test_preflight_ok_with_valid_authorization():
    result = preflight(TARGET, allow_policy(), auth(), now=NOW)
    assert result.ok is True
    assert result.authorization_binding is not None
    checks = {c["check"]: c["ok"] for c in result.checks}
    assert checks["operator_approval_verified"] is True
    assert all(c["ok"] for c in result.checks)


def test_preflight_refuses_provenance_free_authorization():
    result = preflight(TARGET, allow_policy(), auth(approve=False), now=NOW)
    assert result.ok is False
    checks = {c["check"]: c["ok"] for c in result.checks}
    assert checks["operator_approval_verified"] is False


def test_preflight_refuses_protected_project():
    protected = TargetIdentity(87779099, "gitlab-ai-hackathon/x/termivance", "GITLAB_PAGES_SITE")
    result = preflight(protected, allow_policy(), None, now=NOW)
    assert result.ok is False
    checks = {c["check"]: c for c in result.checks}
    assert checks["target_not_protected"]["ok"] is False


def test_preflight_refuses_example_policy():
    result = preflight(TARGET, example_policy(), auth(), now=NOW)
    assert result.ok is False
    assert {c["check"]: c["ok"] for c in result.checks}["policy_permits"] is False


def test_preflight_refuses_missing_authorization():
    result = preflight(TARGET, allow_policy(), None, now=NOW)
    assert result.ok is False
    assert {c["check"]: c["ok"] for c in result.checks}["authorization_valid"] is False


def test_preflight_refuses_wrong_target_authorization():
    other = TargetIdentity(99999999, "grp/other", "GITLAB_PAGES_SITE")
    wrong = auth(target=other)
    result = preflight(TARGET, allow_policy(), wrong, now=NOW)
    assert result.ok is False


def test_preflight_refuses_expired_authorization():
    expired = auth(ttl=timedelta(minutes=1))
    result = preflight(TARGET, allow_policy(), expired, now=NOW + timedelta(hours=1))
    assert result.ok is False


def test_preflight_refuses_wrong_action():
    wrong = auth(action="delete_project")
    result = preflight(TARGET, allow_policy(), wrong, now=NOW)
    assert result.ok is False


# -- deterministic decision binding --------------------------------------------


def test_no_discovery_source_means_no_mutation():
    receipt = retire_pages(TARGET, allow_policy(), auth(), now=NOW)
    assert receipt.mutation_attempted is False
    assert receipt.verdict == Verdict.BLOCKED
    assert any("eligibility" in note for note in receipt.notes)


def test_dry_run_from_record_is_safe_to_retire():
    snapshot = make_snapshot(TARGET, operator_control=True)
    receipt = retire_pages(TARGET, allow_policy(), auth(), snapshot=snapshot, now=NOW)
    assert receipt.mutation_attempted is False
    assert receipt.verdict == Verdict.SAFE_TO_RETIRE
    assert receipt.eligibility is not None
    assert receipt.eligibility.decision.verdict == Verdict.SAFE_TO_RETIRE


def test_policy_and_authorization_cannot_override_inconclusive_graph():
    # Policy + authorization are valid, but the graph has no affirmative control.
    snapshot = make_snapshot(TARGET)
    receipt = retire_pages(TARGET, allow_policy(), auth(), snapshot=snapshot, now=NOW)
    assert receipt.verdict == Verdict.BLOCKED
    assert receipt.mutation_attempted is False


def test_never_published_target_cannot_be_safe_to_retire():
    snapshot = make_snapshot(TARGET, operator_control=True, published=False)
    receipt = retire_pages(TARGET, allow_policy(), auth(), snapshot=snapshot, now=NOW)
    assert receipt.verdict == Verdict.BLOCKED
    assert receipt.eligibility is not None
    kinds = {o["kind"]: o["status"] for o in receipt.eligibility.decision.obligations}
    assert kinds["PAGES_PUBLISHED"] == "VIOLATED"


def test_developer_only_permission_cannot_be_safe_to_retire():
    snapshot = make_snapshot(TARGET, operator_control=True, can_manage_pages=False)
    receipt = retire_pages(TARGET, allow_policy(), auth(), snapshot=snapshot, now=NOW)
    assert receipt.verdict == Verdict.BLOCKED
    kinds = {o["kind"]: o["status"] for o in receipt.eligibility.decision.obligations}  # type: ignore[union-attr]
    assert kinds["RETIREMENT_PERMISSION"] == "VIOLATED"


def test_blocked_decision_never_dispatches_delete():
    transport = FakeTransport(
        {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")}
    )
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        mutation_client=PagesMutationClient("t", transport=transport),
        snapshot=make_snapshot(TARGET),
        now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    assert transport.calls == []


# -- real transition -----------------------------------------------------------


def test_authorized_execute_awards_observed_absent_on_real_transition(tmp_path, monkeypatch):
    # publication (initial) + publication (revalidation) + absent read-back
    patch_served(
        monkeypatch, [(200, f"<html>{MARKER}</html>"), (200, f"<html>{MARKER}</html>"), (404, "")]
    )
    del_transport = FakeTransport(
        {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")}
    )
    read_client = with_approval(
        scripted_client(
            pages_sequence=[published(), published(), published(), published(), gone()]
        ),
        auth(),
    )
    receipt = live_retire(
        auth(),
        read_client=read_client,
        mutation_transport=del_transport,
        ledger_path=tmp_path / "ledger.json",
    )
    assert del_transport.calls and del_transport.calls[0][0] == "DELETE"
    assert receipt.mutation is not None and receipt.mutation.accepted
    assert receipt.verdict == Verdict.OBSERVED_ABSENT
    assert receipt.eligibility is not None and receipt.revalidation is not None


def test_two_unrelated_404s_do_not_prove_absence(monkeypatch):
    """Both channels 404, but the site was never proven published: no DELETE."""
    patch_served(monkeypatch, [(404, ""), (404, "")])
    del_transport = FakeTransport(
        {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")}
    )
    read_client = scripted_client(pages_sequence=[published(), gone()])
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport),
        read_client=read_client,
        served_url=URL,
        marker=MARKER,
        control_attestation=control(),
        now=NOW,
    )
    # Publication could not be proven (marker never served) => not safe => no DELETE.
    assert receipt.verdict == Verdict.BLOCKED
    assert receipt.verdict != Verdict.OBSERVED_ABSENT
    assert del_transport.calls == []


def test_never_published_target_never_retires(monkeypatch):
    """The Pages API reports zero deployments: publication is not established."""
    patch_served(monkeypatch, [(200, f"<html>{MARKER}</html>"), (200, f"<html>{MARKER}</html>")])
    del_transport = FakeTransport(
        {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")}
    )
    read_client = scripted_client(
        pages_sequence=[HttpReply(200, json.dumps({"url": URL, "deployments": []}))],
        deployments=0,
    )
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport),
        read_client=read_client,
        served_url=URL,
        marker=MARKER,
        control_attestation=control(),
        now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    assert del_transport.calls == []


def test_mutation_403_is_inconclusive_not_absent(tmp_path, monkeypatch):
    patch_served(
        monkeypatch,
        [(200, f"<html>{MARKER}</html>"), (200, f"<html>{MARKER}</html>"), (404, "")],
    )
    del_transport = FakeTransport(
        {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(403, "", "403")}
    )
    read_client = with_approval(
        scripted_client(
            pages_sequence=[published(), published(), published(), published(), gone()]
        ),
        auth(),
    )
    receipt = live_retire(
        auth(),
        read_client=read_client,
        mutation_transport=del_transport,
        ledger_path=tmp_path / "ledger.json",
    )
    assert receipt.mutation is not None and receipt.mutation.accepted is False
    assert receipt.verdict == Verdict.INCONCLUSIVE


def test_successful_api_action_without_verified_absence_is_inconclusive(tmp_path, monkeypatch):
    """A 204 DELETE plus an unusable served-URL read-back proves no absence."""
    patch_served(
        monkeypatch,
        [
            (200, f"<html>{MARKER}</html>"),
            (200, f"<html>{MARKER}</html>"),
            (None, ""),
        ],
    )
    del_transport = FakeTransport(
        {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")}
    )
    read_client = with_approval(
        scripted_client(
            pages_sequence=[published(), published(), published(), published(), gone()]
        ),
        auth(),
    )
    receipt = live_retire(
        auth(),
        read_client=read_client,
        mutation_transport=del_transport,
        ledger_path=tmp_path / "ledger.json",
    )
    assert receipt.mutation is not None and receipt.mutation.accepted
    assert receipt.verdict == Verdict.INCONCLUSIVE
    assert receipt.verdict != Verdict.OBSERVED_ABSENT


def test_reappearance_after_unpublish_is_blocked(monkeypatch):
    patch_served(
        monkeypatch,
        [
            (200, f"<html>{MARKER}</html>"),
            (200, f"<html>{MARKER}</html>"),
            (200, f"<html>{MARKER}</html>"),
        ],
    )
    del_transport = FakeTransport(
        {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")}
    )
    read_client = scripted_client(
        pages_sequence=[published(), published(), published(), published(), published()]
    )
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport),
        read_client=read_client,
        served_url=URL,
        marker=MARKER,
        control_attestation=control(),
        now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    assert receipt.verdict != Verdict.OBSERVED_ABSENT


def test_authorized_target_with_missing_provider_observation_is_blocked():
    """Valid policy + valid authorization, but the provider identity is absent."""
    read_client = GitLabClient("t", transport=FakeTransport({}))
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        read_client=read_client,
        served_url=URL,
        marker=MARKER,
        control_attestation=control(),
        now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    assert receipt.mutation_attempted is False
    kinds = {o["kind"]: o["status"] for o in receipt.eligibility.decision.obligations}  # type: ignore[union-attr]
    assert kinds["PROVIDER_OBSERVATION"] == "UNKNOWN"


def test_target_drift_during_revalidation_blocks_mutation(monkeypatch):
    """The project changes between eligibility and execution: refuse."""
    patch_served(
        monkeypatch,
        [(200, f"<html>{MARKER}</html>"), (200, f"<html>{MARKER}</html>")],
    )
    drifted = json.loads(json.dumps(project_payload(TARGET)))
    drifted["path_with_namespace"] = "grp/somewhere-else"
    responses = live_responses(TARGET, pages_url=URL)
    transport = ScriptedTransport(
        responses,
        scripted={
            "/pages": [published(), published(), published(), published()],
            f"/projects/{TARGET.project_id}": [
                HttpReply(200, json.dumps(project_payload(TARGET))),
                HttpReply(200, json.dumps(project_payload(TARGET))),
                HttpReply(200, json.dumps(drifted)),
            ],
        },
    )
    del_transport = FakeTransport(
        {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")}
    )
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport),
        read_client=GitLabClient("t", transport=transport),
        served_url=URL,
        marker=MARKER,
        control_attestation=control(),
        now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    assert del_transport.calls == []


def test_receipt_serialization_includes_boundaries(tmp_path, monkeypatch):
    patch_served(
        monkeypatch,
        [(200, f"<html>{MARKER}</html>"), (200, f"<html>{MARKER}</html>"), (404, "")],
    )
    del_transport = FakeTransport(
        {("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")}
    )
    read_client = with_approval(
        scripted_client(
            pages_sequence=[published(), published(), published(), published(), gone()]
        ),
        auth(),
    )
    receipt = live_retire(
        auth(),
        read_client=read_client,
        mutation_transport=del_transport,
        ledger_path=tmp_path / "ledger.json",
    )
    data = receipt.to_dict()
    assert data["schema"] == "termivance.retirement_receipt/v2"
    assert "not proof of absence" in data["note"]
    assert data["eligibility"]["snapshot_digest"]
    assert data["revalidation"]["snapshot_digest"]


# -- durable single use --------------------------------------------------------


def test_authorization_cannot_be_reused_across_cli_invocations(tmp_path, monkeypatch):
    path = tmp_path / "auth.json"
    authorization = auth()
    path.write_text(json.dumps(authorization.to_dict()), encoding="utf-8")
    patch_served(
        monkeypatch,
        [
            (200, f"<html>{MARKER}</html>"),
            (200, f"<html>{MARKER}</html>"),
            (404, ""),
            (200, f"<html>{MARKER}</html>"),
            (200, f"<html>{MARKER}</html>"),
        ],
    )

    first = FakeTransport({("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")})
    read_client = with_approval(
        scripted_client(
            pages_sequence=[published(), published(), published(), published(), gone()]
        ),
        authorization,
    )
    receipt = live_retire(
        load_authorization(path),
        read_client=read_client,
        mutation_transport=first,
        ledger_path=tmp_path / "ledger.json",
    )
    assert receipt.mutation_attempted is True
    assert len(first.calls) == 1

    # A *separate* invocation reloading the same JSON file must be refused — and
    # the refusal must come from the durable ledger, after provenance checks.
    second = FakeTransport({("DELETE", f"/projects/{TARGET.project_id}/pages"): HttpReply(204, "")})
    replay_client = with_approval(
        scripted_client(pages_sequence=[published(), published()]), authorization
    )
    again = live_retire(
        load_authorization(path),
        read_client=replay_client,
        mutation_transport=second,
        ledger_path=tmp_path / "ledger.json",
    )
    assert again.verdict == Verdict.BLOCKED
    assert second.calls == []
    assert any("already consumed" in note for note in again.notes)


def test_ledger_refuses_direct_double_consumption(tmp_path):
    ledger = AuthorizationLedger(tmp_path / "ledger.json")
    authorization = auth()
    ledger.consume(authorization, operation_id="op-1", now=NOW)
    with pytest.raises(LedgerError):
        ledger.consume(authorization, operation_id="op-2", now=NOW)


# -- fabricated / untrusted authorization --------------------------------------


def test_authorization_json_without_provenance_is_refused(tmp_path):
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(auth().to_dict()), encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["operator_approval"] = None
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuthorizationError):
        load_authorization(path)


def test_approval_bound_to_a_different_authorization_is_refused(tmp_path):
    path = tmp_path / "auth.json"
    data = auth().to_dict()
    data["operator_approval"]["binding"] = "0" * 64  # type: ignore[index]
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuthorizationError):
        load_authorization(path)


def test_approval_statement_must_reference_the_exact_endpoint(tmp_path):
    path = tmp_path / "auth.json"
    authorization = auth()
    authorization.approval = OperatorApproval(
        operator="termivance-operator",
        statement="please retire something",
        approved_at=NOW,
        channel="operator-channel",
        binding=authorization.binding(),
    )
    path.write_text(json.dumps(authorization.to_dict()), encoding="utf-8")
    with pytest.raises(AuthorizationError):
        load_authorization(path)


def test_signature_required_when_key_is_configured(tmp_path):
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(auth().to_dict()), encoding="utf-8")
    with pytest.raises(AuthorizationError):
        load_authorization(path, approval_key="operator-held-key")


def test_control_attestation_target_mismatch_is_refused():
    other = TargetIdentity(99999999, "grp/other", "GITLAB_PAGES_SITE")
    with pytest.raises(AttestationError):
        control().verify(other)


def test_control_attestation_is_required_for_redeployment_control():
    # No attestation and no active mechanism: still not SAFE (no negative inference).
    read_client = GitLabClient(
        "t", transport=ScriptedTransport(live_responses(TARGET, pages_url=URL))
    )
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        read_client=read_client,
        served_url=URL,
        marker=MARKER,
        snapshot=None,
        now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    kinds = {o["kind"]: o["status"] for o in receipt.eligibility.decision.obligations}  # type: ignore[union-attr]
    assert kinds["REDEPLOYMENT_PATH"] == "UNKNOWN"


def test_authorization_from_prose_always_refused():
    with pytest.raises(AuthorizationError):
        Authorization.from_prose("operator said yes")


def test_approval_key_env_name_is_stable():
    assert APPROVAL_KEY_ENV == "TERMIVANCE_APPROVAL_HMAC_KEY"


def test_missing_authorization_file_fails_closed(tmp_path):
    with pytest.raises(AuthorizationError):
        load_authorization(tmp_path / "absent.json")
