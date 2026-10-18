"""Read-only GitLab REST client.

The B2 evaluation path must contain no executable route to a destructive call.
This module enforces that structurally: :class:`GitLabClient` exposes only
``GET`` and raises :class:`ReadOnlyViolation` for any other method. Output
publishing lives in a separate module (:mod:`termivance.publish`).

Standard library only (``urllib``), so no network dependency is required to
import or test the package.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

READ_ONLY_METHODS: frozenset[str] = frozenset({"GET"})

DEFAULT_BASE_URL = "https://gitlab.com/api/v4"


class ReadOnlyViolation(RuntimeError):
    """Raised if a non-read-only method is attempted through the client."""


class TokenUnavailable(RuntimeError):
    """Raised when no GitLab credential can be obtained locally."""


@dataclass(slots=True)
class HttpReply:
    status: int
    body: str
    error: str | None = None


@runtime_checkable
class Transport(Protocol):
    def request(
        self, method: str, url: str, headers: Mapping[str, str], timeout: float
    ) -> HttpReply: ...


@dataclass(slots=True)
class RecordedCall:
    method: str
    url: str
    status: int | None


class UrllibTransport:
    """Default transport using the standard library."""

    def request(
        self, method: str, url: str, headers: Mapping[str, str], timeout: float
    ) -> HttpReply:
        req = urllib.request.Request(url, method=method, headers=dict(headers))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
                return HttpReply(status=resp.status, body=resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace") if exc.fp else ""
            return HttpReply(status=exc.code, body=body, error=f"HTTP {exc.code}")
        except urllib.error.URLError as exc:
            return HttpReply(status=0, body="", error=f"network error: {exc.reason}")


@dataclass(slots=True)
class RecordingTransport:
    """Transport wrapper that records every call, to prove read-only behaviour."""

    inner: Transport
    calls: list[RecordedCall] = field(default_factory=list)

    def request(
        self, method: str, url: str, headers: Mapping[str, str], timeout: float
    ) -> HttpReply:
        reply = self.inner.request(method, url, headers, timeout)
        self.calls.append(RecordedCall(method=method, url=url, status=reply.status))
        return reply

    def methods_used(self) -> set[str]:
        return {c.method.upper() for c in self.calls}


#: error classifications used by the discovery layer
ERR_AUTH = "AUTH_DENIED"
ERR_NOT_FOUND = "NOT_FOUND"
ERR_MALFORMED = "MALFORMED"
ERR_TIMEOUT = "TIMEOUT"
ERR_NETWORK = "NETWORK"
ERR_SERVER = "SERVER_ERROR"


@dataclass(frozen=True, slots=True)
class ApiResult:
    ok: bool
    status: int | None
    data: object | None
    endpoint: str
    method: str
    error_kind: str | None = None

    def error_text(self) -> str:
        return f"{self.error_kind or 'OK'} ({self.status})"


class GitLabClient:
    """Read-only GitLab REST client."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        transport: Transport | None = None,
        timeout: float = 20.0,
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._transport: Transport = transport or UrllibTransport()
        self._timeout = timeout

    @property
    def base_url(self) -> str:
        return self._base_url

    def _headers(self) -> dict[str, str]:
        # Least-privilege read header. The token is never logged or stored.
        return {"PRIVATE-TOKEN": self._token, "Accept": "application/json"}

    def get_json(self, endpoint: str, *, params: Mapping[str, object] | None = None) -> ApiResult:
        return self._request("GET", endpoint, params=params)

    def get_text(self, endpoint: str, *, params: Mapping[str, object] | None = None) -> ApiResult:
        return self._request("GET", endpoint, params=params, expect_json=False)

    # Any other method is refused before a transport call happens.
    def request(self, method: str, endpoint: str) -> ApiResult:
        return self._request(method, endpoint)

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, object] | None = None,
        expect_json: bool = True,
    ) -> ApiResult:
        if method.upper() not in READ_ONLY_METHODS:
            raise ReadOnlyViolation(
                f"method {method!r} is not read-only; publishing is a separate module"
            )
        url = self._base_url + endpoint
        if params:
            query = urllib.parse.urlencode(dict(params))
            url = f"{url}?{query}"
        try:
            reply = self._transport.request(method.upper(), url, self._headers(), self._timeout)
        except Exception:  # noqa: BLE001 - defensive: any transport failure fails closed
            return ApiResult(False, None, None, endpoint, method, ERR_NETWORK)
        return self._classify(reply, endpoint, method, expect_json)

    def _classify(
        self, reply: HttpReply, endpoint: str, method: str, expect_json: bool
    ) -> ApiResult:
        status = reply.status
        if status == 0:
            kind = ERR_TIMEOUT if reply.error and "timed out" in reply.error else ERR_NETWORK
            return ApiResult(False, status, None, endpoint, method, kind)
        if status in (401, 403):
            return ApiResult(False, status, None, endpoint, method, ERR_AUTH)
        if status == 404:
            return ApiResult(False, status, None, endpoint, method, ERR_NOT_FOUND)
        if status >= 500:
            return ApiResult(False, status, None, endpoint, method, ERR_SERVER)
        if status >= 400:
            return ApiResult(False, status, None, endpoint, method, ERR_MALFORMED)
        if not expect_json:
            return ApiResult(True, status, reply.body, endpoint, method)
        try:
            data = json.loads(reply.body) if reply.body else None
        except json.JSONDecodeError:
            return ApiResult(False, status, None, endpoint, method, ERR_MALFORMED)
        return ApiResult(True, status, data, endpoint, method)


def load_local_token(*, run: Callable[[], str] | None = None) -> str:
    """Load the GitLab PAT from the local credential store or ``GITLAB_TOKEN``.

    The value is never printed or persisted. ``run`` is injectable for tests.
    """
    env = os.environ.get("GITLAB_TOKEN")
    if env:
        return env
    runner = run or _run_git_credential
    try:
        output = runner()
    except Exception as exc:  # noqa: BLE001
        raise TokenUnavailable(f"could not read GitLab credential: {exc}") from exc
    for line in str(output).splitlines():
        if line.startswith("password="):
            return line[len("password=") :]
    raise TokenUnavailable("no GitLab credential available from the local store")


def _run_git_credential() -> str:
    proc = subprocess.run(  # noqa: S603
        ["git", "credential", "fill"],
        input="protocol=https\nhost=gitlab.com\n\n",
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return proc.stdout
