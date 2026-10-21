"""Tests for the disposable Pages publication evidence (5-level model).

Validates:
1. Multi-level evidence model separating CI job, Pages deployment, API access,
   and served URL;
2. Level 1 honesty: pipeline SUCCESS is NEVER inferred as a successful Pages
   job when the jobs API is inaccessible; unrelated deploy-stage jobs and
   wrong Pages-job commit SHAs are refused;
3. Level 2 honesty: only the documented Pages deployments API counts; the
   ordinary environment Deployments API is never consulted as a substitute;
4. Level 4 identity binding: only the exact pinned target URLs may be probed
   (a spoofed attacker.gitlab.io mirror or an unrelated *.gitlab.io site is
   refused); redirects are followed only to the other pinned URL;
5. Level 5 separation: observed served presence vs source-corroborated
   publication (unreadable marker source does NOT award the stronger claim);
6. Marker/URL override refusal (identity binding cannot be weakened);
7. Target binding, access-blocked and 404 classifications;
8. Safety: DELETE is never dispatched through the SAME transport injected
   into the function under test; zero unauthorized mutations.
"""

from __future__ import annotations

import json
import urllib.parse
from datetime import UTC, datetime

import pytest
from conftest import FakeTransport

from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.pages_publication import (
    DISPOSABLE_NAMESPACE_PAGES_URL,
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
PIPELINE_ID = 2960507698
QUOTED_MARKER = urllib.parse.quote("site/marker.txt", safe="")
QUOTED_INDEX = urllib.parse.quote("site/index.html", safe="")
CI_CONTENT = (
    "create-pages:\n  stage: deploy\n  script:\n"
    "    - cp site/index.html public/index.html\n  pages: true\n"
)


def _replies(
    *,
    pipeline_status="success",
    pipeline_list=None,
    jobs_api_status=200,
    job_name="create-pages",
    job_status="success",
    job_commit=None,
    pages_api_status=403,
    pages_deployments_status=403,
    pages_deployments_body=None,
    ordinary_deployments_body=None,
    repo_marker_present=True,
    repo_files_status=200,
):
    """Provider surface for the publication verifier.

    Ordering matters (FakeTransport matches by URL fragment): the Pages
    deployments endpoint must precede the bare Pages endpoint.
    """
    if pipeline_list is None:
        pipeline_list = [
            {"id": PIPELINE_ID, "sha": COMMIT_SHA, "status": pipeline_status}
        ]
    job_commit = job_commit or COMMIT_SHA
    jobs_api_body = (
        json.dumps(
            [
                {
                    "name": job_name,
                    "status": job_status,
                    "stage": "deploy",
                    "commit": {"id": job_commit},
                }
            ]
        )
        if jobs_api_status == 200
        else json.dumps({"error": "Forbidden"})
    )
    pages_deployments_body = pages_deployments_body or (
        json.dumps({"error": "Forbidden"})
        if pages_deployments_status == 403
        else json.dumps([{"id": 42, "created_at": "2026-10-21T10:00:00Z"}])
    )
    pages_api_body = (
        json.dumps({"error": "Forbidden"})
        if pages_api_status == 403
        else json.dumps({"url": DISPOSABLE_PAGES_URL, "deployments": [{}]})
    )
    marker_content = EXPECTED_MARKER if repo_marker_present else "DIFFERENT_MARKER"

    return {
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/pipelines?per_page=1"): HttpReply(
            200, json.dumps(pipeline_list)
        ),
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/pipelines/{PIPELINE_ID}/jobs"): (
            HttpReply(jobs_api_status, jobs_api_body)
        ),
        # Pages deployments API must precede the bare /pages endpoint.
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/pages/deployments"): HttpReply(
            pages_deployments_status, pages_deployments_body
        ),
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/deployments"): HttpReply(
            200, ordinary_deployments_body or json.dumps([{"id": 7}])
        ),
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/pages"): HttpReply(
            pages_api_status, pages_api_body
        ),
        (
            "GET",
            f"/projects/{DISPOSABLE_TARGET_PID}/repository/files/.gitlab-ci.yml/raw",
        ): HttpReply(200, CI_CONTENT),
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/repository/files/{QUOTED_MARKER}/raw"): (
            HttpReply(repo_files_status, marker_content)
        ),
        ("GET", f"/projects/{DISPOSABLE_TARGET_PID}/repository/files/{QUOTED_INDEX}/raw"): (
            HttpReply(
                repo_files_status,
                f"<html><body>{marker_content}</body></html>",
            )
        ),
    }


