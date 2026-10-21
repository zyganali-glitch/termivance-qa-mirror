"""Tests for B4 WORK-B4-19 Track 1: Real Disposable Pages Publication Evidence.

Validates:
1. Multi-level evidence model separating CI job, deployment, API access, and served URL;
2. Authoritative verification of genuinely published site with matching marker;
3. Detection and fail-closed handling of marker mismatch (including repo source mismatch);
4. Honest reporting of Pages API 403 and Deployments API 403 without promoting to absence;
5. Separation of Level 1 (pipeline job query) and Level 2 (deployments query);
6. Target binding: non-disposable target projects refused with WRONG_TARGET_REFUSED;
7. Origin binding: non-HTTPS or untrusted hosts refused with UNTRUSTED_ORIGIN_REFUSED;
8. Cloudflare challenge / access blocked evaluating to INCONCLUSIVE_ACCESS_BLOCKED;
9. HTTP 404 evaluating to NOT_SERVED_AT_PROBED_URL;
10. Prohibited operation assertion: DELETE /projects/:id/pages is never called;
11. Injectable http_getter parameter for deterministic offline verification.
"""

from __future__ import annotations

import json
import urllib.parse
from datetime import UTC, datetime

import pytest
from conftest import FakeTransport

from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.pages_publication import (
    DISPOSABLE_PAGES_URL,
    DISPOSABLE_TARGET_PID,
    EXPECTED_MARKER,
    PublicationVerificationStatus,
    verify_disposable_pages_publication,
)
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 21, 12, 0, 0, tzinfo=UTC)
TARGET = TargetIdentity(
    DISPOSABLE_TARGET_PID,
    "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
    "GITLAB_PAGES_SITE",
)
COMMIT_SHA = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"


def _fake_client(
    *,
    pipeline_status="success",
    ci_has_pages=True,
    pages_api_status=403,
    deployments_api_status=403,
    jobs_api_status=200,
    job_status="success",
    repo_marker_present=True,
):
    ci_content = (
        ("create-pages:\n  stage: deploy\n  script:\n"
        "    - cp site/index.html public/index.html\n  pages: true\n")
        if ci_has_pages
        else "build:\n  stage: test\n  script:\n    - echo no pages\n"
    )
    pages_api_body = (
        json.dumps({"error": "Forbidden"})
        if pages_api_status == 403
        else json.dumps({"url": DISPOSABLE_PAGES_URL, "deployments": [{}]})
    )
    dep_api_body = (
        json.dumps({"error": "Forbidden"})
        if deployments_api_status == 403
        else json.dumps([{"id": 42, "created_at": "2026-10-21T10:00:00Z"}])
    )
    jobs_api_body = (
        json.dumps([{"name": "create-pages", "status": job_status, "stage": "deploy"}])
        if jobs_api_status == 200
        else json.dumps({"error": "Forbidden"})
    )
    marker_content = EXPECTED_MARKER if repo_marker_present else "DIFFERENT_MARKER"

    quoted_marker = urllib.parse.quote("site/marker.txt", safe="")
    quoted_index = urllib.parse.quote("site/index.html", safe="")

    replies = {
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/pipelines?per_page=1"): HttpReply(
            200, json.dumps([{"id": 2960507698, "sha": COMMIT_SHA, "status": pipeline_status}])
        ),
        (
            "GET",
            f"/projects/{DISPOSABLE_TARGET_PID}/pipelines/2960507698/jobs",
        ): HttpReply(jobs_api_status, jobs_api_body),
        (
            "GET",
            f"/projects/{DISPOSABLE_TARGET_PID}/repository/files/.gitlab-ci.yml/raw",
        ): HttpReply(200, ci_content),
        (
            "GET",
            f"/projects/{DISPOSABLE_TARGET_PID}/repository/files/.gitlab-ci.yml/raw?ref={COMMIT_SHA}",
        ): HttpReply(200, ci_content),
        (
            "GET",
            f"/projects/{DISPOSABLE_TARGET_PID}/repository/files/.gitlab-ci.yml/raw?ref=main",
        ): HttpReply(200, ci_content),
        (
            "GET",
            f"/projects/{DISPOSABLE_TARGET_PID}/repository/files/{quoted_marker}/raw?ref={COMMIT_SHA}",
        ): HttpReply(200, marker_content),
        (
            "GET",
            f"/projects/{DISPOSABLE_TARGET_PID}/repository/files/{quoted_index}/raw?ref={COMMIT_SHA}",
        ): HttpReply(200, f"<html><body>{marker_content}</body></html>"),
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/pages/deployments"): HttpReply(
            deployments_api_status, dep_api_body
        ),
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/deployments"): HttpReply(
            deployments_api_status, dep_api_body
        ),
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/pages"): HttpReply(
            pages_api_status, pages_api_body
        ),
    }
    return GitLabClient("dummy_token", transport=FakeTransport(replies))


def test_publication_verified_live_served():
    """When pipeline job succeeds, marker is verified live, and developer role API returns 403."""
    body_content = f"<html><body><p>Marker: {EXPECTED_MARKER}</p></body></html>"

    def mock_getter(url, timeout=15.0):
        return 200, None, body_content

    client = _fake_client(deployments_api_status=403)
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=mock_getter
    )

    assert record.status == PublicationVerificationStatus.VERIFIED_LIVE_SERVED
    assert record.is_verified_live is True
    assert record.levels.level1_ci_job_success is True
    assert record.levels.level1_ci_job_status == "success"
    # Level 2 is honest: Developer credentials return 403 AUTH_DENIED, NOT inferred True
    assert record.levels.level2_deployment_created is False
    assert record.levels.level2_deployment_status == "NOT_OBSERVED_AUTH_DENIED"
    assert record.levels.level3_pages_api_status == 403
    assert record.levels.level3_pages_api_visible is False
    assert record.levels.level4_served_url_accessible is True
    assert record.levels.level5_marker_independently_observed is True
    assert record.levels.level5_observed_marker == EXPECTED_MARKER
    assert record.served_body_digest_sha256 is not None
    assert "genuinely published and live" in record.summary


