"""Tests for bounded-absence observation (fail-closed negative evidence)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from conftest import FakeTransport

from termivance import absence as absence_mod
from termivance.absence import observe_absence, publication_pre_state
from termivance.evidence import PagesPreState
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.pages import observe_publication
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

TARGET = TargetIdentity(12345678, "grp/disposable", "GITLAB_PAGES_SITE")
URL = "https://grp.gitlab.io/disposable/"
MARKER = "TERMIVANCE-B3-DISPOSABLE-MARKER"
NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
PRE = PagesPreState(
    served_url=URL,
    marker=MARKER,
    marker_observed=True,
    deployment_present=True,
    observed_at=NOW - timedelta(minutes=5),
)


def _client(api_reply: HttpReply) -> GitLabClient:
    return GitLabClient(
        "t", transport=FakeTransport({("GET", "/projects/12345678/pages"): api_reply})
    )


def _patch_http(monkeypatch, status, error=None, body=""):  # type: ignore[no-untyped-def]
    from termivance import pages as pages_mod

    def handler(url, timeout=20.0, **_kw):
        return status, error, body

    monkeypatch.setattr(absence_mod, "https_get", handler)
    monkeypatch.setattr(pages_mod, "https_get", handler)


def test_absent_when_proven_transition_and_both_channels_gone(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=PRE,
        action_accepted=True,
        action_endpoint="/projects/12345678/pages",
        now=NOW,
    )
    assert probe.verdict == Verdict.OBSERVED_ABSENT
    assert probe.pages_api_status == 404
    assert probe.served_http_status == 404


def test_two_unrelated_404s_without_pre_state_are_inconclusive(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(_client(HttpReply(404, "", "HTTP 404")), TARGET, URL, now=NOW)
    assert probe.verdict == Verdict.INCONCLUSIVE
    assert probe.notes


def test_previously_nonexistent_site_is_inconclusive(monkeypatch):
    _patch_http(monkeypatch, 404)
    never = PagesPreState(
        served_url=URL,
        marker=MARKER,
        marker_observed=False,
        deployment_present=False,
        observed_at=NOW,
    )
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=never,
        action_accepted=True,
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_missing_action_record_is_inconclusive(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")), TARGET, URL, pre_state=PRE, now=NOW
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_mismatched_pre_state_url_is_inconclusive(monkeypatch):
    _patch_http(monkeypatch, 404)
    other = PagesPreState(
        served_url="https://grp.gitlab.io/other/",
        marker=MARKER,
        marker_observed=True,
        deployment_present=True,
        observed_at=NOW,
    )
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=other,
        action_accepted=True,
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_blocked_when_site_still_served(monkeypatch):
    _patch_http(monkeypatch, 200)
    probe = observe_absence(
        _client(HttpReply(200, json.dumps({"url": URL}))),
        TARGET,
        URL,
        pre_state=PRE,
        action_accepted=True,
        now=NOW,
    )
    assert probe.verdict == Verdict.BLOCKED


def test_inconclusive_on_api_403(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(403, "", "HTTP 403")),
        TARGET,
        URL,
        pre_state=PRE,
        action_accepted=True,
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_inconclusive_when_url_returns_200_but_api_gone(monkeypatch):
    _patch_http(monkeypatch, 200)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=PRE,
        action_accepted=True,
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_inconclusive_on_network_timeout(monkeypatch):
    _patch_http(monkeypatch, None, "timed out")
    probe = observe_absence(
        _client(HttpReply(0, "", "network error: timed out")),
        TARGET,
        URL,
        pre_state=PRE,
        action_accepted=True,
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_inconclusive_on_cloudflare_challenge(monkeypatch):
    _patch_http(monkeypatch, 403, None, "<html>Just a moment...</html>")
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=PRE,
        action_accepted=True,
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_receipt_marks_scope_and_pre_state(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=PRE,
        action_accepted=True,
        now=NOW,
    )
    data = probe.to_dict()
    assert data["observation"]["observed_scope"] == ["pages_api", "served_url"]
    assert data["observation"]["pre_state"]["genuinely_published"] is True
    assert data["verdict"] == "OBSERVED_ABSENT"


@pytest.mark.parametrize("status", [401, 403, 500, 0])
def test_never_absent_for_error_statuses(monkeypatch, status):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(status, "", f"HTTP {status}")),
        TARGET,
        URL,
        pre_state=PRE,
        action_accepted=True,
        now=NOW,
    )
    assert probe.verdict != Verdict.OBSERVED_ABSENT


# -- publication pre-state -----------------------------------------------------


def test_publication_requires_deployment_and_marker(monkeypatch):
    _patch_http(monkeypatch, 200, None, f"<html>{MARKER}</html>")
    api = HttpReply(200, json.dumps({"url": URL, "deployments": [{"id": 1}]}))
    client = GitLabClient("t", transport=FakeTransport({("GET", "/projects/12345678/pages"): api}))
    probe = observe_publication(client, TARGET, URL, MARKER, now=NOW)
    assert probe.genuinely_published is True
    assert publication_pre_state(probe).genuinely_published is True


def test_publication_without_marker_is_not_proven(monkeypatch):
    _patch_http(monkeypatch, 200, None, "<html>nothing to see</html>")
    api = HttpReply(200, json.dumps({"url": URL, "deployments": [{"id": 1}]}))
    client = GitLabClient("t", transport=FakeTransport({("GET", "/projects/12345678/pages"): api}))
    assert observe_publication(client, TARGET, URL, MARKER, now=NOW).genuinely_published is False


def test_publication_without_deployment_is_not_proven(monkeypatch):
    _patch_http(monkeypatch, 200, None, f"<html>{MARKER}</html>")
    api = HttpReply(200, json.dumps({"url": URL, "deployments": []}))
    client = GitLabClient("t", transport=FakeTransport({("GET", "/projects/12345678/pages"): api}))
    assert observe_publication(client, TARGET, URL, MARKER, now=NOW).genuinely_published is False


def test_publication_403_is_not_proven(monkeypatch):
    _patch_http(monkeypatch, 200, None, f"<html>{MARKER}</html>")
    api = HttpReply(403, "", "HTTP 403")
    client = GitLabClient("t", transport=FakeTransport({("GET", "/projects/12345678/pages"): api}))
    assert observe_publication(client, TARGET, URL, MARKER, now=NOW).genuinely_published is False