def _client(replies):
    return GitLabClient("dummy_token", transport=FakeTransport(replies))


def _getter_ok(url, timeout=15.0):
    return 200, None, f"<html><body><p>Marker: {EXPECTED_MARKER}</p></body></html>"


def test_publication_verified_live_served():
    """Marker verified live and corroborated in repo source; Pages API 403."""
    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.status == PublicationVerificationStatus.VERIFIED_LIVE_SERVED
    assert record.is_verified_live is True
    assert record.levels.level1_ci_job_success is True
    assert record.levels.level1_ci_job_status == "success"
    # Level 2 is honest: Pages deployments API returns 403, NOT inferred True
    assert record.levels.level2_deployment_created is False
    assert record.levels.level2_deployment_status == "NOT_OBSERVED_AUTH_DENIED"
    assert record.levels.level3_pages_api_status == 403
    assert record.levels.level3_pages_api_visible is False
    assert record.levels.level4_served_url_accessible is True
    assert record.levels.level5_marker_independently_observed is True
    assert record.levels.level5_source_corroborated is True
    assert record.levels.level5_observed_marker == EXPECTED_MARKER
    assert record.served_body_digest_sha256 is not None
    assert "genuinely published and live" in record.summary
    data = record.to_dict()
    assert data["freshness_scope"].startswith("EVALUATION_TIME_ONLY")


def test_publication_level2_pages_deployments_visible():
    """Pages deployments API 200 with deployments → level2 True."""
    client = _client(_replies(pages_deployments_status=200))
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.levels.level2_deployment_created is True
    assert record.levels.level2_deployment_status == "PAGES_DEPLOYMENTS_FOUND"


def test_pipeline_success_with_inaccessible_jobs_never_infers_pages_job():
    """Overall pipeline SUCCESS + jobs API 403 → Level 1 NOT_OBSERVED, never success."""
    client = _client(_replies(jobs_api_status=403))
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.levels.level1_ci_job_success is False
    assert record.levels.level1_ci_job_status == "NOT_OBSERVED_AUTH_DENIED"
    assert record.levels.level1_ci_job_name is None


def test_unrelated_deploy_stage_job_is_not_a_pages_job():
    """A job merely running in the deploy stage is not the Pages job."""
    client = _client(_replies(job_name="deploy-app"))
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.levels.level1_ci_job_success is False
    assert record.levels.level1_ci_job_status == "NOT_FOUND_IN_PIPELINE"


def test_wrong_pages_job_sha_fails_level1():
    """A Pages job bound to a different commit SHA does not count as success."""
    client = _client(_replies(job_commit="f" * 40))
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.levels.level1_ci_job_success is False
    assert (record.levels.level1_ci_job_status or "").startswith("SHA_MISMATCH")


def test_ordinary_deployments_api_is_never_consulted_for_level2():
    """Generic environment deployments must not back the Pages-deployment level."""
    replies = _replies(pages_deployments_status=403)
    transport = FakeTransport(replies)
    client = GitLabClient("dummy_token", transport=transport)
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    # Level 2 stays NOT_OBSERVED even though the ordinary deployments API
    # would return a non-empty list.
    assert record.levels.level2_deployment_created is False
    assert record.levels.level2_deployment_status == "NOT_OBSERVED_AUTH_DENIED"
    # The ordinary deployments endpoint was never called at all.
    called_urls = [url for _m, url in transport.calls]
    ordinary = [
        url
        for url in called_urls
        if url.endswith("/deployments") and "/pages/deployments" not in url
    ]
    assert not ordinary


def test_publication_pipeline_success_but_pages_job_failed():
    """Overall pipeline succeeded but create-pages job failed: Level 1 False."""
    client = _client(_replies(job_status="failed"))
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.levels.level1_ci_job_success is False
    assert record.levels.level1_ci_job_status == "failed"


def test_publication_wrong_target_refused():
    """Refuse any target project other than disposable demo 87785099."""
    client = _client(_replies())
    canonical_target = TargetIdentity(87779099, "group/canonical", "GITLAB_PAGES_SITE")
    record = verify_disposable_pages_publication(client, canonical_target, now=NOW)
    assert record.status == PublicationVerificationStatus.WRONG_TARGET_REFUSED
    assert record.is_verified_live is False
    assert "WRONG_TARGET_REFUSED" in record.summary


