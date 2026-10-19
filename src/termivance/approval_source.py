"""GitLab-authenticated operator approval provenance (P0-B trust boundary).

A local JSON document — or model text — naming an "operator" proves nothing:
anyone with a credential able to create issues could write its own
``operator_approval`` block, read it back through its own client, and call that
"consent". A single self-consistent comparison can therefore never establish a
trusted operator on its own. Verification is bound to an **independent operator
trust policy**, supplied from outside the executor's authorization-writing
capability:

* the policy (``termivance.operator_trust/v1``) lists the trusted operators the
  *organization* recognizes — username **and** the provider-issued user ID, so a
  renamed or spoofed username cannot replay trust;
* the policy states which projects may carry operator approval issues, when an
  approval goes stale, and whether the operator-held HMAC signature is
  mandatory;
* the approval issue is read back from GitLab verbatim at verification time and
  its binding content (endpoint, action, nonce, binding digest, target, validity
  window) must appear as exact, unambiguous lines — duplicated or edited lines
  are refused instead of matched by substring search;
* by default the approval block must also carry a valid HMAC signature made with
  an operator-held key (``TERMIVANCE_APPROVAL_HMAC_KEY``) that the executor does
  not possess: possessing a GitLab PAT for the *executor* account can never
  manufacture an operator approval under this policy.

The record is read back from the provider (``GET /projects/:id/issues/:iid``)
verbatim, before any mutation may be dispatched — the local JSON file only
supplies the *expected* content, never the proof. Closing the issue revokes the
approval; a policy revocation of the operator identity likewise refuses all
future verification. The executor never creates this record itself: it is
created in the operator's browser session, outside the agent's control.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from termivance.authorization import Authorization, AuthorizationError
from termivance.gitlab_client import GitLabClient

#: The only operator-approval channel that can authorize a *real mutation*.
TRUSTED_CHANNEL = "gitlab_issue"

#: Tolerance when comparing provider ``created_at`` against authorization
#: issuance/expiration times (different machines, transport latency).
CLOCK_SKEW = timedelta(minutes=5)

TRUST_SCHEMA = "termivance.operator_trust/v1"


class TrustPolicyError(AuthorizationError):
    """Raised when an operator trust policy is missing, malformed or untrusted."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class TrustedOperator:
    """One operator identity trusted by the organization's policy."""

    username: str
    user_id: int

    def to_dict(self) -> dict[str, object]:
        return {"username": self.username, "user_id": self.user_id}


@dataclass(frozen=True, slots=True)
class OperatorTrustPolicy:
    """The independently established set of identities allowed to approve.

    This document is *operator-owned*: it is never generated, rewritten or
    auto-discovered by the executor. Verification fails closed when it is
    missing for a real mutation.
    """

    schema_version: int
    trusted_operators: tuple[TrustedOperator, ...]
    approval_project_ids: tuple[int, ...]
    signature_required: bool = True
    approval_freshness_seconds: int = 86_400
    revocations: tuple[tuple[str, datetime], ...] = ()

    def operator_for(self, username: str) -> TrustedOperator | None:
        for operator in self.trusted_operators:
            if operator.username == username:
                return operator
        return None

    def is_revoked(self, username: str, now: datetime) -> datetime | None:
        for revoked_user, revoked_at in self.revocations:
            if revoked_user == username and revoked_at <= now:
                return revoked_at
        return None

    def describe(self) -> str:
        names = ", ".join(op.username for op in self.trusted_operators)
        return (
            f"trust policy "
            f"(operators={names!r}, "
            f"approval_projects={list(self.approval_project_ids)}, "
            f"signature_required={self.signature_required})"
        )


