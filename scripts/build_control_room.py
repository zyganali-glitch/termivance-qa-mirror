#!/usr/bin/env python3
"""Build the static interactive Control Room UI from recorded evidence (v2).

The Control Room is a judge-facing single page generated *deterministically*
from files on disk. It performs no network fetch at view time: everything is
embedded into ``data.js`` (``window.TERMIVANCE_DATA``), so the page works from
``file://`` without any server, proxy or CDN, and never contacts GitLab itself.

Interactive capabilities (all read-only, all client-side):

* Portfolio browser — click an asset, see its observed resource records, each
  with exact ID/type/state/endpoint/timestamp/freshness/provenance and
  explicit ``NOT_OBSERVED`` facts;
* interactive dependency/risk graph — clickable nodes highlight edges and a
  details pane renders the node's full recorded payload;
* read-only "What if we retire this?" — per-resource hypothetical factors come
  from the precomputed deterministic simulation record; the page never runs a
  decision engine of its own and never fabricates an outcome;
* provenance chips distinguish LIVE_ANONYMOUS reads, RECORDED_LIVE items,
  INFERRED relations, FIXTURE/UNAVAILABLE artifacts;
* an authorization-gates panel and capability matrix state exactly what the
  runtime could and could not do — there is *no* destructive button anywhere;
  the page cannot trigger anything and states that in the interface itself.

Inputs (all optional; a missing input is rendered as UNAVAILABLE, never as
omitted and never invented):

* ``--portfolio``   portfolio JSON record (multi-resource, v2)
* ``--risk-map``    risk map JSON record (with cross-resource nodes)
* ``--decision``    deterministic decision JSON
* ``--receipt``     retirement receipt JSON (absent at the current stage)
* ``--capsule``     proof capsule JSON
* ``--simulation``  simulation JSON record
* ``--workflow``    workflow assessment JSON
* ``--tripwire``    tripwire report JSON
* ``--duo-external`` external Duo-session evidence-ladder JSON
* ``--duo-reconciliation`` recorded termivance.duo_reconciliation/v1 record
* ``--witness``     recorded termivance.resurrection_witness/v1 record

The provenance label is honest (QA-FIX D): ``RECORDED_LIVE`` only when the
supplied receipt is a *coherent, recognized* v3 receipt that records an
attempted, accepted mutation. A receipt with an unknown schema, a malformed
body, no recorded attempt or no 2xx provider status is classified
``INVALID`` / ``BLOCKED`` / ``NOT_RUN`` by a fail-closed classifier — schema
presence alone is never live evidence, provider acceptance is never absence,
and ``OBSERVED_ABSENT`` may appear only because the coherent receipt's own
recorded verdict says so.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

NOT_OBSERVED = "NOT_OBSERVED"
UNAVAILABLE = "UNAVAILABLE"

#: The only receipt schema this build understands. A receipt file whose schema
#: is unrecognized is rendered ``INVALID`` — never as evidence.
RECOGNIZED_RECEIPT_SCHEMAS = frozenset({"termivance.retirement_receipt/v3"})

#: Verdicts that assert an evidence-backed retirement outcome. These may be
#: displayed only because a *coherent recognized* receipt itself records the
#: deterministic code's verdict; the Control Room re-verifies nothing.
AUTHORITATIVE_VERDICTS = frozenset({"RETIRED", "OBSERVED_ABSENT", "RESURRECTION_CONTROLLED"})
KNOWN_VERDICTS = frozenset(
    {
        "NOT_RUN",
        "BLOCKED",
        "INCONCLUSIVE",
        "SAFE_TO_RETIRE",
        "RETIRED",
        "OBSERVED_ABSENT",
        "RESURRECTION_CONTROLLED",
    }
)


def _validate_receipt_durable_provenance(
    receipt: dict[str, object],
    *,
    ledger: object | None = None,
    target: object | None = None,
) -> tuple[str, str, str]:
    """Check whether the receipt carries the durable provenance chain required
    to distinguish a locally fabricated JSON from an authenticated ledger record.

    Returns ``(evidence_level, ledger_validation, detail)``.

    A locally supplied JSON object, even one with internally consistent fields,
    must NOT receive a label claiming actual ledger validation unless the actual
    durable ledger file has been read and authenticated using the established
    receipt/ledger contracts.

    If genuine validation cannot occur in the static builder, the result is
    explicitly labeled as an internally consistent but unverified recorded claim.
    A user-supplied ledger path string is not evidence that the file was read.
    """
    authorization_binding = receipt.get("authorization_binding")
    authorization_record = receipt.get("authorization_record")
    operation_id = receipt.get("operation_id")

    # Level 1: mandatory binding and operation ID
    if not isinstance(authorization_binding, str) or not authorization_binding:
        return (
            "UNTRUSTED_LOCAL_CLAIM",
            "UNVERIFIED_NO_LEDGER",
            "the receipt carries no authorization_binding; a receipt without an "
            "authorization chain could have been fabricated by any code",
        )
    if not isinstance(operation_id, str) or not operation_id:
        return (
            "UNTRUSTED_LOCAL_CLAIM",
            "UNVERIFIED_NO_LEDGER",
            "the receipt carries no operation_id; without a unique operation "
            "identifier the claim cannot be bound to any ledger record",
        )

    # Level 2: structural record completeness
    if not isinstance(authorization_record, dict):
        return (
            "UNVERIFIED_RECORDED_CLAIM",
            "UNVERIFIED_NO_LEDGER",
            "the receipt has an authorization binding and operation ID but no "
            "execution-time authorization record; unverified recorded claim",
        )

    # Level 3: internal consistency of authorization record fields
    record_binding = authorization_record.get("binding")
    record_nonce = authorization_record.get("nonce")
    record_action = authorization_record.get("action")
    record_target_key = authorization_record.get("target_key")

    if not all(
        isinstance(v, str) and bool(v)
        for v in (record_binding, record_nonce, record_action, record_target_key)
    ):
        return (
            "UNVERIFIED_RECORDED_CLAIM",
            "UNVERIFIED_NO_LEDGER",
            "the execution-time authorization record is incomplete; the receipt "
            "is an unverified recorded claim whose provenance cannot be validated",
        )
    if str(record_binding) != authorization_binding:
        return (
            "UNTRUSTED_LOCAL_CLAIM",
            "LEDGER_VERIFICATION_FAILED",
            "the execution-time authorization record disagrees with the "
            "receipt's authorization_binding; internal inconsistency makes "
            "this an untrusted local claim",
        )

    # Level 4: genuine durable ledger verification
    ledger_obj = ledger
    if isinstance(ledger_obj, (str, Path)):
        p = Path(ledger_obj)
        if p.exists() and p.is_file():
            try:
                from termivance.ledger import AuthorizationLedger

                l_cand = AuthorizationLedger(p)
                l_cand.health_check()
                ledger_obj = l_cand
            except Exception as exc:
                return (
                    "UNTRUSTED_LOCAL_CLAIM",
                    "LEDGER_VERIFICATION_FAILED",
                    f"durable ledger path exists but failed health check: {exc}",
                )

    if ledger_obj is not None:
        try:
            from termivance.capsule import validate_mutation_receipt
            from termivance.target import TargetIdentity

            target_to_use = target
            if target_to_use is None and isinstance(receipt.get("target"), dict):
                target_to_use = TargetIdentity.from_dict(dict(receipt["target"]))  # type: ignore[arg-type]

            if target_to_use is not None:
                validate_mutation_receipt(receipt, target_to_use, ledger=ledger_obj)
                return (
                    "LEDGER_VALIDATED",
                    "LEDGER_VALIDATED",
                    "the receipt was authenticated against the durable ledger; "
                    f"operation {operation_id} is verified in state CONSUMED_ACCEPTED",
                )
            return (
                "UNVERIFIED_RECORDED_CLAIM",
                "UNVERIFIED_NO_LEDGER",
                "target identity could not be resolved to validate against ledger",
            )
        except Exception as exc:
            return (
                "UNTRUSTED_LOCAL_CLAIM",
                "LEDGER_VERIFICATION_FAILED",
                f"durable ledger verification failed: {exc}",
            )

    # No durable ledger was read or authenticated
    return (
        "UNVERIFIED_RECORDED_CLAIM",
        "UNVERIFIED_NO_LEDGER",
        "the receipt carries internally consistent authorization fields, but "
        "no durable ledger was read or authenticated; this is an unverified "
        "recorded claim, not proof",
    )


def classify_receipt(
    receipt: object,
    *,
    ledger: object | None = None,
    target: object | None = None,
) -> dict[str, object]:
    """Classify a supplied receipt artifact into its honest truth state.

    Strictly separates:
    1. claimed_verdict: what the local receipt asserts
    2. receipt_integrity: whether its structure and integrity checks pass
    3. ledger_validation: whether the actual durable ledger has been validated
    4. mutation_evidence: whether a provider-accepted mutation is genuinely established
    5. absence_evidence: whether bounded absence is supported by provider read-back
    6. display_verdict: the strongest legitimately displayable conclusion

    Never promotes a claimed verdict into a verified outcome.
    If verification is unavailable, uses UNVERIFIED_RECORDED_CLAIM.
    The UI must not show OBSERVED_ABSENT, RESURRECTION_CONTROLLED, MUTATION_ACCEPTED,
    or RECORDED_LIVE as verified outcomes merely because a supplied JSON document
    contains those fields.
    """
    if receipt is None:
        return {
            "receipt_state": "NOT_RUN",
            "display_verdict": "NOT_RUN",
            "claimed_verdict": None,
            "receipt_integrity": "NOT_RUN",
            "ledger_validation": "NOT_APPLICABLE",
            "mutation_evidence": "NOT_RUN",
            "absence_evidence": "NOT_RUN",
            "evidence_level": "NOT_APPLICABLE",
            "evidence_level_detail": "no receipt to classify",
            "mutation_attempted": None,
            "mutation_accepted": None,
            "recorded_verdict": None,
            "record": None,
            "note": (
                "no receipt artifact was supplied; the runtime records no "
                "mutation attempt and this page will not pretend otherwise"
            ),
        }
    if not isinstance(receipt, dict):
        return {
            "receipt_state": "INVALID",
            "display_verdict": "INVALID",
            "claimed_verdict": None,
            "receipt_integrity": "INVALID",
            "ledger_validation": "NOT_APPLICABLE",
            "mutation_evidence": "INVALID",
            "absence_evidence": "INVALID",
            "evidence_level": "NOT_APPLICABLE",
            "evidence_level_detail": "not a JSON object",
            "mutation_attempted": None,
            "mutation_accepted": None,
            "recorded_verdict": None,
            "record": None,
            "note": (
                "the supplied receipt artifact is not a JSON object; it is "
                "rendered INVALID, never as evidence"
            ),
        }
    schema = str(receipt.get("schema") or "")
    if schema not in RECOGNIZED_RECEIPT_SCHEMAS:
        return {
            "receipt_state": "INVALID",
            "display_verdict": "INVALID",
            "claimed_verdict": str(receipt.get("verdict") or "") or None,
            "receipt_integrity": "INVALID",
            "ledger_validation": "NOT_APPLICABLE",
            "mutation_evidence": "INVALID",
            "absence_evidence": "INVALID",
            "evidence_level": "UNTRUSTED_LOCAL_CLAIM",
            "evidence_level_detail": (
                "unrecognized schema; this object could have been fabricated "
                "by any code — it carries no recognized provenance chain"
            ),
            "mutation_attempted": None,
            "mutation_accepted": None,
            "recorded_verdict": None,
            "record": receipt,
            "note": (
                f"unrecognized receipt schema {schema!r}; only a coherent "
                f"{'/'.join(sorted(RECOGNIZED_RECEIPT_SCHEMAS))} receipt carries "
                "recorded facts, anything else is INVALID"
            ),
        }
    verdict = str(receipt.get("verdict") or "")
    if verdict not in KNOWN_VERDICTS:
        return {
            "receipt_state": "INVALID",
            "display_verdict": "INVALID",
            "claimed_verdict": verdict,
            "receipt_integrity": "INVALID",
            "ledger_validation": "NOT_APPLICABLE",
            "mutation_evidence": "INVALID",
            "absence_evidence": "INVALID",
            "evidence_level": "UNTRUSTED_LOCAL_CLAIM",
            "evidence_level_detail": (
                "the receipt carries no recognized verdict; even with the right "
                "schema, an incoherent body is an untrusted local claim"
            ),
            "mutation_attempted": receipt.get("mutation_attempted") is True,
            "mutation_accepted": None,
            "recorded_verdict": None,
            "record": receipt,
            "note": (
                f"the receipt carries no recognized verdict {verdict!r}; an "
                "incoherent receipt is INVALID, never evidence"
            ),
        }
    attempted = receipt.get("mutation_attempted") is True
    mutation = receipt.get("mutation")
    accepted = isinstance(mutation, dict) and mutation.get("accepted") is True
    status = mutation.get("status") if isinstance(mutation, dict) else None
    if attempted and accepted and not (isinstance(status, int) and 200 <= status < 300):
        return {
            "receipt_state": "INVALID",
            "display_verdict": "INVALID",
            "claimed_verdict": verdict,
            "receipt_integrity": "INVALID",
            "ledger_validation": "NOT_APPLICABLE",
            "mutation_evidence": "INVALID",
            "absence_evidence": "INVALID",
            "evidence_level": "UNTRUSTED_LOCAL_CLAIM",
            "evidence_level_detail": (
                "claims accepted mutation without integer 2xx status; "
                "internally incoherent — an untrusted local claim"
            ),
            "mutation_attempted": True,
            "mutation_accepted": None,
            "recorded_verdict": verdict,
            "record": receipt,
            "note": (
                "the receipt claims an accepted mutation without an integer 2xx "
                "provider status; an incoherent acceptance is INVALID, never "
                "evidence"
            ),
        }

    # Structurally coherent: assess durable provenance
    evidence_level, ledger_val, evidence_detail = _validate_receipt_durable_provenance(
        receipt, ledger=ledger, target=target
    )

    if not attempted:
        display = (
            "BLOCKED"
            if verdict == "BLOCKED"
            else ("UNVERIFIED_RECORDED_CLAIM" if verdict in AUTHORITATIVE_VERDICTS else verdict)
        )
        return {
            "receipt_state": display,
            "display_verdict": display,
            "claimed_verdict": verdict,
            "receipt_integrity": "STRUCTURALLY_COHERENT",
            "ledger_validation": "NOT_APPLICABLE",
            "mutation_evidence": "NOT_ATTEMPTED",
            "absence_evidence": "NOT_OBSERVED",
            "evidence_level": evidence_level,
            "evidence_level_detail": evidence_detail,
            "mutation_attempted": False,
            "mutation_accepted": None,
            "recorded_verdict": verdict,
            "record": receipt,
            "note": (
                "the recorded run did not attempt the destructive action; its "
                "recorded verdict is surfaced, never promoted"
            ),
        }

    if not accepted:
        return {
            "receipt_state": "ATTEMPT_NOT_ACCEPTED",
            "display_verdict": "ATTEMPT_NOT_ACCEPTED",
            "claimed_verdict": verdict,
            "receipt_integrity": "STRUCTURALLY_COHERENT",
            "ledger_validation": ledger_val,
            "mutation_evidence": "ATTEMPT_NOT_ACCEPTED",
            "absence_evidence": "NOT_OBSERVED",
            "evidence_level": evidence_level,
            "evidence_level_detail": evidence_detail,
            "mutation_attempted": True,
            "mutation_accepted": False,
            "recorded_verdict": verdict,
            "record": receipt,
            "note": (
                "the run attempted the DELETE but the provider did not accept "
                "it; recorded verdict is surfaced, never promoted"
            ),
        }

    # Attempted and claims accepted:
    # A locally supplied JSON receipt in the static builder can NEVER establish
    # verified absence or provider truth. It is an UNVERIFIED_RECORDED_CLAIM.
    mutation_ev = "LEDGER_RECORDED_ACCEPTED" if ledger_val == "LEDGER_VALIDATED" else "CLAIM_ONLY"
    return {
        "receipt_state": "UNVERIFIED_RECORDED_CLAIM",
        "display_verdict": "UNVERIFIED_RECORDED_CLAIM",
        "claimed_verdict": verdict,
        "receipt_integrity": "STRUCTURALLY_COHERENT",
        "ledger_validation": ledger_val,
        "mutation_evidence": mutation_ev,
        "absence_evidence": "UNVERIFIED",
        "evidence_level": evidence_level,
        "evidence_level_detail": evidence_detail,
        "mutation_attempted": True,
        "mutation_accepted": True,
        "recorded_verdict": verdict,
        "record": receipt,
        "note": (
            f"the receipt asserts verdict {verdict!r} with accepted mutation, "
            "but without independent provider read-back and ledger verification "
            "this is an UNVERIFIED_RECORDED_CLAIM; the UI displays the asserted "
            "verdict only as an untrusted recorded claim, not as verified provider truth"
        ),
    }


def _load(path: str | None) -> object:
    if path is None:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _portfolio_read_provenance(portfolio: object) -> str:
    if isinstance(portfolio, dict) and portfolio.get("provenance") == "ANONYMOUS_PUBLIC_READ":
        return "LIVE_ANONYMOUS"
    if isinstance(portfolio, dict) and portfolio.get("provenance") == "AUTHENTICATED_READ":
        return "RECORDED_LIVE"
    return "UNAVAILABLE"


def _gates(classification: dict[str, object]) -> list[dict[str, object]]:
    gate_state = str(classification.get("receipt_state") or "NOT_RUN")
    gate_note = str(classification.get("note") or "")
    return [
        {
            "gate": "READ-ONLY GITLAB API (GET)",
            "state": "AVAILABLE",
            "detail": (
                "anonymous public reads are permitted; authenticated reads "
                "require operator-supplied credentials (none stored on the "
                "executor machine)"
            ),
        },
        {
            "gate": "DELETE /projects/87785099/pages (the sole approved destructive action)",
            "state": gate_state,
            "detail": (
                "bound to immutable numeric project id, exact endpoint, one-time "
                "operator-signed approval + trust policy, durable single-use ledger, "
                "fresh SAFE_TO_RETIRE decision and operator-provided credential; "
                "GitHub-namespace approvals and API-key possession never equal consent. "
                f"Receipt truth state: {gate_note}"
            ),
        },
        {
            "gate": "Project deletion / any other project's mutation",
            "state": "STRUCTURALLY_REFUSED",
            "detail": (
                "the mutation client can only ever issue "
                "DELETE /projects/<positive-int>/pages; project deletion is "
                "unreachable by construction"
            ),
        },
        {
            "gate": "Paid plans / on-demand credits / token transfer",
            "state": "AUTHORIZED_FALSE",
            "detail": (
                "personal spend target 0.00 USD; no paid plan may be enabled "
                "without explicit operator authorization"
            ),
        },
    ]


def sanitize_paths_and_identities(obj: object) -> object:
    """Recursively sanitize absolute local machine/user paths in data structures.

    Normalizes any Windows or Linux home-directory or scratch path into a stable
    repository-relative path or redacted descriptor.
    """
    if isinstance(obj, str):
        s = obj
        # Normalize paths pointing into evidence/ to repository-relative
        m = re.search(r"(?:[A-Za-z]:[/\\]|/)?.*?[/\\](evidence[/\\][A-Za-z0-9_.\-/\\]+)", s)
        if m:
            return m.group(1).replace("\\", "/")
        # Redact any other absolute user-profile path
        if re.search(r"[A-Za-z]:[/\\]Users[/\\]", s, re.IGNORECASE):
            return re.sub(
                r"^[A-Za-z]:[/\\]Users[/\\][^/\\]+[/\\]",
                "[REDACTED_LOCAL_PATH]/",
                s,
                flags=re.IGNORECASE,
            ).replace("\\", "/")
        if re.search(r"^/home/[^/]+/", s):
            return re.sub(r"^/home/[^/]+/", "[REDACTED_LOCAL_PATH]/", s)
        return s
    if isinstance(obj, dict):
        return {k: sanitize_paths_and_identities(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_paths_and_identities(item) for item in obj]
    return obj


def build_data(args: argparse.Namespace) -> dict[str, object]:
    decision = _load(args.decision)
    receipt = _load(args.receipt)
    portfolio = _load(args.portfolio)
    risk_map = _load(args.risk_map)
    simulation = _load(args.simulation)
    capsule = _load(args.capsule)
    duo_ext_path = getattr(args, "duo_external", None)
    if duo_ext_path is None:
        p_duo = (
            Path(__file__).resolve().parents[1]
            / "evidence"
            / "b4"
            / "duo_session_9671626_readback.json"
        )
        if p_duo.exists():
            duo_ext_path = str(p_duo)
    duo_evidence = _load(duo_ext_path)
    demo_discovery_path = (
        Path(__file__).resolve().parents[1] / "evidence" / "b4" / "demo_duo_target_discovery.json"
    )
    demo_discovery = _load(str(demo_discovery_path)) if demo_discovery_path.exists() else None

    # Primary target-specific Duo reconciliation (Session 9710085, Issue #5)
    duo_recon_primary_path = getattr(args, "duo_reconciliation_primary", None)
    if duo_recon_primary_path is None:
        p5 = (
            Path(__file__).resolve().parents[1]
            / "evidence"
            / "b4"
            / "duo_reconciliation_issue_5.json"
        )
        if p5.exists():
            duo_recon_primary_path = str(p5)
    duo_reconciliation_primary = _load(duo_recon_primary_path)

    # Historical contextual Duo reconciliation (Session 9671626, Issue #3)
    duo_reconciliation = _load(getattr(args, "duo_reconciliation", None))
    witness = _load(getattr(args, "witness", None))
    supervised_review = _load(getattr(args, "supervised_review", None))
    workflow = _load(args.workflow)
    tripwire = _load(args.tripwire)

    pages_publication = _load(getattr(args, "pages_publication", None))
    resurrection_monitoring = _load(getattr(args, "resurrection_monitoring", None))
    repair_sets = _load(getattr(args, "repair_sets", None))
    freshness_decay = _load(getattr(args, "freshness_decay", None))

    def _recognized(record: object, schema: str) -> dict[str, object] | None:
        if isinstance(record, dict) and record.get("schema") == schema:
            return record
        return None

    reconciliation_section = _recognized(duo_reconciliation, "termivance.duo_reconciliation/v1")
    reconciliation_primary_section = _recognized(
        duo_reconciliation_primary, "termivance.duo_reconciliation/v1"
    )
    witness_section = _recognized(witness, "termivance.resurrection_witness/v1")
    supervised_review_section = _recognized(supervised_review, "termivance.supervised_review/v1")
    pages_publication_section = _recognized(pages_publication, "termivance.pages_publication/v1")
    resurrection_monitoring_section = _recognized(
        resurrection_monitoring, "termivance.resurrection_monitor/v1"
    )
    repair_sets_section = _recognized(repair_sets, "termivance.bounded_repair_set/v1")
    freshness_decay_section = _recognized(freshness_decay, "termivance.proof_decay/v1")

    # QA-FIX D & Defect A: receipt truth is decided by the fail-closed classifier.
    # A locally supplied JSON receipt in the static builder can never raise top-level
    # provenance to RECORDED_LIVE and can never display unverified absence.
    ledger_path_arg = getattr(args, "ledger", None)
    classification = classify_receipt(receipt, ledger=ledger_path_arg)
    receipt_state = str(
        classification.get("display_verdict") or classification.get("receipt_state") or "NOT_RUN"
    )
    read_provenance = _portfolio_read_provenance(portfolio)
    provenance = read_provenance

    snapshot_metadata = {
        "is_static_viewer": True,
        "live_api_requests_at_view_time": 0,
        "destructive_controls_count": 0,
        "snapshot_recorded_at": "2026-10-19T16:26:02.530404+00:00",
        "snapshot_fresh_until": "2026-10-19T16:41:02.530404+00:00",
        "freshness_status": "EXPIRED_HISTORICAL_SNAPSHOT",
        "is_fresh": False,
        "is_stale": True,
        "observed_target_commit": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
        "observed_redeployment_mechanism": "create-pages with pages: true in .gitlab-ci.yml",
        "provenance_statement": (
            "Static historical evidence snapshot — zero live API requests at view time; "
            "the recorded 15-minute freshness window has expired; preserved historical "
            "evidence proves a surviving redeployment mechanism existed at the observed commit."
        ),
    }

    data: dict[str, object] = {
        "schema": "termivance.control_room/v2",
        "provenance_label": provenance,
        "read_provenance": read_provenance,
        "snapshot_metadata": snapshot_metadata,
        "mutation_status": (NOT_OBSERVED if receipt_state == "NOT_RUN" else receipt_state),
        "built_at": datetime.now(tz=UTC).isoformat(),
        "demo_target_discovery": demo_discovery,
        "interactive_contract": {
            "page_is_static": True,
            "network_fetches_at_view_time": 0,
            "destructive_buttons": 0,
            "note": (
                "this page embeds recorded facts and can trigger nothing; every "
                "mutation path is CLI-gated by the operator trust chain"
            ),
        },
        "sections": {
            "decision": decision if isinstance(decision, dict) else {"state": UNAVAILABLE},
            "portfolio": ({"state": UNAVAILABLE} if not isinstance(portfolio, dict) else portfolio),
            "risk_map": risk_map if isinstance(risk_map, dict) else {"state": UNAVAILABLE},
            "receipt": classification,
            "capsule": capsule if isinstance(capsule, dict) else {"state": UNAVAILABLE},
            "duo_reconciliation": (
                reconciliation_section
                if reconciliation_section is not None
                else {"state": UNAVAILABLE}
            ),
            "duo_reconciliation_primary": (
                reconciliation_primary_section
                if reconciliation_primary_section is not None
                else {"state": UNAVAILABLE}
            ),
            "witness": (witness_section if witness_section is not None else {"state": UNAVAILABLE}),
            "supervised_review": (
                supervised_review_section
                if supervised_review_section is not None
                else {"state": UNAVAILABLE}
            ),
            "simulation": (simulation if isinstance(simulation, dict) else {"state": UNAVAILABLE}),
            "workflow": workflow if isinstance(workflow, dict) else {"state": UNAVAILABLE},
            "tripwire": tripwire if isinstance(tripwire, dict) else {"state": UNAVAILABLE},
            "pages_publication": (
                pages_publication_section
                if pages_publication_section is not None
                else {"state": UNAVAILABLE}
            ),
            "resurrection_monitoring": (
                resurrection_monitoring_section
                if resurrection_monitoring_section is not None
                else {"state": UNAVAILABLE}
            ),
            "bounded_repair_sets": (
                repair_sets_section if repair_sets_section is not None else {"state": UNAVAILABLE}
            ),
            "freshness_decay": (
                freshness_decay_section
                if freshness_decay_section is not None
                else {"state": UNAVAILABLE}
            ),
        },
        "authorization_gates": _gates(classification),
        # Rendered as inert text by the page: live proof that provider-shaped
        # content is escaped, never interpreted as HTML.
        "escape_probe": "<img src=x onerror=alert(1)>&\"'",
        "external_evidence": {
            "duo_session": (
                (
                    {**_load(duo_evidence.get("source_record")), **duo_evidence}  # type: ignore[dict-item]
                    if isinstance(duo_evidence, dict)
                    and "evidence_ladder" not in duo_evidence
                    and isinstance(_load(duo_evidence.get("source_record")), dict)
                    else duo_evidence
                )
                if isinstance(duo_evidence, dict)
                else {"state": UNAVAILABLE}
            ),
        },
        "boundaries": [
            "A successful mutation is not proof of retirement; absence is only "
            "claimed by the receipt-bound bounded-absence rules.",
            "NOT_RUN / BLOCKED / NOT_OBSERVED are first-class states and are "
            "never promoted to success.",
            "Unpublishing targets exactly one disposable Pages project; the "
            "canonical repository and every other project are out of scope.",
            "Unsigned SHA-256 digests in the ledger are local tamper evidence, "
            "never cryptographic authentication of provider events.",
        ],
        "verify": {
            "command": "python -m termivance.cli capsule-verify evidence/b4/proof_capsule.json",
            "note": "local integrity check only — it never re-observes GitLab",
        },
        "generated_by": "scripts/build_control_room.py (deterministic, from recorded files)",
    }
    return data


def write_data_js(data: dict[str, object], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "data.js"
    clean_data = sanitize_paths_and_identities(data)
    payload = json.dumps(clean_data, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text("window.TERMIVANCE_DATA = " + payload + ";\n", encoding="utf-8")
    return path


def ensure_index(out_dir: Path) -> Path:
    index = out_dir / "index.html"
    template_dir = Path(__file__).resolve().parents[1] / "control_room"
    source = template_dir / "index.html"
    index.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "portfolio",
        "risk-map",
        "decision",
        "receipt",
        "capsule",
        "simulation",
        "workflow",
        "tripwire",
        "duo-external",
        "duo-reconciliation",
        "duo-reconciliation-primary",
        "witness",
        "supervised-review",
        "ledger",
        "pages-publication",
        "resurrection-monitoring",
        "repair-sets",
        "freshness-decay",
    ):
        parser.add_argument(f"--{name}", dest=name.replace("-", "_"), default=None)
    parser.add_argument("--out-dir", default="control_room")
    args = parser.parse_args()

    data = build_data(args)
    out_dir = Path(args.out_dir)
    data_path = write_data_js(data, out_dir)
    index_path = ensure_index(out_dir)
    digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
    print(f"control room built: {data_path} + {index_path}")
    print(f"provenance: {data['provenance_label']}")
    print(f"data.js sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
