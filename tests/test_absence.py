"""Tests for bounded-absence observation (fail-closed negative evidence)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from termivance import absence as absence_mod
from termivance.absence import observe_absence
from termivance.evidence import PagesObservation, bounded_absence
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict
from tests.conftest import FakeTransport

TARGET = TargetIdentity(12345678, "grp/disposable", "GITLAB_PAGES_SITE")
URL = "https://grp.gitlab.io/disposable/"
NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


def _client(api_reply: HttpReply) -> GitLabClient:
    return GitLabClient(
        "t", transport=FakeTransport({("GET", "/projects/12345678/pages"): api_reply})
    )


def _patch_http(monkeypatch, status, error=None):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        absence_mod, "https_get_status", lambda url, timeout=20.0: (status, error)
    )


def test_absent_when_api_and_url_both_gone(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(_client(HttpReply(404, "", "HTTP 404")), TARGET, URL, now=NOW)
    assert probe.verdict == Verdict.OBSERVED_ABSENT
    assert probe.pages_api_status == 404
    assert probe.served_http_status == 404


def test_blocked_when_site_still_served(monkeypatch):
    _patch_http(monkeypatch, 200)
    probe = observe_absence(
        _client(HttpReply(200, json.dumps({"url": URL}))), TARGET, URL, now=NOW
    )
    assert probe.verdict == Verdict.BLOCKED


def test_inconclusive_on_api_403(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(_client(HttpReply(403, "", "HTTP 403")), TARGET, URL, now=NOW)
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_inconclusive_when_url_returns_200_but_api_gone(monkeypatch):
    _patch_http(monkeypatch, 200)
    probe = observe_absence(_client(HttpReply(404, "", "HTTP 404")), TARGET, URL, now=NOW)
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_inconclusive_on_network_timeout(monkeypatch):
    _patch_http(monkeypatch, None, "timed out")
    probe = observe_absence(
        _client(HttpReply(0, "", "network error: timed out")), TARGET, URL, now=NOW
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_inconclusive_when_stale():
    observation = PagesObservation(
        target=TARGET,
        observed_scope=frozenset({"pages_api", "served_url"}),
        observation_time_utc=NOW,
        source="test",
        api_status=404,
        served_url=URL,
        http_status=404,
        fresh_until=NOW + timedelta(seconds=1),
    )
    assert bounded_absence(observation, NOW + timedelta(days=1)) == Verdict.INCONCLUSIVE


def test_receipt_marks_scope(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(_client(HttpReply(404, "", "HTTP 404")), TARGET, URL, now=NOW)
    data = probe.to_dict()
    assert data["observation"]["observed_scope"] == ["pages_api", "served_url"]
    assert data["verdict"] == "OBSERVED_ABSENT"


@pytest.mark.parametrize("status", [401, 403, 500, 0])
def test_never_absent_for_error_statuses(monkeypatch, status):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(_client(HttpReply(status, "", f"HTTP {status}")), TARGET, URL, now=NOW)
    assert probe.verdict != Verdict.OBSERVED_ABSENT
