"""Output publishing (separate from the read-only evaluator).

Publishing a report (creating an issue or note) is a write action. It is kept
out of :mod:`termivance.engine` and :mod:`termivance.gitlab_client` on purpose so
the evaluation path structurally cannot mutate anything. Nothing here can
retire, delete or unpublish a resource.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass

from termivance.gitlab_client import DEFAULT_BASE_URL


@dataclass(frozen=True, slots=True)
class PublishResult:
    ok: bool
    status: int | None
    endpoint: str
    data: object | None
    error: str | None = None


class GitLabPublisher:
    """Minimal POST-only publisher for issue/note creation (non-destructive)."""

    ALLOWED_ENDPOINTS_SUFFIX = ("/issues", "/notes")

    def __init__(
        self, token: str, *, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _post(self, endpoint: str, payload: Mapping[str, object]) -> PublishResult:
        if not endpoint.endswith(self.ALLOWED_ENDPOINTS_SUFFIX):
            raise PermissionError(
                f"publisher refuses endpoint {endpoint!r}; only issue/note creation is allowed"
            )
        url = self._base_url + endpoint
        body = json.dumps(dict(payload)).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310
            url,
            data=body,
            method="POST",
            headers={"PRIVATE-TOKEN": self._token, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8", "replace") or "null")
                return PublishResult(True, resp.status, endpoint, data)
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", "replace") if exc.fp else ""
            return PublishResult(False, exc.code, endpoint, None, text[:400])
        except urllib.error.URLError as exc:
            return PublishResult(False, None, endpoint, None, str(exc.reason))

    def create_issue(
        self, project_id: int, *, title: str, description: str, labels: str | None = None
    ) -> PublishResult:
        payload: dict[str, object] = {"title": title, "description": description}
        if labels:
            payload["labels"] = labels
        return self._post(f"/projects/{project_id}/issues", payload)

    def create_issue_note(self, project_id: int, issue_iid: int, *, body: str) -> PublishResult:
        return self._post(f"/projects/{project_id}/issues/{issue_iid}/notes", {"body": body})