def test_publication_with_level2_deployment_visible():
    """When deployments API returns 200 with deployments, level2_deployment_created is True."""
    body_content = f"<html><body><p>Marker: {EXPECTED_MARKER}</p></body></html>"

    def mock_getter(url, timeout=15.0):
        return 200, None, body_content

    client = _fake_client(deployments_api_status=200)
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=mock_getter
    )

    assert record.levels.level2_deployment_created is True
    assert record.levels.level2_deployment_status == "DEPLOYMENTS_FOUND"


def test_publication_pipeline_success_but_pages_job_failed():
    """Overall pipeline succeeded, but create-pages job failed: Level 1 must report False."""
    body_content = f"<html><body><p>Marker: {EXPECTED_MARKER}</p></body></html>"

    def mock_getter(url, timeout=15.0):
        return 200, None, body_content

    client = _fake_client(job_status="failed")
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=mock_getter
    )

    assert record.levels.level1_ci_job_success is False
    assert record.levels.level1_ci_job_status == "failed"


def test_publication_wrong_target_refused():
    """Refuse any target project other than disposable demo 87785099."""
    client = _fake_client()
    canonical_target = TargetIdentity(87779099, "group/canonical", "GITLAB_PAGES_SITE")
    record = verify_disposable_pages_publication(client, canonical_target, now=NOW)

    assert record.status == PublicationVerificationStatus.WRONG_TARGET_REFUSED
    assert record.is_verified_live is False
    assert "WRONG_TARGET_REFUSED" in record.summary


def test_publication_untrusted_origin_refused():
    """Refuse non-HTTPS URLs or untrusted hostnames."""
    client = _fake_client()

    # Insecure HTTP
    rec1 = verify_disposable_pages_publication(
        client,
        TARGET,
        served_url="http://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/",
        now=NOW,
    )
    assert rec1.status == PublicationVerificationStatus.UNTRUSTED_ORIGIN_REFUSED

    # Untrusted domain
    rec2 = verify_disposable_pages_publication(
        client, TARGET, served_url="https://attacker.evil.com/fake-pages/", now=NOW
    )
    assert rec2.status == PublicationVerificationStatus.UNTRUSTED_ORIGIN_REFUSED


def test_publication_source_marker_mismatch():
    """When served body has marker, but repo source files do not, report MARKER_MISMATCH."""
    body_content = f"<html><body><p>Marker: {EXPECTED_MARKER}</p></body></html>"

    def mock_getter(url, timeout=15.0):
        return 200, None, body_content

    client = _fake_client(repo_marker_present=False)
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=mock_getter
    )

    assert record.status == PublicationVerificationStatus.MARKER_MISMATCH
    assert record.is_verified_live is False
    assert "not corroborated in repo files" in record.summary


def test_publication_marker_mismatch_in_body():
    """When served URL returns 200 but marker is missing, status is MARKER_MISMATCH."""
    body_content = "<html><body><p>Unrelated content without marker</p></body></html>"

    def mock_getter(url, timeout=15.0):
        return 200, None, body_content

    client = _fake_client()
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=mock_getter
    )

    assert record.status == PublicationVerificationStatus.MARKER_MISMATCH
    assert record.is_verified_live is False
    assert record.levels.level4_served_url_accessible is True
    assert record.levels.level5_marker_independently_observed is False


def test_publication_cloudflare_challenge_inconclusive():
    """When served URL returns challenge or 403, status is INCONCLUSIVE_ACCESS_BLOCKED."""

    def mock_getter(url, timeout=15.0):
        return 403, "Cloudflare Challenge Interstitial", ""

    client = _fake_client()
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=mock_getter
    )

    assert record.status == PublicationVerificationStatus.INCONCLUSIVE_ACCESS_BLOCKED
    assert record.is_verified_live is False
    assert "INCONCLUSIVE" in record.summary


def test_publication_404_not_served_at_probed_url():
    """When served URL returns 404, status is NOT_SERVED_AT_PROBED_URL."""

    def mock_getter(url, timeout=15.0):
        return 404, "Not Found", ""

    client = _fake_client()
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=mock_getter
    )

    assert record.status == PublicationVerificationStatus.NOT_SERVED_AT_PROBED_URL
    assert record.is_verified_live is False
    assert "not proof of universal absence" in record.summary


def test_prohibited_delete_not_called():
    """Safety assertion: verify_disposable_pages_publication never issues DELETE."""
    calls = []
    fake_transport = FakeTransport({})
    original_request = fake_transport.request

    def tracking_request(method, endpoint, **kwargs):
        calls.append((method, endpoint))
        if method == "DELETE":
            pytest.fail(f"PROHIBITED MUTATION DISPATCHED: {method} {endpoint}")
        return original_request(method, endpoint, **kwargs)

    fake_transport.request = tracking_request  # type: ignore[method-assign]

    def mock_getter(url, timeout=15.0):
        return 200, None, EXPECTED_MARKER

    client = _fake_client()
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=mock_getter
    )
    assert record.is_verified_live is True
    assert not any(method == "DELETE" for method, _ in calls)
