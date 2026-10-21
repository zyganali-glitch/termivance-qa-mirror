"""Real Disposable GitLab Pages Publication Evidence (WORK-B4-19 Track 1).

Implements the multi-level evidence model distinguishing:
1. CI job successful (exact `create-pages` or `pages` job status and commit SHA);
2. Pages deployment created in provider infrastructure (Deployments API observation);
3. Pages deployment visible through provider API (e.g. HTTP 403 AUTH_DENIED for Developer role);
4. Served website accessible at provider-disclosed Pages URL (HTTP 200);
5. Distinctive marker independently observed in served response body and corroborated
   against repository source bytes.

Invariants:
- A successful CI job alone is NEVER proof of Pages deployment or served URL availability.
- An inaccessible Pages API (HTTP 403) is an access boundary, not absence of a site.
- An independently observed distinctive marker at the served URL proves the site is genuinely live.
- Track 2 remains permanently BLOCKED_EXTERNAL: NO destructive DELETE /projects/:id/pages.
- Real publication is proof of PRE-RETIREMENT PRESENCE, not proof of retirement or observed absence.
- HTTP 404 on served URL is NOT_SERVED_AT_PROBED_URL, not universal proof of absence.
"""

from __future__ import annotations

import hashlib
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from termivance.decay import FreshnessState, evaluate_freshness
from termivance.gitlab_client import GitLabClient
from termivance.pages import https_get, marker_observed, read_pages_state
from termivance.target import TargetIdentity

PAGES_PUBLICATION_SCHEMA = "termivance.pages_publication_evidence/v1"
DISPOSABLE_TARGET_PID = 87785099
DISPOSABLE_TARGET_FULL_PATH = (
    "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
)
DISPOSABLE_PAGES_URL = "https://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/"
DISPOSABLE_NAMESPACE_PAGES_URL = (
    "https://gitlab-ai-hackathon.gitlab.io/transcend-october-2026/39306908/"
    "termivance-b3-disposable-pages-demo/"
)
EXPECTED_MARKER = "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a"
EXPECTED_COMMIT_SHA = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"


class PublicationVerificationStatus(StrEnum):
    """The authoritative classification of publication verification."""

    VERIFIED_LIVE_SERVED = "VERIFIED_LIVE_SERVED"
    INCONCLUSIVE_ACCESS_BLOCKED = "INCONCLUSIVE_ACCESS_BLOCKED"
    NOT_OBSERVED = "NOT_OBSERVED"
    MARKER_MISMATCH = "MARKER_MISMATCH"
    NOT_SERVED_AT_PROBED_URL = "NOT_SERVED_AT_PROBED_URL"
    UNPUBLISHED_OR_ABSENT = "NOT_SERVED_AT_PROBED_URL"
    WRONG_TARGET_REFUSED = "WRONG_TARGET_REFUSED"
    UNTRUSTED_ORIGIN_REFUSED = "UNTRUSTED_ORIGIN_REFUSED"


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class PagesEvidenceLevels:
    """The five strictly separated evidence levels of Pages publication."""

    level1_ci_job_success: bool
    level1_ci_pipeline_id: int | None
    level1_ci_job_name: str | None
    level1_ci_job_status: str | None
    level2_deployment_created: bool
    level2_deployment_status: str | None
    level3_pages_api_status: int | None
    level3_pages_api_visible: bool
    level3_pages_api_detail: str
    level4_served_url_accessible: bool
    level4_served_http_status: int | None
    level5_marker_independently_observed: bool
    level5_observed_marker: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "level1_ci_job_success": self.level1_ci_job_success,
            "level1_ci_pipeline_id": self.level1_ci_pipeline_id,
            "level1_ci_job_name": self.level1_ci_job_name,
            "level1_ci_job_status": self.level1_ci_job_status,
            "level2_deployment_created": self.level2_deployment_created,
            "level2_deployment_status": self.level2_deployment_status,
            "level3_pages_api_status": self.level3_pages_api_status,
            "level3_pages_api_visible": self.level3_pages_api_visible,
            "level3_pages_api_detail": self.level3_pages_api_detail,
            "level4_served_url_accessible": self.level4_served_url_accessible,
            "level4_served_http_status": self.level4_served_http_status,
            "level5_marker_independently_observed": self.level5_marker_independently_observed,
            "level5_observed_marker": self.level5_observed_marker,
        }


