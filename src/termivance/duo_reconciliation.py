"""Evidence-bound reconciliation of GitLab Duo candidate claims (read-only).

The GitLab Duo Custom Flow produces *candidate claims* — text a human operator
read in a session. The executor can never treat that text as authority: the
deterministic Python engine is the only component allowed to award
``SAFE_TO_RETIRE``, ``OBSERVED_ABSENT`` or ``RESURRECTION_CONTROLLED``. This
module performs the honest middle step the protocol demands: it takes the
recorded candidate claims (``termivance.duo_claims/v1``, derived strictly from
the operator-confirmed external evidence record — never fabricated) and
*reconciles* each one against fresh **anonymous, read-only** observations of the
public GitLab surface, assigning exactly one evidence status per claim:

* ``SUPPORTED`` — an independent anonymous observation corroborates the claim's
  checkable core;
* ``CONTRADICTED`` — an independent observation positively conflicts with it;
* ``UNRESOLVED`` — the observation neither proves nor disproves it (including
  the "consistent with, but not proof" class: consistency is never promoted);
* ``STALE`` — a supporting/refuting observation exists but has left its
  freshness window; re-observe before drawing any conclusion;
* ``UNSUPPORTED`` — no independently observable surface for the claim exists at
  all (flow internals); it is never promoted;
* ``NOT_AUTHENTICALLY_ATTRIBUTABLE`` — the claim's basis (note/discussion
  content) cannot be read by the observing identity at all (HTTP 401); an
  access observation is not absence, and it certainly is not attribution.

There is no mutation surface here, no verdict, and no authority: the output
record (``termivance.duo_reconciliation/v1``) is explicitly marked
non-authoritative, and a claim can never be promoted beyond what an anonymous
GET actually shows.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path

from termivance.gitlab_client import ApiResult, GitLabClient

DUO_CLAIMS_SCHEMA = "termivance.duo_claims/v1"
DUO_RECONCILIATION_SCHEMA = "termivance.duo_reconciliation/v1"

#: Every reconciliation stays fresh for this long after acquisition.
RECONCILIATION_TTL_SECONDS = 900

#: The only origins a recorded claim may carry. Anything else is refused: an
#: unidentified origin cannot be reconciled honestly.
CLAIM_ORIGINS: frozenset[str] = frozenset(
    {
        "ANONYMOUS_API_OBSERVATION",
        "OPERATOR_CONFIRMED_NOTE_CONTENT",
        "OPERATOR_CONFIRMED_UI",
    }
)

#: The closed set of anonymous read-only check kinds.
CHECK_KINDS: frozenset[str] = frozenset(
    {
        "PROJECT_READ",
        "ISSUE_METADATA",
        "CONSISTENCY_INFERENCE",
        "ISSUE_NOTE_READ",
        "SESSION_UI_PROBE",
        "OBSERVABILITY_PROBE",
        "FLOW_INTERNALS",
    }
)

#: The closed set of observability surfaces an OBSERVABILITY_PROBE may address.
PROBE_SURFACES: frozenset[str] = frozenset({"notes", "discussions", "session_ui"})


class ClaimStatus(StrEnum):
    """One evidence status per claim — fail-closed, never promoted."""

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNRESOLVED = "UNRESOLVED"
    STALE = "STALE"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_AUTHENTICALLY_ATTRIBUTABLE = "NOT_AUTHENTICALLY_ATTRIBUTABLE"


class ReconciliationError(RuntimeError):
    """Raised when a claims record is malformed; malformed input fails closed."""


def _utc(value: datetime | None = None) -> datetime:
    result = value or datetime.now(tz=UTC)
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


# ---------------------------------------------------------------------------
# The recorded anonymous observation of the Duo evidence surface
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DuoSurfaceObservation:
    """One anonymous, read-only observation pass over the Duo evidence surface.

    Every field is an HTTP status or a provider payload; 401/403/404 are
    recorded as access observations and are never promoted to presence,
    absence or attribution.
    """

    observed_at: datetime
    project_id: int
    issue_iid: int
    session_url: str
    project_read_status: int | None
    issue_read_status: int | None
    issue_metadata: dict[str, object]
    notes_read_status: int | None
    discussions_read_status: int | None
    session_ui_status: int | None
    provenance: str = "ANONYMOUS_PUBLIC_READ"

    def to_dict(self) -> dict[str, object]:
        return {
            "observed_at": _utc(self.observed_at).isoformat(),
            "project_id": self.project_id,
            "issue_iid": self.issue_iid,
            "session_url": self.session_url,
            "project_read_status": self.project_read_status,
            "issue_read_status": self.issue_read_status,
            "issue_metadata": dict(self.issue_metadata),
            "notes_read_status": self.notes_read_status,
            "discussions_read_status": self.discussions_read_status,
            "session_ui_status": self.session_ui_status,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> DuoSurfaceObservation:
        return cls(
            observed_at=datetime.fromisoformat(str(data["observed_at"])),
            project_id=int(data["project_id"]),
            issue_iid=int(data["issue_iid"]),
            session_url=str(data.get("session_url") or ""),
            project_read_status=(
                int(data["project_read_status"])
                if data.get("project_read_status") is not None
                else None
            ),
            issue_read_status=(
                int(data["issue_read_status"])
                if data.get("issue_read_status") is not None
                else None
            ),
            issue_metadata=dict(data.get("issue_metadata") or {}),  # type: ignore[arg-type]
            notes_read_status=(
                int(data["notes_read_status"])
                if data.get("notes_read_status") is not None
                else None
            ),
            discussions_read_status=(
                int(data["discussions_read_status"])
                if data.get("discussions_read_status") is not None
                else None
            ),
            session_ui_status=(
                int(data["session_ui_status"])
                if data.get("session_ui_status") is not None
                else None
            ),
            provenance=str(data.get("provenance") or "ANONYMOUS_PUBLIC_READ"),
        )


def _status_of(result: ApiResult) -> int | None:
    return result.status


def probe_web_status(url: str, *, timeout: float = 15.0) -> int | None:
    """GET an absolute web URL anonymously; return the final HTTP status or None.

    The agent-sessions UI is not an API endpoint, so the session-surface probe
    needs a plain web request. Anything other than a definite HTTP status is
    returned as ``None`` — unknown is never promoted.
    """
    import urllib.error  # local import: keep module import dependency-free
    import urllib.request

    if not url:
        return None
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "termivance-read-only-reconciliation/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception:  # noqa: BLE001 - any probe failure is unknown, never evidence
        return None


def _issue_fields(data: dict[str, object]) -> dict[str, object]:
    """The recorded subset of issue metadata used for reconciliation."""
    keep: dict[str, object] = {}
    for key in ("state", "title", "labels", "user_notes_count", "updated_at", "created_at"):
        if key in data:
            keep[key] = data[key]
    author = data.get("author")
    if isinstance(author, dict):
        keep["author"] = {k: author.get(k) for k in ("username", "id", "name") if k in author}
    return keep


def observe_duo_surface(
    client: GitLabClient,
    *,
    project_id: int,
    issue_iid: int,
    session_url: str,
    web_probe: Callable[[str], int | None] | None = None,
    now: datetime | None = None,
) -> DuoSurfaceObservation:
    """One anonymous GET-only observation pass over the Duo evidence surface.

    ``web_probe`` returns the HTTP status of an absolute web URL (the session
    UI page is not an API endpoint); it is injectable for tests. When omitted,
    the session UI status is recorded as ``None`` — unknown, never invented.
    """
    observed = _utc(now)
    project = client.get_json(f"/projects/{project_id}")
    issue = client.get_json(f"/projects/{project_id}/issues/{issue_iid}")
    notes = client.get_json(f"/projects/{project_id}/issues/{issue_iid}/notes?per_page=1")
    discussions = client.get_json(
        f"/projects/{project_id}/issues/{issue_iid}/discussions?per_page=1"
    )
    metadata: dict[str, object] = {}
    if issue.ok and isinstance(issue.data, dict):
        metadata = _issue_fields(issue.data)
    session_status: int | None = None
    if web_probe is not None and session_url:
        session_status = web_probe(session_url)
    return DuoSurfaceObservation(
        observed_at=observed,
        project_id=project_id,
        issue_iid=issue_iid,
        session_url=session_url,
        project_read_status=_status_of(project),
        issue_read_status=_status_of(issue),
        issue_metadata=metadata,
        notes_read_status=_status_of(notes),
        discussions_read_status=_status_of(discussions),
        session_ui_status=session_status,
    )


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DuoClaim:
    """One recorded candidate claim, derived from the external evidence record."""

    claim_id: str
    text: str
    origin: str
    check_kind: str
    expect: dict[str, object] = field(default_factory=dict)
    source_ladder: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "origin": self.origin,
            "check_kind": self.check_kind,
            "expect": dict(self.expect),
            "source_ladder": self.source_ladder,
        }


def load_claims(path: str | Path) -> tuple[dict[str, object], tuple[DuoClaim, ...]]:
    """Load and validate a ``termivance.duo_claims/v1`` record (fail closed)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReconciliationError(f"could not load claims record {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ReconciliationError("claims record must be a JSON object")
    if data.get("schema") != DUO_CLAIMS_SCHEMA:
        raise ReconciliationError(
            f"unsupported claims schema {data.get('schema')!r}; expected {DUO_CLAIMS_SCHEMA}"
        )
    raw_claims = data.get("claims")
    if not isinstance(raw_claims, list) or not raw_claims:
        raise ReconciliationError("claims record carries no claims")
    claims: list[DuoClaim] = []
    seen: set[str] = set()
    for entry in raw_claims:
        if not isinstance(entry, dict):
            raise ReconciliationError("every claim must be a JSON object")
        claim = DuoClaim(
            claim_id=str(entry.get("claim_id") or ""),
            text=str(entry.get("text") or ""),
            origin=str(entry.get("origin") or ""),
            check_kind=str(entry.get("check_kind") or ""),
            expect=dict(entry.get("expect") or {}),  # type: ignore[arg-type]
            source_ladder=str(entry.get("source_ladder") or ""),
        )
        if not claim.claim_id or not claim.text:
            raise ReconciliationError("every claim needs a claim_id and text")
        if claim.claim_id in seen:
            raise ReconciliationError(
                f"duplicate claim id {claim.claim_id!r}; duplicated claims are ambiguous "
                "and cannot be reconciled"
            )
        if claim.origin not in CLAIM_ORIGINS:
            raise ReconciliationError(
                f"claim {claim.claim_id!r} carries unknown origin {claim.origin!r}"
            )
        if claim.check_kind not in CHECK_KINDS:
            raise ReconciliationError(
                f"claim {claim.claim_id!r} carries unknown check kind {claim.check_kind!r}"
            )
        seen.add(claim.claim_id)
        claims.append(claim)
    return dict(data), tuple(claims)


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ClaimReconciliation:
    """One claim and its single, fail-closed evidence status."""

    claim_id: str
    text: str
    origin: str
    check_kind: str
    status: str
    detail: str
    observed: dict[str, object] = field(default_factory=dict)
    source_ladder: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "origin": self.origin,
            "check_kind": self.check_kind,
            "status": self.status,
            "detail": self.detail,
            "observed": dict(self.observed),
            "source_ladder": self.source_ladder,
        }


