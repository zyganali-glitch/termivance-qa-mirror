"""Tests for the deterministic, authorized retirement executor and preflight."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from conftest import FakeTransport

from termivance import absence as absence_mod
from termivance.authorization import (
    Authorization,
    AuthorizationError,
    load_authorization,
)
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.pages import PagesMutationClient
from termivance.policy import Policy
from termivance.retirement import preflight, retire_pages
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
TARGET = TargetIdentity(12345678, "grp/disposable-pages", "GITLAB_PAGES_SITE")
URL = "https://grp.gitlab.io/disposable-pages/"
ACTION = "unpublish_pages"


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


def auth(ttl=timedelta(minutes=10), max_uses=1):
    return Authorization.issue(TARGET, ACTION, nonce="op-approval-1", now=NOW,
                               ttl=ttl, max_uses=max_uses)


# -- preflight -----------------------------------------------------------------

def test_preflight_ok_with_valid_authorization():
    result = preflight(TARGET, allow_policy(), auth(), now=NOW)
    assert result.ok is True
    assert result.authorization_binding is not None
    assert all(c["ok"] for c in result.checks)


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
    wrong = Authorization.issue(other, ACTION, nonce="x", now=NOW)
    result = preflight(TARGET, allow_policy(), wrong, now=NOW)
    assert result.ok is False


def test_preflight_refuses_expired_authorization():
    expired = auth(ttl=timedelta(minutes=1))
    result = preflight(TARGET, allow_policy(), expired, now=NOW + timedelta(hours=1))
    assert result.ok is False


def test_preflight_refuses_wrong_action():
    wrong = Authorization.issue(TARGET, "delete_project", nonce="x", now=NOW)
    result = preflight(TARGET, allow_policy(), wrong, now=NOW)
    assert result.ok is False


# -- executor ------------------------------------------------------------------

def test_dry_run_never_mutates():
    receipt = retire_pages(TARGET, allow_policy(), auth(), now=NOW)
    assert receipt.mutation_attempted is False
    assert receipt.mutation is None
    assert receipt.verdict == Verdict.SAFE_TO_RETIRE


def test_blocked_preflight_no_mutation():
    transport = FakeTransport({("DELETE", "/projects/12345678/pages"): HttpReply(204, "")})
    receipt = retire_pages(
        TARGET, allow_policy(), None, mutation_client=PagesMutationClient("t", transport=transport),
        now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    assert transport.calls == []


def test_authorized_execute_calls_delete_and_reads_back(monkeypatch):
    monkeypatch.setattr(absence_mod, "https_get_status", lambda url, timeout=20.0: (404, None))
    del_transport = FakeTransport({("DELETE", "/projects/12345678/pages"): HttpReply(204, "")})
    read_transport = FakeTransport({("GET", "/projects/12345678/pages"): HttpReply(404, "", "404")})
    receipt = retire_pages(
        TARGET,
        allow_policy(),
        auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport),
        read_client=GitLabClient("t", transport=read_transport),
        served_url=URL,
        now=NOW,
    )
    assert del_transport.calls[0][0] == "DELETE"
    assert receipt.mutation is not None and receipt.mutation.accepted
    assert receipt.verdict == Verdict.OBSERVED_ABSENT


def test_authorization_is_single_use(monkeypatch):
    monkeypatch.setattr(absence_mod, "https_get_status", lambda url, timeout=20.0: (404, None))
    a = auth()
    del_transport = FakeTransport({("DELETE", "/projects/12345678/pages"): HttpReply(204, "")})
    read_transport = FakeTransport({("GET", "/projects/12345678/pages"): HttpReply(404, "", "404")})
    retire_pages(
        TARGET, allow_policy(), a,
        mutation_client=PagesMutationClient("t", transport=del_transport),
        read_client=GitLabClient("t", transport=read_transport), served_url=URL, now=NOW,
    )
    second_transport = FakeTransport({("DELETE", "/projects/12345678/pages"): HttpReply(204, "")})
    receipt = retire_pages(
        TARGET, allow_policy(), a,
        mutation_client=PagesMutationClient("t", transport=second_transport), now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED
    assert second_transport.calls == []


def test_mutation_403_is_inconclusive_not_absent():
    reply = HttpReply(403, "", "403")
    del_transport = FakeTransport({("DELETE", "/projects/12345678/pages"): reply})
    receipt = retire_pages(
        TARGET, allow_policy(), auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport), now=NOW,
    )
    assert receipt.mutation is not None and receipt.mutation.accepted is False
    assert receipt.verdict == Verdict.INCONCLUSIVE


def test_accepted_mutation_without_readback_is_retired_not_absent():
    del_transport = FakeTransport({("DELETE", "/projects/12345678/pages"): HttpReply(204, "")})
    receipt = retire_pages(
        TARGET, allow_policy(), auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport), now=NOW,
    )
    assert receipt.verdict == Verdict.RETIRED
    assert receipt.verdict != Verdict.OBSERVED_ABSENT


def test_accepted_mutation_but_site_still_served_is_blocked(monkeypatch):
    monkeypatch.setattr(absence_mod, "https_get_status", lambda url, timeout=20.0: (200, None))
    del_transport = FakeTransport({("DELETE", "/projects/12345678/pages"): HttpReply(204, "")})
    read_transport = FakeTransport({("GET", "/projects/12345678/pages"): HttpReply(200, "{}")})
    receipt = retire_pages(
        TARGET, allow_policy(), auth(),
        mutation_client=PagesMutationClient("t", transport=del_transport),
        read_client=GitLabClient("t", transport=read_transport), served_url=URL, now=NOW,
    )
    assert receipt.verdict == Verdict.BLOCKED


def test_receipt_is_non_authoritative_note_and_dict():
    receipt = retire_pages(TARGET, allow_policy(), None, now=NOW)
    data = receipt.to_dict()
    assert data["schema"] == "termivance.retirement_receipt/v1"
    assert "not proof of absence" in data["note"]


# -- authorization serialization ----------------------------------------------

def test_authorization_round_trip(tmp_path):
    a = auth()
    path = tmp_path / "auth.json"
    import json

    path.write_text(json.dumps(a.to_dict()), encoding="utf-8")
    loaded = load_authorization(path)
    assert loaded.target.key() == TARGET.key()
    assert loaded.action == ACTION
    assert loaded.binding() == a.binding()
    assert loaded.is_valid(NOW, TARGET, ACTION) is True


def test_load_authorization_missing_file_fails_closed(tmp_path):
    with pytest.raises(AuthorizationError):
        load_authorization(tmp_path / "absent.json")


def test_authorization_from_prose_always_refused():
    with pytest.raises(AuthorizationError):
        Authorization.from_prose("operator said yes")
