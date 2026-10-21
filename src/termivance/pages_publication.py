"""Real Disposable GitLab Pages Publication Evidence (WORK-B4-19 Track 1).

Implements the multi-level evidence model distinguishing:
1. CI job successful (exact ``create-pages``/``pages`` job status, commit SHA
   binding, and jobs-API observability — overall pipeline SUCCESS is NEVER
   inferred as a successful Pages job);
2. Pages deployment observed through the documented GitLab Pages deployments
   API (``GET /projects/:id/pages/deployments``). The ordinary environment
   Deployments API (``GET /projects/:id/deployments``) is a different surface
   and is NEVER treated as equivalent Pages-deployment evidence. If the Pages
   deployments API is inaccessible, the level reports ``NOT_OBSERVED``;
3. Pages administration API state (``GET /projects/:id/pages``) and its role
   restriction kept distinct from every other level (e.g. HTTP 403
   AUTH_DENIED for the Developer role is an access boundary, not absence);
4. Served website accessible at an exact provider-verified, strictly pinned
   target-bound HTTPS Pages URL. A generic ``*.gitlab.io`` allowlist is NOT
   sufficient to prove a website belongs to project 87785099: only the two
   pinned URLs of the disposable target (unique domain and namespace path)
   may ever be probed, with safe redirect handling;
5. Distinctive marker returned by the server and independently corroborated
   against repository source bytes at an independently observed exact commit.
   Observed served presence is separated from the stronger source-bound
   claim: if the marker source cannot be read, source-corroborated
   publication is NOT awarded.

Invariants:
- A successful CI job alone is NEVER proof of Pages deployment or served URL availability.
- An inaccessible Pages API (HTTP 403) is an access boundary, not absence of a site.
- Marker and URL parameters can never be overridden to weaken identity binding.
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
#: The two exact, provider-verified Pages URLs of the disposable target
#: (unique domain and namespace-path form). These are the ONLY URLs Level 4
#: may ever probe; a generic *.gitlab.io allowlist cannot bind a site to
#: project 87785099.
PINNED_PAGES_URLS: frozenset[str] = frozenset(
    {
        "https://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/",
        (
            "https://gitlab-ai-hackathon.gitlab.io/transcend-october-2026/39306908/"
            "termivance-b3-disposable-pages-demo/"
        ),
    }
)
DISPOSABLE_PAGES_URL = "https://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/"
DISPOSABLE_NAMESPACE_PAGES_URL = (
    "https://gitlab-ai-hackathon.gitlab.io/transcend-october-2026/39306908/"
    "termivance-b3-disposable-pages-demo/"
)
#: The exact expected distinctive marker. Arbitrary marker overrides that
#: would weaken identity binding are refused.
EXPECTED_MARKER = "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a"
EXPECTED_COMMIT_SHA = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
#: Job names that qualify as the target's Pages job. An unrelated job that
#: merely runs in a deploy stage is NOT a Pages job.
PAGES_JOB_NAMES: frozenset[str] = frozenset({"create-pages", "pages"})


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
    MARKER_OVERRIDE_REFUSED = "MARKER_OVERRIDE_REFUSED"
    SERVED_MARKER_SOURCE_NOT_CORROBORATED = "SERVED_MARKER_SOURCE_NOT_CORROBORATED"


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
    #: Tri-state source corroboration at Level 5: True (marker verified in
    #: repository source at the observed commit), False (source read but
    #: marker absent), None (marker source could not be read — the stronger
    #: source-bound claim is then NOT awarded).
    level5_source_corroborated: bool | None = None

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
            "level5_source_corroborated": self.level5_source_corroborated,
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
            "freshness_scope": (
                "EVALUATION_TIME_ONLY: the recorded freshness state describes the "
                "observation at its recorded evaluation time; it is never a "
                "current/live freshness claim at view time"
            ),
            "summary": self.summary,
            "prohibited_actions": [
                "DELETE /projects/87785099/pages was NOT called.",
                "Track 2 remains permanently BLOCKED_EXTERNAL under organizer denial.",
                "Publication is proof of presence, NOT proof of retirement or absence.",
            ],
        }


def _is_pinned_target_url(url: str) -> bool:
    """Only the exact pinned Pages URLs of project 87785099 may be probed."""
    try:
        normalized = url.rstrip("/") + "/" if not url.endswith("/") else url
    except Exception:  # noqa: BLE001
        return False
    return url in PINNED_PAGES_URLS or normalized in PINNED_PAGES_URLS


def _empty_levels(
    *, l1_status: str, l2_status: str, l3_detail: str
) -> PagesEvidenceLevels:
    return PagesEvidenceLevels(
        level1_ci_job_success=False,
        level1_ci_pipeline_id=None,
        level1_ci_job_name=None,
        level1_ci_job_status=l1_status,
        level2_deployment_created=False,
        level2_deployment_status=l2_status,
        level3_pages_api_status=None,
        level3_pages_api_visible=False,
        level3_pages_api_detail=l3_detail,
        level4_served_url_accessible=False,
        level4_served_http_status=None,
        level5_marker_independently_observed=False,
        level5_observed_marker=None,
        level5_source_corroborated=None,
    )


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
    """Independently verify disposable Pages publication across all 5 evidence levels.

    Identity-binding invariants (cannot be weakened by parameters):

    * ``marker`` must be exactly :data:`EXPECTED_MARKER`; any other value is
      refused with ``MARKER_OVERRIDE_REFUSED``.
    * ``served_url`` must be one of the exact pinned Pages URLs of the
      disposable target; any other URL (including other ``*.gitlab.io``
      hosts) is refused with ``UNTRUSTED_ORIGIN_REFUSED``.
    """
    observed = _utc(now)
    tgt = target or TargetIdentity(
        DISPOSABLE_TARGET_PID, DISPOSABLE_TARGET_FULL_PATH, "GITLAB_PAGES_SITE"
    )

    # Invariant: Refuse any target project other than the authorized disposable demo project
    if tgt.project_id != DISPOSABLE_TARGET_PID or tgt.full_path != DISPOSABLE_TARGET_FULL_PATH:
        return DisposablePagesPublicationRecord(
            target=tgt,
            observed_at=observed,
            commit_sha=None,
            served_url=served_url,
            marker=marker,
            status=PublicationVerificationStatus.WRONG_TARGET_REFUSED,
            levels=_empty_levels(
                l1_status="REFUSED_WRONG_TARGET",
                l2_status="REFUSED_WRONG_TARGET",
                l3_detail=(
                    "Target validation failed: only disposable demo project 87785099 "
                    "at its exact full path is authorized."
                ),
            ),
            served_body_digest_sha256=None,
            freshness=FreshnessState.FRESH,
            summary=(
                f"WRONG_TARGET_REFUSED: target project {tgt.project_id} ({tgt.full_path}) "
                "is not the authorized disposable Pages target (87785099, "
                "gitlab-ai-hackathon/transcend-october-2026/39306908/"
                "termivance-b3-disposable-pages-demo)."
            ),
        )

    # Invariant: Refuse marker overrides that would weaken identity binding.
    if marker != EXPECTED_MARKER:
        return DisposablePagesPublicationRecord(
            target=tgt,
            observed_at=observed,
            commit_sha=None,
            served_url=served_url,
            marker=marker,
            status=PublicationVerificationStatus.MARKER_OVERRIDE_REFUSED,
            levels=_empty_levels(
                l1_status="REFUSED_MARKER_OVERRIDE",
                l2_status="REFUSED_MARKER_OVERRIDE",
                l3_detail=(
                    "Marker validation failed: only the exact expected distinctive "
                    "marker of the disposable target is authorized."
                ),
            ),
            served_body_digest_sha256=None,
            freshness=FreshnessState.FRESH,
            summary=(
                f"MARKER_OVERRIDE_REFUSED: supplied marker {marker!r} is not the exact "
                f"expected marker {EXPECTED_MARKER!r}; an arbitrary marker cannot "
                "weaken target identity binding."
            ),
        )

    # Invariant: Refuse URLs that are not the exact pinned Pages URLs of the target.
    if not _is_pinned_target_url(served_url):
        return DisposablePagesPublicationRecord(
            target=tgt,
            observed_at=observed,
            commit_sha=None,
            served_url=served_url,
            marker=marker,
            status=PublicationVerificationStatus.UNTRUSTED_ORIGIN_REFUSED,
            levels=_empty_levels(
                l1_status="REFUSED_UNTRUSTED_ORIGIN",
                l2_status="REFUSED_UNTRUSTED_ORIGIN",
                l3_detail=(
                    "URL validation failed: a generic *.gitlab.io host cannot prove "
                    "a website belongs to project 87785099; only the exact pinned "
                    "target URLs may be probed."
                ),
            ),
            served_body_digest_sha256=None,
            freshness=FreshnessState.FRESH,
            summary=(
                f"UNTRUSTED_ORIGIN_REFUSED: served URL '{served_url}' is not one of "
                "the exact pinned Pages URLs of the disposable target; a generic "
                "*.gitlab.io allowlist is not sufficient identity binding."
            ),
        )

    # Level 1: Exact Pages job evidence with commit binding. The jobs API
    # must be observable; overall pipeline SUCCESS is NEVER inferred as a
    # successful Pages job.
    pipeline_res = client.get_json(f"/projects/{tgt.project_id}/pipelines?per_page=1")
    l1_success = False
    l1_pipeline_id = None
    l1_job_name = None
    l1_job_status: str | None = None
    commit_sha = None

    if pipeline_res.ok and isinstance(pipeline_res.data, list) and pipeline_res.data:
        latest = pipeline_res.data[0]
        if isinstance(latest, dict):
            l1_pipeline_id = latest.get("id")
            commit_sha = latest.get("sha")

    if l1_pipeline_id is None:
        l1_job_status = "NO_PIPELINE_OBSERVED"
    else:
        jobs_res = client.get_json(
            f"/projects/{tgt.project_id}/pipelines/{l1_pipeline_id}/jobs"
        )
        if jobs_res.ok and isinstance(jobs_res.data, list):
            pages_job = None
            for job in jobs_res.data:
                if isinstance(job, dict) and str(job.get("name", "")) in PAGES_JOB_NAMES:
                    pages_job = job
                    break
            if pages_job is None:
                l1_job_status = "NOT_FOUND_IN_PIPELINE"
            else:
                l1_job_name = str(pages_job.get("name", ""))
                job_status = str(pages_job.get("status", "unknown"))
                # Commit binding: the Pages job must run at the pipeline's SHA.
                job_commit = None
                job_commit_obj = pages_job.get("commit")
                if isinstance(job_commit_obj, dict):
                    job_commit = job_commit_obj.get("id")
                if commit_sha and job_commit and job_commit != commit_sha:
                    l1_job_status = f"SHA_MISMATCH_JOB_{(job_commit or '')[:10]}"
                else:
                    l1_job_status = job_status
                    l1_success = job_status == "success"
        elif jobs_res.status in (401, 403):
            l1_job_status = "NOT_OBSERVED_AUTH_DENIED"
        elif jobs_res.status == 404:
            l1_job_status = "NOT_OBSERVED_NOT_FOUND"
        else:
            # Jobs API inaccessible: report NOT_OBSERVED. Never fall back to
            # inferring a successful Pages job from overall pipeline SUCCESS.
            l1_job_status = "NOT_OBSERVED"

    # Level 2: Pages deployment observation through the documented Pages
    # deployments API only. The ordinary environment Deployments API is a
    # different surface and is never consulted as a substitute.
    dep_res = client.get_json(f"/projects/{tgt.project_id}/pages/deployments")
    l2_created = False
    if dep_res.ok and isinstance(dep_res.data, list):
        l2_created = len(dep_res.data) > 0
        l2_status = "PAGES_DEPLOYMENTS_FOUND" if l2_created else "NO_PAGES_DEPLOYMENTS"
    elif dep_res.status in (401, 403):
        l2_status = "NOT_OBSERVED_AUTH_DENIED"
    elif dep_res.status == 404:
        l2_status = "NOT_OBSERVED_NOT_FOUND"
    else:
        l2_status = f"NOT_OBSERVED_HTTP_{dep_res.status}"

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

    # Level 5 source corroboration: marker in repository source bytes at the
    # observed commit. Tri-state: True / False / None (source not readable).
    source_marker_corroborated: bool | None = None
    source_ref = commit_sha or "main"
    for path in ("site/marker.txt", "site/index.html"):
        quoted_path = urllib.parse.quote(path, safe="")
        raw_res = client.get_text(
            f"/projects/{tgt.project_id}/repository/files/{quoted_path}/raw?ref={source_ref}"
        )
        if raw_res.ok and isinstance(raw_res.data, str):
            if marker in raw_res.data:
                source_marker_corroborated = True
                break
            source_marker_corroborated = False
        # A failed read leaves the tri-state untouched for this path; if no
        # source file is readable at all, the state stays None.

    # Level 4 & Level 5: Served URL and Distinctive Marker Read-back.
    # Only the pinned URLs are ever probed; redirects are followed only to
    # the other pinned URL of the same target.
    getter = http_getter or https_get
    active_url = served_url
    http_status, http_err, body = getter(active_url, timeout=timeout)
    if http_status in (301, 308):
        redirect_target = next(
            (u for u in PINNED_PAGES_URLS if u != active_url),
            None,
        )
        if redirect_target is not None:
            # Safe redirect handling: re-probe only the other exact pinned URL.
            http_status, http_err, body = getter(redirect_target, timeout=timeout)
            if http_status not in (301, 308):
                active_url = redirect_target
        # A redirect chain that never resolves to a pinned 200 stays unfollowed.

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
        level5_source_corroborated=source_marker_corroborated,
    )

    # Freshness evaluation (evaluation-time semantics only)
    fresh_eval = evaluate_freshness(observed, now=observed)

    # Authoritative status derivation
    if l4_accessible and l5_marker_seen:
        if source_marker_corroborated is False:
            verif_status = PublicationVerificationStatus.MARKER_MISMATCH
            summary = (
                f"Served URL {active_url} returned HTTP 200 with marker '{marker}', "
                f"but marker was not corroborated in repo files at commit '{commit_sha}'."
            )
        elif source_marker_corroborated is None:
            # Observed served presence is separated from the stronger
            # source-bound claim: the marker source could not be read.
            verif_status = PublicationVerificationStatus.SERVED_MARKER_SOURCE_NOT_CORROBORATED
            digest_prefix = body_digest[:16] if body_digest else "unknown"
            summary = (
                f"Served URL {active_url} returned HTTP 200 with matching marker "
                f"'{marker}' (digest {digest_prefix}...), but the marker source in "
                f"the repository at commit '{commit_sha}' could NOT be read; "
                "source-corroborated publication is NOT awarded. This is an "
                "observed served presence, not the stronger source-bound claim."
            )
        else:
            verif_status = PublicationVerificationStatus.VERIFIED_LIVE_SERVED
            digest_prefix = body_digest[:16] if body_digest else "unknown"
            summary = (
                f"Disposable Pages site on {tgt.project_id} is genuinely published and "
                f"live. Served URL {active_url} returned HTTP 200 with matching marker "
                f"'{marker}' (digest {digest_prefix}...), corroborated against "
                f"repository source at commit '{commit_sha}'. Pages API is HTTP 403 "
                "(Developer role). This proves pre-retirement presence; unpublish "
                "remains BLOCKED_EXTERNAL."
            )
    elif l4_accessible and not l5_marker_seen:
        verif_status = PublicationVerificationStatus.MARKER_MISMATCH
        summary = (
            f"Served URL {active_url} returned HTTP 200, but distinctive marker '{marker}' "
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
            f"Served URL {active_url} returned HTTP 404; site is not served at probed URL. "
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
