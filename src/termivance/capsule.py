"""Retirement Proof Capsule — portable, tamper-evident evidence package.

One capsule combines, when actually available: the exact target identity, the
deterministic graph decision, the operator approval provenance, the mutation
response together with its durable ledger record, independent post-mutation
observations, the strongest supported bounded verdicts, evidence acquisition
times, provenance labels and *explicit* ``BLOCKED`` / ``NOT_RUN`` /
``NOT_OBSERVED`` states. A SHA-256 integrity manifest commits to the exact
canonical content of every section.

Honest boundaries, enforced in code and stated in the rendered text:

* ``verify_capsule`` proves *integrity of the captured evidence only* — it is a
  local consistency check over bytes, not an independent GitLab re-observation;
  a valid hash never becomes provider truth, perpetual validity, or a
  successful retirement of anything;
* a missing live result ships as an explicit ``NOT_RUN``/``BLOCKED``/
  ``NOT_OBSERVED`` state, never as an omission or a manufactured success.

The same module carries the P0-C receipt validation used for bounded-absence
claims: :func:`validate_mutation_receipt` refuses any receipt that is not
structurally bound to exactly this target, this exact endpoint and this
mutation, and durably sealed in the ledger.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from termivance.evidence import PagesPreState
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

CAPSULE_SCHEMA = "termivance.proof_capsule/v1"
RECEIPT_SCHEMAS: frozenset[str] = frozenset(
    {"termivance.retirement_receipt/v2", "termivance.retirement_receipt/v3"}
)
#: Maximum seconds between eligibility establishment and the mutation request.
#: Discovery evidence (snapshots) is stated fresh for this long by default.
DEFAULT_TTL_SECONDS = 900


class CapsuleError(ValueError):
    """Raised when a proof capsule is malformed or fails integrity."""


class ReceiptValidationError(CapsuleError):
    """Raised when a mutation receipt cannot be bound to an absence claim."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _now_iso(now: datetime | None) -> str:
    return _as_utc(now or datetime.now(tz=UTC)).isoformat()


