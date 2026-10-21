"""Deterministic Exact-Target Resurrection Monitor and Current-Truth Downgrade.

Implements an on-demand, read-only exact-target monitor that re-observes current
provider state, compares against historical transition receipts without mutating
them, and downgrades current-truth classifications when reappearance or redeployment
conditions are detected.

Critical evidence boundaries:
1. Mechanism Presence != Active Resurrection: A Pages publishing job in `.gitlab-ci.yml`
   proves a potential redeployment mechanism, not an actual resurrected site.
2. Observed Reappearance: A newly observed served marker after previously verified absence
   proves actual reappearance (current truth downgraded to RESURRECTED_NOT_ABSENT).
3. Probe Failure != Continued Absence: A failed provider probe (401/403/timeout) cannot
   prove absence; it evaluates to INCONCLUSIVE_PROBE_FAILED.
4. Scheduled CI != Resurrection Prevention: A scheduled job is only an execution
   mechanism, not prevention.
5. Receipt Immobility: Historical transition receipts remain immutable audit records;
   current-truth downgrade updates the current assessment without rewriting the past.
6. Anti-Self-Award Standard: `RESURRECTION_CONTROLLED` is NEVER awarded merely because
   a monitor exists. It requires verified neutralization or active tripwire control.
7. Verified Historical Receipt Mandatory: Unverified caller claims cannot award
   CONTINUED_ABSENCE_OBSERVED or downgrade to RESURRECTED_NOT_ABSENT; they evaluate to
   HISTORICAL_RECEIPT_UNVERIFIED.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from termivance.decay import FreshnessState, evaluate_freshness
from termivance.discovery import detect_pages_mechanism
from termivance.gitlab_client import GitLabClient
from termivance.pages import https_get, marker_observed, read_pages_state
from termivance.protected import is_protected, protection_reason
from termivance.target import TargetIdentity

if TYPE_CHECKING:
    pass

RESURRECTION_MONITOR_SCHEMA = "termivance.resurrection_monitor/v1"
DEFAULT_TTL_SECONDS = 900


class CurrentTruthStatus(StrEnum):
    """Deterministic classification of current target truth."""

    RESURRECTED_NOT_ABSENT = "RESURRECTED_NOT_ABSENT"
    REDEPLOYMENT_MECHANISM_ACTIVE = "REDEPLOYMENT_MECHANISM_ACTIVE"
    STALE_REVALIDATION_REQUIRED = "STALE_REVALIDATION_REQUIRED"
    INCONCLUSIVE_PROBE_FAILED = "INCONCLUSIVE_PROBE_FAILED"
    CONTINUED_ABSENCE_OBSERVED = "CONTINUED_ABSENCE_OBSERVED"
    ABSENCE_NOT_CLAIMED = "ABSENCE_NOT_CLAIMED"
    TARGET_MUTATION_BLOCKED = "TARGET_MUTATION_BLOCKED"
    HISTORICAL_RECEIPT_UNVERIFIED = "HISTORICAL_RECEIPT_UNVERIFIED"
    CURRENT_OBSERVATION_MISMATCH = "CURRENT_OBSERVATION_MISMATCH"


class RedeploymentRisk(StrEnum):
    """Classification of redeployment mechanism risk."""

    MECHANISM_PRESENT = "MECHANISM_PRESENT"
    NO_MECHANISM_FOUND = "NO_MECHANISM_FOUND"
    CONFIG_INACCESSIBLE = "CONFIG_INACCESSIBLE"


class ResurrectionControlStatus(StrEnum):
    """Classification of resurrection control."""

    NOT_CLAIMED = "NOT_CLAIMED"
    MECHANISM_NEUTRALIZED = "MECHANISM_NEUTRALIZED"
    ACTIVE_CONTROL_VERIFIED = "ACTIVE_CONTROL_VERIFIED"


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


def validate_historical_absence_receipt(
    history: dict[str, object] | None,
    target: TargetIdentity,
    *,
    ledger: object | None = None,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """Validate that historical truth is an authentic v3 retirement receipt proving absence.

    This is NOT a receipt-shape check. A dictionary with a plausible schema,
    ``mutation_attempted: true``, ``accepted: true``, ``verdict:
    OBSERVED_ABSENT`` and a parseable timestamp is not proof. The actual
    authoritative receipt chain is validated by reusing the established
    contracts:

    1. history is a non-empty dictionary with schema
       ``termivance.retirement_receipt/v3``;
    2. the target is not protected (reject 87779099, 87777871, 87786164) and
       the receipt is bound to exactly this target (project ID *and* full
       path);
    3. the recorded verdict is ``OBSERVED_ABSENT``;
    4. the full mutation receipt chain validates through
       :func:`termivance.capsule.validate_mutation_receipt` against a durable
       authorization ledger in state ``CONSUMED_ACCEPTED``: exact project ID,
       full path and resource kind; authorized pre-state with independently
       observed original publication (marker digest binding); the exact
       approved action and an accepted provider DELETE on the exact Pages
       endpoint; durable single-use ledger evidence; temporal and SHA
       coherence; receipt integrity;
    5. the post-action absence section records independent read-backs of the
       Pages API and of the *same* served URL, observed after the mutation
       was requested, with an ``OBSERVED_ABSENT`` bounded verdict.
    """
    if not isinstance(history, dict) or not history:
        return False, "No historical receipt dictionary supplied."

    if is_protected(target.project_id):
        reason = protection_reason(target.project_id)
        return False, f"Target project {target.project_id} is protected: {reason}."

    schema = history.get("schema")
    if schema != "termivance.retirement_receipt/v3":
        return False, (
            f"Unrecognized schema: '{schema}' (requires termivance.retirement_receipt/v3)."
        )

    hist_target = history.get("target")
    if not isinstance(hist_target, dict):
        return False, "Historical receipt lacks target dictionary."
    hist_pid = hist_target.get("project_id")
    if hist_pid != target.project_id:
        return False, f"Target project ID mismatch: expected {target.project_id}, got {hist_pid}."
    hist_path = str(hist_target.get("full_path") or "")
    if hist_path != target.full_path:
        return False, (
            f"Target full path mismatch: expected {target.full_path!r}, got {hist_path!r}."
        )

    if isinstance(hist_pid, int) and is_protected(hist_pid):
        return False, f"Historical receipt targets protected project {hist_pid}."

    verdict = history.get("verdict")
    if verdict != "OBSERVED_ABSENT":
        return False, f"Historical receipt verdict is '{verdict}', not 'OBSERVED_ABSENT'."

    # Full mutation receipt chain against the durable ledger. Without a
    # durable ledger the receipt cannot be authenticated at all.
    from termivance.capsule import ReceiptValidationError, validate_mutation_receipt

    if ledger is None:
        return False, (
            "No durable authorization ledger was supplied; a locally recorded "
            "receipt cannot be authenticated without the durable single-use "
            "ledger evidence of the exact operation."
        )
    try:
        binding = validate_mutation_receipt(history, target, ledger=ledger, now=now)
    except ReceiptValidationError as exc:
        return False, f"Historical receipt failed the authoritative receipt chain: {exc}"
    if not binding.accepted:
        return False, "Historical receipt mutation was not accepted by provider."

    # Post-action absence read-backs: independent observations of the Pages
    # API and the same served URL, recorded after the mutation was requested.
    absence = history.get("absence")
    if not isinstance(absence, dict):
        return False, "Historical receipt lacks the post-action absence read-back section."
    absence_verdict = str(absence.get("verdict") or "")
    if absence_verdict != "OBSERVED_ABSENT":
        return False, (
            f"Post-action absence verdict is '{absence_verdict}', not 'OBSERVED_ABSENT'; "
            "an unverified post-state cannot prove a previous absence."
        )
    pages_api = absence.get("pages_api")
    if not isinstance(pages_api, dict) or pages_api.get("status") is None:
        return False, "Post-action absence lacks an independent Pages API read-back."
    if pages_api.get("status") in (401, 403):
        return False, (
            "Post-action Pages API read-back was access-denied (HTTP "
            f"{pages_api.get('status')}); an access boundary is not absence."
        )
    served = absence.get("served_url")
    if not isinstance(served, dict) or served.get("http_status") != 404:
        return False, (
            "Post-action absence lacks an independent served-URL 404 read-back "
            "of the same URL."
        )
    observation = absence.get("observation")
    receipt_served_url = None
    if isinstance(observation, dict):
        receipt_served_url = observation.get("served_url")
    if not receipt_served_url:
        return False, "Historical receipt does not record the served URL that was observed."
    pre_state_served_url = getattr(binding.pre_state, "served_url", None)
    if pre_state_served_url and receipt_served_url != pre_state_served_url:
        return False, (
            "Post-action absence observed a different URL than the pre-state "
            "publication; absence must be read back at the same exact URL."
        )

    # Temporal coherence: the absence read-back must postdate the mutation.
    try:
        mutation = history.get("mutation")
        requested_at = (
            datetime.fromisoformat(str(mutation.get("requested_at")))
            if isinstance(mutation, dict) and mutation.get("requested_at")
            else None
        )
        absence_observed = (
            datetime.fromisoformat(str(observation.get("observed_at")))
            if isinstance(observation, dict) and observation.get("observed_at")
            else None
        )
        if requested_at is None or absence_observed is None:
            return False, "Historical receipt lacks mutation/absence observation timestamps."
        if absence_observed < requested_at:
            return False, (
                "Clock inversion: the post-action absence observation predates "
                "the mutation request; temporal coherence is violated."
            )
    except (TypeError, ValueError) as exc:
        return False, f"Historical receipt timestamps are malformed: {exc}"

    ts = (
        history.get("observed_at")
        or (history.get("preflight", {}) or {}).get("observed_at")
        or (history.get("absence", {}) or {}).get("observed_at")
    )
    if not ts:
        return False, "Historical receipt lacks valid observation timestamp."
    try:
        datetime.fromisoformat(str(ts))
    except Exception:  # noqa: BLE001
        return False, f"Historical receipt observation timestamp is malformed: '{ts}'."

    return True, "Historical retirement receipt verified against the durable ledger chain."


@dataclass(frozen=True, slots=True)
class TargetCurrentObservation:
    """Current live observation of target provider surfaces."""

    project_id: int
    full_path: str
    default_branch: str
    commit_sha: str | None
    ci_config_present: bool
    redeployment_mechanism: bool
    redeployment_signals: tuple[str, ...]
    pages_api_status: int | None
    pages_api_accessible: bool
    served_url: str | None
    served_http_status: int | None
    served_marker_observed: bool
    observed_at: datetime
    pages_api_deployment_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "full_path": self.full_path,
            "default_branch": self.default_branch,
            "commit_sha": self.commit_sha,
            "ci_config_present": self.ci_config_present,
            "redeployment_mechanism": self.redeployment_mechanism,
            "redeployment_signals": list(self.redeployment_signals),
            "pages_api_status": self.pages_api_status,
            "pages_api_accessible": self.pages_api_accessible,
            "pages_api_deployment_count": self.pages_api_deployment_count,
            "served_url": self.served_url,
            "served_http_status": self.served_http_status,
            "served_marker_observed": self.served_marker_observed,
            "observed_at": _utc(self.observed_at).isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ResurrectionMonitoringReport:
    """The immutable monitoring outcome comparing historical truth with current facts."""

    target: TargetIdentity
    evaluated_at: datetime
    historical_truth: dict[str, object]
    current_observation: TargetCurrentObservation
    current_truth: CurrentTruthStatus
    redeployment_risk: RedeploymentRisk
    resurrection_control: ResurrectionControlStatus
    diff_reasons: tuple[str, ...]
    required_revalidation_actions: tuple[str, ...]
    freshness_state: FreshnessState

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": RESURRECTION_MONITOR_SCHEMA,
            "authority": "DETERMINISTIC_READ_ONLY_MONITOR",
            "target": self.target.to_dict(),
            "evaluated_at": _utc(self.evaluated_at).isoformat(),
            "historical_truth": dict(self.historical_truth),
            "current_observation": self.current_observation.to_dict(),
            "current_truth": self.current_truth.value,
            "redeployment_risk": self.redeployment_risk.value,
            "resurrection_control": self.resurrection_control.value,
            "diff_reasons": list(self.diff_reasons),
            "required_revalidation_actions": list(self.required_revalidation_actions),
            "freshness_state": self.freshness_state.value,
            "invariants": [
                "Mechanism presence proves redeployment risk, not active resurrection.",
                "Newly observed served marker proves actual reappearance.",
                "Failed provider probe cannot prove continued absence.",
                "Historical transition receipts remain immutable audit records.",
                "RESURRECTION_CONTROLLED is never awarded merely because a monitor exists.",
                "Unverified historical claims cannot award CONTINUED_ABSENCE_OBSERVED.",
                "The current observation must bind to the same exact target and URL "
                "as the historical receipt, not merely a caller-supplied project ID.",
                "A schema-correct receipt without the durable ledger chain and "
                "post-action read-backs is not proof of a previous absence.",
                "A verified historical absence requires a nonempty exact current "
                "served URL matching the authenticated historical URL; a missing "
                "or unrelated current URL proves nothing about the authorized URL.",
                "Continued absence requires the current CI configuration to be "
                "positively observed; CONFIG_INACCESSIBLE is uncertainty, not a "
                "proven negative.",
                "The current observation must be fresh within the evaluation TTL, "
                "independently of the historical receipt's original timestamp.",
            ],
        }


def observe_target_surfaces(
    client: GitLabClient,
    target: TargetIdentity,
    *,
    served_url: str | None = None,
    marker: str | None = None,
    now: datetime | None = None,
    timeout: float = 10.0,
    http_getter: Callable[[str, float], tuple[int | None, str | None, str]] | None = None,
) -> TargetCurrentObservation:
    """Perform read-only GET queries on target provider surfaces."""
    evaluated_at = _utc(now)

    # 1. Branch and commit
    branch_res = client.get_json(f"/projects/{target.project_id}/repository/branches/main")
    commit_sha = None
    default_branch = "main"
    if branch_res.ok and isinstance(branch_res.data, dict):
        commit_dict = branch_res.data.get("commit")
        if isinstance(commit_dict, dict):
            commit_sha = commit_dict.get("id")

    # 2. CI configuration
    ci_ref = commit_sha or "main"
    ci_res = client.get_text(
        f"/projects/{target.project_id}/repository/files/.gitlab-ci.yml/raw?ref={ci_ref}"
    )
    ci_present = bool(ci_res.ok and ci_res.status == 200)
    has_mechanism = False
    signals: list[str] = []
    if ci_present and isinstance(ci_res.data, str):
        mech_bool, sig_list = detect_pages_mechanism(ci_res.data)
        has_mechanism = bool(mech_bool)
        signals = sorted(sig_list)

    # 3. Pages API state
    pages_state = read_pages_state(client, target, now=evaluated_at)

    # 4. Served URL probe
    http_status = None
    marker_seen = False
    if served_url:
        getter = http_getter or https_get
        s_status, _s_err, body = getter(served_url, timeout=timeout)
        http_status = s_status
        if marker and body:
            marker_seen = marker_observed(body, marker)

    return TargetCurrentObservation(
        project_id=target.project_id,
        full_path=target.full_path,
        default_branch=default_branch,
        commit_sha=commit_sha,
        ci_config_present=ci_present,
        redeployment_mechanism=has_mechanism,
        redeployment_signals=tuple(signals),
        pages_api_status=pages_state.status,
        pages_api_accessible=pages_state.accessible,
        pages_api_deployment_count=pages_state.deployment_count,
        served_url=served_url,
        served_http_status=http_status,
        served_marker_observed=marker_seen,
        observed_at=evaluated_at,
    )


def monitor_resurrection(
    target: TargetIdentity,
    *,
    current_observation: TargetCurrentObservation,
    historical_truth: dict[str, object] | None = None,
    ledger: object | None = None,
    now: datetime | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> ResurrectionMonitoringReport:
    """Evaluate current provider observation against historical truth.

    Implements strict current-truth downgrade semantics:
    - Protects protected targets permanently (TARGET_MUTATION_BLOCKED).
    - Validates that the current observation is actually for the same target
      (project ID *and* full path) and, when both are recorded, the same
      served URL as the historical receipt — a caller-supplied project ID
      alone is not sufficient (CURRENT_OBSERVATION_MISMATCH).
    - Requires a verified historical absence receipt
      (termivance.retirement_receipt/v3 authenticated against a durable
      authorization ledger, with post-action read-backs) before evaluating
      downgrade from OBSERVED_ABSENT.
    - When a verified historical absence is the prerequisite, requires a
      nonempty exact current served URL matching the authenticated
      historical URL; a missing or unrelated current URL is refused
      (CURRENT_OBSERVATION_MISMATCH) and a synthetic served status is never
      attributed to the authorized URL.
    - Requires the current CI configuration to be positively observed before
      claiming the redeployment mechanism is absent; an inaccessible CI
      configuration is reported as uncertainty (CONFIG_INACCESSIBLE), never
      substituted with a proven negative.
    - Validates the freshness of the current observation independently of
      the historical receipt's original timestamp; continued absence is
      never awarded from expired, target-mismatched, failed or unbound
      current observations.
    - If historical truth is missing, malformed, or unverified: reports
      HISTORICAL_RECEIPT_UNVERIFIED and evaluates baseline truth without assuming prior absence.
    - If previously verified OBSERVED_ABSENT:
      - If served URL returns HTTP 200 with matching marker -> RESURRECTED_NOT_ABSENT
      - If redeployment mechanism detected in current CI -> REDEPLOYMENT_MECHANISM_ACTIVE
      - If historical receipt expired (>900s) -> STALE_REVALIDATION_REQUIRED
      - If provider probe failed (401/403/timeout) -> INCONCLUSIVE_PROBE_FAILED
      - If multi-surface corroboration verifies absence -> CONTINUED_ABSENCE_OBSERVED
    """
    evaluated_at = _utc(now)
    history = dict(historical_truth or {})
    diff_reasons: list[str] = []
    revalidation_actions: list[str] = []

    # Protected target check
    if is_protected(target.project_id):
        reason = protection_reason(target.project_id)
        return ResurrectionMonitoringReport(
            target=target,
            evaluated_at=evaluated_at,
            historical_truth=history,
            current_observation=current_observation,
            current_truth=CurrentTruthStatus.TARGET_MUTATION_BLOCKED,
            redeployment_risk=RedeploymentRisk.NO_MECHANISM_FOUND,
            resurrection_control=ResurrectionControlStatus.NOT_CLAIMED,
            diff_reasons=(f"Target project {target.project_id} is protected: {reason}.",),
            required_revalidation_actions=(
                "Retirement is permanently prohibited on protected projects.",
            ),
            freshness_state=FreshnessState.FRESH,
        )

    # Current observation must be for the same exact target, not merely a
    # caller-supplied project ID.
    observation_target_ok = (
        current_observation.project_id == target.project_id
        and current_observation.full_path == target.full_path
    )
    receipt_served_url: str | None = None
    if isinstance(history.get("absence"), dict):
        absence_obs = history["absence"].get("observation")  # type: ignore[union-attr]
        if isinstance(absence_obs, dict):
            receipt_served_url = absence_obs.get("served_url")
    observation_url_ok = True
    if (
        receipt_served_url
        and current_observation.served_url
        and current_observation.served_url != receipt_served_url
    ):
        observation_url_ok = False

    if not observation_target_ok or not observation_url_ok:
        mismatch_reasons: list[str] = []
        if not observation_target_ok:
            mismatch_reasons.append(
                f"Current observation is for project {current_observation.project_id} "
                f"({current_observation.full_path}), expected {target.project_id} "
                f"({target.full_path})."
            )
        if not observation_url_ok:
            mismatch_reasons.append(
                f"Current observation probes URL {current_observation.served_url!r}, "
                f"but the historical receipt observed {receipt_served_url!r}."
            )
        return ResurrectionMonitoringReport(
            target=target,
            evaluated_at=evaluated_at,
            historical_truth=history,
            current_observation=current_observation,
            current_truth=CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH,
            redeployment_risk=RedeploymentRisk.NO_MECHANISM_FOUND,
            resurrection_control=ResurrectionControlStatus.NOT_CLAIMED,
            diff_reasons=(
                "CURRENT_OBSERVATION_MISMATCH: " + " ".join(mismatch_reasons),
            ),
            required_revalidation_actions=(
                "Re-observe the exact target (project ID, full path and served URL) "
                "bound by the historical receipt.",
            ),
            freshness_state=FreshnessState.NOT_OBSERVED,
        )

    # Evaluate historical receipt verification (full authoritative chain)
    receipt_verified = False
    if history:
        receipt_verified, receipt_reason = validate_historical_absence_receipt(
            history, target, ledger=ledger, now=evaluated_at
        )
        if not receipt_verified:
            diff_reasons.append(f"Historical receipt unverified: {receipt_reason}")
            revalidation_actions.append(
                "Supply an authentic termivance.retirement_receipt/v3 with an "
                "OBSERVED_ABSENT verdict, authenticated against the durable "
                "authorization ledger of the exact operation."
            )

    # Strict current-URL binding to the AUTHENTICATED historical receipt URL.
    # A verified historical absence is the prerequisite for any current-truth
    # downgrade, so the current observation must carry a nonempty exact served
    # URL matching the authenticated receipt URL. A missing or unrelated
    # current URL can never support continued absence, actual reappearance, or
    # any inference that a synthetic served status came from the authorized
    # URL.
    if receipt_verified and receipt_served_url:
        if not current_observation.served_url:
            return ResurrectionMonitoringReport(
                target=target,
                evaluated_at=evaluated_at,
                historical_truth=history,
                current_observation=current_observation,
                current_truth=CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH,
                redeployment_risk=RedeploymentRisk.NO_MECHANISM_FOUND,
                resurrection_control=ResurrectionControlStatus.NOT_CLAIMED,
                diff_reasons=(
                    "CURRENT_SERVED_URL_MISSING: the verified historical absence "
                    f"receipt observed {receipt_served_url!r}, but the current "
                    "observation records no served URL; a missing current URL "
                    "can never support continued absence or reappearance.",
                ),
                required_revalidation_actions=(
                    "Re-observe the exact served URL bound by the authenticated "
                    "historical receipt.",
                ),
                freshness_state=FreshnessState.NOT_OBSERVED,
            )
        if current_observation.served_url != receipt_served_url:
            return ResurrectionMonitoringReport(
                target=target,
                evaluated_at=evaluated_at,
                historical_truth=history,
                current_observation=current_observation,
                current_truth=CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH,
                redeployment_risk=RedeploymentRisk.NO_MECHANISM_FOUND,
                resurrection_control=ResurrectionControlStatus.NOT_CLAIMED,
                diff_reasons=(
                    "CURRENT_SERVED_URL_UNBOUND: the current observation probes "
                    f"{current_observation.served_url!r}, but the authenticated "
                    f"historical receipt observed {receipt_served_url!r}; a "
                    "synthetic served status from an unrelated URL is never "
                    "evidence about the authorized URL.",
                ),
                required_revalidation_actions=(
                    "Re-observe the exact served URL bound by the authenticated "
                    "historical receipt.",
                ),
                freshness_state=FreshnessState.NOT_OBSERVED,
            )

    # Historical truth facts
    prior_verdict = str(history.get("verdict", "BLOCKED")) if receipt_verified else "BLOCKED"
    prior_sha = (
        history.get("commit_sha") or (history.get("preflight", {}) or {}).get("commit_sha")
    )
    prior_observed_at = (
        history.get("observed_at")
        or (history.get("preflight", {}) or {}).get("observed_at")
        or (history.get("absence", {}) or {}).get("observed_at")
    )

    # Evaluate freshness of historical observation
    freshness = evaluate_freshness(
        str(prior_observed_at) if prior_observed_at else None,
        now=evaluated_at,
        expected_sha=str(prior_sha) if prior_sha else None,
        observed_sha=current_observation.commit_sha,
        ttl_seconds=ttl_seconds,
    )

    # Validate the freshness of the CURRENT observation independently of the
    # historical receipt's original timestamp: an expired (or otherwise
    # invalid) current observation can never award continued absence, no
    # matter how fresh or authentic the historical receipt is.
    current_freshness = evaluate_freshness(
        current_observation.observed_at,
        now=evaluated_at,
        ttl_seconds=ttl_seconds,
    )

    # Check commit drift
    if prior_sha and current_observation.commit_sha and prior_sha != current_observation.commit_sha:
        diff_reasons.append(
            f"Source commit drifted from '{prior_sha}' to '{current_observation.commit_sha}'."
        )
        revalidation_actions.append("Revalidate target repository CI and deployment mechanisms.")

    # Check redeployment mechanism
    if current_observation.redeployment_mechanism:
        redeployment_risk = RedeploymentRisk.MECHANISM_PRESENT
        signals_list = list(current_observation.redeployment_signals)
        diff_reasons.append(
            f"Surviving CI redeployment mechanism detected: {signals_list}."
        )
    elif not current_observation.ci_config_present:
        redeployment_risk = RedeploymentRisk.CONFIG_INACCESSIBLE
        diff_reasons.append("CI configuration is not accessible to observing identity.")
    else:
        redeployment_risk = RedeploymentRisk.NO_MECHANISM_FOUND

    # Authoritative current truth derivation
    current_truth: CurrentTruthStatus

    # Case: History supplied but failed receipt validation
    if history and not receipt_verified:
        current_truth = CurrentTruthStatus.HISTORICAL_RECEIPT_UNVERIFIED
        if (
            current_observation.served_marker_observed
            and current_observation.served_http_status == 200
        ):
            diff_reasons.append(
                "Target site is currently published and serving its marker, "
                "but historical absence receipt was unverified."
            )
        elif current_observation.pages_api_status in (401, 403):
            diff_reasons.append(
                "Provider Pages API returned access restriction; baseline cannot be verified."
            )

    # Case 1: Actual reappearance observed (served marker seen) after verified absence
    elif (
        receipt_verified
        and current_observation.served_marker_observed
        and current_observation.served_http_status == 200
    ):
        current_truth = CurrentTruthStatus.RESURRECTED_NOT_ABSENT
        diff_reasons.append(
            "CRITICAL: Target resource was previously verified OBSERVED_ABSENT, but matching "
            "served marker was independently observed live at served URL; absence is REVERSED."
        )
        revalidation_actions.append(
            "Conduct full security audit and re-evaluate retirement obligations."
        )

    # Case 2: Historical absence verified, but CI mechanism is active
    elif receipt_verified and current_observation.redeployment_mechanism:
        current_truth = CurrentTruthStatus.REDEPLOYMENT_MECHANISM_ACTIVE
        diff_reasons.append(
            "Historical absence was verified, but an active CI deployment mechanism exists "
            "that could republish the site on next pipeline execution."
        )
        revalidation_actions.append("Neutralize create-pages CI job or attest control.")

    # Case 3: Historical receipt has expired
    elif receipt_verified and freshness.state == FreshnessState.EXPIRED:
        current_truth = CurrentTruthStatus.STALE_REVALIDATION_REQUIRED
        age_str = f"{freshness.age_seconds:.1f}s"
        diff_reasons.append(
            f"Historical absence receipt has EXPIRED (age {age_str} > {ttl_seconds}s TTL)."
        )
        revalidation_actions.append("Perform fresh independent provider read-back probes.")

    # Case 3b: the CURRENT observation itself is stale or invalid. Continued
    # absence is never awarded from an expired current observation, even with
    # an otherwise valid historical receipt.
    elif receipt_verified and not current_freshness.is_valid_for_evaluation:
        current_truth = CurrentTruthStatus.STALE_REVALIDATION_REQUIRED
        age_str = (
            f"{current_freshness.age_seconds:.1f}s"
            if current_freshness.age_seconds is not None
            else "unknown"
        )
        diff_reasons.append(
            f"CURRENT_OBSERVATION_STALE: the current observation (age {age_str}, "
            f"state {current_freshness.state.value}) is outside the {ttl_seconds}s "
            "evaluation window; continued absence cannot be awarded from a stale "
            "current observation."
        )
        revalidation_actions.append(
            "Re-observe the target's current provider surfaces now."
        )

    # Case 4: Probe failed or inaccessible (multi-surface corroboration
    # required!). An unobserved current CI configuration is included here:
    # CONFIG_INACCESSIBLE is uncertainty, never a proven negative, so the
    # absence of a redeployment mechanism cannot be claimed from it.
    elif receipt_verified and (
        current_observation.pages_api_status in (401, 403, 500, 502, 503)
        or current_observation.pages_api_status is None
        or current_observation.served_http_status in (None, 0, 401, 403, 500, 502, 503)
        or not current_observation.ci_config_present
    ):
        current_truth = CurrentTruthStatus.INCONCLUSIVE_PROBE_FAILED
        if (
            current_observation.pages_api_status in (401, 403, 500, 502, 503)
            or current_observation.pages_api_status is None
            or current_observation.served_http_status in (None, 0, 401, 403, 500, 502, 503)
        ):
            diff_reasons.append(
                "Provider surfaces are inaccessible or returned errors (Pages API: "
                f"{current_observation.pages_api_status}, "
                f"Served URL: {current_observation.served_http_status}); "
                "unknown cannot be promoted to continued absence."
            )
        if not current_observation.ci_config_present:
            diff_reasons.append(
                "CURRENT_CI_CONFIGURATION_NOT_OBSERVED: the current CI "
                "configuration was not observed; the absence of a redeployment "
                "mechanism is unproven (CONFIG_INACCESSIBLE is uncertainty, not "
                "a proven negative)."
            )
        revalidation_actions.append("Retry probes with appropriate network/access permissions.")

    # Case 5: Continued absence legitimately observed across ALL surfaces:
    # - Pages API reports undeployed (status 404 or 200 with deployment_count == 0)
    # - Served URL returns HTTP 404 and marker NOT observed
    # - Current CI configuration POSITIVELY observed with NO redeployment mechanism
    # - Current observation itself is fresh within the evaluation window
    # - Evidence is fresh and valid for evaluation
    elif (
        receipt_verified
        and current_observation.ci_config_present
        and (
            current_observation.pages_api_status == 404
            or (
                current_observation.pages_api_accessible
                and current_observation.pages_api_status == 200
                and current_observation.pages_api_deployment_count == 0
            )
        )
        and current_observation.served_http_status == 404
        and not current_observation.served_marker_observed
        and not current_observation.redeployment_mechanism
        and freshness.is_valid_for_evaluation
        and current_freshness.is_valid_for_evaluation
    ):
        current_truth = CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED

    # Case 6: Baseline unmutated / not claimed
    else:
        if (
            current_observation.served_marker_observed
            and current_observation.served_http_status == 200
        ):
            current_truth = CurrentTruthStatus.TARGET_MUTATION_BLOCKED
            diff_reasons.append(
                "Target Pages site is currently published and serving its distinctive marker."
            )
        elif prior_verdict == "BLOCKED":
            current_truth = CurrentTruthStatus.TARGET_MUTATION_BLOCKED
        else:
            current_truth = CurrentTruthStatus.ABSENCE_NOT_CLAIMED

    # Resurrection control standard: never awarded merely because monitor exists
    resurrection_control = ResurrectionControlStatus.NOT_CLAIMED

    return ResurrectionMonitoringReport(
        target=target,
        evaluated_at=evaluated_at,
        historical_truth=history,
        current_observation=current_observation,
        current_truth=current_truth,
        redeployment_risk=redeployment_risk,
        resurrection_control=resurrection_control,
        diff_reasons=tuple(diff_reasons),
        required_revalidation_actions=tuple(revalidation_actions),
        freshness_state=freshness.state,
    )
