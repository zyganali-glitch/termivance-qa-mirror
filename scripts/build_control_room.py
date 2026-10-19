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
AUTHORITATIVE_VERDICTS = frozenset(
    {"RETIRED", "OBSERVED_ABSENT", "RESURRECTION_CONTROLLED"}
)
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


def _validate_receipt_durable_provenance(receipt: dict[str, object]) -> tuple[str, str]:
    """Check whether the receipt carries the durable provenance chain required
    to distinguish a locally fabricated JSON from a credible recorded claim.

    Returns ``(evidence_level, detail)`` where evidence_level is one of:

    * ``UNTRUSTED_LOCAL_CLAIM`` — the receipt-shaped object lacks mandatory
      cross-validation fields; it could have been constructed by any code.
    * ``STRUCTURALLY_COHERENT_RECORDED_CLAIM`` — the receipt has the correct
      structure but its provenance has not been independently verified against
      a durable ledger or the provider; it is a *recorded claim*, not proof.
    * ``LEDGER_CROSS_VALIDATED`` — a structurally coherent receipt whose
      execution-time authorization record, operation ID, target key and nonce
      are all present and internally consistent (could be validated against a
      durable ledger); this is the strongest level the static Control Room can
      assess without actually reading the ledger file.

    The static build can never reach ``PROVIDER_ACCEPTED`` — that requires an
    independent provider read-back at observation time, which the static page
    does not perform and must not pretend to.
    """
    # Mandatory cross-validation fields
    authorization_binding = receipt.get("authorization_binding")
    authorization_record = receipt.get("authorization_record")
    operation_id = receipt.get("operation_id")
    ledger_path = receipt.get("ledger_path")

    # Level 1: must have basic structural completeness
    if not isinstance(authorization_binding, str) or not authorization_binding:
        return (
            "UNTRUSTED_LOCAL_CLAIM",
            "the receipt carries no authorization_binding; a receipt without an "
            "authorization chain could have been fabricated by any code",
        )
    if not isinstance(operation_id, str) or not operation_id:
        return (
            "UNTRUSTED_LOCAL_CLAIM",
            "the receipt carries no operation_id; without a unique operation "
            "identifier the claim cannot be bound to any ledger record",
        )

    # Level 2: structurally coherent — has all expected fields
    if not isinstance(authorization_record, dict):
        return (
            "STRUCTURALLY_COHERENT_RECORDED_CLAIM",
            "the receipt has an authorization binding and operation ID but no "
            "execution-time authorization record; the v3 cross-validation "
            "fields are incomplete — this is a recorded claim, not proof",
        )

    # Level 3: cross-validation — check internal consistency
    record_binding = authorization_record.get("binding")
    record_nonce = authorization_record.get("nonce")
    record_action = authorization_record.get("action")
    record_target_key = authorization_record.get("target_key")

    if not all(
        isinstance(v, str) and bool(v)
        for v in (record_binding, record_nonce, record_action, record_target_key)
    ):
        return (
            "STRUCTURALLY_COHERENT_RECORDED_CLAIM",
            "the execution-time authorization record is incomplete; the receipt "
            "is a recorded claim whose provenance cannot be cross-validated",
        )
    if str(record_binding) != authorization_binding:
        return (
            "UNTRUSTED_LOCAL_CLAIM",
            "the execution-time authorization record disagrees with the "
            "receipt's authorization_binding; internal inconsistency makes "
            "this an untrusted local claim",
        )

    # Consistent — but still only a local claim without ledger verification
    ledger_note = (
        f" ledger_path={ledger_path!r}" if ledger_path else
        " (no ledger path recorded)"
    )
    return (
        "LEDGER_CROSS_VALIDATED",
        f"the receipt's execution-time authorization record is internally "
        f"consistent (binding, nonce, action, target_key all present and "
        f"agreeing);{ledger_note} — this is the strongest level a static "
        "build can assess; actual ledger and provider verification require "
        "the runtime, not this display page",
    )


