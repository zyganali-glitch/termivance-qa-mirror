"""GitLab Pages API access.

Two clearly separated concerns live here:

* read-only Pages state/discovery, which reuses the GET-only
  :class:`termivance.gitlab_client.GitLabClient`;
* the *only* mutation Termivance may ever perform:
  ``DELETE /projects/:id/pages`` against one exact authorized target.

The mutation client structurally refuses every other endpoint. In particular it
can never issue ``DELETE /projects/:id`` (project deletion) and can never touch a
path that is not exactly ``/projects/<positive-int>/pages``.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from termivance.gitlab_client import (
    DEFAULT_BASE_URL,
    ApiResult,
    GitLabClient,
    HttpReply,
    Transport,
    UrllibTransport,
)
from termivance.target import TargetIdentity

#: The complete set of endpoints the mutation client will ever call. Project
#: deletion (``/projects/:id``) is intentionally absent and can never match.
_ALLOWED_PAGES_ENDPOINT = re.compile(r"^/projects/[1-9][0-9]*/pages$")

#: The exact, documented GitLab Pages unpublish endpoint suffix.
PAGES_PATH_SUFFIX = "/pages"


class MutationRefused(RuntimeError):
    """Raised when a mutation attempt is outside the single allowed endpoint."""


class MutationTransportError(RuntimeError):
    """Raised when the network itself fails during a mutation request."""


def _utc_now(now: datetime | None) -> datetime:
    value = now or datetime.now(tz=UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class PagesState:
    """A read-only observation of a project's Pages state."""

    target: TargetIdentity
    endpoint: str
    status: int | None
    error_kind: str | None
    present: bool
    url: str | None
    observed_at: datetime
    deployment_count: int = 0

    @property
    def accessible(self) -> bool:
        return self.error_kind is None and self.status is not None and self.status < 400

    @property
    def has_deployment(self) -> bool:
        """True only when the Pages API affirmatively reports a deployment."""
        return bool(self.accessible and self.deployment_count > 0)

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target.to_dict(),
            "endpoint": self.endpoint,
            "method": "GET",
            "status": self.status,
            "error_kind": self.error_kind,
            "present": self.present,
            "url": self.url,
            "deployment_count": self.deployment_count,
            "has_deployment": self.has_deployment,
            "observed_at": _utc_now(self.observed_at).isoformat(),
        }


def read_pages_state(client: GitLabClient, target: TargetIdentity, *, now=None) -> PagesState:
    """Read-only ``GET /projects/:id/pages``. Never mutates."""
    result: ApiResult = client.get_json(f"/projects/{target.project_id}{PAGES_PATH_SUFFIX}")
    url = None
    deployments: list[object] = []
    if result.ok and isinstance(result.data, dict):
        url = result.data.get("url")
        raw = result.data.get("deployments")
        if isinstance(raw, list):
            deployments = raw
    return PagesState(
        target=target,
        endpoint=result.endpoint,
        status=result.status,
        error_kind=result.error_kind,
        present=bool(result.ok),
        url=url if isinstance(url, str) else None,
        observed_at=_utc_now(now),
        deployment_count=len(deployments),
    )


@dataclass(frozen=True, slots=True)
class MutationResult:
    """The exact record of one authorized, endpoint-restricted mutation."""

    ok: bool
    method: str
    endpoint: str
    status: int | None
    body: str
    error_kind: str | None
    requested_at: datetime
    ip_address: str | None = None

    @property
    def accepted(self) -> bool:
        return self.ok and self.status is not None and 200 <= self.status < 300

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "accepted": self.accepted,
            "method": self.method,
            "endpoint": self.endpoint,
            "status": self.status,
            "error_kind": self.error_kind,
            "body_digest_material": self.body[:2000],
            "requested_at": _utc_now(self.requested_at).isoformat(),
            "ip_address": self.ip_address,
        }


def _classify(status: int, error: str | None) -> str | None:
    if status == 0:
        return "TIMEOUT" if error and "timed out" in error else "NETWORK"
    if status in (401, 403):
        return "AUTH_DENIED"
    if status == 404:
        return "NOT_FOUND"
    if status >= 500:
        return "SERVER_ERROR"
    if status >= 400:
        return "MALFORMED"
    return None


