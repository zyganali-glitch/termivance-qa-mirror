"""Deterministic, authorized Pages retirement.

This is the only module that can combine an authorization, a policy and the one
allowed mutation. It enforces, in order and fail-closed:

1. the target is not on the protected registry;
2. the policy explicitly permits this exact target and action (and is not an
   example-only policy);
3. an exact-target, unexpired, unexhausted authorization with verifiable operator
   provenance exists;
4. **fresh, exact-target provider discovery** is performed and a complete
   retirement obligation graph is evaluated;
5. the graph must return the authoritative deterministic ``SAFE_TO_RETIRE`` —
   including proven publication, effective Pages permission and a controlled
   redeployment path. Operator prose and model assessment can never substitute
   for this decision;
6. the authorization is *durably* reserved (single use across processes), then
   revalidated, then consumed immediately before mutation;
7. exactly one ``DELETE /projects/:id/pages`` call is issued;
8. the outcome is *never* treated as proof of absence: a bounded-absence verdict
   requires a proven pre-publication state and independent post-action read-back
   of the *same* URL.

No other mutation exists in Termivance, and this module can never delete a
project.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from termivance.absence import (
    DEFAULT_TTL_SECONDS,
    AbsenceProbe,
    observe_absence,
    publication_pre_state,
)
from termivance.approval_source import TRUSTED_CHANNEL, ApprovalProvenance, verify_approval_source
from termivance.attestation import ControlAttestation
from termivance.authorization import Authorization, AuthorizationError
from termivance.capsule import MutationBinding
from termivance.discovery import (
    Snapshot,
    discover_live,
    graph_from_snapshot,
    with_pages_marker,
)
from termivance.engine import DEFAULT_ACTION, Decision, evaluate
from termivance.evidence import PagesPreState
from termivance.gitlab_client import GitLabClient
from termivance.ledger import AuthorizationLedger, LedgerError
from termivance.pages import (
    MutationResult,
    PagesMutationClient,
    PublicationProbe,
    observe_publication,
)
from termivance.policy import Policy, PolicyError, assert_mutation_permitted
from termivance.protected import is_protected, protection_reason
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict


class PreflightRefused(RuntimeError):
    """Raised when preflight determines the mutation must not proceed."""


class RetirementRefused(RuntimeError):
    """Raised when the deterministic decision refuses the mutation."""


def _utc(value: datetime | None) -> datetime:
    value = value or datetime.now(tz=UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class Preflight:
    ok: bool
    target: TargetIdentity
    action: str
    authorization_binding: str | None
    checks: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "target": self.target.to_dict(),
            "action": self.action,
            "authorization_binding": self.authorization_binding,
            "checks": list(self.checks),
        }


def _check(name: str, ok: bool, detail: str) -> dict[str, object]:
    return {"check": name, "ok": ok, "detail": detail}


def preflight(
    target: TargetIdentity,
    policy: Policy,
    authorization: Authorization | None,
    *,
    action: str = DEFAULT_ACTION,
    now: datetime | None = None,
    approval_key: str | None = None,
    ledger: AuthorizationLedger | None = None,
    mutation_intent: bool = False,
    approval_project_id: int | None = None,
    approval_issue_iid: int | None = None,
    approval_client: GitLabClient | None = None,
) -> Preflight:
    """Evaluate every static precondition. Never mutates. Returns a check log.

    ``mutation_intent=True`` is the *real* execution posture (a mutation
    executor is wired in): the durable-ledger, trusted-channel and
    GitLab-authenticated-provenance gates are then hard requirements. In dry
    runs the same gates are reported as advisories so rehearsal never modifies
    anything and never pretends an approval exists.
    """
    now = _utc(now)
    checks: list[dict[str, object]] = []

    protected = is_protected(target.project_id)
    checks.append(
        _check(
            "target_not_protected",
            not protected,
            protection_reason(target.project_id) if protected else "target is not protected",
        )
    )

    policy_ok = True
    policy_detail = "policy permits this exact target/action"
    try:
        assert_mutation_permitted(policy, target, action)
    except PolicyError as exc:
        policy_ok, policy_detail = False, str(exc)
    checks.append(_check("policy_permits", policy_ok, policy_detail))

    auth_ok = authorization is not None and authorization.is_valid(now, target, action)
    auth_detail = (
        "no authorization supplied"
        if authorization is None
        else (
            f"authorization valid for exact target/action until "
            f"{authorization.expires_at.isoformat()}"
            if auth_ok
            else "authorization is missing, expired, exhausted, or bound elsewhere"
        )
    )
    checks.append(_check("authorization_valid", auth_ok, auth_detail))

    provenance_ok = False
    provenance_detail = "no authorization supplied"
    if authorization is not None:
        try:
            authorization.verify_approval(key=approval_key, require=True)
            provenance_ok = True
            provenance_detail = (
                f"operator approval verified (operator={authorization.approval.operator!r}, "
                f"statement_sha256={authorization.approval.statement_sha256[:16]}…)"
                if authorization.approval
                else "approval verified"
            )
        except AuthorizationError as exc:
            provenance_detail = str(exc)
    checks.append(_check("operator_approval_verified", provenance_ok, provenance_detail))

    # -- P0-B: only a GitLab-authenticated operator record can authorize a real
    #    mutation; every other channel is advisory in dry runs and forbidden live.
    if authorization is not None:
        channel = authorization.approval.channel if authorization.approval else None
        if mutation_intent and channel != TRUSTED_CHANNEL:
            checks.append(
                _check(
                    "approval_provenance_gitlab",
                    False,
                    f"approval channel {channel!r} cannot authorize a real mutation; "
                    "only a GitLab-authenticated operator issue can "
                    f"(channel must be {TRUSTED_CHANNEL!r})",
                )
            )
        elif not mutation_intent:
            checks.append(
                _check(
                    "approval_provenance_gitlab",
                    True,
                    f"advisory in dry runs: channel {channel!r} would still refuse a real "
                    f"mutation unless backed by a GitLab-authenticated operator issue "
                    f"({TRUSTED_CHANNEL!r})",
                )
            )
        else:
            checks.append(
                _check(
                    "approval_provenance_gitlab",
                    True,
                    f"approval channel is {TRUSTED_CHANNEL!r}; provider read-back "
                    "performed below",
                )
            )
    else:
        checks.append(
            _check(
                "approval_provenance_gitlab",
                mutation_intent is False,
                "no authorization supplied",
            )
        )

    approval_record: ApprovalProvenance | None = None
    if authorization is not None and authorization.approval is not None:
        if mutation_intent:
            gate_ok = False
            gate_detail = ""
            if approval_project_id is None or approval_issue_iid is None:
                gate_detail = (
                    "a real mutation requires the GitLab approval record reference "
                    "(--approval-project-id / --approval-issue-iid) to verify the "
                    "operator-issued GitLab issue out-of-band"
                )
            elif approval_client is None:
                gate_detail = (
                    "no GitLab read access was supplied to read back the operator "
                    "approval record; provenance cannot be verified"
                )
            else:
                try:
                    approval_record = verify_approval_source(
                        approval_client,
                        authorization,
                        project_id=approval_project_id,
                        issue_iid=approval_issue_iid,
                        now=now,
                    )
                except AuthorizationError as exc:
                    gate_detail = str(exc)
                else:
                    gate_ok = True
                    gate_detail = (
                        "GitLab-authenticated operator approval verified: issue "
                        f"{approval_record.issue_iid} in project "
                        f"{approval_record.project_id}, author "
                        f"{approval_record.author_username!r}, created "
                        f"{approval_record.created_at.isoformat()}"
                    )
            checks.append(_check("gitlab_approval_record_verified", gate_ok, gate_detail))
        else:
            checks.append(
                _check(
                    "gitlab_approval_record_verified",
                    True,
                    "advisory in dry runs: a real mutation additionally verifies the "
                    f"operator-issued {TRUSTED_CHANNEL!r} issue by reading it back "
                    "from GitLab immediately before dispatch",
                )
            )

    # -- P0-A: a real mutation requires a durable, single-use ledger.
    if mutation_intent:
        if ledger is None:
            ledger_ok, ledger_detail = False, (
                "no durable single-use authorization ledger was supplied; a real "
                "mutation can never execute without one (--ledger)"
            )
        elif not ledger.path_is_durable():
            ledger_ok, ledger_detail = False, (
                f"ledger path {ledger.path!s} is not durable (terminal/wastebin/dead "
                "storage)"
            )
        else:
            try:
                ledger.health_check()
            except LedgerError as exc:
                ledger_ok, ledger_detail = False, str(exc)
            else:
                ledger_ok, ledger_detail = True, (
                    f"durable ledger present and ready at {ledger.path}; the "
                    "single-use reservation is sealed immediately before dispatch"
                )
        checks.append(_check("durable_ledger_required", ledger_ok, ledger_detail))
    else:
        checks.append(
            _check(
                "durable_ledger_required",
                True,
                "advisory in dry runs: a real mutation additionally requires a durable, "
                "single-use authorization ledger",
            )
        )

    ok = all(bool(c["ok"]) for c in checks)
    return Preflight(
        ok=ok,
        target=target,
        action=action,
        authorization_binding=authorization.binding() if authorization is not None else None,
        checks=tuple(checks),
    )


@dataclass(frozen=True, slots=True)
class Eligibility:
    """The exact-target discovery + graph evaluation bound to one mutation."""

    snapshot: Snapshot
    snapshot_digest: str
    decision: Decision
    publication: PublicationProbe | None
    pre_state: PagesPreState | None
    established_at: datetime

    @property
    def eligible(self) -> bool:
        return self.decision.verdict == Verdict.SAFE_TO_RETIRE

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot_digest": self.snapshot_digest,
            "snapshot_observed_at": _utc(self.snapshot.observed_at).isoformat(),
            "classification": self.snapshot.classification.value,
            "decision": self.decision.to_dict(),
            "publication": self.publication.to_dict() if self.publication else None,
            "pre_state": self.pre_state.to_dict() if self.pre_state else None,
            "established_at": _utc(self.established_at).isoformat(),
            "eligible": self.eligible,
        }


def _digest(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(canonical.encode("utf-8")).hexdigest()


def establish_eligibility(
    target: TargetIdentity,
    policy: Policy,
    authorization: Authorization | None,
    *,
    read_client: GitLabClient,
    action: str = DEFAULT_ACTION,
    served_url: str | None = None,
    marker: str | None = None,
    control_attestation: ControlAttestation | None = None,
    approval_key: str | None = None,
    now: datetime | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> Eligibility:
    """Fresh exact-target discovery, publication proof and full graph evaluation."""
    observed = _utc(now)
    snapshot = discover_live(
        read_client, target, action=action, now=observed, ttl_seconds=ttl_seconds
    )

    if control_attestation is not None:
        control_attestation.verify(target, key=approval_key)
        record = control_attestation.to_record(now=observed, ttl=timedelta(seconds=ttl_seconds))
        snapshot = replace(snapshot, records=(*snapshot.records, record))

    publication: PublicationProbe | None = None
    pre_state: PagesPreState | None = None
    if served_url and marker:
        publication = observe_publication(read_client, target, served_url, marker, now=observed)
        pre_state = publication_pre_state(publication)
        snapshot = with_pages_marker(
            snapshot,
            served_url=served_url,
            marker_observed=publication.marker_observed,
            marker=marker,
            now=observed,
        )

    graph = graph_from_snapshot(snapshot)
    decision = evaluate(
        graph, policy=policy, action=action, now=observed, authorization=authorization
    )
    return Eligibility(
        snapshot=snapshot,
        snapshot_digest=_digest(snapshot.to_dict()),
        decision=decision,
        publication=publication,
        pre_state=pre_state,
        established_at=observed,
    )


@dataclass(frozen=True, slots=True)
class RetirementReceipt:
    """The complete evidence record of one authorized retirement attempt."""

    target: TargetIdentity
    action: str
    authorization_binding: str | None
    preflight: Preflight
    eligibility: Eligibility | None
    revalidation: Eligibility | None
    mutation: MutationResult | None
    absence: AbsenceProbe | None
    mutation_attempted: bool
    verdict: Verdict
    operation_id: str
    ledger_path: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "termivance.retirement_receipt/v2",
            "target": self.target.to_dict(),
            "action": self.action,
            "authorization_binding": self.authorization_binding,
            "operation_id": self.operation_id,
            "mutation_attempted": self.mutation_attempted,
            "verdict": self.verdict.value,
            "preflight": self.preflight.to_dict(),
            "eligibility": self.eligibility.to_dict() if self.eligibility else None,
            "revalidation": self.revalidation.to_dict() if self.revalidation else None,
            "mutation": self.mutation.to_dict() if self.mutation else None,
            "absence": self.absence.to_dict() if self.absence else None,
            "ledger_path": self.ledger_path,
            "notes": list(self.notes),
            "authoritative": self.verdict
            in {Verdict.RETIRED, Verdict.OBSERVED_ABSENT, Verdict.RESURRECTION_CONTROLLED},
            "note": (
                "A successful mutation is not proof of absence. OBSERVED_ABSENT requires a "
                "proven pre-retirement publication, an accepted authorized unpublish, and "
                "independent Pages-API and served-URL read-back of the same URL within the "
                "stated observation interval."
            ),
        }


def _blocked(
    target: TargetIdentity,
    action: str,
    pre: Preflight,
    *,
    operation_id: str,
    verdict: Verdict = Verdict.BLOCKED,
    eligibility: Eligibility | None = None,
    revalidation: Eligibility | None = None,
    mutation: MutationResult | None = None,
    notes: tuple[str, ...] = (),
    ledger_path: str | None = None,
) -> RetirementReceipt:
    return RetirementReceipt(
        target=target,
        action=action,
        authorization_binding=pre.authorization_binding,
        preflight=pre,
        eligibility=eligibility,
        revalidation=revalidation,
        mutation=mutation,
        absence=None,
        mutation_attempted=False,
        verdict=verdict,
        operation_id=operation_id,
        ledger_path=ledger_path,
        notes=notes,
    )


def _decision_note(eligibility: Eligibility) -> str:
    failing = [
        f"{o['kind']}={o['status']}"
        for o in eligibility.decision.obligations
        if o.get("mandatory") and o.get("status") != "SATISFIED"
    ]
    return (
        f"deterministic decision was {eligibility.decision.verdict.value}; "
        f"unresolved mandatory obligations: {', '.join(failing) or 'none'}"
    )


def retire_pages(
    target: TargetIdentity,
    policy: Policy,
    authorization: Authorization | None,
    *,
    mutation_client: PagesMutationClient | None = None,
    read_client: GitLabClient | None = None,
    served_url: str | None = None,
    marker: str | None = None,
    snapshot: Snapshot | None = None,
    control_attestation: ControlAttestation | None = None,
    ledger: AuthorizationLedger | None = None,
    approval_key: str | None = None,
    approval_project_id: int | None = None,
    approval_issue_iid: int | None = None,
    operation_id: str | None = None,
    now: datetime | None = None,
    action: str = DEFAULT_ACTION,
) -> RetirementReceipt:
    """Run preflight, the deterministic decision, then the single authorized mutation.

    ``mutation_client`` may be omitted for a dry run; in that case no network
    mutation is possible. A dry run still requires fresh discovery (``read_client``)
    or a recorded ``snapshot``: without either, eligibility cannot be established
    and the receipt is ``BLOCKED``.

    A *real* mutation (``mutation_client is not None``) additionally requires,
    in this order and failing closed:

    1. a trustworthy operator approval whose provenance is verified by reading
       the operator-issued GitLab approval issue back from the provider;
    2. a durable single-use authorization ledger (``ledger``) that passes its
       readiness self-check — then reserved, revalidated and consumed.
    """
    observed = _utc(now)
    op_id = operation_id or f"op-{secrets.token_hex(8)}"
    ledger_path = str(ledger.path) if ledger is not None else None
    mutation_intent = mutation_client is not None

    pre = preflight(
        target,
        policy,
        authorization,
        action=action,
        now=observed,
        approval_key=approval_key,
        ledger=ledger,
        mutation_intent=mutation_intent,
        approval_project_id=approval_project_id,
        approval_issue_iid=approval_issue_iid,
        approval_client=read_client,
    )
    if not pre.ok:
        notes = ["static preflight refused the mutation"]
        failed = [str(c["detail"]) for c in pre.checks if not c["ok"]]
        notes.extend(f"  - {d}" for d in failed)
        return _blocked(
            target,
            action,
            pre,
            operation_id=op_id,
            notes=tuple(notes),
            ledger_path=ledger_path,
        )

    eligibility: Eligibility | None = None
    if read_client is not None:
        eligibility = establish_eligibility(
            target,
            policy,
            authorization,
            read_client=read_client,
            action=action,
            served_url=served_url,
            marker=marker,
            control_attestation=control_attestation,
            approval_key=approval_key,
            now=observed,
        )
    elif snapshot is not None:
        graph = graph_from_snapshot(snapshot)
        decision = evaluate(
            graph, policy=policy, action=action, now=observed, authorization=authorization
        )
        eligibility = Eligibility(
            snapshot=snapshot,
            snapshot_digest=_digest(snapshot.to_dict()),
            decision=decision,
            publication=None,
            pre_state=None,
            established_at=observed,
        )
    else:
        return _blocked(
            target,
            action,
            pre,
            operation_id=op_id,
            notes=(
                "no fresh discovery source or recorded snapshot was supplied: eligibility "
                "cannot be established, so no mutation may be attempted",
            ),
            ledger_path=ledger_path,
        )

    assert eligibility is not None
    if not eligibility.eligible:
        return _blocked(
            target,
            action,
            pre,
            operation_id=op_id,
            eligibility=eligibility,
            notes=(_decision_note(eligibility),),
            ledger_path=ledger_path,
        )

    if mutation_client is None:
        # Dry run: the deterministic decision passed but no executor is wired in.
        return _blocked(
            target,
            action,
            pre,
            operation_id=op_id,
            eligibility=eligibility,
            verdict=Verdict.SAFE_TO_RETIRE,
            notes=("dry run: no mutation executor was supplied",),
            ledger_path=ledger_path,
        )

    # Immediate revalidation against the live provider, after the durable
    # reservation point but before any DELETE is dispatched.
    if read_client is not None:
        revalidation = establish_eligibility(
            target,
            policy,
            authorization,
            read_client=read_client,
            action=action,
            served_url=served_url,
            marker=marker,
            control_attestation=control_attestation,
            approval_key=approval_key,
            now=observed,
        )
        if not revalidation.eligible:
            return _blocked(
                target,
                action,
                pre,
                operation_id=op_id,
                eligibility=eligibility,
                revalidation=revalidation,
                notes=(
                    "immediate revalidation refused the mutation: " + _decision_note(revalidation),
                ),
                ledger_path=ledger_path,
            )
    else:
        revalidation = eligibility

    assert authorization is not None  # guaranteed by preflight

    # Durable single-use reservation. Written before the mutation; a crash after
    # this point burns the authorization (conservative).
    assert ledger is not None and authorization is not None  # preflight guarantees both
    try:
        ledger.health_check()
    except LedgerError as exc:
        return _blocked(
            target,
            action,
            pre,
            operation_id=op_id,
            eligibility=eligibility,
            revalidation=revalidation,
            notes=(f"durable authorization ledger is not ready: {exc}",),
            ledger_path=ledger_path,
        )
    try:
        ledger.consume(authorization, operation_id=op_id, now=observed)
    except LedgerError as exc:
        return _blocked(
            target,
            action,
            pre,
            operation_id=op_id,
            eligibility=eligibility,
            revalidation=revalidation,
            notes=(f"durable authorization reservation refused: {exc}",),
            ledger_path=ledger_path,
        )

    # Revalidate and consume immediately before mutation.
    authorization.consume(observed, target, action)

    mutation = mutation_client.unpublish_pages(target, now=observed)

    absence: AbsenceProbe | None = None
    if mutation.accepted and read_client is not None and served_url:
        # The live dispatch binding is the strongest provenance a claim can
        # carry: this process itself issued the accepted, endpoint-restricted
        # mutation and the ledger sealed it durably beforehand.
        assert ledger is not None and authorization is not None  # preflight guarantees
        binding = MutationBinding(
            target=target,
            action=action,
            endpoint=mutation.endpoint,
            operation_id=op_id,
            authorization_binding=pre.authorization_binding,
            accepted=mutation.accepted,
            status=mutation.status,
            pre_state=eligibility.pre_state or PagesPreState(
                served_url=served_url,
                marker=marker or "",
                marker_observed=False,
                deployment_present=False,
                observed_at=observed,
            ),
            ledger_entry=ledger.consumption_record(
                authorization.binding(), operation_id=op_id
            ),
            source="live_dispatch",
        )
        absence = observe_absence(
            read_client,
            target,
            served_url,
            pre_state=eligibility.pre_state,
            mutation_receipt=binding,
            now=observed,
        )

    notes: list[str] = []
    if not mutation.accepted:
        verdict = Verdict.INCONCLUSIVE
        notes.append(
            "the mutation was not accepted; nothing is proven removed and no absence is claimed"
        )
    elif absence is not None:
        verdict = absence.verdict
        if verdict != Verdict.OBSERVED_ABSENT:
            notes.append(
                "the mutation was accepted but bounded absence was not proven; the weaker "
                "honest verdict is retained"
            )
    else:
        verdict = Verdict.RETIRED
        notes.append(
            "the mutation was accepted but no independent read-back was performed; RETIRED "
            "records the action, it does not claim absence"
        )

    if ledger is not None:
        ledger.finalize(
            authorization.binding(),
            outcome=mutation.error_kind or ("ACCEPTED" if mutation.accepted else "REFUSED"),
        )

    return RetirementReceipt(
        target=target,
        action=action,
        authorization_binding=pre.authorization_binding,
        preflight=pre,
        eligibility=eligibility,
        revalidation=revalidation,
        mutation=mutation,
        absence=absence,
        mutation_attempted=True,
        verdict=verdict,
        operation_id=op_id,
        ledger_path=ledger_path,
        notes=tuple(notes),
    )


__all__ = [
    "AuthorizationError",
    "Eligibility",
    "Preflight",
    "PreflightRefused",
    "RetirementReceipt",
    "RetirementRefused",
    "establish_eligibility",
    "preflight",
    "retire_pages",
]
