"""Tests for B4 Resurrection Monitoring and Current-Truth Downgrade.

Validates:
1. Exact-target monitoring re-observing provider state;
2. Current-truth downgrade from OBSERVED_ABSENT to RESURRECTED_NOT_ABSENT on reappearance;
3. Current-truth downgrade to REDEPLOYMENT_MECHANISM_ACTIVE when CI mechanism is active;
4. Current-truth downgrade to STALE_REVALIDATION_REQUIRED when historical receipt expires (>900s);
5. Current-truth downgrade to INCONCLUSIVE_PROBE_FAILED when provider probes fail;
6. Source commit drift detection between historical receipt and current observation;
7. Anti-self-award standard: RESURRECTION_CONTROLLED is never awarded merely because monitor exists;
8. Immutable historical truth: monitoring does not mutate or rewrite previous receipts;
9. Mere mechanism presence in CI proves redeployment risk, not an active site.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from termivance.decay import FreshnessState
from termivance.resurrection_monitor import (
    CurrentTruthStatus,
    RedeploymentRisk,
    ResurrectionControlStatus,
    TargetCurrentObservation,
    monitor_resurrection,
)
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 21, 12, 0, 0, tzinfo=UTC)
TARGET = TargetIdentity(
    87785099,
    "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
    "GITLAB_PAGES_SITE",
)
COMMIT_SHA = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"


def _make_obs(
    *,
    commit_sha: str = COMMIT_SHA,
    has_mechanism: bool = True,
    signals: tuple[str, ...] = ("pages_true", "pages_keyword"),
    pages_api_status: int = 403,
    served_status: int | None = 200,
    marker_observed: bool = True,
    observed_at: datetime = NOW,
) -> TargetCurrentObservation:
    return TargetCurrentObservation(
        project_id=TARGET.project_id,
        full_path=TARGET.full_path,
        default_branch="main",
        commit_sha=commit_sha,
        ci_config_present=True,
        redeployment_mechanism=has_mechanism,
        redeployment_signals=signals,
        pages_api_status=pages_api_status,
        pages_api_accessible=(pages_api_status < 400),
        served_url="https://gitlab-ai-hackathon.gitlab.io/.../termivance-b3-disposable-pages-demo/",
        served_http_status=served_status,
        served_marker_observed=marker_observed,
        observed_at=observed_at,
    )


def test_actual_reappearance_downgrades_to_resurrected_not_absent():
    """When a target was previously OBSERVED_ABSENT and now serves its marker,
    current truth is downgraded to RESURRECTED_NOT_ABSENT."""
    historical_truth = {
        "verdict": "SAFE_TO_RETIRE",
        "observed_absence": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": (NOW - timedelta(seconds=200)).isoformat(),
    }
    current_obs = _make_obs(served_status=200, marker_observed=True)

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.RESURRECTED_NOT_ABSENT
    assert report.resurrection_control == ResurrectionControlStatus.NOT_CLAIMED
    assert any("absence is REVERSED" in diff for diff in report.diff_reasons)
    assert report.freshness_state == FreshnessState.FRESH


def test_redeployment_mechanism_active_downgrades_absence():
    """When historical absence was claimed, but current CI has active pages deployment job,
    current truth is downgraded to REDEPLOYMENT_MECHANISM_ACTIVE."""
    historical_truth = {
        "verdict": "SAFE_TO_RETIRE",
        "observed_absence": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": (NOW - timedelta(seconds=200)).isoformat(),
    }
    # Marker not currently served (404), but mechanism exists in CI
    current_obs = _make_obs(served_status=404, marker_observed=False, has_mechanism=True)

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.REDEPLOYMENT_MECHANISM_ACTIVE
    assert report.redeployment_risk == RedeploymentRisk.MECHANISM_PRESENT
    assert any("active CI deployment mechanism exists" in diff for diff in report.diff_reasons)


def test_stale_historical_receipt_downgrades_to_revalidation_required():
    """When historical receipt is older than 900s TTL, current truth requires revalidation."""
    historical_truth = {
        "verdict": "SAFE_TO_RETIRE",
        "observed_absence": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": (NOW - timedelta(seconds=1200)).isoformat(),  # 1200s > 900s
    }
    # Probes return 404, mechanism neutralized, but receipt is stale
    current_obs = _make_obs(
        served_status=404, marker_observed=False, has_mechanism=False, signals=()
    )

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.STALE_REVALIDATION_REQUIRED
    assert report.freshness_state == FreshnessState.EXPIRED
    assert any("EXPIRED" in diff for diff in report.diff_reasons)


def test_inaccessible_provider_probe_downgrades_to_inconclusive():
    """Failed provider probes cannot prove continued absence; they evaluate to INCONCLUSIVE."""
    historical_truth = {
        "verdict": "SAFE_TO_RETIRE",
        "observed_absence": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": (NOW - timedelta(seconds=100)).isoformat(),
    }
    # Pages API returns 403, served URL probe timed out / inaccessible (None)
    current_obs = _make_obs(
        served_status=None,
        marker_observed=False,
        pages_api_status=403,
        has_mechanism=False,
        signals=(),
    )

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.INCONCLUSIVE_PROBE_FAILED
    assert any("inaccessible" in diff for diff in report.diff_reasons)


def test_source_commit_drift_detected():
    """Commit drift between historical receipt and current observation is reported."""
    historical_truth = {
        "verdict": "BLOCKED",
        "observed_absence": "NOT_CLAIMED",
        "commit_sha": "original_commit_sha_0123456789abcdef",
        "observed_at": (NOW - timedelta(seconds=100)).isoformat(),
    }
    current_obs = _make_obs(commit_sha="new_drifted_commit_sha_9876543210fedcba")

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert any("commit drifted" in diff for diff in report.diff_reasons)
    assert any("Revalidate" in act for act in report.required_revalidation_actions)


def test_continued_absence_legitimately_observed():
    """When receipt is fresh, commit matches, mechanism is neutralized, and served URL is 404."""
    historical_truth = {
        "verdict": "SAFE_TO_RETIRE",
        "observed_absence": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": (NOW - timedelta(seconds=100)).isoformat(),
    }
    current_obs = _make_obs(
        served_status=404,
        marker_observed=False,
        has_mechanism=False,
        signals=(),
        pages_api_status=404,
    )

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.current_truth == CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED
    assert report.resurrection_control == ResurrectionControlStatus.NOT_CLAIMED


def test_anti_self_award_resurrection_control():
    """RESURRECTION_CONTROLLED is never awarded merely because a monitor exists."""
    historical_truth = {
        "verdict": "SAFE_TO_RETIRE",
        "observed_absence": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": (NOW - timedelta(seconds=50)).isoformat(),
    }
    current_obs = _make_obs(
        served_status=404, marker_observed=False, has_mechanism=False, signals=()
    )

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=historical_truth,
        now=NOW,
    )

    assert report.resurrection_control == ResurrectionControlStatus.NOT_CLAIMED
    assert report.resurrection_control != "RESURRECTION_CONTROLLED"


def test_historical_receipt_immobility():
    """Monitoring preserves historical truth dict without mutating it."""
    orig_history = {
        "verdict": "SAFE_TO_RETIRE",
        "observed_absence": "OBSERVED_ABSENT",
        "commit_sha": COMMIT_SHA,
        "observed_at": (NOW - timedelta(seconds=300)).isoformat(),
    }
    orig_copy = dict(orig_history)
    current_obs = _make_obs(served_status=200, marker_observed=True)

    report = monitor_resurrection(
        TARGET,
        current_observation=current_obs,
        historical_truth=orig_history,
        now=NOW,
    )

    assert orig_history == orig_copy
    assert report.historical_truth == orig_copy
    assert report.current_truth == CurrentTruthStatus.RESURRECTED_NOT_ABSENT