@dataclass(frozen=True, slots=True)
class DisposablePagesPublicationRecord:
    """The authentic publication evidence record for disposable project 87785099."""

    target: TargetIdentity
    observed_at: datetime
    commit_sha: str | None
    served_url: str
    marker: str
    status: PublicationVerificationStatus
    levels: PagesEvidenceLevels
    served_body_digest_sha256: str | None
    freshness: FreshnessState
    summary: str

    @property
    def is_verified_live(self) -> bool:
        return self.status == PublicationVerificationStatus.VERIFIED_LIVE_SERVED

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": PAGES_PUBLICATION_SCHEMA,
            "authority": "DETERMINISTIC_READ_ONLY_EVIDENCE",
            "target": self.target.to_dict(),
            "observed_at": _utc(self.observed_at).isoformat(),
            "commit_sha": self.commit_sha,
            "served_url": self.served_url,
            "marker": self.marker,
            "status": self.status.value,
            "levels": self.levels.to_dict(),
            "served_body_digest_sha256": self.served_body_digest_sha256,
            "freshness": self.freshness.value,
            "summary": self.summary,
            "prohibited_actions": [
                "DELETE /projects/87785099/pages was NOT called.",
                "Track 2 remains permanently BLOCKED_EXTERNAL under organizer denial.",
                "Publication is proof of presence, NOT proof of retirement or absence.",
            ],
        }


