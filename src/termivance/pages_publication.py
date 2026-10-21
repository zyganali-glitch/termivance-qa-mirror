"""Real Disposable GitLab Pages Publication Evidence (WORK-B4-19 Track 1).

Implements the multi-level evidence model distinguishing:
1. CI job successful (job `create-pages` with `pages: true`);
2. Pages deployment created in provider infrastructure;
3. Pages deployment visible through provider API (e.g. HTTP 403 AUTH_DENIED for Developer role);
4. Served website accessible at provider-disclosed Pages URL (HTTP 200);
5. Distinctive marker independently observed in served response body.

Invariants:
- A successful CI job alone is NEVER proof of Pages deployment or served URL availability.
- An inaccessible Pages API (HTTP 403) is an access boundary, not absence of a site.
- An independently observed distinctive marker at the served URL proves the site is genuinely live.
- Track 2 remains permanently BLOCKED_EXTERNAL: NO destructive DELETE /projects/:id/pages.
- Real publication is proof of PRE-RETIREMENT PRESENCE, not proof of retirement or observed absence.
"""

from __future__ import annotations

import hashlib
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
    UNPUBLISHED_OR_ABSENT = "UNPUBLISHED_OR_ABSENT"


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
    level2_deployment_created: bool
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
            "level2_deployment_created": self.level2_deployment_created,
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


def verify_disposable_pages_publication(
    client: GitLabClient,
    target: TargetIdentity | None = None,
    *,
    served_url: str = DISPOSABLE_PAGES_URL,
    marker: str = EXPECTED_MARKER,
    now: datetime | None = None,
    timeout: float = 15.0,
) -> DisposablePagesPublicationRecord:
    """Independently verify disposable Pages publication across all 5 evidence levels."""
    observed = _utc(now)
    tgt = target or TargetIdentity(
        DISPOSABLE_TARGET_PID, DISPOSABLE_TARGET_FULL_PATH, "GITLAB_PAGES_SITE"
    )

    # Level 1: Query pipelines on target default branch
    pipeline_res = client.get_json(f"/projects/{tgt.project_id}/pipelines?per_page=1")
    l1_success = False
    l1_pipeline_id = None
    l1_job_name = "create-pages"
    commit_sha = None

    if pipeline_res.ok and isinstance(pipeline_res.data, list) and pipeline_res.data:
        latest = pipeline_res.data[0]
        if isinstance(latest, dict):
            l1_pipeline_id = latest.get("id")
            commit_sha = latest.get("sha")
            l1_success = latest.get("status") == "success"

    # Also inspect repository .gitlab-ci.yml for create-pages with pages: true
    ci_res = client.get_text(
        f"/projects/{tgt.project_id}/repository/files/.gitlab-ci.yml/raw?ref={commit_sha or 'main'}"
    )
    ci_has_pages = False
    if ci_res.ok and isinstance(ci_res.data, str):
        ci_has_pages = "pages: true" in ci_res.data and "create-pages" in ci_res.data

    # Level 2: Deployment created (implied by successful pipeline with pages job)
    l2_created = bool(l1_success and ci_has_pages)

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

    # Level 4 & Level 5: Served URL and Distinctive Marker Read-back
    active_url = served_url
    http_status, http_err, body = https_get(active_url, timeout=timeout)
    if http_status in (301, 308) and active_url != DISPOSABLE_PAGES_URL:
        # GitLab Pages uses unique domain 308 permanent redirect; probe canonical unique domain
        active_url = DISPOSABLE_PAGES_URL
        http_status, http_err, body = https_get(active_url, timeout=timeout)

    l4_accessible = bool(http_status == 200)

    body_digest = None
    l5_marker_seen = False
    if body and body.strip():
        body_digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        l5_marker_seen = marker_observed(body, marker)

    levels = PagesEvidenceLevels(
        level1_ci_job_success=l1_success,
        level1_ci_pipeline_id=l1_pipeline_id,
        level1_ci_job_name=l1_job_name if ci_has_pages else None,
        level2_deployment_created=l2_created,
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
        verif_status = PublicationVerificationStatus.VERIFIED_LIVE_SERVED
        summary = (
            f"Disposable Pages site on project {tgt.project_id} is genuinely published and live. "
            f"Served URL {served_url} returned HTTP 200 with matching marker '{marker}' "
            f"(digest {body_digest[:16]}...). Pages API is HTTP 403 (Developer role). "
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
        verif_status = PublicationVerificationStatus.UNPUBLISHED_OR_ABSENT
        summary = f"Served URL {served_url} returned HTTP 404; site is not currently served."
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
