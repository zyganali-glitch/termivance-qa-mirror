"""Deterministic proof decay and evidence freshness revalidation engine.

Implements the contractual six-state evidence freshness model:
- FRESH: observation age 0 <= t <= 600s (contractual TTL = 900s). Valid for graph evaluation.
- EXPIRING: observation age 600 < t <= 900s. Valid with warning.
- EXPIRED: observation age t > 900s. Invalid for mutation authorization; triggers refusal.
- REVALIDATION_REQUIRED: source commit SHA has changed, or prerequisite evidence expired.
- NOT_OBSERVED: evidence was never gathered or endpoint returned an error.
- INCONCLUSIVE: conflicting observations, unparseable timestamp, or clock skew.

Boundary specifications:
- Exact tested points: 0, 600, 601, 899, 900, 901 seconds.
- Missing or invalid timestamps fail closed (EXPIRED / INCONCLUSIVE).
- Negative age (future timestamp / clock skew) fails closed (INCONCLUSIVE).
- Changed source SHA triggers REVALIDATION_REQUIRED.
- Expiring evidence cannot be extended by reopening a saved JSON file or viewer refresh.
- Time expiration can never turn a BLOCKED verdict into SAFE_TO_RETIRE.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

MAX_TTL_SECONDS: int = 900
FRESH_THRESHOLD_SECONDS: int = 600
PROOF_DECAY_SCHEMA: str = "termivance.proof_decay/v1"


class FreshnessState(StrEnum):
    """The six deterministic freshness lifecycle states."""

    FRESH = "FRESH"
    EXPIRING = "EXPIRING"
    EXPIRED = "EXPIRED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    NOT_OBSERVED = "NOT_OBSERVED"
    INCONCLUSIVE = "INCONCLUSIVE"


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


def _parse_timestamp(raw: str | datetime | None) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return _utc(raw)
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        dt = datetime.fromisoformat(raw.strip())
        return _utc(dt)
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True, slots=True)
class FreshnessResult:
    """The deterministic freshness evaluation result for one observation."""

    state: FreshnessState
    age_seconds: float | None
    ttl_seconds: int
    observed_at: datetime | None
    evaluated_at: datetime
    detail: str
    expected_sha: str | None = None
    observed_sha: str | None = None
    requires_revalidation: bool = False

    @property
    def is_valid_for_evaluation(self) -> bool:
        """True only if the observation is within the valid TTL window (FRESH or EXPIRING)."""
        return self.state in {FreshnessState.FRESH, FreshnessState.EXPIRING}

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": PROOF_DECAY_SCHEMA,
            "state": self.state.value,
            "age_seconds": round(self.age_seconds, 3) if self.age_seconds is not None else None,
            "ttl_seconds": self.ttl_seconds,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "evaluated_at": self.evaluated_at.isoformat(),
            "detail": self.detail,
            "expected_sha": self.expected_sha,
            "observed_sha": self.observed_sha,
            "requires_revalidation": self.requires_revalidation,
            "is_valid_for_evaluation": self.is_valid_for_evaluation,
        }


def evaluate_freshness(
    observed_at: str | datetime | None,
    *,
    now: datetime | None = None,
    expected_sha: str | None = None,
    observed_sha: str | None = None,
    ttl_seconds: int = MAX_TTL_SECONDS,
    fresh_threshold_seconds: int = FRESH_THRESHOLD_SECONDS,
    not_observed: bool = False,
    contradiction: bool = False,
    clock_skew_tolerance_seconds: float = 0.0,
) -> FreshnessResult:
    """Deterministically evaluate the freshness state of provider evidence.

    Follows fail-closed boundary rules:
    - If not_observed: returns NOT_OBSERVED.
    - If contradiction: returns INCONCLUSIVE.
    - If missing or unparseable timestamp: fails closed -> EXPIRED.
    - If future timestamp (age < -tolerance): fails closed -> INCONCLUSIVE (clock skew).
    - If expected_sha != observed_sha (both non-empty): returns REVALIDATION_REQUIRED.
    - Otherwise compares age against fresh threshold and TTL:
      - 0 <= age <= 600: FRESH
      - 600 < age <= 900: EXPIRING
      - age > 900: EXPIRED
    """
    if ttl_seconds <= 0 or ttl_seconds > MAX_TTL_SECONDS:
        raise ValueError(
            f"ttl_seconds ({ttl_seconds}) must be between 1 and {MAX_TTL_SECONDS}s."
        )
    if fresh_threshold_seconds < 0 or fresh_threshold_seconds > ttl_seconds:
        raise ValueError(
            f"fresh_threshold_seconds ({fresh_threshold_seconds}) "
            f"must be between 0 and {ttl_seconds}s."
        )

    evaluated_at = _utc(now)

    if not_observed:
        return FreshnessResult(
            state=FreshnessState.NOT_OBSERVED,
            age_seconds=None,
            ttl_seconds=ttl_seconds,
            observed_at=None,
            evaluated_at=evaluated_at,
            detail="Evidence was not observed by the provider probe.",
            expected_sha=expected_sha,
            observed_sha=observed_sha,
            requires_revalidation=True,
        )

    if contradiction:
        return FreshnessResult(
            state=FreshnessState.INCONCLUSIVE,
            age_seconds=None,
            ttl_seconds=ttl_seconds,
            observed_at=None,
            evaluated_at=evaluated_at,
            detail="Contradictory observations detected across provider surfaces.",
            expected_sha=expected_sha,
            observed_sha=observed_sha,
            requires_revalidation=True,
        )

    parsed_time = _parse_timestamp(observed_at)
    if parsed_time is None:
        return FreshnessResult(
            state=FreshnessState.EXPIRED,
            age_seconds=None,
            ttl_seconds=ttl_seconds,
            observed_at=None,
            evaluated_at=evaluated_at,
            detail="Missing or unparseable observation timestamp; failing closed as EXPIRED.",
            expected_sha=expected_sha,
            observed_sha=observed_sha,
            requires_revalidation=True,
        )

    age = (evaluated_at - parsed_time).total_seconds()

    # Clock skew check: future timestamp beyond negative tolerance
    if age < -clock_skew_tolerance_seconds:
        return FreshnessResult(
            state=FreshnessState.INCONCLUSIVE,
            age_seconds=age,
            ttl_seconds=ttl_seconds,
            observed_at=parsed_time,
            evaluated_at=evaluated_at,
            detail=(
                f"Negative observation age ({age:.2f}s) indicates future timestamp or "
                "local clock skew; failing closed as INCONCLUSIVE."
            ),
            expected_sha=expected_sha,
            observed_sha=observed_sha,
            requires_revalidation=True,
        )

    # Source commit drift check: commit changed -> revalidation required
    if expected_sha and observed_sha and expected_sha != observed_sha:
        return FreshnessResult(
            state=FreshnessState.REVALIDATION_REQUIRED,
            age_seconds=age,
            ttl_seconds=ttl_seconds,
            observed_at=parsed_time,
            evaluated_at=evaluated_at,
            detail=(
                f"Source commit SHA drifted from expected '{expected_sha}' to "
                f"observed '{observed_sha}'; provider facts must be revalidated."
            ),
            expected_sha=expected_sha,
            observed_sha=observed_sha,
            requires_revalidation=True,
        )

    # Boundary comparison: 0 <= age <= 600 -> FRESH
    if 0.0 <= age <= float(fresh_threshold_seconds):
        return FreshnessResult(
            state=FreshnessState.FRESH,
            age_seconds=age,
            ttl_seconds=ttl_seconds,
            observed_at=parsed_time,
            evaluated_at=evaluated_at,
            detail=f"Evidence is FRESH (age {age:.1f}s <= {fresh_threshold_seconds}s).",
            expected_sha=expected_sha,
            observed_sha=observed_sha,
            requires_revalidation=False,
        )

    # 600 < age <= 900 -> EXPIRING
    if float(fresh_threshold_seconds) < age <= float(ttl_seconds):
        return FreshnessResult(
            state=FreshnessState.EXPIRING,
            age_seconds=age,
            ttl_seconds=ttl_seconds,
            observed_at=parsed_time,
            evaluated_at=evaluated_at,
            detail=(
                f"Evidence is EXPIRING (age {age:.1f}s in ({fresh_threshold_seconds}s, "
                f"{ttl_seconds}s]); valid with warning, refresh recommended."
            ),
            expected_sha=expected_sha,
            observed_sha=observed_sha,
            requires_revalidation=False,
        )

    # age > 900 -> EXPIRED
    return FreshnessResult(
        state=FreshnessState.EXPIRED,
        age_seconds=age,
        ttl_seconds=ttl_seconds,
        observed_at=parsed_time,
        evaluated_at=evaluated_at,
        detail=(
            f"Evidence has EXPIRED (age {age:.1f}s > {ttl_seconds}s TTL); "
            "cannot be used for mutation preflights or authoritative absence."
        ),
        expected_sha=expected_sha,
        observed_sha=observed_sha,
        requires_revalidation=True,
    )


def evaluate_evidence_bundle(
    records: list[dict[str, object]],
    *,
    now: datetime | None = None,
    expected_sha: str | None = None,
    observed_sha: str | None = None,
    ttl_seconds: int = MAX_TTL_SECONDS,
) -> dict[str, object]:
    """Evaluate freshness for a collection of observation records."""
    evaluated_at = _utc(now)
    results: list[dict[str, object]] = []
    overall_state = FreshnessState.FRESH

    priority = {
        FreshnessState.EXPIRED: 5,
        FreshnessState.INCONCLUSIVE: 4,
        FreshnessState.NOT_OBSERVED: 3,
        FreshnessState.REVALIDATION_REQUIRED: 2,
        FreshnessState.EXPIRING: 1,
        FreshnessState.FRESH: 0,
    }

    worst_priority = 0

    for rec in records:
        obs_time = rec.get("observed_at") or rec.get("observed_at_utc")
        status_code = rec.get("status")
        error_kind = rec.get("error_kind")
        is_probe_failure = bool(
            error_kind in {"AUTH_DENIED", "TIMEOUT", "NOT_FOUND", "CONNECTION_ERROR", "MALFORMED"}
            or (isinstance(status_code, int) and status_code in (401, 403, 404, 500, 502, 503))
            or rec.get("ok") is False
        )
        if is_probe_failure:
            item_res = FreshnessResult(
                state=FreshnessState.NOT_OBSERVED,
                age_seconds=None,
                ttl_seconds=ttl_seconds,
                observed_at=None,
                evaluated_at=evaluated_at,
                detail=(
                    f"Provider probe failed ({error_kind or status_code}); "
                    "unobserved facts cannot be FRESH."
                ),
                expected_sha=expected_sha,
                observed_sha=observed_sha,
                requires_revalidation=True,
            )
        else:
            item_res = evaluate_freshness(
                str(obs_time) if obs_time else None,
                now=evaluated_at,
                expected_sha=expected_sha,
                observed_sha=observed_sha,
                ttl_seconds=ttl_seconds,
            )
        res_dict = item_res.to_dict()
        res_dict["endpoint"] = rec.get("endpoint")
        res_dict["kind"] = rec.get("kind")
        results.append(res_dict)

        if priority[item_res.state] > worst_priority:
            worst_priority = priority[item_res.state]
            overall_state = item_res.state

    return {
        "schema": PROOF_DECAY_SCHEMA,
        "evaluated_at": evaluated_at.isoformat(),
        "overall_state": overall_state.value,
        "total_records": len(records),
        "fresh_count": sum(1 for r in results if r["state"] == FreshnessState.FRESH.value),
        "expiring_count": sum(1 for r in results if r["state"] == FreshnessState.EXPIRING.value),
        "expired_count": sum(1 for r in results if r["state"] == FreshnessState.EXPIRED.value),
        "revalidation_required_count": sum(
            1 for r in results if r["state"] == FreshnessState.REVALIDATION_REQUIRED.value
        ),
        "not_observed_count": sum(
            1 for r in results if r["state"] == FreshnessState.NOT_OBSERVED.value
        ),
        "inconclusive_count": sum(
            1 for r in results if r["state"] == FreshnessState.INCONCLUSIVE.value
        ),
        "records": results,
    }
