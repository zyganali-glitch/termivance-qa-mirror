#!/usr/bin/env python3
"""Deterministic self-test for the QA observer's fail-closed semantics.

Runs entirely offline against a synthetic GitLab surface. It proves that the
observer can never report a QA success when a mandatory public identity, the
mirror SHA or the current-pipeline binding is missing or wrong.

Usage:  python3 observer/selftest.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import observe  # noqa: E402

NOW_SHA = "a" * 40
OTHER_SHA = "b" * 40
PIPELINE_ID = 4242
JOB_ID = 77


def fake_surface(project_id: int = 87779099, disposable_id: int = 87785099) -> dict[str, str]:
    return {
        f"/projects/{project_id}": json.dumps(
            {"id": project_id, "path_with_namespace": "grp/canonical", "visibility": "public"}
        ),
        f"/projects/{project_id}/repository/branches/main": json.dumps(
            {"name": "main", "commit": {"id": NOW_SHA}}
        ),
        f"/projects/{project_id}/repository/files/.gitlab-ci.yml/raw?ref=main": "stages:\n  - verify\n",
        f"/projects/{project_id}/pipelines?per_page=3&order_by=id&sort=desc": json.dumps(
            [{"id": PIPELINE_ID, "sha": NOW_SHA, "status": "success"}]
        ),
        f"/projects/{project_id}/pipelines/{PIPELINE_ID}": json.dumps(
            {"id": PIPELINE_ID, "sha": NOW_SHA, "status": "success", "ref": "main"}
        ),
        f"/projects/{project_id}/pipelines/{PIPELINE_ID}/jobs": json.dumps(
            [
                {
                    "id": JOB_ID,
                    "name": "verification",
                    "stage": "verify",
                    "status": "success",
                    "allow_failure": False,
                    "user": {"name": "Some Person", "username": "person"},
                }
            ]
        ),
        f"/projects/{project_id}/jobs/{JOB_ID}/trace": "trace is not public",
        f"/projects/{project_id}/issues?per_page=20": json.dumps([]),
        f"/projects/{project_id}/pages": json.dumps({"url": "https://x.example/"}),
        f"/projects/{project_id}/environments": json.dumps([]),
        f"/projects/{project_id}/duo_workflows": json.dumps([]),
        f"/projects/{disposable_id}": json.dumps(
            {"id": disposable_id, "path_with_namespace": "grp/disposable"}
        ),
        f"/projects/{disposable_id}/repository/branches/main": json.dumps(
            {"name": "main", "commit": {"id": NOW_SHA}}
        ),
        f"/projects/{disposable_id}/pipelines?per_page=3&order_by=id&sort=desc": json.dumps([]),
        f"/projects/{disposable_id}/pages": json.dumps({"url": "https://d.example/"}),
        f"/projects/{disposable_id}/environments": json.dumps([]),
    }


def make_http(surface: dict[str, str], *, missing: set[str] | None = None):  # type: ignore[no-untyped-def]
    missing = missing or set()

    def http_get(base: str, endpoint: str, timeout: float = 25.0) -> dict[str, object]:
        for key, body in surface.items():
            if endpoint == key:
                if endpoint in missing:
                    return {"status": 404, "body": '{"message":"404 Not Found"}', "error": "HTTP 404"}
                if endpoint.endswith(".gitlab-ci.yml/raw?ref=main"):
                    return {"status": 200, "body": body, "error": None}
                status = 401 if endpoint.endswith("/trace") else 200
                if status == 401:
                    return {"status": 401, "body": '{"message":"401 Unauthorized"}', "error": "HTTP 401"}
                return {"status": 200, "body": body, "error": None}
        return {"status": 404, "body": '{"message":"404 Not Found"}', "error": "HTTP 404"}

    return http_get


def write_targets(tmp: str) -> str:
    path = os.path.join(tmp, "targets.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "gitlab_base": "https://example.invalid/api/v4",
                "canonical": {
                    "project_id": 87779099,
                    "source_files": ["src/example.py"],
                },
                "disposable": {"project_id": 87785099},
            },
            handle,
        )
    return path


def run_case(
    name: str,
    *,
    mirror_sha: str,
    surface: dict[str, str] | None = None,
    missing: set[str] | None = None,
) -> tuple[str, dict[str, object]]:
    surface = surface or fake_surface()
    surface = {**surface, "/projects/87779099/repository/files/src%2Fexample.py/raw?ref=" + NOW_SHA: "x = 1\n"}
    with tempfile.TemporaryDirectory() as tmp:
        targets = write_targets(tmp)
        os.environ["MIRROR_SHA"] = mirror_sha
        os.environ["GITHUB_RUN_ID"] = "selftest"
        original = observe.http_get
        observe.http_get = make_http(surface, missing=missing)  # type: ignore[assignment]
        try:
            rc = observe.run(types.SimpleNamespace(targets=targets, out=os.path.join(tmp, "evidence")))
            with open(os.path.join(tmp, "evidence", "latest", "manifest.json"), encoding="utf-8") as fh:
                manifest = json.load(fh)
        finally:
            observe.http_get = original  # type: ignore[assignment]
    return f"rc={rc} status={manifest['qa_status']}", manifest


def main() -> int:
    failures: list[str] = []

    label, manifest = run_case("pass", mirror_sha=NOW_SHA)
    print("synced-and-complete:", label)
    if manifest["qa_status"] != "PASS" or "rc=0" not in label:
        failures.append("a fully observed, in-sync run must pass")
    binding = manifest["current_pipeline_binding"]
    if binding["match"] is not True:
        failures.append("pipeline commit binding must match the live main commit")
    if binding["job_trace"] != "NOT_OBSERVED":
        failures.append("a 401 job trace must be reported as NOT_OBSERVED")
    serialized = json.dumps(manifest)
    if "Some Person" in serialized:
        failures.append("personal names must be redacted from published evidence")
    if binding["jobs"] and binding["jobs"][0]["name"] != "verification":
        failures.append("CI job names must survive sanitization")

    label, manifest = run_case("drift", mirror_sha=OTHER_SHA)
    print("drift:", label)
    if manifest["qa_status"] != "NOT_VERIFIED" or "rc=1" not in label:
        failures.append("mirror drift must never report QA success")

    label, manifest = run_case("no-mirror", mirror_sha="")
    print("unknown-mirror:", label)
    if manifest["qa_status"] != "NOT_VERIFIED" or "rc=1" not in label:
        failures.append("an unknown mirror SHA must never report QA success")

    label, _ = run_case(
        "missing-mandatory",
        mirror_sha=NOW_SHA,
        missing={"/projects/87779099/pipelines?per_page=3&order_by=id&sort=desc"},
    )
    print("missing-mandatory-pipeline:", label)
    if "status=NOT_VERIFIED" not in label or "rc=1" not in label:
        failures.append("an unobserved mandatory endpoint must never report QA success")

    label, _ = run_case(
        "missing-canonical",
        mirror_sha=NOW_SHA,
        surface=fake_surface(project_id=1),
    )
    print("absent-canonical-source:", label)
    if "status=NOT_VERIFIED" not in label or "rc=1" not in label:
        failures.append("an absent canonical source must never report QA success")

    if failures:
        print("\nSELFTEST FAILED")
        for item in failures:
            print(" -", item)
        return 1
    print("\nSELFTEST PASSED (fail-closed semantics verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
