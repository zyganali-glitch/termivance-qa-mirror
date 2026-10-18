"""Tests for the endpoint-restricted GitLab Pages mutation capability."""

from __future__ import annotations

import pytest
from conftest import FakeTransport

from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.pages import (
    MutationRefused,
    PagesMutationClient,
    mutation_is_structurally_safe,
    read_pages_state,
)
from termivance.target import TargetIdentity

PAGES_TARGET = TargetIdentity(12345678, "grp/disposable", "GITLAB_PAGES_SITE")


def test_read_pages_state_present():
    transport = FakeTransport(
        {("GET", "/projects/12345678/pages"): HttpReply(200, '{"url": "https://x.gitlab.io/y/"}')}
    )
    client = GitLabClient("t", transport=transport)
    state = read_pages_state(client, PAGES_TARGET)
    assert state.present is True
    assert state.url == "https://x.gitlab.io/y/"
    assert state.accessible is True
    assert transport.calls[0][0] == "GET"


def test_read_pages_state_auth_denied():
    transport = FakeTransport({("GET", "/projects/12345678/pages"): HttpReply(403, "", "HTTP 403")})
    client = GitLabClient("t", transport=transport)
    state = read_pages_state(client, PAGES_TARGET)
    assert state.error_kind == "AUTH_DENIED"
    assert state.present is False
    assert state.accessible is False


def test_unpublish_calls_exact_endpoint_once():
    transport = FakeTransport({("DELETE", "/projects/12345678/pages"): HttpReply(204, "")})
    client = PagesMutationClient("t", transport=transport)
    result = client.unpublish_pages(PAGES_TARGET)
    assert result.accepted is True
    assert result.status == 204
    assert len(transport.calls) == 1
    assert transport.calls[0][0] == "DELETE"
    assert transport.calls[0][1].endswith("/projects/12345678/pages")


def test_unpublish_never_targets_project_root():
    transport = FakeTransport({("DELETE", "/projects/12345678/pages"): HttpReply(204, "")})
    client = PagesMutationClient("t", transport=transport)
    client.unpublish_pages(PAGES_TARGET)
    for _method, url in transport.calls:
        assert not url.rstrip("/").endswith("/projects/12345678")


def test_delete_refuses_project_deletion():
    client = PagesMutationClient("t", transport=FakeTransport({}))
    with pytest.raises(MutationRefused):
        client._delete("/projects/12345678")


def test_delete_refuses_other_endpoints():
    client = PagesMutationClient("t", transport=FakeTransport({}))
    for bad in ("/projects/12345678/repository", "/projects/12345678/pages/domains", "/user"):
        with pytest.raises(MutationRefused):
            client._delete(bad)


def test_mutation_structurally_safe():
    assert mutation_is_structurally_safe() is True


def test_unpublish_auth_denied_is_not_accepted():
    reply = HttpReply(403, "", "HTTP 403")
    transport = FakeTransport({("DELETE", "/projects/12345678/pages"): reply})
    client = PagesMutationClient("t", transport=transport)
    result = client.unpublish_pages(PAGES_TARGET)
    assert result.accepted is False
    assert result.error_kind == "AUTH_DENIED"


def test_unpublish_network_failure_fails_closed():
    class Boom:
        def request(self, *_a, **_k):  # type: ignore[no-untyped-def]
            raise OSError("boom")

    client = PagesMutationClient("t", transport=Boom())
    result = client.unpublish_pages(PAGES_TARGET)
    assert result.accepted is False
    assert result.error_kind == "NETWORK"