def _match_fields(expected: object, observed: object) -> tuple[bool, list[str]]:
    """Recursive subset match; returns ``(all_match, mismatched_paths)``."""
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            return False, [f"{expected!r} is not an object in the observation"]
        mismatches: list[str] = []
        for key, want in expected.items():
            ok, nested = _match_fields(want, observed.get(key))
            if not ok:
                mismatches.extend(f"{key}.{path}" if path else key for path in nested)
        return (not mismatches), mismatches
    if expected != observed:
        return False, [repr(expected)]
    return True, []


def _reconcile_claim(
    claim: DuoClaim,
    surface: DuoSurfaceObservation,
    *,
    stale: bool,
) -> ClaimReconciliation:
    kind = claim.check_kind
    observed: dict[str, object] = {"observed_at": _utc(surface.observed_at).isoformat()}
    status: ClaimStatus
    detail: str

    if kind == "PROJECT_READ":
        observed["project_read_status"] = surface.project_read_status
        if surface.project_read_status == 200:
            status, detail = (
                ClaimStatus.SUPPORTED,
                "the project is publicly readable to this anonymous identity (HTTP 200)",
            )
        else:
            status, detail = (
                ClaimStatus.UNRESOLVED,
                f"the project read returned {surface.project_read_status!r} to this "
                "identity; an access observation, never evidence for or against the claim",
            )
    elif kind == "ISSUE_METADATA":
        observed["issue_read_status"] = surface.issue_read_status
        observed["issue_metadata"] = dict(surface.issue_metadata)
        expected_fields = claim.expect.get("fields") or {}
        if surface.issue_read_status == 200 and surface.issue_metadata:
            all_match, mismatches = _match_fields(expected_fields, surface.issue_metadata)
            if all_match:
                status, detail = (
                    ClaimStatus.SUPPORTED,
                    "the anonymous issue read confirms every stated field exactly",
                )
            else:
                status, detail = (
                    ClaimStatus.CONTRADICTED,
                    "the anonymous issue read conflicts with the claim on: "
                    + ", ".join(mismatches),
                )
        else:
            status, detail = (
                ClaimStatus.UNRESOLVED,
                f"the issue read returned {surface.issue_read_status!r}; the claim's "
                "metadata cannot be checked from this observation",
            )
    elif kind == "CONSISTENCY_INFERENCE":
        observed["issue_read_status"] = surface.issue_read_status
        observed["issue_metadata"] = dict(surface.issue_metadata)
        expected_fields = claim.expect.get("fields") or {}
        if surface.issue_read_status == 200 and surface.issue_metadata:
            all_match, mismatches = _match_fields(expected_fields, surface.issue_metadata)
            if all_match:
                status, detail = (
                    ClaimStatus.UNRESOLVED,
                    "the observable core matches, but 'consistent with' is not proof: "
                    "the inference is never promoted to SUPPORTED",
                )
            else:
                status, detail = (
                    ClaimStatus.CONTRADICTED,
                    "the observable core conflicts with the claim on: " + ", ".join(mismatches),
                )
        else:
            status, detail = (
                ClaimStatus.UNRESOLVED,
                f"the issue read returned {surface.issue_read_status!r}; even the "
                "observable core cannot be checked",
            )
    elif kind == "ISSUE_NOTE_READ":
        observed["notes_read_status"] = surface.notes_read_status
        observed["note_id_claimed"] = claim.expect.get("note_id")
        if surface.notes_read_status == 200:
            # Anonymous read succeeded: we may check *existence* of the id, but
            # attribution to a claimed author stays a manual, human step.
            status, detail = (
                ClaimStatus.UNRESOLVED,
                "note content is readable to this anonymous identity; existence may "
                "be checked, but authorship attribution is never awarded by this "
                "tool — a human must verify it in the authenticated UI",
            )
        else:
            status, detail = (
                ClaimStatus.NOT_AUTHENTICALLY_ATTRIBUTABLE,
                f"note/discussion reads returned {surface.notes_read_status!r} to this "
                "anonymous identity; an access observation is not absence and is "
                "certainly not attribution — the claim cannot be attributed",
            )
    elif kind == "SESSION_UI_PROBE":
        observed["session_ui_status"] = surface.session_ui_status
        observed["session_url"] = surface.session_url
        status, detail = (
            ClaimStatus.UNRESOLVED,
            "the agent-sessions UI is an authenticated surface; the anonymous probe "
            f"returned {surface.session_ui_status!r} — an access observation that can "
            "neither confirm nor deny the session's recorded state, and is never "
            "promoted",
        )
    elif kind == "OBSERVABILITY_PROBE":
        surface_name = str(claim.expect.get("surface") or "")
        if surface_name not in PROBE_SURFACES:
            raise ReconciliationError(
                f"claim {claim.claim_id!r} probes unknown surface {surface_name!r}"
            )
        if surface_name == "notes":
            actual = surface.notes_read_status
        elif surface_name == "discussions":
            actual = surface.discussions_read_status
        else:
            actual = surface.session_ui_status
        expected_status = claim.expect.get("status")
        observed["surface"] = surface_name
        observed["expected_status"] = expected_status
        observed["actual_status"] = actual
        if actual is None:
            status, detail = (
                ClaimStatus.UNRESOLVED,
                "no observation was recorded for this surface; unknown is never promoted to proof",
            )
        elif actual == expected_status:
            status, detail = (
                ClaimStatus.SUPPORTED,
                f"the anonymous probe reproduces the recorded access observation (HTTP {actual})",
            )
        else:
            status, detail = (
                ClaimStatus.CONTRADICTED,
                f"the surface now returns HTTP {actual}, not the recorded "
                f"{expected_status}; the observability boundary changed and the "
                "claim must be re-derived",
            )
    elif kind == "FLOW_INTERNALS":
        status, detail = (
            ClaimStatus.UNSUPPORTED,
            "flow-execution internals have no independently observable surface; "
            "the claim can never be promoted by this tool",
        )
    else:  # pragma: no cover - load_claims refuses unknown kinds
        raise ReconciliationError(f"unhandled check kind {kind!r}")

    if stale and status in (ClaimStatus.SUPPORTED, ClaimStatus.CONTRADICTED):
        detail = (
            f"the underlying observation left its freshness window; provisional "
            f"finding was {status.value}: {detail}"
        )
        status = ClaimStatus.STALE
    return ClaimReconciliation(
        claim_id=claim.claim_id,
        text=claim.text,
        origin=claim.origin,
        check_kind=kind,
        status=status.value,
        detail=detail,
        observed=observed,
        source_ladder=claim.source_ladder,
    )