def load_operator_trust(path: str | Path) -> OperatorTrustPolicy:
    """Load the operator-owned trust policy from disk. Fails closed."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrustPolicyError(
            f"operator trust policy at {source} is unreadable; refusing to guess: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise TrustPolicyError(f"operator trust policy at {source} is malformed")
    if str(data.get("schema") or "") != TRUST_SCHEMA:
        raise TrustPolicyError(
            f"operator trust policy at {source} reports an unsupported schema; "
            f"expected {TRUST_SCHEMA!r}"
        )
    operators: list[TrustedOperator] = []
    raw_operators = data.get("trusted_operators")
    if not isinstance(raw_operators, list) or not raw_operators:
        raise TrustPolicyError(f"operator trust policy at {source} lists no trusted operators")
    for entry in raw_operators:
        if not isinstance(entry, dict):
            raise TrustPolicyError(f"operator trust policy at {source} has a malformed operator")
        username, user_id = entry.get("username"), entry.get("user_id")
        if not isinstance(username, str) or not username.strip():
            raise TrustPolicyError(
                f"operator trust policy at {source} has an operator without a username"
            )
        if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
            raise TrustPolicyError(
                f"operator trust policy at {source} has an operator ({username!r}) "
                "without a positive provider-issued user_id"
            )
        operators.append(TrustedOperator(username=username, user_id=user_id))
    raw_projects = data.get("approval_project_ids")
    if not isinstance(raw_projects, list) or not raw_projects:
        raise TrustPolicyError(f"operator trust policy at {source} lists no approval projects")
    projects: list[int] = []
    for value in raw_projects:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise TrustPolicyError(
                f"operator trust policy at {source} has an invalid approval project id {value!r}"
            )
        projects.append(value)
    revocations: list[tuple[str, datetime]] = []
    for entry in data.get("revocations") or []:
        if not isinstance(entry, dict):
            raise TrustPolicyError(f"operator trust policy at {source} has a malformed revocation")
        try:
            revocations.append(
                (str(entry["username"]), _as_utc(datetime.fromisoformat(str(entry["revoked_at"]))))
            )
        except (KeyError, ValueError) as exc:
            raise TrustPolicyError(
                f"operator trust policy at {source} has an invalid revocation: {exc}"
            ) from exc
    return OperatorTrustPolicy(
        schema_version=int(data.get("schema_version") or 1),
        trusted_operators=tuple(operators),
        approval_project_ids=tuple(projects),
        signature_required=bool(data.get("signature_required", True)),
        approval_freshness_seconds=int(data.get("approval_freshness_seconds") or 86_400),
        revocations=tuple(revocations),
    )


@dataclass(frozen=True, slots=True)
class ApprovalProvenance:
    """The provider-verified features of one operator approval record."""

    project_id: int
    issue_iid: int
    issue_state: str
    author_username: str
    author_user_id: int
    body: str
    created_at: datetime
    endpoint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source": TRUSTED_CHANNEL,
            "project_id": self.project_id,
            "issue_iid": self.issue_iid,
            "issue_state": self.issue_state,
            "author_username": self.author_username,
            "author_user_id": self.author_user_id,
            "body": self.body,
            "created_at": _as_utc(self.created_at).isoformat(),
            "endpoint": self.endpoint,
        }


def read_approval_issue(
    client: GitLabClient, *, project_id: int, issue_iid: int
) -> ApprovalProvenance:
    """Read the operator's approval issue back from GitLab. Fails closed."""
    endpoint = f"/projects/{project_id}/issues/{issue_iid}"
    result = client.get_json(endpoint)
    if not result.ok or not isinstance(result.data, dict):
        raise AuthorizationError(
            "the operator approval record could not be read back from GitLab "
            f"(GET {endpoint}: status={result.status}, error={result.error_kind})"
        )
    body_raw = result.data.get("description")
    author = result.data.get("author") or {}
    author_name = author.get("username")
    author_id = author.get("id")
    if not isinstance(author_name, str) or not author_name.strip():
        raise AuthorizationError("the operator approval record has no attributable author")
    if isinstance(author_id, bool) or not isinstance(author_id, int) or author_id <= 0:
        raise AuthorizationError(
            "the operator approval record has no provider-issued author user ID; "
            "an approval whose author cannot be positively identified from the "
            "provider is refused"
        )
    if not isinstance(body_raw, str) or not body_raw.strip():
        raise AuthorizationError("the operator approval record has no approval statement")
    created_raw = str(result.data.get("created_at") or "")
    try:
        created = datetime.fromisoformat(created_raw)
    except ValueError as exc:
        raise AuthorizationError("the operator approval record has an invalid created_at") from exc
    issue_state = str(result.data.get("state") or "")
    if issue_state != "opened":
        raise AuthorizationError(
            "the operator approval issue is not open (state="
            f"{issue_state!r}); a closed, locked or invalid issue cannot "
            "authorize a mutation"
        )
    return ApprovalProvenance(
        project_id=project_id,
        issue_iid=issue_iid,
        issue_state=issue_state,
        author_username=author_name,
        author_user_id=author_id,
        body=body_raw,
        created_at=_as_utc(created),
        endpoint=endpoint,
    )