class PagesMutationClient:
    """The single, endpoint-restricted mutation capability in Termivance.

    Only ``DELETE /projects/<id>/pages`` is ever dispatched. Any other endpoint,
    including project deletion, is refused *before* any network call.
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        transport: Transport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._transport: Transport = transport or UrllibTransport()
        self._timeout = timeout

    def _headers(self) -> Mapping[str, str]:
        return {"PRIVATE-TOKEN": self._token, "Accept": "application/json"}

    def unpublish_pages(self, target: TargetIdentity, *, now=None) -> MutationResult:
        """Call the exact authorized Pages unpublish endpoint for one target."""
        endpoint = f"/projects/{target.project_id}{PAGES_PATH_SUFFIX}"
        return self._delete(endpoint, now=now)

    def _delete(self, endpoint: str, *, now=None) -> MutationResult:
        """Dispatch one DELETE, refusing every endpoint but the exact Pages path."""
        if not _ALLOWED_PAGES_ENDPOINT.match(endpoint):
            raise MutationRefused(f"endpoint {endpoint!r} is not the allowed Pages endpoint")
        requested = _utc_now(now)
        url = self._base_url + endpoint
        try:
            reply: HttpReply = self._transport.request(
                "DELETE", url, self._headers(), self._timeout
            )
        except Exception:  # noqa: BLE001 - network failure fails closed
            return MutationResult(
                ok=False,
                method="DELETE",
                endpoint=endpoint,
                status=None,
                body="",
                error_kind="NETWORK",
                requested_at=requested,
            )
        text = reply.body or ""
        return MutationResult(
            ok=reply.error is None and 200 <= reply.status < 300,
            method="DELETE",
            endpoint=endpoint,
            status=reply.status,
            body=text,
            error_kind=_classify(reply.status, reply.error),
            requested_at=requested,
        )


def mutation_is_structurally_safe() -> bool:
    """Self-check: prove project deletion can never match the allowlist."""
    return not _ALLOWED_PAGES_ENDPOINT.match("/projects/12345") and bool(
        _ALLOWED_PAGES_ENDPOINT.match("/projects/12345/pages")
    )


def https_get(
    url: str, *, timeout: float = 20.0, max_bytes: int = 65536
) -> tuple[int | None, str | None, str]:
    """Independently observe a served URL. Returns ``(http_status, error, body)``.

    Redirects are not followed: a redirect to a login page or an interstitial is
    never treated as evidence of absence (or of presence) by callers.
    """
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "termivance-b3"})
    try:
        opener = urllib.request.build_opener(_NoRedirect)
        with opener.open(request, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read(max_bytes)
            return resp.status, None, raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, None, ""
    except Exception as exc:  # noqa: BLE001
        return None, str(exc), ""


def https_get_status(url: str, *, timeout: float = 20.0) -> tuple[int | None, str | None]:
    """Independently observe a served URL. Returns ``(http_status, error)``."""
    status, error, _body = https_get(url, timeout=timeout)
    return status, error


def marker_observed(body: str, marker: str) -> bool:
    """True only for a non-empty marker found in a non-empty served body."""
    if not marker.strip() or not body.strip():
        return False
    return marker in body


@dataclass(frozen=True, slots=True)
class PublicationProbe:
    """Pre-retirement proof that one exact target is genuinely published."""

    target: TargetIdentity
    served_url: str
    marker: str
    api_status: int | None
    api_error: str | None
    deployment_count: int
    http_status: int | None
    http_error: str | None
    marker_observed: bool
    observed_at: datetime

    @property
    def deployment_present(self) -> bool:
        return bool(
            self.api_error is None
            and self.api_status is not None
            and 200 <= self.api_status < 300
            and self.deployment_count > 0
        )

    @property
    def genuinely_published(self) -> bool:
        return bool(
            self.deployment_present
            and self.marker_observed
            and self.http_status is not None
            and 200 <= self.http_status < 300
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target.to_dict(),
            "served_url": self.served_url,
            "marker": self.marker,
            "api": {"status": self.api_status, "error": self.api_error},
            "deployment_count": self.deployment_count,
            "deployment_present": self.deployment_present,
            "served_url_probe": {
                "http_status": self.http_status,
                "error": self.http_error,
                "marker_observed": self.marker_observed,
            },
            "genuinely_published": self.genuinely_published,
            "observed_at": _utc_now(self.observed_at).isoformat(),
        }


def observe_publication(
    client: GitLabClient,
    target: TargetIdentity,
    served_url: str,
    marker: str,
    *,
    now: datetime | None = None,
    timeout: float = 20.0,
) -> PublicationProbe:
    """Prove (or refuse to assume) that the target is genuinely published.

    Requires both channels: a live Pages deployment reported by the provider API
    *and* the distinctive marker served at the exact URL. Either channel missing
    means the site is not proven published.
    """
    observed = _utc_now(now)
    state = read_pages_state(client, target, now=observed)
    http_status, http_error, body = https_get(served_url, timeout=timeout)
    return PublicationProbe(
        target=target,
        served_url=served_url,
        marker=marker,
        api_status=state.status,
        api_error=state.error_kind,
        deployment_count=state.deployment_count,
        http_status=http_status,
        http_error=http_error,
        marker_observed=marker_observed(body, marker),
        observed_at=observed,
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Do not follow redirects: a login redirect is not evidence of absence."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def dumps(result: MutationResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True)