def classify_receipt(receipt: object) -> dict[str, object]:
    """Classify a supplied receipt artifact into its honest truth state.

    Repair A: the classifier now distinguishes six evidence levels:

    1. **No receipt** → ``NOT_RUN``
    2. **Not a recognized coherent receipt** → ``INVALID``
    3. **Coherent non-attempt** → the recorded verdict exactly
    4. **Attempted but not accepted** → ``ATTEMPT_NOT_ACCEPTED``
    5. **Accepted mutation (coherent)** → ``MUTATION_ACCEPTED`` (never absence)
    6. **Authoritative verdict** → the recorded verdict (``OBSERVED_ABSENT`` etc.)

    Additionally, every classification now carries ``evidence_level`` which
    marks the trust boundary between:

    * ``UNTRUSTED_LOCAL_CLAIM`` — a locally supplied JSON or fabricated object
    * ``STRUCTURALLY_COHERENT_RECORDED_CLAIM`` — has the right shape but no
      independent verification
    * ``LEDGER_CROSS_VALIDATED`` — internally consistent with authorization
      record cross-checks (the strongest a static build can show)
    * ``NOT_APPLICABLE`` — for NOT_RUN / INVALID states

    A locally supplied receipt-shaped JSON can NEVER become trusted provider
    evidence. Even ``LEDGER_CROSS_VALIDATED`` is explicitly marked as a local
    consistency check — the Control Room does not re-read the ledger at build
    time and cannot prove authenticity. Only the runtime's
    ``validate_mutation_receipt`` against a real durable ledger, plus the
    independent post-mutation read-back in ``observe_absence``, can establish
    provider-grade evidence.
    """

    if receipt is None:
        return {
            "receipt_state": "NOT_RUN",
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
    if attempted and accepted and not (
        isinstance(status, int) and 200 <= status < 300
    ):
        return {
            "receipt_state": "INVALID",
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

    # For structurally coherent receipts, assess the durable provenance level
    evidence_level, evidence_detail = _validate_receipt_durable_provenance(receipt)

    if not attempted:
        return {
            "receipt_state": verdict,
            "evidence_level": evidence_level,
            "evidence_level_detail": evidence_detail,
            "mutation_attempted": False,
            "mutation_accepted": None,
            "recorded_verdict": verdict,
            "record": receipt,
            "note": (
                "the recorded run did not attempt the destructive action; its "
                "recorded verdict is surfaced exactly, never promoted"
            ),
        }
    if not accepted:
        return {
            "receipt_state": "ATTEMPT_NOT_ACCEPTED",
            "evidence_level": evidence_level,
            "evidence_level_detail": evidence_detail,
            "mutation_attempted": True,
            "mutation_accepted": False,
            "recorded_verdict": verdict,
            "record": receipt,
            "note": (
                "the run attempted the DELETE but the provider did not accept "
                "it; the recorded verdict is surfaced, never promoted"
            ),
        }
    if verdict in AUTHORITATIVE_VERDICTS:
        return {
            "receipt_state": verdict,
            "evidence_level": evidence_level,
            "evidence_level_detail": evidence_detail,
            "mutation_attempted": True,
            "mutation_accepted": True,
            "recorded_verdict": verdict,
            "record": receipt,
            "note": (
                "the coherent receipt itself records this deterministic verdict; "
                "this page displays the recorded verdict — the evidence_level "
                "indicates the trust boundary of this locally supplied claim "
                "(a static build cannot re-verify provider facts)"
            ),
        }
    return {
        "receipt_state": "MUTATION_ACCEPTED",
        "evidence_level": evidence_level,
        "evidence_level_detail": evidence_detail,
        "mutation_attempted": True,
        "mutation_accepted": True,
        "recorded_verdict": verdict,
        "record": receipt,
        "note": (
            "provider accepted the DELETE — provider action-acceptance only, "
            "never absence; absence requires proven pre-publication, accepted "
            "authorized unpublish and independent read-back; evidence_level "
            "indicates the trust boundary of this recorded claim"
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


def build_data(args: argparse.Namespace) -> dict[str, object]:
    decision = _load(args.decision)
    receipt = _load(args.receipt)
    portfolio = _load(args.portfolio)
    risk_map = _load(args.risk_map)
    simulation = _load(args.simulation)
    capsule = _load(args.capsule)
    duo_evidence = _load(args.duo_external)
    duo_reconciliation = _load(getattr(args, "duo_reconciliation", None))
    witness = _load(getattr(args, "witness", None))
    supervised_review = _load(getattr(args, "supervised_review", None))
    workflow = _load(args.workflow)
    tripwire = _load(args.tripwire)

    def _recognized(record: object, schema: str) -> dict[str, object] | None:
        if isinstance(record, dict) and record.get("schema") == schema:
            return record
        return None

    reconciliation_section = _recognized(
        duo_reconciliation, "termivance.duo_reconciliation/v1"
    )
    witness_section = _recognized(witness, "termivance.resurrection_witness/v1")
    supervised_review_section = _recognized(
        supervised_review, "termivance.supervised_review/v1"
    )

    # QA-FIX D: receipt truth is decided by the fail-closed classifier — mere
    # schema presence is never live evidence and never flips RECORDED_LIVE.
    classification = classify_receipt(receipt)
    receipt_state = str(classification["receipt_state"])
    receipt_records_live_event = receipt_state == "MUTATION_ACCEPTED" or (
        receipt_state in AUTHORITATIVE_VERDICTS and classification.get("mutation_accepted") is True
    )
    read_provenance = _portfolio_read_provenance(portfolio)
    provenance = "RECORDED_LIVE" if receipt_records_live_event else read_provenance

    data: dict[str, object] = {
        "schema": "termivance.control_room/v2",
        "provenance_label": provenance,
        "read_provenance": read_provenance,
        "mutation_status": (
            NOT_OBSERVED if receipt_state == "NOT_RUN" else receipt_state
        ),
        "built_at": datetime.now(tz=UTC).isoformat(),
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
            "portfolio": (
                {"state": UNAVAILABLE} if not isinstance(portfolio, dict) else portfolio
            ),
            "risk_map": risk_map if isinstance(risk_map, dict) else {"state": UNAVAILABLE},
            "receipt": classification,
            "capsule": capsule if isinstance(capsule, dict) else {"state": UNAVAILABLE},
            "duo_reconciliation": (
                reconciliation_section
                if reconciliation_section is not None
                else {"state": UNAVAILABLE}
            ),
            "witness": (
                witness_section if witness_section is not None else {"state": UNAVAILABLE}
            ),
            "supervised_review": (
                supervised_review_section
                if supervised_review_section is not None
                else {"state": UNAVAILABLE}
            ),
            "simulation": (
                simulation if isinstance(simulation, dict) else {"state": UNAVAILABLE}
            ),
            "workflow": workflow if isinstance(workflow, dict) else {"state": UNAVAILABLE},
            "tripwire": tripwire if isinstance(tripwire, dict) else {"state": UNAVAILABLE},
        },
        "authorization_gates": _gates(classification),
        # Rendered as inert text by the page: live proof that provider-shaped
        # content is escaped, never interpreted as HTML.
        "escape_probe": '<img src=x onerror=alert(1)>&"\'',
        "external_evidence": {
            "duo_session": (
                duo_evidence
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
    payload = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
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
        "witness",
        "supervised-review",
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