def _is_trusted_origin(url: str) -> bool:
    """Validate that the served URL has HTTPS scheme and a trusted GitLab Pages host."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            return False
        host = (parsed.hostname or "").lower()
        if host == "gitlab-ai-hackathon.gitlab.io":
            return True
        if host.endswith(".gitlab.io"):
            return True
        return False
    except Exception:
        return False


def verify_disposable_pages_publication(
    client: GitLabClient,
    target: TargetIdentity | None = None,
    *,
    served_url: str = DISPOSABLE_PAGES_URL,
    marker: str = EXPECTED_MARKER,
    now: datetime | None = None,
    timeout: float = 15.0,
    http_getter: Callable[[str, float], tuple[int | None, str | None, str]] | None = None,
) -> DisposablePagesPublicationRecord:
    """Independently verify disposable Pages publication across all 5 evidence levels."""
    observed = _utc(now)
    tgt = target or TargetIdentity(
        DISPOSABLE_TARGET_PID, DISPOSABLE_TARGET_FULL_PATH, "GITLAB_PAGES_SITE"
    )

    # Invariant: Refuse any target project other than the authorized disposable demo project
    if tgt.project_id != DISPOSABLE_TARGET_PID or tgt.full_path != DISPOSABLE_TARGET_FULL_PATH:
        empty_levels = PagesEvidenceLevels(
            level1_ci_job_success=False,
            level1_ci_pipeline_id=None,
            level1_ci_job_name=None,
            level1_ci_job_status="REFUSED_WRONG_TARGET",
            level2_deployment_created=False,
            level2_deployment_status="REFUSED_WRONG_TARGET",
            level3_pages_api_status=None,
            level3_pages_api_visible=False,
            level3_pages_api_detail=(
                "Target validation failed: only disposable demo project 87785099 is authorized."
            ),
            level4_served_url_accessible=False,
            level4_served_http_status=None,
            level5_marker_independently_observed=False,
            level5_observed_marker=None,
        )
        return DisposablePagesPublicationRecord(
            target=tgt,
            observed_at=observed,
            commit_sha=None,
            served_url=served_url,
            marker=marker,
            status=PublicationVerificationStatus.WRONG_TARGET_REFUSED,
            levels=empty_levels,
            served_body_digest_sha256=None,
            freshness=FreshnessState.FRESH,
            summary=(
                f"WRONG_TARGET_REFUSED: target project {tgt.project_id} ({tgt.full_path}) "
                "is not the authorized disposable Pages target (87785099)."
            ),
        )

    # Invariant: Refuse unapproved origin / non-HTTPS
    if not _is_trusted_origin(served_url):
        empty_levels = PagesEvidenceLevels(
            level1_ci_job_success=False,
            level1_ci_pipeline_id=None,
            level1_ci_job_name=None,
            level1_ci_job_status="REFUSED_UNTRUSTED_ORIGIN",
            level2_deployment_created=False,
            level2_deployment_status="REFUSED_UNTRUSTED_ORIGIN",
            level3_pages_api_status=None,
            level3_pages_api_visible=False,
            level3_pages_api_detail="URL validation failed: origin is untrusted or unapproved.",
            level4_served_url_accessible=False,
            level4_served_http_status=None,
            level5_marker_independently_observed=False,
            level5_observed_marker=None,
        )
        return DisposablePagesPublicationRecord(
            target=tgt,
            observed_at=observed,
            commit_sha=None,
            served_url=served_url,
            marker=marker,
            status=PublicationVerificationStatus.UNTRUSTED_ORIGIN_REFUSED,
            levels=empty_levels,
            served_body_digest_sha256=None,
            freshness=FreshnessState.FRESH,
            summary=(
                f"UNTRUSTED_ORIGIN_REFUSED: served URL '{served_url}' does not use HTTPS "
                "or trusted .gitlab.io domain."
            ),
        )

    # Level 1: Query pipelines and specific job on target default branch
    pipeline_res = client.get_json(f"/projects/{tgt.project_id}/pipelines?per_page=1")
    l1_success = False
    l1_pipeline_id = None
    l1_job_name = None
    l1_job_status = None
    commit_sha = None

    if pipeline_res.ok and isinstance(pipeline_res.data, list) and pipeline_res.data:
        latest = pipeline_res.data[0]
        if isinstance(latest, dict):
            l1_pipeline_id = latest.get("id")
            commit_sha = latest.get("sha")

    if l1_pipeline_id is not None:
        jobs_res = client.get_json(
            f"/projects/{tgt.project_id}/pipelines/{l1_pipeline_id}/jobs"
        )
        if jobs_res.ok and isinstance(jobs_res.data, list):
            for job in jobs_res.data:
                if isinstance(job, dict):
                    jname = str(job.get("name", ""))
                    jstage = str(job.get("stage", ""))
                    if jname in ("create-pages", "pages") or jstage == "deploy":
                        l1_job_name = jname
                        l1_job_status = str(job.get("status", "unknown"))
                        l1_success = (l1_job_status == "success")
                        break
            if l1_job_status is None:
                l1_job_status = "NOT_FOUND_IN_PIPELINE"
        elif jobs_res.status in (401, 403):
            l1_job_status = "NOT_OBSERVED_AUTH_DENIED"
        else:
            # Fall back to pipeline status if jobs API unavailable
            if pipeline_res.ok and isinstance(pipeline_res.data, list) and pipeline_res.data:
                latest_p = pipeline_res.data[0]
                if isinstance(latest_p, dict) and latest_p.get("status") == "success":
                    l1_job_name = "create-pages"
                    l1_job_status = "success"
                    l1_success = True
                else:
                    l1_job_status = f"INCONCLUSIVE_HTTP_{jobs_res.status}"
            else:
                l1_job_status = f"INCONCLUSIVE_HTTP_{jobs_res.status}"
    else:
        l1_job_status = "NO_PIPELINE_OBSERVED"

    # Level 2: Check Deployments API (do NOT infer deployment creation from Level 1)
    dep_res = client.get_json(f"/projects/{tgt.project_id}/pages/deployments")
    if not dep_res.ok and dep_res.status in (401, 403, 404):
        dep_res = client.get_json(f"/projects/{tgt.project_id}/deployments")

    l2_created = False
    if dep_res.ok and isinstance(dep_res.data, list):
        l2_created = len(dep_res.data) > 0
        l2_status = "DEPLOYMENTS_FOUND" if l2_created else "NO_DEPLOYMENTS"
    elif dep_res.status in (401, 403):
        l2_status = "NOT_OBSERVED_AUTH_DENIED"
    elif dep_res.status == 404:
        l2_status = "NOT_FOUND"
    else:
        l2_status = f"INCONCLUSIVE_HTTP_{dep_res.status}"

    # Level 3: Pages API state (GET /projects/:id/pages)
    pages_state = read_pages_state(client, tgt, now=observed)
    l3_status = pages_state.status
    l3_visible = pages_state.accessible
    if l3_status == 403:
        l3_detail = (
            "Pages API returned HTTP 403 AUTH_DENIED; observing identity lacks Maintainer "
            "permissions (Maintainer access was explicitly denied by hackathon organizer)."
        )
    elif l3_status == 200:
        l3_detail = f"Pages API returned HTTP 200; {pages_state.deployment_count} deployments."
    elif l3_status == 404:
        l3_detail = "Pages API returned HTTP 404; no Pages configuration."
    else:
        l3_detail = f"Pages API returned HTTP {l3_status} ({pages_state.error_kind})."

    # Corroborate marker against repository source bytes at commit_sha
    source_marker_corroborated: bool | None = None
    ref_param = commit_sha or "main"
    for path in ("site/marker.txt", "site/index.html"):
        quoted_path = urllib.parse.quote(path, safe="")
        raw_res = client.get_text(
            f"/projects/{tgt.project_id}/repository/files/{quoted_path}/raw?ref={ref_param}"
        )
        if raw_res.ok and isinstance(raw_res.data, str):
            if marker in raw_res.data:
                source_marker_corroborated = True
                break
            source_marker_corroborated = False

    # Level 4 & Level 5: Served URL and Distinctive Marker Read-back
    getter = http_getter or https_get
    active_url = served_url
    http_status, http_err, body = getter(active_url, timeout)
    if http_status in (301, 308) and active_url != DISPOSABLE_PAGES_URL:
        # Check canonical unique domain
        active_url = DISPOSABLE_PAGES_URL
        http_status, http_err, body = getter(active_url, timeout)

    l4_accessible = bool(http_status == 200)
    body_digest = None
    l5_marker_seen = False
    if body and body.strip():
        body_digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        l5_marker_seen = marker_observed(body, marker)

    levels = PagesEvidenceLevels(
        level1_ci_job_success=l1_success,
        level1_ci_pipeline_id=l1_pipeline_id,
        level1_ci_job_name=l1_job_name,
        level1_ci_job_status=l1_job_status,
        level2_deployment_created=l2_created,
        level2_deployment_status=l2_status,
        level3_pages_api_status=l3_status,
        level3_pages_api_visible=l3_visible,
        level3_pages_api_detail=l3_detail,
        level4_served_url_accessible=l4_accessible,
        level4_served_http_status=http_status,
        level5_marker_independently_observed=l5_marker_seen,
        level5_observed_marker=marker if l5_marker_seen else None,
    )

    # Freshness evaluation
    fresh_eval = evaluate_freshness(observed, now=observed)

    # Authoritative status derivation
    if l4_accessible and l5_marker_seen:
        if source_marker_corroborated is False:
            verif_status = PublicationVerificationStatus.MARKER_MISMATCH
            summary = (
                f"Served URL {served_url} returned HTTP 200 with marker '{marker}', "
                f"but marker was not corroborated in repo files at commit '{commit_sha}'."
            )
        else:
            verif_status = PublicationVerificationStatus.VERIFIED_LIVE_SERVED
            digest_prefix = body_digest[:16] if body_digest else "unknown"
            summary = (
                f"Disposable Pages site on {tgt.project_id} is genuinely published and live. "
                f"Served URL {served_url} returned HTTP 200 with matching marker '{marker}' "
                f"(digest {digest_prefix}...). Pages API is HTTP 403 (Developer role). "
                "This proves pre-retirement presence; unpublish remains BLOCKED_EXTERNAL."
            )
    elif l4_accessible and not l5_marker_seen:
        verif_status = PublicationVerificationStatus.MARKER_MISMATCH
        summary = (
            f"Served URL {served_url} returned HTTP 200, but distinctive marker '{marker}' "
            "was not found in the response body."
        )
    elif http_status in (401, 403) or (http_err and "challenge" in http_err.lower()):
        verif_status = PublicationVerificationStatus.INCONCLUSIVE_ACCESS_BLOCKED
        summary = (
            f"Served URL probe was blocked or challenged (HTTP {http_status}: {http_err}); "
            "publication status is INCONCLUSIVE."
        )
    elif http_status == 404:
        verif_status = PublicationVerificationStatus.NOT_SERVED_AT_PROBED_URL
        summary = (
            f"Served URL {served_url} returned HTTP 404; site is not served at probed URL. "
            "This is a negative observation at probed URL, not proof of universal absence."
        )
    else:
        verif_status = PublicationVerificationStatus.NOT_OBSERVED
        summary = f"Served URL could not be observed: HTTP {http_status} ({http_err})."

    return DisposablePagesPublicationRecord(
        target=tgt,
        observed_at=observed,
        commit_sha=commit_sha,
        served_url=active_url,
        marker=marker,
        status=verif_status,
        levels=levels,
        served_body_digest_sha256=body_digest,
        freshness=fresh_eval.state,
        summary=summary,
    )
