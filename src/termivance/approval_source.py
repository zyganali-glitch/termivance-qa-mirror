"""GitLab-authenticated operator approval provenance (P0-B trust boundary).

A local JSON document — or model text — naming an "operator" proves nothing:
anyone can write an ``operator_approval`` block by hand. Since B4, an approval
that authorizes a *real mutation* must additionally be backed by a record that
was created out-of-band in GitLab itself, by the operator's authenticated
account: specifically an **open GitLab issue** whose author username equals the
operator recorded on the authorization and whose body states the exact
endpoint, the exact action, the authorization nonce, the approval binding
digest and the exact target path.

The record is read back from the provider (``GET /projects/:id/issues/:iid``),
verbatim, before any mutation may be dispatched — the local JSON file only
supplies the *expected* content, never the proof. Closing the issue revokes
the approval. The executor never creates this record itself: it is created in
the operator's browser session, outside the agent's control.

An out-of-band HMAC key (``TERMIVANCE_APPROVAL_HMAC_KEY``) remains supported as
an *additional* layer on top of the GitLab-authenticated record.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from termivance.authorization import Authorization, AuthorizationError
from termivance.gitlab_client import GitLabClient

#: The only operator-approval channel that can authorize a *real mutation*.
TRUSTED_CHANNEL = "gitlab_issue"

#: Tolerance when comparing provider ``created_at`` against authorization
#: issuance/expiration times (different machines, transport latency).
CLOCK_SKEW = timedelta(minutes=5)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ApprovalProvenance:
    """The provider-verified features of one operator approval record."""

    project_id: int
    issue_iid: int
    issue_state: str
    author_username: str
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
    author = (result.data.get("author") or {}).get("username")
    if not isinstance(author, str) or not author.strip():
        raise AuthorizationError("the operator approval record has no attributable author")
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
        author_username=author,
        body=body_raw,
        created_at=_as_utc(created),
        endpoint=endpoint,
    )


def verify_approval_source(
    client: GitLabClient,
    authorization: Authorization,
    *,
    project_id: int,
    issue_iid: int,
    now: datetime | None = None,
    clock_skew: timedelta = CLOCK_SKEW,
) -> ApprovalProvenance:
    """Verify operator approval provenance end-to-end against the provider.

    Proves that a GitLab issue existed at verification time, authored by the
    operator recorded on the authorization, stating the exact endpoint, action,
    nonce, binding digest and target path of *this* authorization, and created
    within the authorization's validity window. Any failure raises
    :class:`AuthorizationError`; nothing about the record is trusted from the
    local file except the mutually confirmed binding content.
    Args ``now`` and ``clock_skew`` exist for deterministic tests and
    explicit operator-supplied observation times.
    """
    approval = authorization.approval
    if approval is None:
        raise AuthorizationError("the authorization carries no operator approval to verify")
    provenance = read_approval_issue(
        client, project_id=project_id, issue_iid=issue_iid
    )

    endpoint = authorization.exact_endpoint
    required: tuple[tuple[str, str], ...] = (
        (endpoint, "the exact endpoint"),
        (authorization.action, "the authorized action"),
        (authorization.nonce, "the authorization nonce"),
        (authorization.binding(), "the approval binding digest"),
        (authorization.target.full_path, "the exact target path"),
    )
    for needle, what in required:
        if needle not in provenance.body:
            raise AuthorizationError(
                f"the operator approval record does not state {what} ({needle}); "
                "an approval cannot be manufactured from a generic statement"
            )

    # The operator identity recorded locally must equal the provider-verified
    # author: the agent's own file cannot name a different operator.
    if provenance.author_username != approval.operator:
        raise AuthorizationError(
            "the operator approval record was created by "
            f"{provenance.author_username!r}, not by the operator "
            f"{approval.operator!r} recorded on the authorization; refusing "
            "forged or mismatched provenance"
        )

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
    issue created by the operator and is read back from the provider.
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
    "TRUSTED_CHANNEL",
    "approval_statement_template",
    "read_approval_issue",
    "verify_approval_source",
]
