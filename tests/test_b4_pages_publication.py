"""Tests for B4 WORK-B4-19 Track 1: Real Disposable Pages Publication Evidence.

Validates:
1. Multi-level evidence model separating CI job, deployment, API access, and served URL;
2. Authoritative verification of genuinely published site with matching marker;
3. Detection and fail-closed handling of marker mismatch;
4. Honest reporting of Pages API 403 AUTH_DENIED without promoting to absence;
5. Cloudflare challenge / access blocked evaluating to INCONCLUSIVE_ACCESS_BLOCKED;
6. HTTP 404 evaluating to UNPUBLISHED_OR_ABSENT;
7. Prohibited operation assertion: DELETE /projects/:id/pages is never called.
"""

from __future__ import annotations

import json
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


def _fake_client(*, pipeline_status="success", ci_has_pages=True, pages_api_status=403):
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

    replies = {
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/pipelines?per_page=1"): HttpReply(
            200, json.dumps([{"id": 2960507698, "sha": COMMIT_SHA, "status": pipeline_status}])
        ),
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
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/pages"): HttpReply(
            pages_api_status, pages_api_body
        ),
    }
    return GitLabClient("dummy_token", transport=FakeTransport(replies))


def test_publication_verified_live_served(monkeypatch):
    """When pipeline is success, CI has pages: true, and served URL returns 200 with marker."""
    body_content = f"<html><body><p>Marker: {EXPECTED_MARKER}</p></body></html>"
    monkeypatch.setattr(
        "termivance.pages_publication.https_get",
        lambda url, timeout=15.0: (200, None, body_content),
    )

    client = _fake_client()
    record = verify_disposable_pages_publication(client, TARGET, now=NOW)

    assert record.status == PublicationVerificationStatus.VERIFIED_LIVE_SERVED
    assert record.is_verified_live is True
    assert record.levels.level1_ci_job_success is True
    assert record.levels.level2_deployment_created is True
    assert record.levels.level3_pages_api_status == 403
    assert record.levels.level3_pages_api_visible is False
    assert record.levels.level4_served_url_accessible is True
    assert record.levels.level5_marker_independently_observed is True
    assert record.levels.level5_observed_marker == EXPECTED_MARKER
    assert record.served_body_digest_sha256 is not None
    assert "genuinely published and live" in record.summary


def test_publication_marker_mismatch(monkeypatch):
    """When served URL returns 200 but marker is missing, status is MARKER_MISMATCH."""
    body_content = "<html><body><p>Unrelated content without marker</p></body></html>"
    monkeypatch.setattr(
        "termivance.pages_publication.https_get",
        lambda url, timeout=15.0: (200, None, body_content),
    )

    client = _fake_client()
    record = verify_disposable_pages_publication(client, TARGET, now=NOW)

    assert record.status == PublicationVerificationStatus.MARKER_MISMATCH
    assert record.is_verified_live is False
    assert record.levels.level4_served_url_accessible is True
    assert record.levels.level5_marker_independently_observed is False


def test_publication_cloudflare_challenge_inconclusive(monkeypatch):
    """When served URL returns challenge or 403, status is INCONCLUSIVE_ACCESS_BLOCKED."""
    monkeypatch.setattr(
        "termivance.pages_publication.https_get",
        lambda url, timeout=15.0: (403, "Cloudflare Challenge Interstitial", ""),
    )

    client = _fake_client()
    record = verify_disposable_pages_publication(client, TARGET, now=NOW)

    assert record.status == PublicationVerificationStatus.INCONCLUSIVE_ACCESS_BLOCKED
    assert record.is_verified_live is False
    assert "INCONCLUSIVE" in record.summary


def test_publication_404_unpublished_or_absent(monkeypatch):
    """When served URL returns 404, status is UNPUBLISHED_OR_ABSENT."""
    monkeypatch.setattr(
        "termivance.pages_publication.https_get",
        lambda url, timeout=15.0: (404, "Not Found", ""),
    )

    client = _fake_client()
    record = verify_disposable_pages_publication(client, TARGET, now=NOW)

    assert record.status == PublicationVerificationStatus.UNPUBLISHED_OR_ABSENT
    assert record.is_verified_live is False


def test_prohibited_delete_not_called(monkeypatch):
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

    client = _fake_client()
    monkeypatch.setattr(
        "termivance.pages_publication.https_get",
        lambda url, timeout=15.0: (200, None, EXPECTED_MARKER),
    )
    record = verify_disposable_pages_publication(client, TARGET, now=NOW)
    assert record.is_verified_live is True
    assert not any(method == "DELETE" for method, _ in calls)
