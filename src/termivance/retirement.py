"""Deterministic, authorized Pages retirement.

This is the only module that can combine an authorization, a policy and the one
allowed mutation. It enforces, in order and fail-closed:

1. the target is not on the protected registry;
2. the policy explicitly permits this exact target and action (and is not an
   example-only policy);
3. an exact-target, unexpired, unexhausted authorization exists;
4. the authorization is revalidated and consumed immediately before mutation;
5. exactly one ``DELETE /projects/:id/pages`` call is issued;
6. the outcome is *never* treated as proof of absence.

No other mutation exists in Termivance, and this module can never delete a
project.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from termivance.absence import AbsenceProbe, observe_absence
from termivance.authorization import Authorization, AuthorizationError
from termivance.engine import DEFAULT_ACTION
from termivance.gitlab_client import GitLabClient
from termivance.pages import MutationResult, PagesMutationClient
from termivance.policy import Policy, PolicyError, assert_mutation_permitted
from termivance.protected import is_protected, protection_reason
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict


class PreflightRefused(RuntimeError):
    """Raised when preflight determines the mutation must not proceed."""


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
) -> Preflight:
    """Evaluate every precondition. Never mutates. Returns a full check log."""
    now = (now or datetime.now(tz=UTC)).astimezone(UTC)
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

    ok = all(bool(c["ok"]) for c in checks)
    return Preflight(
        ok=ok,
        target=target,
        action=action,
        authorization_binding=authorization.binding() if authorization is not None else None,
        checks=tuple(checks),
    )


@dataclass(frozen=True, slots=True)
class RetirementReceipt:
    """The complete evidence record of one authorized retirement attempt."""

    target: TargetIdentity
    action: str
    authorization_binding: str | None
    preflight: Preflight
    mutation: MutationResult | None
    absence: AbsenceProbe | None
    mutation_attempted: bool
    verdict: Verdict

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "termivance.retirement_receipt/v1",
            "target": self.target.to_dict(),
            "action": self.action,
            "authorization_binding": self.authorization_binding,
            "mutation_attempted": self.mutation_attempted,
            "verdict": self.verdict.value,
            "preflight": self.preflight.to_dict(),
            "mutation": self.mutation.to_dict() if self.mutation else None,
            "absence": self.absence.to_dict() if self.absence else None,
            "authoritative": self.verdict
            in {Verdict.RETIRED, Verdict.OBSERVED_ABSENT, Verdict.RESURRECTION_CONTROLLED},
            "note": (
                "A successful mutation is not proof of absence. OBSERVED_ABSENT requires an "
                "independent Pages-API and served-URL read-back within the observation interval."
            ),
        }


def retire_pages(
    target: TargetIdentity,
    policy: Policy,
    authorization: Authorization | None,
    *,
    mutation_client: PagesMutationClient | None = None,
    read_client: GitLabClient | None = None,
    served_url: str | None = None,
    now: datetime | None = None,
    action: str = DEFAULT_ACTION,
) -> RetirementReceipt:
    """Run preflight, then (only if it passes) the single authorized mutation.

    ``mutation_client`` may be omitted for a dry run; in that case no network
    mutation is possible.
    """
    now = (now or datetime.now(tz=UTC)).astimezone(UTC)
    pre = preflight(target, policy, authorization, action=action, now=now)
    if not pre.ok:
        return RetirementReceipt(
            target=target,
            action=action,
            authorization_binding=pre.authorization_binding,
            preflight=pre,
            mutation=None,
            absence=None,
            mutation_attempted=False,
            verdict=Verdict.BLOCKED,
        )

    if mutation_client is None:
        # Dry run: preflight passed but no executor is wired in.
        return RetirementReceipt(
            target=target,
            action=action,
            authorization_binding=pre.authorization_binding,
            preflight=pre,
            mutation=None,
            absence=None,
            mutation_attempted=False,
            verdict=Verdict.SAFE_TO_RETIRE,
        )

    # Revalidate and consume immediately before mutation.
    assert authorization is not None  # guaranteed by preflight
    authorization.consume(now, target, action)

    mutation = mutation_client.unpublish_pages(target, now=now)

    absence: AbsenceProbe | None = None
    if mutation.accepted and read_client is not None and served_url:
        absence = observe_absence(read_client, target, served_url, now=now)

    if not mutation.accepted:
        # A failed mutation removed nothing. This is not a proven-retired state;
        # it is unresolved and must be surfaced honestly.
        verdict = Verdict.INCONCLUSIVE
    elif absence is not None:
        # Only an independent read-back may award OBSERVED_ABSENT. If the site is
        # still served (or evidence is stale/contradictory) we keep the weaker,
        # honest verdict.
        verdict = absence.verdict
    else:
        # The mutation was accepted but no independent read-back was performed.
        # RETIRED records that the action executed; it does not claim absence.
        verdict = Verdict.RETIRED

    return RetirementReceipt(
        target=target,
        action=action,
        authorization_binding=pre.authorization_binding,
        preflight=pre,
        mutation=mutation,
        absence=absence,
        mutation_attempted=True,
        verdict=verdict,
    )


__all__ = [
    "AuthorizationError",
    "Preflight",
    "PreflightRefused",
    "RetirementReceipt",
    "preflight",
    "retire_pages",
]