def test_publication_wrong_target_full_path_refused():
    """A same-ID target with a different full path is refused."""
    impostor = TargetIdentity(
        DISPOSABLE_TARGET_PID, "evil-namespace/termivance-pages-disposable", "GITLAB_PAGES_SITE"
    )
    client = _client(_replies())
    record = verify_disposable_pages_publication(client, impostor, now=NOW)
    assert record.status == PublicationVerificationStatus.WRONG_TARGET_REFUSED


def test_spoofed_attacker_gitlab_io_mirror_refused():
    """A spoofed attacker.gitlab.io mirror serving the exact marker is refused:
    a generic *.gitlab.io host cannot prove the site belongs to 87785099."""

    def spoofed_getter(url, timeout=15.0):
        return 200, None, f"<html><body>{EXPECTED_MARKER}</body></html>"

    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client,
        TARGET,
        served_url="https://attacker.gitlab.io/termivance-mirror/",
        now=NOW,
        http_getter=spoofed_getter,
    )
    assert record.status == PublicationVerificationStatus.UNTRUSTED_ORIGIN_REFUSED
    assert record.is_verified_live is False
    assert "generic *.gitlab.io allowlist is not sufficient" in record.summary


def test_unrelated_gitlab_pages_url_refused():
    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client,
        TARGET,
        served_url="https://someone-else.gitlab.io/unrelated-site/",
        now=NOW,
        http_getter=_getter_ok,
    )
    assert record.status == PublicationVerificationStatus.UNTRUSTED_ORIGIN_REFUSED


def test_insecure_http_url_refused():
    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client,
        TARGET,
        served_url="http://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/",
        now=NOW,
    )
    assert record.status == PublicationVerificationStatus.UNTRUSTED_ORIGIN_REFUSED


def test_arbitrary_marker_override_refused():
    """An arbitrary supplied marker can never weaken identity binding."""
    client = _client(_replies())

    def attacker_getter(url, timeout=15.0):
        return 200, None, "<html><body>attacker chosen content</body></html>"

    record = verify_disposable_pages_publication(
        client,
        TARGET,
        marker="attacker chosen content",
        now=NOW,
        http_getter=attacker_getter,
    )
    assert record.status == PublicationVerificationStatus.MARKER_OVERRIDE_REFUSED
    assert record.is_verified_live is False


def test_unobserved_marker_source_separates_served_presence():
    """Served marker observed but repo source unreadable → the stronger
    source-corroborated claim is NOT awarded."""
    client = _client(_replies(repo_files_status=404))
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.status == PublicationVerificationStatus.SERVED_MARKER_SOURCE_NOT_CORROBORATED
    assert record.is_verified_live is False
    assert record.levels.level4_served_url_accessible is True
    assert record.levels.level5_marker_independently_observed is True
    assert record.levels.level5_source_corroborated is None
    assert "source-corroborated publication is NOT awarded" in record.summary


def test_publication_source_marker_mismatch():
    """Served body has marker but repo source files do not → MARKER_MISMATCH."""
    client = _client(_replies(repo_marker_present=False))
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.status == PublicationVerificationStatus.MARKER_MISMATCH
    assert record.is_verified_live is False
    assert record.levels.level5_source_corroborated is False
    assert "not corroborated in repo files" in record.summary


def test_publication_marker_mismatch_in_body():
    """Served URL 200 but marker missing from body → MARKER_MISMATCH."""
    def unrelated_getter(url, timeout=15.0):
        return 200, None, "<html><body><p>Unrelated content without marker</p></body></html>"

    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=unrelated_getter
    )
    assert record.status == PublicationVerificationStatus.MARKER_MISMATCH
    assert record.is_verified_live is False
    assert record.levels.level4_served_url_accessible is True
    assert record.levels.level5_marker_independently_observed is False


def test_publication_cloudflare_challenge_inconclusive():
    def challenge_getter(url, timeout=15.0):
        return 403, "Cloudflare Challenge Interstitial", ""

    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=challenge_getter
    )
    assert record.status == PublicationVerificationStatus.INCONCLUSIVE_ACCESS_BLOCKED
    assert record.is_verified_live is False
    assert "INCONCLUSIVE" in record.summary