def _binding_lines(body: str) -> list[tuple[str, str]]:
    """Normalized ``(stripped_line)`` view used for exact line matching."""
    return [line.strip() for line in body.splitlines()]


def _require_exact_lines(provenance: ApprovalProvenance, expected: dict[str, str]) -> None:
    """Every binding line must appear exactly once, verbatim.

    Substring matching accepts adversarial duplicates (an approval issue that
    states two different nonces, one of them ours, is ambiguous, and ambiguity
    must fail closed). Exact single-occurrence matching refuses both.
    """
    lines = _binding_lines(provenance.body)
    for key, expectation in expected.items():
        prefix = f"{key}:"
        matches = [
            line
            for line in lines
            if line.startswith(prefix) and line[len(prefix) :].strip() == expectation
        ]
        if len(matches) > 1:
            raise AuthorizationError(
                f"the operator approval record states {key!r} {len(matches)} times; "
                "duplicated binding content is ambiguous and cannot authorize a "
                "single-use mutation"
            )
        if not matches:
            raise AuthorizationError(
                f"the operator approval record does not state {key!r} exactly as "
                f"required: expected the exact line {prefix} {expectation!r}; an "
                "approval whose binding content was edited cannot be honored and "
                "must be re-issued from the approval template"
            )


def verify_approval_source(
    client: GitLabClient,
    authorization: Authorization,
    *,
    project_id: int,
    issue_iid: int,
    trust: OperatorTrustPolicy,
    approval_key: str | None = None,
    now: datetime | None = None,
    clock_skew: timedelta = CLOCK_SKEW,
) -> ApprovalProvenance:
    """Verify operator approval provenance against the provider *and* the trust policy.

    The provenance chain is only trustworthy when every layer holds:

    1. an independent, operator-owned trust policy exists and names the author —
       by username **and** provider-issued user ID;
    2. the issue lives in a policy-approved project, is open, and is fresh;
    3. the operator identity is not revoked by the policy;
    4. the issue body states the exact binding content once, verbatim;
    5. when the policy demands it (default), the approval block carries an HMAC
       signature made with the operator-held key — a credential held by a coding
       agent cannot forge it.

    Any failure raises :class:`AuthorizationError`; nothing from the local file
    is trusted here except content mutually confirmed by the provider read-back.
    """
    approval = authorization.approval
    if approval is None:
        raise AuthorizationError("the authorization carries no operator approval to verify")
    if trust is None:
        raise TrustPolicyError(
            "an independent operator trust policy is required to verify a real "
            "operator approval; an approval evaluated only against executor-"
            "controlled files is never consent"
        )
    verify_now = _as_utc(now or datetime.now(tz=UTC))
    if operator_revoked := trust.is_revoked(approval.operator, verify_now):
        raise AuthorizationError(
            f"the operator identity {approval.operator!r} was revoked by the "
            f"operator trust policy at {operator_revoked.isoformat()}; a revoked "
            "operator can never approve a mutation"
        )

    provenance = read_approval_issue(client, project_id=project_id, issue_iid=issue_iid)
    now_value = _as_utc(now or datetime.now(tz=UTC))

    # -- independent trust: the author must be an organization-trusted operator,
    #    confirmed by the provider-issued identity, not by what any file says.
    trusted = trust.operator_for(provenance.author_username)
    if trusted is None:
        raise AuthorizationError(
            f"the approval issue author {provenance.author_username!r} is not a "
            "trusted operator in the independently established operator trust "
            "policy; an executor-named operator is not consent"
        )
    if trusted.user_id != provenance.author_user_id:
        raise AuthorizationError(
            "the approval issue author carries a different provider user ID "
            f"({provenance.author_user_id}) than the trusted operator record "
            f"({trusted.user_id}); refusing identity confusion"
        )
    if project_id not in trust.approval_project_ids:
        raise AuthorizationError(
            f"project {project_id} is not an approval project in the operator "
            "trust policy; approvals recorded elsewhere cannot authorize mutations"
        )

    # -- freshness: an approval must still be organization-current at verify time.
    freshness = timedelta(seconds=trust.approval_freshness_seconds)
    if provenance.created_at < now_value - freshness:
        raise AuthorizationError(
            "the operator approval record is stale: it was created "
            f"{now_value - provenance.created_at} ago, beyond the trust policy's "
            f"{freshness} approval freshness window; ask the operator to re-issue it"
        )
    if provenance.created_at > now_value + clock_skew:
        raise AuthorizationError(
            "the operator approval record claims a creation time in the future; "
            "refusing a fabricated provenance"
        )

    # -- exact, unambiguous binding content.
    _require_exact_lines(
        provenance,
        {
            "endpoint": authorization.exact_endpoint,
            "action": authorization.action,
            "nonce": authorization.nonce,
            "binding": authorization.binding(),
            "target": (
                f"{authorization.target.full_path} (project "
                f"{authorization.target.project_id}, kind "
                f"{authorization.target.resource_kind})"
            ),
            "valid": (
                f"{authorization.issued_at.isoformat()} .. "
                f"{authorization.expires_at.isoformat()} (single use)"
            ),
        },
    )

    # -- executor-independent human consent: the operator-held HMAC key.
    if trust.signature_required:
        if not approval_key:
            raise AuthorizationError(
                "the operator trust policy requires an operator-held approval "
                "signature key; an unsigned approval cannot become a real mutation "
                "because a coding agent with issue-creating access could otherwise "
                "manufacture its own operator consent"
            )
        expected = hmac.new(
            approval_key.encode("utf-8"),
            authorization.binding().encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not approval.signature or not hmac.compare_digest(expected, approval.signature):
            raise AuthorizationError(
                "operator approval signature is missing or invalid for the "
                "operator-held key configured in the trust policy"
            )

    # -- the approval must have been created inside the authorization's lifetime.
    issued = authorization.issued_at
    expires = authorization.expires_at
    if provenance.created_at < issued - clock_skew:
        raise AuthorizationError(
            "the operator approval record predates the authorization issuance "
            f"time beyond the {clock_skew} tolerance"
        )
    if provenance.created_at > expires + clock_skew:
        raise AuthorizationError(
            "the operator approval record was created after the authorization "
            f"expired (beyond the {clock_skew} tolerance)"
        )
    return provenance


def approval_statement_template(authorization: Authorization) -> str:
    """Render the exact approval text the operator must paste into a GitLab issue.

    This is a *draft* produced for the operator's convenience: the statement
    only becomes a trustworthy approval once it exists as an authentic GitLab
    issue created by the operator, matching the independent trust policy,
    carrying the operator-held signature, and read back from the provider.
    """
    return (
        "Operator approval — Termivance retirement mutation\n"
        "\n"
        f"endpoint: {authorization.exact_endpoint}\n"
        f"action: {authorization.action}\n"
        f"target: {authorization.target.full_path} (project "
        f"{authorization.target.project_id}, kind "
        f"{authorization.target.resource_kind})\n"
        f"nonce: {authorization.nonce}\n"
        f"binding: {authorization.binding()}\n"
        f"valid: {authorization.issued_at.isoformat()} .. "
        f"{authorization.expires_at.isoformat()} (single use)\n"
        "\n"
        f"I, the author of this issue, authorize exactly one {authorization.action} "
        f"operation using {authorization.exact_endpoint} on project "
        f"{authorization.target.project_id} as stated above. Closing this issue "
        "revokes this approval."
    )


__all__ = [
    "ApprovalProvenance",
    "CLOCK_SKEW",
    "TRUST_SCHEMA",
    "TRUSTED_CHANNEL",
    "OperatorTrustPolicy",
    "TrustPolicyError",
    "TrustedOperator",
    "approval_statement_template",
    "load_operator_trust",
    "read_approval_issue",
    "verify_approval_source",
]