@dataclass(frozen=True, slots=True)
class DuoReconciliation:
    """The complete, non-authoritative reconciliation of one claims record."""

    claims_source: str
    duo_session_id: str
    flow_catalog_item_id: int | None
    surface: DuoSurfaceObservation
    results: tuple[ClaimReconciliation, ...]
    observed_at: datetime
    fresh_until: datetime

    def to_dict(self) -> dict[str, object]:
        totals: dict[str, int] = {}
        for result in self.results:
            totals[result.status] = totals.get(result.status, 0) + 1
        return {
            "schema": DUO_RECONCILIATION_SCHEMA,
            "authority": "NON_AUTHORITATIVE",
            "claims_source": self.claims_source,
            "duo_session_id": self.duo_session_id,
            "flow_catalog_item_id": self.flow_catalog_item_id,
            "observed_at": _utc(self.observed_at).isoformat(),
            "fresh_until": _utc(self.fresh_until).isoformat(),
            "surface": self.surface.to_dict(),
            "claims": [r.to_dict() for r in self.results],
            "totals": dict(sorted(totals.items())),
            "boundary": (
                "Duo output is candidate claims only; every status here is derived "
                "from anonymous read-only observations; no verdict may originate "
                "from this record and no claim is ever promoted beyond what a GET "
                "actually showed"
            ),
        }

    def render(self) -> str:
        lines = [
            f"DUO RECONCILIATION ({self.duo_session_id}) @ {_utc(self.observed_at).isoformat()}",
            f"authority: NON_AUTHORITATIVE — claims source: {self.claims_source}",
            "-" * 100,
        ]
        for result in self.results:
            lines.append(f"[{result.status:<28}] {result.claim_id}  ({result.check_kind})")
            lines.append(f"{'':>31}{result.text}")
            lines.append(f"{'':>31}{result.detail}")
        lines.append("-" * 100)
        payload = self.to_dict()
        totals = payload["totals"]
        assert isinstance(totals, dict)
        summary = ", ".join(f"{name}={count}" for name, count in totals.items())
        lines.append(f"totals: {summary}")
        lines.append(f"boundary: {payload['boundary']}")
        return "\n".join(lines)


