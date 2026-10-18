import pytest
from conftest import FakeTransport

from termivance.gitlab_client import (
    ERR_AUTH,
    ERR_MALFORMED,
    ERR_NETWORK,
    ERR_NOT_FOUND,
    ERR_SERVER,
    GitLabClient,
    HttpReply,
    ReadOnlyViolation,
    RecordingTransport,
    TokenUnavailable,
    Transport,
    load_local_token,
)


def client_with(responses, *, record=False):
    transport = FakeTransport(responses)
    wrapped = RecordingTransport(inner=transport) if record else transport
    return GitLabClient("test-token", transport=wrapped), wrapped


def test_non_read_only_method_refused():
    client, _ = client_with({})
    with pytest.raises(ReadOnlyViolation):
        client.request("DELETE", "/projects/1/pages")
    with pytest.raises(ReadOnlyViolation):
        client.request("POST", "/projects/1/issues")


def test_get_json_ok_and_endpoint_recorded():
    replies = {("GET", "/projects/1"): HttpReply(200, '{"id": 1}')}
    client, wrapped = client_with(replies, record=True)
    result = client.get_json("/projects/1")
    assert result.ok and result.data == {"id": 1}
    assert all(c.method == "GET" for c in wrapped.calls)


@pytest.mark.parametrize(
    "status,expected",
    [(401, ERR_AUTH), (403, ERR_AUTH), (404, ERR_NOT_FOUND), (500, ERR_SERVER)],
)
def test_error_classification(status, expected):
    client, _ = client_with({("GET", "/x"): HttpReply(status, "", f"HTTP {status}")})
    result = client.get_json("/x")
    assert not result.ok and result.error_kind == expected


def test_malformed_json_classified():
    client, _ = client_with({("GET", "/x"): HttpReply(200, "{not json")})
    assert client.get_json("/x").error_kind == ERR_MALFORMED


def test_network_error_classified():
    client, _ = client_with({("GET", "/x"): HttpReply(0, "", "network error: boom")})
    assert client.get_json("/x").error_kind == ERR_NETWORK


def test_params_encoded_do_not_expose_token():
    client, wrapped = client_with({("GET", "/issues"): HttpReply(200, "[]")}, record=True)
    client.get_json("/issues", params={"state": "opened", "per_page": 100})
    assert "test-token" not in wrapped.calls[0].url
    assert wrapped.calls[0].method == "GET"


def test_load_local_token_from_env(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "abc123")
    assert load_local_token() == "abc123"


def test_load_local_token_from_runner():
    assert load_local_token(run=lambda: "protocol=https\npassword=secret\n") == "secret"


def test_load_local_token_raises_when_absent(monkeypatch):
    monkeypatch.delenv("GITLAB_TOKEN", raising=False)
    with pytest.raises(TokenUnavailable):
        load_local_token(run=lambda: "username=zyganali\n")


def test_transport_protocol_shape():
    assert isinstance(FakeTransport({}), Transport)
