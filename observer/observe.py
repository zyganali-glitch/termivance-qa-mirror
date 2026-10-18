#!/usr/bin/env python3
"""Termivance independent GitLab observer (GitHub Actions).

This script is part of the *non-canonical* QA bridge. It is NOT the Termivance
product and it never mutates anything. On every run it:

* contacts real, public GitLab REST API endpoints with its own read-only,
  unauthenticated network calls (it never trusts executor-authored JSON);
* preserves the sanitized original provider responses (redacted fields are
  listed in the manifest) together with HTTP method, status, acquisition
  timestamp, exact resource identifiers, artifact digest and workflow run id;
* compares the live GitLab ``main`` commit to the GitHub ``gitlab-main`` mirror
  branch and reports any divergence as DRIFT;
* classifies every observation honestly.

Provenance classifications (distinct meanings, never interchangeable):

``LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS``
    A successful read-only GitLab API response observed by this run.
``RECORDED_LIVE``
    An archived observation; it is a record, not a fresh live read.
``FIXTURE``
    Synthetic data; never provider evidence.
``NOT_OBSERVED``
    The endpoint was not successfully observed (403/401/timeout/other). The real
    status/error is preserved; nothing is fabricated.

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime

DEFAULT_BASE = "https://gitlab.com/api/v4"

# Keys whose values may contain personal data or secrets and must never be
# published in a public repository. Redaction is by exact key name (case-folded).
SENSITIVE_KEYS = frozenset(
    {
        "email",
        "public_email",
        "private_email",
        "commit_email",
        "author_email",
        "notification_email",
        "avatar_url",
        "name",  # keep usernames, drop human names
        "token",
        "runners_token",
        "pipeline_token",
        "job_token",
        "private_token",
        "ssh_url_to_repo",
        "http_url_to_repo",
        "ci_config_path",
    }
)

REDACTED = "[REDACTED]"


def utcnow() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sanitize(value: object) -> object:
    """Recursively redact sensitive keys; preserves structure and order."""
    if isinstance(value, dict):
        return {
            key: (REDACTED if str(key).lower() in SENSITIVE_KEYS else sanitize(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def redacted_keys(value: object, found: set[str] | None = None) -> set[str]:
    found = found if found is not None else set()
    if isinstance(value, dict):
        for key, val in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                found.add(str(key))
            redacted_keys(val, found)
    elif isinstance(value, list):
        for item in value:
            redacted_keys(item, found)
    return found


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Probe:
    """One read-only observation of one GitLab resource."""

    def __init__(self, name: str, endpoint: str, http: dict[str, object]) -> None:
        self.name = name
        self.endpoint = endpoint
        self.http = http

    @property
    def ok(self) -> bool:
        return self.http.get("status") is not None and 200 <= int(self.http["status"]) < 300

    @property
    def classification(self) -> str:
        return (
            "LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS" if self.ok else "NOT_OBSERVED"
        )


def http_get(base: str, endpoint: str, timeout: float = 25.0) -> dict[str, object]:
    """One unauthenticated, read-only GET. Never sends credentials."""
    url = endpoint if endpoint.startswith("http") else base + endpoint
    request = urllib.request.Request(
        url, method="GET", headers={"User-Agent": "termivance-qa-observer", "Accept": "*/*"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", "replace")
            return {"status": resp.status, "body": body, "error": None}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return {"status": exc.code, "body": body, "error": f"HTTP {exc.code}"}
    except urllib.error.URLError as exc:
        return {"status": None, "body": "", "error": f"network error: {exc.reason}"}
    except Exception as exc:  # noqa: BLE001
        return {"status": None, "body": "", "error": f"error: {exc}"}


def parse_body(body: str) -> object:
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"_non_json_body_preview": body[:2000]}


def build_probe(name: str, base: str, endpoint: str) -> Probe:
    return Probe(name, endpoint, http_get(base, endpoint))


def probe_summary(probe: Probe) -> dict[str, object]:
    """Extract a small, deterministic set of facts from a successful probe."""
    data = parse_body(str(probe.http.get("body") or ""))
    summary: dict[str, object] = {}
    if isinstance(data, dict):
        for key in (
            "id",
            "iid",
            "path_with_namespace",
            "visibility",
            "default_branch",
            "name",
            "status",
            "ref",
            "sha",
            "message",
            "web_url",
            "url",
            "provider",
            "created_at",
            "updated_at",
            "active",
            "has_pages",
        ):
            if key in data and str(key).lower() not in SENSITIVE_KEYS:
                summary[key] = data[key]
        if "commit" in data and isinstance(data["commit"], dict):
            summary["commit_id"] = data["commit"].get("id")
    elif isinstance(data, list):
        summary["count"] = len(data)
        summary["first_id"] = data[0].get("id") if data and isinstance(data[0], dict) else None
    return summary


def write_json(path: str, payload: object) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def run(args: argparse.Namespace) -> int:
    with open(args.targets, encoding="utf-8") as handle:
        targets = json.load(handle)

    base = str(targets.get("gitlab_base", DEFAULT_BASE))
    project_id = int(targets["canonical"]["project_id"])
    disposable_id = int(targets["disposable"]["project_id"])
    b2_pipeline_id = targets["canonical"].get("b2_pipeline_id")
    b2_commit = targets["canonical"].get("b2_commit")
    b2_issue_iid = targets["canonical"].get("b2_issue_iid")

    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "zyganali-glitch/termivance-qa-mirror")
    run_url = f"{server}/{repo}/actions/runs/{run_id}"
    mirror_sha = os.environ.get("MIRROR_SHA", "").strip()

    out_dir = os.path.join(args.out, "latest")
    os.makedirs(out_dir, exist_ok=True)

    endpoints: list[tuple[str, str]] = [
        ("canonical_project", f"/projects/{project_id}"),
        ("canonical_main_branch", f"/projects/{project_id}/repository/branches/main"),
        ("canonical_tree", f"/projects/{project_id}/repository/tree?ref=main&per_page=100"),
        ("canonical_pipelines", f"/projects/{project_id}/pipelines?per_page=10"),
        ("canonical_issues", f"/projects/{project_id}/issues?per_page=20"),
        ("canonical_issue_b2", f"/projects/{project_id}/issues/{b2_issue_iid}")
        if b2_issue_iid
        else None,
        ("canonical_issue_b2_notes", f"/projects/{project_id}/issues/{b2_issue_iid}/notes")
        if b2_issue_iid
        else None,
        ("canonical_pages", f"/projects/{project_id}/pages"),
        ("canonical_environments", f"/projects/{project_id}/environments"),
        ("duo_workflows_probe", f"/projects/{project_id}/duo_workflows"),
        ("disposable_project", f"/projects/{disposable_id}"),
        ("disposable_main_branch", f"/projects/{disposable_id}/repository/branches/main"),
        ("disposable_pipelines", f"/projects/{disposable_id}/pipelines?per_page=5"),
        ("disposable_pages", f"/projects/{disposable_id}/pages"),
        ("disposable_environments", f"/projects/{disposable_id}/environments"),
    ]
    if b2_commit:
        endpoints.append(("canonical_b2_commit", f"/projects/{project_id}/repository/commits/{b2_commit}"))
    if b2_pipeline_id:
        endpoints.append(("canonical_b2_pipeline", f"/projects/{project_id}/pipelines/{b2_pipeline_id}"))
        endpoints.append(
            ("canonical_b2_pipeline_jobs", f"/projects/{project_id}/pipelines/{b2_pipeline_id}/jobs")
        )

    manifest_entries: list[dict[str, object]] = []
    for item in endpoints:
        if item is None:
            continue
        name, endpoint = item  # type: ignore[misc]
        probe = build_probe(name, base, endpoint)
        raw = parse_body(str(probe.http.get("body") or ""))
        sanitized = sanitize(raw)
        artifact = {
            "name": name,
            "endpoint": endpoint,
            "method": "GET",
            "http_status": probe.http.get("status"),
            "http_error": probe.http.get("error"),
            "acquired_at_utc": utcnow(),
            "classification": probe.classification,
            "limitations": (
                "public unauthenticated read"
                if probe.ok
                else "endpoint not observed with public read access; real status preserved"
            ),
            "redacted_keys": sorted(redacted_keys(raw)),
            "sanitized_body": sanitized,
        }
        artifact_text = json.dumps(artifact, indent=2, sort_keys=True)
        digest = sha256_text(artifact_text)
        write_json(os.path.join(out_dir, f"{name}.json"), {**artifact, "artifact_sha256": digest})

        manifest_entries.append(
            {
                "name": name,
                "endpoint": endpoint,
                "method": "GET",
                "http_status": probe.http.get("status"),
                "observed_at_utc": artifact["acquired_at_utc"],
                "classification": probe.classification,
                "artifact_sha256": digest,
                "summary": probe_summary(probe),
            }
        )

    # --- drift analysis -------------------------------------------------------
    live_main = next(
        (e for e in manifest_entries if e["name"] == "canonical_main_branch"), None
    )
    live_main_sha = None
    if live_main and live_main["http_status"] == 200:
        summary = live_main.get("summary") or {}
        live_main_sha = summary.get("commit_id") or summary.get("sha")

    drift = {
        "live_gitlab_main_sha": live_main_sha,
        "github_gitlab_main_mirror_sha": mirror_sha or None,
        "status": "UNKNOWN",
        "detail": "",
    }
    if live_main_sha is None:
        drift["status"] = "NOT_OBSERVED"
        drift["detail"] = "could not read live GitLab main branch with public access"
    elif not mirror_sha:
        drift["status"] = "NO_MIRROR"
        drift["detail"] = "no gitlab-main mirror SHA was provided to this run"
    elif live_main_sha == mirror_sha:
        drift["status"] = "IN_SYNC"
        drift["detail"] = "GitHub gitlab-main mirror matches the live GitLab main commit exactly"
    else:
        drift["status"] = "DRIFT"
        drift["detail"] = "mirror and live GitLab main differ; mirror is stale or divergent"

    b2_pipeline = next(
        (e for e in manifest_entries if e["name"] == "canonical_b2_pipeline"), None
    )
    b2_check = {"expected_sha": b2_commit, "observed_sha": None, "match": None}
    if b2_pipeline and b2_pipeline["http_status"] == 200:
        b2_check["observed_sha"] = (b2_pipeline.get("summary") or {}).get("sha")
        b2_check["match"] = b2_check["observed_sha"] == b2_commit
    else:
        b2_check["match"] = None

    manifest = {
        "schema": "termivance.qa_observer_manifest/v1",
        "generated_at_utc": utcnow(),
        "workflow": {"run_id": run_id, "run_url": run_url, "repository": repo},
        "gitlab_base": base,
        "canonical_project_id": project_id,
        "disposable_project_id": disposable_id,
        "observations": manifest_entries,
        "drift": drift,
        "b2_pipeline_commit_binding": b2_check,
        "provenance_note": (
            "Each entry is an independent, read-only GitLab API observation made by this "
            "GitHub Actions run. NOT_OBSERVED entries preserve the real non-2xx status and "
            "make no claim. An archived observation is not perpetual proof of current state."
        ),
    }
    write_json(os.path.join(out_dir, "manifest.json"), manifest)

    # Rolling per-run copy for history.
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    write_json(os.path.join(args.out, "history", f"{stamp}-run{run_id}.json"), manifest)

    observed = sum(
        1 for e in manifest_entries if e["classification"].startswith("LIVE_GITLAB")
    )
    print(
        f"observer complete: {observed}/{len(manifest_entries)} live observations; "
        f"drift={drift['status']}"
    )
    return 0 if drift["status"] in {"IN_SYNC", "NO_MIRROR", "NOT_OBSERVED"} else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Termivance independent GitLab observer")
    parser.add_argument("--targets", default="observer/targets.json")
    parser.add_argument("--out", default="evidence")
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