def reconcile_duo(
    claims_data: dict[str, object],
    claims: tuple[DuoClaim, ...],
    surface: DuoSurfaceObservation,
    *,
    claims_source: str,
    ttl_seconds: int = RECONCILIATION_TTL_SECONDS,
    now: datetime | None = None,
) -> DuoReconciliation:
    """Reconcile every recorded candidate claim against one surface observation."""
    evaluated = _utc(now)
    fresh_until = _utc(surface.observed_at) + timedelta(seconds=ttl_seconds)
    stale = evaluated > fresh_until
    results = tuple(_reconcile_claim(claim, surface, stale=stale) for claim in claims)
    return DuoReconciliation(
        claims_source=claims_source,
        duo_session_id=str(claims_data.get("duo_session_id") or ""),
        flow_catalog_item_id=(
            int(claims_data["flow_catalog_item_id"])
            if isinstance(claims_data.get("flow_catalog_item_id"), int)
            else None
        ),
        surface=surface,
        results=results,
        observed_at=_utc(surface.observed_at),
        fresh_until=fresh_until,
    )


def reconciliation_from_data(data: dict[str, object]) -> DuoReconciliation:
    """Rebuild a reconciliation record (for review/transport without re-reading)."""
    surface = DuoSurfaceObservation.from_dict(dict(data["surface"]))  # type: ignore[arg-type]
    results = tuple(
        ClaimReconciliation(
            claim_id=str(entry["claim_id"]),
            text=str(entry["text"]),
            origin=str(entry["origin"]),
            check_kind=str(entry["check_kind"]),
            status=str(entry["status"]),
            detail=str(entry["detail"]),
            observed=dict(entry.get("observed") or {}),  # type: ignore[arg-type]
            source_ladder=str(entry.get("source_ladder") or ""),
        )
        for entry in (data.get("claims") or ())  # type: ignore[union-attr]
        if isinstance(entry, dict)
    )
    return DuoReconciliation(
        claims_source=str(data.get("claims_source") or ""),
        duo_session_id=str(data.get("duo_session_id") or ""),
        flow_catalog_item_id=(
            int(data["flow_catalog_item_id"])
            if isinstance(data.get("flow_catalog_item_id"), int)
            else None
        ),
        surface=surface,
        results=results,
        observed_at=datetime.fromisoformat(str(data["observed_at"])),
        fresh_until=datetime.fromisoformat(str(data["fresh_until"])),
    )


__all__ = [
    "CHECK_KINDS",
    "CLAIM_ORIGINS",
    "DUO_CLAIMS_SCHEMA",
    "DUO_RECONCILIATION_SCHEMA",
    "PROBE_SURFACES",
    "RECONCILIATION_TTL_SECONDS",
    "ClaimReconciliation",
    "ClaimStatus",
    "DuoClaim",
    "DuoReconciliation",
    "DuoSurfaceObservation",
    "ReconciliationError",
    "load_claims",
    "observe_duo_surface",
    "probe_web_status",
    "reconcile_duo",
    "reconciliation_from_data",
]
