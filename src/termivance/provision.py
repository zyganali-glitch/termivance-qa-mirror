"""Disposable GitLab Pages project provisioning (reproducible, non-destructive).

Provisioning creates a *new*, clearly disposable project and a minimal static
Pages site. It never edits or deletes an existing project and it is separate
from the retirement engine: creating a project is never authorization to
unpublish it.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime

from termivance.gitlab_client import DEFAULT_BASE_URL

#: A unique, unmistakable marker written into the served page. It lets an
#: independent observer prove the exact site was published (and later gone).
SITE_MARKER = "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a"

_CI_YAML = """\
# DISPOSABLE B3 demonstration site. Published through GitLab CI/CD Pages.
stages:
  - build
  - deploy

build_site:
  stage: build
  image: alpine:3.20
  script:
    - mkdir -p public
    - cp site/index.html public/index.html
    - cp site/marker.txt public/marker.txt
  artifacts:
    paths:
      - public

# A deliberately arbitrary job name: Pages participation is configured with
# `pages: true`, not by naming the job "pages".
publish_site:
  stage: deploy
  image: alpine:3.20
  needs: ["build_site"]
  script:
    - echo "publishing disposable Pages site"
  pages: true
  artifacts:
    paths:
      - public
"""

_MARKER_TXT = SITE_MARKER + "\n"

_INDEX_HTML = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Termivance B3 disposable Pages demo</title>
  </head>
  <body>
    <h1>Disposable retirement demonstration</h1>
    <p>Unique marker: <code>{marker}</code></p>
    <p>
      This is a temporary, isolated GitLab Pages site created only to demonstrate
      a proof-bounded retirement. It is not the Termivance product.
    </p>
  </body>
</html>
"""


@dataclass(frozen=True, slots=True)
class ProvisionedProject:
    project_id: int
    full_path: str
    web_url: str
    visibility: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "full_path": self.full_path,
            "web_url": self.web_url,
            "visibility": self.visibility,
            "created_at": self.created_at,
        }


def site_files(marker: str = SITE_MARKER) -> dict[str, str]:
    """Return the disposable site's files as a path -> content mapping."""
    return {
        ".gitlab-ci.yml": _CI_YAML,
        "site/index.html": _INDEX_HTML.format(marker=marker),
        "site/marker.txt": marker + "\n",
    }


class ProvisionError(RuntimeError):
    """Raised when provisioning fails; no project is half-created silently."""


def create_disposable_project(
    token: str,
    *,
    namespace_id: int,
    name: str,
    path: str,
    description: str,
    visibility: str = "public",
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 60.0,
) -> ProvisionedProject:
    """Create exactly one new disposable project in an explicit namespace."""
    payload = {
        "name": name,
        "path": path,
        "namespace_id": namespace_id,
        "description": description,
        "visibility": visibility,
    }
    req = urllib.request.Request(  # noqa: S310
        base_url.rstrip("/") + "/projects",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace") if exc.fp else ""
        raise ProvisionError(f"project creation failed: HTTP {exc.code} {body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise ProvisionError(f"project creation failed: {exc.reason}") from exc
    if not isinstance(data, dict):
        raise ProvisionError("unexpected provisioning response")
    return ProvisionedProject(
        project_id=int(data["id"]),
        full_path=str(data["path_with_namespace"]),
        web_url=str(data["web_url"]),
        visibility=str(data.get("visibility")),
        created_at=str(data.get("created_at") or datetime.now(tz=UTC).isoformat()),
    )
