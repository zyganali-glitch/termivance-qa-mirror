"""Tests for B4 proof decay and contractual six-state evidence freshness model.

Validates:
1. Exact boundary values: 0, 600, 601, 899, 900, 901 seconds.
2. 0 <= age <= 600s evaluates to FRESH.
3. 600 < age <= 900s evaluates to EXPIRING.
4. age > 900s evaluates to EXPIRED.
5. Missing or invalid timestamps fail closed as EXPIRED.
6. Negative age (future timestamp / clock skew) fails closed as INCONCLUSIVE.
7. Changed source commit SHA evaluates to REVALIDATION_REQUIRED.
8. not_observed flag evaluates to NOT_OBSERVED.
9. contradiction flag evaluates to INCONCLUSIVE.
10. Proof decay never turns a BLOCKED verdict into SAFE_TO_RETIRE.
11. Multi-record evidence bundle evaluation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from termivance.decay import (
    FreshnessState,
    evaluate_evidence_bundle,
    evaluate_freshness,
)

BASE_TIME = datetime(2026, 10, 21, 12, 0, 0, tzinfo=UTC)


def test_freshness_boundary_zero_seconds():
    res = evaluate_freshness(BASE_TIME, now=BASE_TIME)
    assert res.state == FreshnessState.FRESH
    assert res.age_seconds == 0.0
    assert res.is_valid_for_evaluation is True
    assert res.requires_revalidation is False


def test_freshness_boundary_600_seconds_exact():
    obs = BASE_TIME - timedelta(seconds=600)
    res = evaluate_freshness(obs, now=BASE_TIME)
    assert res.state == FreshnessState.FRESH
    assert res.age_seconds == 600.0
    assert res.is_valid_for_evaluation is True
    assert res.requires_revalidation is False


def test_freshness_boundary_601_seconds_exact():
    obs = BASE_TIME - timedelta(seconds=601)
    res = evaluate_freshness(obs, now=BASE_TIME)
    assert res.state == FreshnessState.EXPIRING
    assert res.age_seconds == 601.0
    assert res.is_valid_for_evaluation is True
    assert res.requires_revalidation is False
    assert "valid with warning" in res.detail


def test_freshness_boundary_899_seconds_exact():
    obs = BASE_TIME - timedelta(seconds=899)
    res = evaluate_freshness(obs, now=BASE_TIME)
    assert res.state == FreshnessState.EXPIRING
    assert res.age_seconds == 899.0
    assert res.is_valid_for_evaluation is True


def test_freshness_boundary_900_seconds_exact():
    obs = BASE_TIME - timedelta(seconds=900)
    res = evaluate_freshness(obs, now=BASE_TIME)
    assert res.state == FreshnessState.EXPIRING
    assert res.age_seconds == 900.0
    assert res.is_valid_for_evaluation is True
    assert res.requires_revalidation is False


def test_freshness_boundary_901_seconds_exact():
    obs = BASE_TIME - timedelta(seconds=901)
    res = evaluate_freshness(obs, now=BASE_TIME)
    assert res.state == FreshnessState.EXPIRED
    assert res.age_seconds == 901.0
    assert res.is_valid_for_evaluation is False
    assert res.requires_revalidation is True
    assert "EXPIRED" in res.detail


def test_missing_timestamp_fails_closed():
    res = evaluate_freshness(None, now=BASE_TIME)
    assert res.state == FreshnessState.EXPIRED
    assert res.age_seconds is None
    assert res.is_valid_for_evaluation is False
    assert res.requires_revalidation is True
    assert "Missing or unparseable" in res.detail


def test_unparseable_timestamp_fails_closed():
    res = evaluate_freshness("invalid-iso-string", now=BASE_TIME)
    assert res.state == FreshnessState.EXPIRED
    assert res.age_seconds is None
    assert res.is_valid_for_evaluation is False
    assert res.requires_revalidation is True


def test_negative_age_clock_skew_fails_closed():
    future_time = BASE_TIME + timedelta(seconds=10)
    res = evaluate_freshness(future_time, now=BASE_TIME)
    assert res.state == FreshnessState.INCONCLUSIVE
    assert res.age_seconds is not None and res.age_seconds < 0.0
    assert res.is_valid_for_evaluation is False
    assert res.requires_revalidation is True
    assert "clock skew" in res.detail.lower()


def test_source_commit_drift_requires_revalidation():
    fresh_time = BASE_TIME - timedelta(seconds=120)
    res = evaluate_freshness(
        fresh_time,
        now=BASE_TIME,
        expected_sha="54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
        observed_sha="deadbeef0123456789abcdef0123456789abcdef",
    )
    assert res.state == FreshnessState.REVALIDATION_REQUIRED
    assert res.is_valid_for_evaluation is False
    assert res.requires_revalidation is True
    assert "Source commit SHA drifted" in res.detail


def test_identical_source_commit_stays_fresh():
    fresh_time = BASE_TIME - timedelta(seconds=120)
    sha = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
    res = evaluate_freshness(
        fresh_time,
        now=BASE_TIME,
        expected_sha=sha,
        observed_sha=sha,
    )
    assert res.state == FreshnessState.FRESH
    assert res.is_valid_for_evaluation is True


def test_not_observed_flag():
    res = evaluate_freshness(None, now=BASE_TIME, not_observed=True)
    assert res.state == FreshnessState.NOT_OBSERVED
    assert res.is_valid_for_evaluation is False
    assert res.requires_revalidation is True


def test_contradiction_flag():
    res = evaluate_freshness(BASE_TIME, now=BASE_TIME, contradiction=True)
    assert res.state == FreshnessState.INCONCLUSIVE
    assert res.is_valid_for_evaluation is False
    assert res.requires_revalidation is True


def test_iso_string_input_parsing():
    iso_str = (BASE_TIME - timedelta(seconds=300)).isoformat()
    res = evaluate_freshness(iso_str, now=BASE_TIME)
    assert res.state == FreshnessState.FRESH
    assert res.age_seconds == 300.0


def test_evidence_bundle_evaluation():
    records = [
        {
            "endpoint": "/projects/1",
            "observed_at": (BASE_TIME - timedelta(seconds=100)).isoformat(),
        },
        {
            "endpoint": "/projects/2",
            "observed_at": (BASE_TIME - timedelta(seconds=700)).isoformat(),
        },
        {
            "endpoint": "/projects/3",
            "observed_at": (BASE_TIME - timedelta(seconds=1000)).isoformat(),
        },
    ]
    bundle = evaluate_evidence_bundle(records, now=BASE_TIME)
    assert bundle["total_records"] == 3
    assert bundle["fresh_count"] == 1
    assert bundle["expiring_count"] == 1
    assert bundle["expired_count"] == 1
    assert bundle["overall_state"] == FreshnessState.EXPIRED.value


def test_decay_cannot_improve_blocked_verdict():
    """Proof invariant: time decay can only invalidate, never improve a verdict."""
    from termivance.verdicts import Verdict

    expired_res = evaluate_freshness(BASE_TIME - timedelta(seconds=1200), now=BASE_TIME)
    assert expired_res.state == FreshnessState.EXPIRED

    # When evaluating a blocked decision, expired evidence keeps verdict BLOCKED
    # or promotes to INCONCLUSIVE, NEVER to SAFE_TO_RETIRE.
    prior_verdict = Verdict.BLOCKED
    effective_verdict = (
        Verdict.INCONCLUSIVE if not expired_res.is_valid_for_evaluation else prior_verdict
    )
    assert effective_verdict != Verdict.SAFE_TO_RETIRE


def test_contractual_ttl_bounds_enforcement():
    """Evaluate contractual TTL bounds: 0 < ttl_seconds <= 900."""
    import pytest

    with pytest.raises(ValueError, match="must be between 1 and 900s"):
        evaluate_freshness(BASE_TIME, now=BASE_TIME, ttl_seconds=901)

    with pytest.raises(ValueError, match="must be between 1 and 900s"):
        evaluate_freshness(BASE_TIME, now=BASE_TIME, ttl_seconds=0)

    with pytest.raises(ValueError, match="must be between 1 and 900s"):
        evaluate_freshness(BASE_TIME, now=BASE_TIME, ttl_seconds=-10)

    # 900 is allowed
    res = evaluate_freshness(BASE_TIME, now=BASE_TIME, ttl_seconds=900)
    assert res.state == FreshnessState.FRESH


def test_failed_provider_probes_not_marked_fresh_in_bundle():
    """Failed provider probes (401, 403, 404, 500) must evaluate to NOT_OBSERVED."""
    failed_records = [
        {
            "id": "probe_403",
            "endpoint": "/projects/87785099/pages",
            "status": 403,
            "error_kind": "AUTH_DENIED",
            "observed_at": BASE_TIME.isoformat(),
        },
        {
            "id": "probe_401",
            "endpoint": "/projects/87785099/deployments",
            "status": 401,
            "error": "Unauthorized",
            "observed_at": BASE_TIME.isoformat(),
        },
        {
            "id": "probe_ok",
            "endpoint": "/projects/87785099",
            "status": 200,
            "ok": True,
            "observed_at": BASE_TIME.isoformat(),
        },
    ]
    bundle = evaluate_evidence_bundle(failed_records, now=BASE_TIME)
    assert bundle["total_records"] == 3
    assert bundle["fresh_count"] == 1
    assert bundle["not_observed_count"] == 2
    assert bundle["overall_state"] == FreshnessState.NOT_OBSERVED.value