def test_publication_404_not_served_at_probed_url():
    def missing_getter(url, timeout=15.0):
        return 404, "Not Found", ""

    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=missing_getter
    )
    assert record.status == PublicationVerificationStatus.NOT_SERVED_AT_PROBED_URL
    assert record.is_verified_live is False
    assert "not proof of universal absence" in record.summary


def test_empty_provider_pipeline_response():
    """Pipelines API 200 with an empty list → NO_PIPELINE_OBSERVED, no commit."""
    client = _client(_replies(pipeline_list=[]))
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.levels.level1_ci_job_status == "NO_PIPELINE_OBSERVED"
    assert record.levels.level1_ci_pipeline_id is None
    assert record.commit_sha is None


def test_unsafe_redirect_at_pinned_url_not_followed():
    """A redirect at the pinned unique-domain URL is not followed anywhere."""

    def redirect_getter(url, timeout=15.0):
        return 301, None, ""

    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=redirect_getter
    )
    assert record.status == PublicationVerificationStatus.NOT_OBSERVED
    assert record.levels.level4_served_url_accessible is False
    assert record.levels.level4_served_http_status == 301


def test_safe_redirect_between_pinned_urls_is_followed():
    """A 301 from the namespace URL is re-probed only at the other pinned URL."""
    probes = []

    def redirect_getter(url, timeout=15.0):
        probes.append(url)
        if url == DISPOSABLE_NAMESPACE_PAGES_URL:
            return 301, None, ""
        return 200, None, f"<html><body>{EXPECTED_MARKER}</body></html>"

    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client,
        TARGET,
        served_url=DISPOSABLE_NAMESPACE_PAGES_URL,
        now=NOW,
        http_getter=redirect_getter,
    )
    assert probes[0] == DISPOSABLE_NAMESPACE_PAGES_URL
    assert record.served_url == DISPOSABLE_PAGES_URL
    assert record.status == PublicationVerificationStatus.VERIFIED_LIVE_SERVED


def test_redirect_loop_between_pinned_urls_fails_closed():
    """A redirect loop never resolves to a served observation."""

    def loop_getter(url, timeout=15.0):
        return 301, None, ""

    client = _client(_replies())
    record = verify_disposable_pages_publication(
        client,
        TARGET,
        served_url=DISPOSABLE_NAMESPACE_PAGES_URL,
        now=NOW,
        http_getter=loop_getter,
    )
    assert record.status == PublicationVerificationStatus.NOT_OBSERVED
    assert record.levels.level4_served_http_status == 301


def test_prohibited_delete_never_dispatched_on_function_transport():
    """Safety assertion: the transport injected into the function under test
    never observes a DELETE (or any non-GET) call."""
    replies = _replies()
    transport = FakeTransport(replies)
    client = GitLabClient("dummy_token", transport=transport)
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.is_verified_live is True
    methods = {m.upper() for m, _url in transport.calls}
    assert methods <= {"GET"}, f"non-read-only methods dispatched: {methods - {'GET'}}"
    assert "DELETE" not in methods


def test_prohibited_delete_intercepted_on_same_transport():
    """A DELETE attempt through the SAME transport fails the test loudly."""
    replies = _replies()
    transport = FakeTransport(replies)
    original_request = transport.request

    def intercepting_request(method, url, headers, timeout):
        assert method.upper() != "DELETE", (
            f"PROHIBITED MUTATION DISPATCHED: {method} {url}"
        )
        return original_request(method, url, headers, timeout)

    transport.request = intercepting_request  # type: ignore[method-assign]
    client = GitLabClient("dummy_token", transport=transport)
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.is_verified_live is True


@pytest.mark.parametrize(
    "status_code",
    [200, 403],
)
def test_pages_api_role_restriction_kept_distinct(status_code):
    """Level 3 reports the Pages administration API state independently."""
    client = _client(_replies(pages_api_status=status_code))
    record = verify_disposable_pages_publication(
        client, TARGET, now=NOW, http_getter=_getter_ok
    )
    assert record.levels.level3_pages_api_status == status_code
    assert record.levels.level3_pages_api_visible is (status_code == 200)
    # Level 3 never overrides the served-URL evidence either way.
    assert record.levels.level4_served_url_accessible is True