def canonical(payload: Any) -> str:
    """Deterministic serialization used for every capsule digest."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _digest(payload: Any) -> str:
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# P0-C: the validated binding between one real mutation and one observation
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MutationBinding:
    """Proof that one exact mutation attempt really happened and was recorded.

    ``source`` distinguishes provenance:

    * ``live_dispatch`` — constructed on the code path that just issued the
      mutation call itself (the strongest binding);
    * ``recorded_receipt_file`` — reconstructed from a saved receipt plus the
      durable ledger record of the same operation.
    """

    target: TargetIdentity
    action: str
    endpoint: str
    operation_id: str
    authorization_binding: str | None
    accepted: bool
    status: int | None
    pre_state: PagesPreState
    ledger_entry: dict[str, object] | None
    source: str

    @property
    def durable(self) -> bool:
        """True only when the operation is sealed in the durable ledger or was
        dispatched by the executor itself in this very process."""
        return bool(self.ledger_entry) or self.source == "live_dispatch"

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "target": self.target.to_dict(),
            "action": self.action,
            "endpoint": self.endpoint,
            "operation_id": self.operation_id,
            "authorization_binding": self.authorization_binding,
            "accepted": self.accepted,
            "status": self.status,
            "pre_state": self.pre_state.to_dict(),
            "ledger_entry": self.ledger_entry,
        }


def exact_pages_endpoint(target: TargetIdentity) -> str:
    return f"/projects/{target.project_id}/pages"


def validate_mutation_receipt(
    receipt_data: dict[str, object],
    target: TargetIdentity,
    *,
    ledger: object,
    now: datetime | None = None,
) -> MutationBinding:
    """Reconstruct and validate a recorded retirement receipt against a target.

    Fails closed (:class:`ReceiptValidationError`) unless:

    * the receipt schema is recognized;
    * the receipt is bound to exactly ``target``;
    * it records one attempted, accepted ``DELETE`` against the exact Pages
      endpoint of that target;
    * the operator authorization binding is present;
    * the same operation is durably sealed in ``ledger`` (state
      ``RESERVED_BEFORE_MUTATION`` or ``CONSUMED_*``).
    """
    if not isinstance(receipt_data, dict):
        raise ReceiptValidationError("mutation receipt must be a JSON object")
    schema = str(receipt_data.get("schema") or "")
    if schema not in RECEIPT_SCHEMAS:
        raise ReceiptValidationError(f"unsupported receipt schema {schema!r}")
    if receipt_data.get("mutation_attempted") is not True:
        raise ReceiptValidationError("the receipt records no mutation attempt")

    raw_target = receipt_data.get("target")
    if not isinstance(raw_target, dict):
        raise ReceiptValidationError("receipt carries no valid target")
    recorded_target = TargetIdentity.from_dict(dict(raw_target))
    if recorded_target.key() != target.key():
        raise ReceiptValidationError(
            f"the mutation receipt is bound to target {recorded_target.key()} but the "
            f"observation targets {target.key()}; cross-target receipts are refused"
        )

    action = str(receipt_data.get("action") or "")
    if action != "unpublish_pages":
        raise ReceiptValidationError(f"unexpected receipt action {action!r}")

    mutation = receipt_data.get("mutation")
    if not isinstance(mutation, dict):
        raise ReceiptValidationError("receipt carries no mutation record")
    accepted = mutation.get("accepted") is True
    if not accepted:
        raise ReceiptValidationError("the recorded mutation was not accepted")
    if str(mutation.get("method") or "") != "DELETE":
        raise ReceiptValidationError("the recorded mutation is not a DELETE")
    endpoint = str(mutation.get("endpoint") or "")
    if endpoint != exact_pages_endpoint(target):
        raise ReceiptValidationError(
            f"receipt endpoint {endpoint!r} is not the exact allowed Pages endpoint "
            f"{exact_pages_endpoint(target)!r}"
        )

    authorization_binding = receipt_data.get("authorization_binding")
    if not isinstance(authorization_binding, str) or not authorization_binding:
        raise ReceiptValidationError("receipt carries no authorization binding")

    operation_id = str(receipt_data.get("operation_id") or "")
    if not operation_id:
        raise ReceiptValidationError("receipt carries no operation_id")

    eligibility = receipt_data.get("eligibility")
    if not isinstance(eligibility, dict):
        raise ReceiptValidationError("receipt carries no eligibility section")
    pre_state_data = eligibility.get("pre_state")
    if not isinstance(pre_state_data, dict):
        raise ReceiptValidationError("receipt eligibility carries no pre-state proof")
    pre_state = PagesPreState.from_dict(dict(pre_state_data))
    if not pre_state.genuinely_published:
        raise ReceiptValidationError(
            "the receipt's pre-state does not prove genuine publication"
        )
    # Temporal coherence: the mutation must have been dispatched after the
    # eligibility was established, and within its stated freshness window.
    try:
        eligibility_at = datetime.fromisoformat(str(eligibility.get("established_at")))
        mutation_requested = mutation.get("requested_at")
        if not mutation_requested:
            raise ReceiptValidationError("receipt does not record when the mutation was requested")
        mutation_requested_at = datetime.fromisoformat(str(mutation_requested))
        if mutation_requested_at < eligibility_at:
            raise ReceiptValidationError(
                "the recorded mutation request predates the eligibility observation; "
                "temporal coherence is violated"
            )
        # A use of an eligibility observation may not legitimately outlive the
        # snapshot's stated discovery freshness.
        if (mutation_requested_at - eligibility_at).total_seconds() > DEFAULT_TTL_SECONDS:
            raise ReceiptValidationError(
                "the eligibility observation had already expired when the mutation "
                "was dispatched; a stale eligibility cannot authorize absence"
            )
    except ReceiptValidationError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ReceiptValidationError("receipt timestamps are malformed") from exc

    from termivance.ledger import AuthorizationLedger, LedgerError  # local: avoid cycle

    if not isinstance(ledger, AuthorizationLedger):
        raise ReceiptValidationError("a durable authorization ledger is required to bind "
                                     "an absence claim")
    try:
        entry = ledger.consumption_record(authorization_binding, operation_id=operation_id)
    except LedgerError as exc:
        raise ReceiptValidationError(f"the authorization ledger is unreadable: {exc}") from exc
    if entry is None:
        raise ReceiptValidationError(
            "no durable ledger record exists for this exact operation and "
            "authorization binding; the claim is refused"
        )
    state = str(entry.get("state") or "")
    if state != "RESERVED_BEFORE_MUTATION" and not state.startswith("CONSUMED_"):
        raise ReceiptValidationError(f"durable ledger record has unexpected state {state!r}")

    return MutationBinding(
        target=recorded_target,
        action=action,
        endpoint=endpoint,
        operation_id=operation_id,
        authorization_binding=authorization_binding,
        accepted=True,
        status=mutation.get("status"),  # type: ignore[arg-type]
        pre_state=pre_state,
        ledger_entry=entry,
        source="recorded_receipt_file",
    )


# ---------------------------------------------------------------------------
# The capsule itself
# ---------------------------------------------------------------------------

PROVENANCE_LABEL = "LIVE_GITLAB_OBSERVED"  # per-section override allowed
EXPLICIT_STATES = ("BLOCKED", "NOT_RUN", "NOT_OBSERVED")


def build_capsule(
    *,
    target: TargetIdentity,
    decision: dict[str, object] | None = None,
    mutation: dict[str, object] | None = None,
    absence: dict[str, object] | None = None,
    authorization: dict[str, object] | None = None,
    source: dict[str, object] | None = None,
    notes: tuple[str, ...] = (),
    now: datetime | None = None,
) -> dict[str, object]:
    """Assemble a proof capsule from deterministic, already-captured facts.

    Everything passed here must already be recorded evidence; no section is
    ever invented. Anything genuinely absent is recorded as an explicit
    ``NOT_OBSERVED``/``NOT_RUN`` entry instead of being omitted.
    """
    generated = _now_iso(now)
    sections: dict[str, object] = {
        "identity": {
            "provider": "GITLAB",
            "target": target.to_dict(),
            "generated_at": generated,
        },
        "limitation_notice": {
            "explicit_states": list(EXPLICIT_STATES),
            "notes": list(notes),
            "not_to_be_claimed": (
                "Integrity verification is a local byte-level check; it never "
                "re-observes GitLab and never extends the bounded verdict beyond "
                "its stated evidence, scope and freshness."
            ),
        },
    }
    if decision is not None:
        sections["decision"] = decision
    else:
        sections["decision"] = {"verdict": "NOT_RUN"}
    if mutation is not None:
        sections["mutation"] = mutation
    else:
        sections["mutation"] = {"attempted": False, "state": "NOT_RUN"}
    if absence is not None:
        sections["absence"] = absence
    else:
        sections["absence"] = {"claimed": False, "state": "NOT_OBSERVED"}
    if authorization is not None:
        sections["authorization"] = authorization
    else:
        sections["authorization"] = {"present": False, "state": "NOT_RUN"}
    if source is not None:
        sections["source_evidence"] = source
    else:
        sections["source_evidence"] = {"state": "NOT_OBSERVED"}

    manifest = {"sections": {name: _digest(section) for name, section in sections.items()}}
    manifest_digest = _digest(manifest)
    return {
        "schema": CAPSULE_SCHEMA,
        "manifest_digest": manifest_digest,
        "manifest": manifest,
        "sections": sections,
    }


def save_capsule(capsule: dict[str, object], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(capsule, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p


def load_capsule(path: str | Path) -> dict[str, object]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CapsuleError("capsule file must contain a JSON object")
    return data


def verify_capsule(capsule: dict[str, object]) -> dict[str, object]:
    """Validate capsule structure, bindings and manifest integrity. Fails closed.

    Raises :class:`CapsuleError` on any substitution, reorder-with-edit,
    missing section, cross-target binding or digest mismatch. The returned
    report states exactly which checks passed.
    """
    if not isinstance(capsule, dict):
        raise CapsuleError("capsule must be a JSON object")
    schema = str(capsule.get("schema") or "")
    if schema != CAPSULE_SCHEMA:
        raise CapsuleError(f"unsupported capsule schema {schema!r}")
    manifest = capsule.get("manifest")
    sections = capsule.get("sections")
    if not isinstance(manifest, dict) or not isinstance(sections, dict):
        raise CapsuleError("capsule manifest/sections are malformed")
    if not isinstance(manifest.get("sections"), dict):
        raise CapsuleError("capsule manifest has no section digests")

    recorded_digest = capsule.get("manifest_digest")
    if not isinstance(recorded_digest, str) or not recorded_digest:
        raise CapsuleError("capsule has no manifest_digest")
    if _digest(manifest) != recorded_digest:
        raise CapsuleError(
            "manifest digest mismatch: capsule content has been modified after creation"
        )

    recorded_sections = dict(manifest["sections"])
    if set(recorded_sections) != set(sections):
        raise CapsuleError(
            "manifest/sections disagree on section names "
            f"({sorted(set(recorded_sections) ^ set(sections))}); a section was added "
            "or removed after creation"
        )
    recomputed = {name: _digest(sections[name]) for name in sorted(sections)}
    mismatches = [name for name in recomputed if recomputed[name] != recorded_sections[name]]
    if mismatches:
        raise CapsuleError(
            f"section digests do not match the manifest: {', '.join(sorted(mismatches))}"
        )

    # Binding checks: every target committed in any section must be the same
    # exact target as the identity section.
    identity = sections["identity"]
    if not isinstance(identity, dict) or not isinstance(identity.get("target"), dict):
        raise CapsuleError("capsule identity section is malformed")
    capsule_target = TargetIdentity.from_dict(dict(identity["target"]))
    failures: list[str] = []
    for name, section in sections.items():
        if not isinstance(section, dict):
            continue
        if "target" in section and isinstance(section["target"], dict):
            section_target = TargetIdentity.from_dict(dict(section["target"]))
            if section_target.key() != capsule_target.key():
                failures.append(
                    f"section {name!r} is bound to a different target than the capsule "
                    "identity"
                )
        if "verdict" in section and section["verdict"] is not None:
            try:
                Verdict(str(section["verdict"]))
            except ValueError:
                failures.append(f"section {name!r} carries an unknown verdict "
                                f"{section['verdict']!r}")
    if failures:
        raise CapsuleError("capsule binding failures: " + "; ".join(failures))

    return {
        "ok": True,
        "schema": schema,
        "manifest_sha256": recorded_digest,
        "sections_verified": sorted(sections),
        "target": capsule_target.to_dict(),
        "integrity_only": True,
        "note": (
            "Integrity verification is local; it does not re-observe GitLab and "
            "does not extend the validity of any bounded verdict."
        ),
    }


def render_capsule(capsule: dict[str, object]) -> str:
    """Human-readable rendering for judges, the demo UI and receipts."""
    try:
        report = verify_capsule(capsule)
    except CapsuleError as exc:
        return f"CAPSULE INVALID: {exc}\n(binding and integrity checks failed closed)"
    sections = capsule.get("sections", {})
    lines = [
        "Termivance Retirement Proof Capsule",
        "===================================",
        f"target: {report['target']}",
        f"integrity manifest: sha256 {report['manifest_sha256'][:32]}…",
        "verification: LOCAL INTEGRITY ONLY (no GitLab re-observation was performed)",
        "",
    ]
    for name in sorted(sections, key=_section_order):
        section = sections[name]
        if not isinstance(section, dict):
            continue
        state = section.get("state") or section.get("verdict") or "-"
        attempted = section.get("attempted", section.get("mutation_attempted"))
        extra = f" attempted={attempted}" if isinstance(attempted, bool) else ""
        lines.append(f"[{name}] state={state}{extra}")
    for notice in ("limitation_notice",):
        section = sections.get(notice)
        if isinstance(section, dict):
            for note in section.get("notes", ()):  # type: ignore[union-attr]
                lines.append(f"note: {note}")
            lines.append(f"boundary: {section.get('not_to_be_claimed', '')}")
    return "\n".join(lines)


def _section_order(name: str) -> tuple[int, str]:
    priority = {"identity": 0, "decision": 1, "mutation": 2, "absence": 3,
                "authorization": 4, "source_evidence": 5, "limitation_notice": 6}
    return (priority.get(name, 9), name)


__all__ = [
    "CAPSULE_SCHEMA",
    "CapsuleError",
    "MutationBinding",
    "ReceiptValidationError",
    "build_capsule",
    "canonical",
    "exact_pages_endpoint",
    "load_capsule",
    "render_capsule",
    "save_capsule",
    "validate_mutation_receipt",
    "verify_capsule",
]
