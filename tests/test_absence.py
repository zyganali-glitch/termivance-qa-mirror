"""Tests for bounded-absence observation (fail-closed negative evidence).

Since B4 (P0-C) an ``OBSERVED_ABSENT`` verdict additionally requires a
validated mutation receipt bound to the exact target, endpoint and a durably
sealed operation. Tests always prove that a caller-supplied pre-state alone —
or a forged ``action_accepted`` flag — cannot mint the claim anymore.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from conftest import FakeTransport

from termivance import absence as absence_mod
from termivance.absence import observe_absence, publication_pre_state
from termivance.capsule import MutationBinding, ReceiptValidationError
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


def binding(
    *,
    target: TargetIdentity = TARGET,
    endpoint: str | None = None,
    accepted: bool = True,
    source: str = "live_dispatch",
    pre: PagesPreState | None = None,
    ledger_entry: dict[str, object] | None = None,
) -> MutationBinding:
    return MutationBinding(
        target=target,
        action="unpublish_pages",
        endpoint=endpoint or f"/projects/{target.project_id}/pages",
        operation_id="op-abc123",
        authorization_binding="0" * 64,
        accepted=accepted,
        status=204 if accepted else 403,
        pre_state=pre if pre is not None else PRE,
        ledger_entry=ledger_entry,
        source=source,
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


# -- real proven transition ------------------------------------------------------


def test_absent_when_proven_transition_and_both_channels_gone(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=PRE,
        mutation_receipt=binding(),
        now=NOW,
    )
    assert probe.verdict == Verdict.OBSERVED_ABSENT
    assert probe.pages_api_status == 404
    assert probe.served_http_status == 404


def test_receipt_bound_action_is_recorded_in_observation(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        mutation_receipt=binding(),
        now=NOW,
    )
    assert probe.observation.action_accepted is True
    assert probe.observation.action_endpoint == "/projects/12345678/pages"
    assert probe.verdict == Verdict.OBSERVED_ABSENT


def test_unsealed_action_cannot_award_observed_absent(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=PRE,
        mutation_receipt=binding(source="recorded_receipt_file", ledger_entry=None),
        now=NOW,
    )
    assert probe.verdict != Verdict.OBSERVED_ABSENT
    assert any("not durably sealed" in note for note in probe.notes)


def test_rejected_mutation_never_proves_absence(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=PRE,
        mutation_receipt=binding(accepted=False),
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


# -- forged / injected claims are refused ----------------------------------------


def test_forged_action_accepted_flag_is_no_longer_possible(monkeypatch):
    """P0-C: a caller-supplied pre-state alone can never award the claim."""
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        pre_state=PRE,
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE
    assert any("no validated mutation receipt" in note for note in probe.notes)


def test_cross_target_receipt_is_refused(monkeypatch):
    _patch_http(monkeypatch, 404)
    other = TargetIdentity(99999999, "grp/other", "GITLAB_PAGES_SITE")
    with pytest.raises(ReceiptValidationError):
        observe_absence(
            _client(HttpReply(404, "", "HTTP 404")),
            TARGET,
            URL,
            mutation_receipt=binding(target=other),
            now=NOW,
        )


def test_cross_endpoint_receipt_is_refused(monkeypatch):
    _patch_http(monkeypatch, 404)
    with pytest.raises(ReceiptValidationError):
        observe_absence(
            _client(HttpReply(404, "", "HTTP 404")),
            TARGET,
            URL,
            mutation_receipt=binding(endpoint="/projects/99999999/pages"),
            now=NOW,
        )


def test_injected_foreign_pre_state_is_refused(monkeypatch):
    _patch_http(monkeypatch, 404)
    injected = PagesPreState(
        served_url=URL,
        marker="EVIL-MARKER",
        marker_observed=True,
        deployment_present=True,
        observed_at=NOW,
    )
    with pytest.raises(ReceiptValidationError):
        observe_absence(
            _client(HttpReply(404, "", "HTTP 404")),
            TARGET,
            URL,
            pre_state=injected,
            mutation_receipt=binding(),
            now=NOW,
        )


# -- evidence-level failures stay fail-closed ------------------------------------


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
        mutation_receipt=binding(pre=never),
        now=NOW,
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
        mutation_receipt=binding(pre=other),
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_blocked_when_site_still_served(monkeypatch):
    _patch_http(monkeypatch, 200)
    probe = observe_absence(
        _client(HttpReply(200, json.dumps({"url": URL}))),
        TARGET,
        URL,
        mutation_receipt=binding(),
        now=NOW,
    )
    assert probe.verdict == Verdict.BLOCKED


def test_inconclusive_on_api_403(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(403, "", "HTTP 403")),
        TARGET,
        URL,
        mutation_receipt=binding(),
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_inconclusive_when_url_returns_200_but_api_gone(monkeypatch):
    _patch_http(monkeypatch, 200)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        mutation_receipt=binding(),
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_inconclusive_on_network_timeout(monkeypatch):
    _patch_http(monkeypatch, None, "timed out")
    probe = observe_absence(
        _client(HttpReply(0, "", "network error: timed out")),
        TARGET,
        URL,
        mutation_receipt=binding(),
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_inconclusive_on_cloudflare_challenge(monkeypatch):
    _patch_http(monkeypatch, 403, None, "<html>Just a moment...</html>")
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        mutation_receipt=binding(),
        now=NOW,
    )
    assert probe.verdict == Verdict.INCONCLUSIVE


def test_receipt_marks_scope_and_pre_state(monkeypatch):
    _patch_http(monkeypatch, 404)
    probe = observe_absence(
        _client(HttpReply(404, "", "HTTP 404")),
        TARGET,
        URL,
        mutation_receipt=binding(),
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
        mutation_receipt=binding(),
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
