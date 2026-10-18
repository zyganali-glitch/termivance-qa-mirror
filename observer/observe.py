#!/usr/bin/env python3
"""Termivance independent GitLab observer (GitHub Actions).

This script is part of the *non-canonical* QA bridge. It is NOT the Termivance
product and it never mutates anything: every GitLab interaction is an
unauthenticated, read-only GET. On every run it:

* contacts real, public GitLab REST API endpoints with its own network calls (it
  never trusts executor-authored JSON);
* preserves the sanitized original provider responses together with HTTP method,
  status, acquisition timestamp, exact resource identifiers and artifact digest;
* reads the **current final pipeline**, its commit binding, its jobs and the
  verification job, independently of any recorded B2 history;
* reads the exact canonical source files at the observed live commit and records
  a SHA-256 manifest of them, plus a SHA-256 manifest over every artifact;
* compares the live GitLab ``main`` commit to the GitHub ``gitlab-main`` mirror
  branch and reports any divergence as DRIFT;
* fails closed: a QA success is impossible when the mandatory public identity,
  mirror or pipeline verification cannot be observed.

Provenance classifications (distinct meanings, never interchangeable):

``LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS``
    A successful read-only GitLab API response observed by this run.
``RECORDED_LIVE``
    An archived observation; it is a record, not a fresh live read.
``FIXTURE``
    Synthetic data; never provider evidence.
``NOT_OBSERVED``
    The endpoint was not successfully observed (401/403/404/timeout/other). The
    real status/error is preserved; nothing is fabricated.

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
import urllib.parse
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
        "committer_email",
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
        "author",
        "committer",
        "user",
    }
)

REDACTED = "[REDACTED]"

#: Endpoints whose successful observation is required for any QA success claim.
MANDATORY = (
    "canonical_project",
    "canonical_main_branch",
    "canonical_latest_pipelines",
    "canonical_latest_pipeline_detail",
    "canonical_latest_pipeline_jobs",
    "canonical_repo_file_ci",
    "disposable_project",
)

MAX_BODY_BYTES = 200_000


def utcnow() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def scrub(text: str) -> str:
    """Best-effort removal of anything that looks like a credential or e-mail."""
    text = re.sub(r"glpat-[A-Za-z0-9_\-]{10,}", "[REDACTED-TOKEN]", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[REDACTED-EMAIL]", text)
    return text


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
        status = self.http.get("status")
        return status is not None and 200 <= int(status) < 300  # type: ignore[arg-type]

    @property
    def classification(self) -> str:
        return "LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS" if self.ok else "NOT_OBSERVED"

    @property
    def body(self) -> str:
        return str(self.http.get("body") or "")


def http_get(base: str, endpoint: str, timeout: float = 25.0) -> dict[str, object]:
    """One unauthenticated, read-only GET. Never sends credentials."""
    url = endpoint if endpoint.startswith("http") else base + endpoint
    request = urllib.request.Request(
        url, method="GET", headers={"User-Agent": "termivance-qa-observer", "Accept": "*/*"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read(MAX_BODY_BYTES)
            return {"status": resp.status, "body": raw.decode("utf-8", "replace"), "error": None}
    except urllib.error.HTTPError as exc:
        body = exc.read(MAX_BODY_BYTES).decode("utf-8", "replace") if exc.fp else ""
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
        return None


def build_probe(name: str, base: str, endpoint: str) -> Probe:
    return Probe(name, endpoint, http_get(base, endpoint))


def probe_summary(probe: Probe) -> dict[str, object]:
    """Extract a small, deterministic set of facts from a successful probe."""
    data = parse_body(probe.body)
    summary: dict[str, object] = {}
    if isinstance(data, dict):
        for key in (
            "id",
            "iid",
            "path_with_namespace",
            "visibility",
            "default_branch",
            "status",
            "ref",
            "sha",
            "source",
            "created_at",
            "updated_at",
            "duration",
            "stage",
            "allow_failure",
            "has_pages",
            "fixture",
        ):
            if key in data and str(key).lower() not in SENSITIVE_KEYS:
                summary[key] = data[key]
        if isinstance(data.get("commit"), dict):
            summary["commit_id"] = data["commit"].get("id")
    elif isinstance(data, list):
        summary["count"] = len(data)
        if data and isinstance(data[0], dict):
            first = data[0]
            if str(first.get("id")).isdigit():
                summary["first_id"] = first.get("id")
            if first.get("sha"):
                summary["first_sha"] = first.get("sha")
            if first.get("status"):
                summary["first_status"] = first.get("status")
    return summary


def write_json(path: str, payload: object) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


class Observer:
    def __init__(self, base: str, out_dir: str) -> None:
        self.base = base
        self.out_dir = out_dir
        self.entries: list[dict[str, object]] = []
        self.artifacts: dict[str, str] = {}
        self.extracted: dict[str, object] = {}

    def probe(self, name, endpoint, *, raw: bool = False, extract=None):  # type: ignore[no-untyped-def]
        probe = build_probe(name, self.base, endpoint)
        body = probe.body
        parsed = None if raw else parse_body(body)
        artifact: dict[str, object] = {
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
            "redacted_keys": sorted(redacted_keys(parsed)),
        }
        if extract is not None and probe.ok:
            value = extract(parsed)
            self.extracted[name] = value
            artifact["extracted"] = sanitize(value)
        if raw:
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            artifact["body_sha256"] = digest
        else:
            artifact["sanitized_body"] = sanitize(parsed) if parsed is not None else scrub(body)[:4000]
            digest = sha256_text(json.dumps(artifact, indent=2, sort_keys=True))
        write_json(
            os.path.join(self.out_dir, f"{name}.json"), {**artifact, "artifact_sha256": digest}
        )
        self.artifacts[name] = digest
        self.entries.append(
            {
                "name": name,
                "endpoint": endpoint,
                "method": "GET",
                "http_status": probe.http.get("status"),
                "http_error": probe.http.get("error"),
                "observed_at_utc": artifact["acquired_at_utc"],
                "classification": probe.classification,
                "artifact_sha256": digest,
                "summary": probe_summary(probe),
            }
        )
        return probe

    def entry(self, name: str) -> dict[str, object] | None:
        return next((e for e in self.entries if e["name"] == name), None)

    def live(self, name: str) -> bool:
        entry = self.entry(name)
        return bool(entry and str(entry["classification"]).startswith("LIVE_GITLAB"))

    def summary(self, name: str) -> dict[str, object]:
        entry = self.entry(name) or {}
        value = entry.get("summary")
        return value if isinstance(value, dict) else {}


def run(args: argparse.Namespace) -> int:  # noqa: C901 - intentionally linear
    with open(args.targets, encoding="utf-8") as handle:
        targets = json.load(handle)

    base = str(targets.get("gitlab_base", DEFAULT_BASE))
    canonical = targets["canonical"]
    disposable = targets["disposable"]
    project_id = int(canonical["project_id"])
    disposable_id = int(disposable["project_id"])
    b2_pipeline_id = canonical.get("b2_pipeline_id")
    b2_commit = canonical.get("b2_commit")
    b2_issue_iid = canonical.get("b2_issue_iid")
    b3_issue_iid = canonical.get("b3_issue_iid")
    source_files = [str(p) for p in canonical.get("source_files", [])]

    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "zyganali-glitch/termivance-qa-mirror")
    run_url = f"{server}/{repo}/actions/runs/{run_id}"
    mirror_sha = os.environ.get("MIRROR_SHA", "").strip()

    out_dir = os.path.join(args.out, "latest")
    os.makedirs(out_dir, exist_ok=True)
    observer = Observer(base, out_dir)

    # --- phase 1: stable, exact-identity endpoints ---------------------------
    for name, endpoint in [
        ("canonical_project", f"/projects/{project_id}"),
        ("canonical_main_branch", f"/projects/{project_id}/repository/branches/main"),
        ("canonical_repo_file_ci", f"/projects/{project_id}/repository/files/.gitlab-ci.yml/raw?ref=main"),
        ("canonical_latest_pipelines", f"/projects/{project_id}/pipelines?per_page=3&order_by=id&sort=desc"),
        ("canonical_issues", f"/projects/{project_id}/issues?per_page=20"),
        ("canonical_pages", f"/projects/{project_id}/pages"),
        ("canonical_environments", f"/projects/{project_id}/environments"),
        ("duo_workflows_probe", f"/projects/{project_id}/duo_workflows"),
        ("disposable_project", f"/projects/{disposable_id}"),
        ("disposable_main_branch", f"/projects/{disposable_id}/repository/branches/main"),
        ("disposable_pipelines", f"/projects/{disposable_id}/pipelines?per_page=3&order_by=id&sort=desc"),
        ("disposable_pages", f"/projects/{disposable_id}/pages"),
        ("disposable_environments", f"/projects/{disposable_id}/environments"),
    ]:
        observer.probe(name, endpoint)

    if b2_issue_iid:
        observer.probe("canonical_issue_b2", f"/projects/{project_id}/issues/{b2_issue_iid}")
        observer.probe(
            "canonical_issue_b2_notes", f"/projects/{project_id}/issues/{b2_issue_iid}/notes"
        )
    if b3_issue_iid:
        observer.probe("canonical_issue_b3", f"/projects/{project_id}/issues/{b3_issue_iid}")
        observer.probe(
            "canonical_issue_b3_notes", f"/projects/{project_id}/issues/{b3_issue_iid}/notes"
        )
    if b2_commit:
        observer.probe(
            "canonical_b2_commit", f"/projects/{project_id}/repository/commits/{b2_commit}"
        )
    if b2_pipeline_id:
        # Historical B2 reference only; never a substitute for the current pipeline.
        observer.probe(
            "canonical_b2_pipeline", f"/projects/{project_id}/pipelines/{b2_pipeline_id}"
        )

    # --- phase 2: live main commit -> exact source manifest -------------------
    main_summary = observer.summary("canonical_main_branch")
    live_main_sha = main_summary.get("commit_id") or main_summary.get("sha")
    live_main_sha = str(live_main_sha) if live_main_sha else None

    source_manifest: dict[str, object] = {"ref": live_main_sha, "files": {}, "combined_sha256": None}
    if live_main_sha and source_files:
        file_digests: dict[str, object] = {}
        for path in source_files:
            quoted = urllib.parse.quote(path, safe="")
            probe = observer.probe(
                f"source_{re.sub(r'[^A-Za-z0-9]+', '_', path).strip('_')}",
                f"/projects/{project_id}/repository/files/{quoted}/raw?ref={live_main_sha}",
                raw=True,
            )
            body = probe.body
            file_digests[path] = {
                "http_status": probe.http.get("status"),
                "classification": probe.classification,
                "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest() if probe.ok else None,
                "bytes": len(body.encode("utf-8")) if probe.ok else 0,
            }
        source_manifest = {
            "ref": live_main_sha,
            "files": file_digests,
            "combined_sha256": sha256_text(json.dumps(file_digests, sort_keys=True)),
        }

    # --- phase 3: current final pipeline, binding, jobs, trace ---------------
    latest_pipeline_id = None
    latest_pipelines = observer.summary("canonical_latest_pipelines")
    if observer.live("canonical_latest_pipelines"):
        latest_pipeline_id = latest_pipelines.get("first_id")

    pipeline_binding: dict[str, object] = {
        "pipeline_id": latest_pipeline_id,
        "pipeline_sha": None,
        "live_main_sha": live_main_sha,
        "status": None,
        "match": None,
        "jobs": [],
        "verification_job": None,
        "job_trace": "NOT_ATTEMPTED",
        "note": "",
    }
    if latest_pipeline_id:
        pid_str = str(latest_pipeline_id)
        observer.probe(
            "canonical_latest_pipeline_detail", f"/projects/{project_id}/pipelines/{pid_str}"
        )
        observer.probe(
            "canonical_latest_pipeline_jobs",
            f"/projects/{project_id}/pipelines/{pid_str}/jobs",
            extract=lambda data: [
                {
                    "id": j.get("id"),
                    "name": j.get("name"),
                    "stage": j.get("stage"),
                    "status": j.get("status"),
                    "allow_failure": j.get("allow_failure"),
                }
                for j in (data or [])
                if isinstance(j, dict)
            ],
        )
        detail = observer.summary("canonical_latest_pipeline_detail")
        pipeline_binding["pipeline_sha"] = detail.get("sha")
        pipeline_binding["status"] = detail.get("status")
        pipeline_binding["ref"] = detail.get("ref")
        pipeline_binding["match"] = (
            detail.get("sha") == live_main_sha if live_main_sha and detail.get("sha") else None
        )

        jobs_value = observer.extracted.get("canonical_latest_pipeline_jobs")
        jobs: list[dict[str, object]] = (
            [j for j in jobs_value if isinstance(j, dict)]
            if isinstance(jobs_value, list)
            else []
        )
        pipeline_binding["jobs"] = jobs
        verification = next(
            (j for j in jobs if j.get("name") == "verification"), jobs[0] if jobs else None
        )
        pipeline_binding["verification_job"] = verification
        if verification and verification.get("id"):
            job_id = str(verification["id"])
            trace = observer.probe(
                "canonical_verification_job_trace", f"/projects/{project_id}/jobs/{job_id}/trace",
                raw=True,
            )
            pipeline_binding["job_trace"] = trace.classification
            pipeline_binding["job_trace_http_status"] = trace.http.get("status")
            pipeline_binding["note"] = (
                "verification job trace observed read-only"
                if trace.ok
                else f"verification job trace not publicly readable (HTTP {trace.http.get('status')}); "
                "job status/stage/identity comes from the public jobs endpoint"
            )

    # --- phase 4: disposible Pages publication/receipt observables -----------
    disposable_state = {
        "project_observed": observer.live("disposable_project"),
        "pages_api_status": (observer.entry("disposable_pages") or {}).get("http_status"),
        "pages_api_classification": (observer.entry("disposable_pages") or {}).get("classification"),
        "latest_pipeline_id": observer.summary("disposable_pipelines").get("first_id"),
        "latest_pipeline_status": observer.summary("disposable_pipelines").get("first_status"),
        "note": (
            "A 403 on the Pages API means the observing identity cannot read Pages state; "
            "it is NOT evidence that a Pages site does not exist."
        ),
    }

    # --- drift ----------------------------------------------------------------
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

    # --- fail-closed QA status -----------------------------------------------
    failures: list[str] = []
    for name in MANDATORY:
        if not observer.live(name):
            status = (observer.entry(name) or {}).get("http_status")
            failures.append(f"mandatory endpoint {name} not observed (HTTP {status})")
    if live_main_sha is None:
        failures.append("live GitLab main commit could not be observed")
    if not mirror_sha:
        failures.append("mirror SHA unknown to this run")
    elif live_main_sha and live_main_sha != mirror_sha:
        failures.append("mirror SHA does not match the live GitLab main commit")
    if pipeline_binding["match"] is not True:
        failures.append("current final pipeline is not bound to the observed live main commit")

    qa_status = "PASS" if not failures else "NOT_VERIFIED"

    evidence_manifest_sha = sha256_text(json.dumps(observer.artifacts, sort_keys=True))

    manifest = {
        "schema": "termivance.qa_observer_manifest/v2",
        "generated_at_utc": utcnow(),
        "workflow": {"run_id": run_id, "run_url": run_url, "repository": repo},
        "gitlab_base": base,
        "canonical_project_id": project_id,
        "disposable_project_id": disposable_id,
        "qa_status": qa_status,
        "qa_failures": failures,
        "mandatory_endpoints": list(MANDATORY),
        "observations": observer.entries,
        "drift": drift,
        "current_pipeline_binding": pipeline_binding,
        "source_manifest_sha256": source_manifest,
        "evidence_manifest_sha256": {
            "algorithm": "sha256",
            "artifact_digests": observer.artifacts,
            "combined_sha256": evidence_manifest_sha,
        },
        "disposable_state": disposable_state,
        "b2_history_reference": {
            "commit": b2_commit,
            "pipeline_id": b2_pipeline_id,
            "issue_iid": b2_issue_iid,
            "note": "Historical B2 reference retained for audit; it is never used as current B3 evidence.",
        },
        "provenance_note": (
            "Each entry is an independent, read-only GitLab API observation made by this "
            "GitHub Actions run. NOT_OBSERVED entries preserve the real non-2xx status and make "
            "no claim. An archived observation is not perpetual proof of current state. A QA "
            "success requires every mandatory public identity, mirror and pipeline check to pass."
        ),
    }
    write_json(os.path.join(out_dir, "manifest.json"), manifest)

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    write_json(os.path.join(args.out, "history", f"{stamp}-run{run_id}.json"), manifest)

    observed = sum(
        1 for e in observer.entries if str(e["classification"]).startswith("LIVE_GITLAB")
    )
    print(
        f"observer complete: {observed}/{len(observer.entries)} live observations; "
        f"drift={drift['status']}; qa_status={qa_status}"
    )
    for failure in failures:
        print(f"  FAIL: {failure}")
    return 0 if qa_status == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Termivance independent GitLab observer")
    parser.add_argument("--targets", default="observer/targets.json")
    parser.add_argument("--out", default="evidence")
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
