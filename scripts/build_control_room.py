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

The provenance label is honest: ``RECORDED_LIVE`` only when a live receipt is
supplied; otherwise the reads label (``LIVE_ANONYMOUS`` when the embedded
portfolio says the evidence was read anonymously and live).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

NOT_OBSERVED = "NOT_OBSERVED"
UNAVAILABLE = "UNAVAILABLE"


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


def _gates(receipt: object) -> list[dict[str, object]]:
    live_receipt = isinstance(receipt, dict) and "schema" in receipt
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
            "state": "LIVE_RECEIPT" if live_receipt else "NOT_RUN",
            "detail": (
                "bound to immutable numeric project id, exact endpoint, one-time "
                "operator-signed approval + trust policy, durable single-use ledger, "
                "fresh SAFE_TO_RETIRE decision and operator-provided credential; "
                "GitHub-namespace approvals and API-key possession never equal consent"
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
    workflow = _load(args.workflow)
    tripwire = _load(args.tripwire)

    live_receipt = isinstance(receipt, dict) and receipt.get("schema") is not None
    read_provenance = _portfolio_read_provenance(portfolio)
    provenance = "RECORDED_LIVE" if live_receipt else read_provenance

    data: dict[str, object] = {
        "schema": "termivance.control_room/v2",
        "provenance_label": provenance,
        "read_provenance": read_provenance,
        "mutation_status": "LIVE_RECEIPT" if live_receipt else NOT_OBSERVED,
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
            "receipt": receipt if isinstance(receipt, dict) else {"state": "NOT_RUN"},
            "capsule": capsule if isinstance(capsule, dict) else {"state": UNAVAILABLE},
            "simulation": (
                simulation if isinstance(simulation, dict) else {"state": UNAVAILABLE}
            ),
            "workflow": workflow if isinstance(workflow, dict) else {"state": UNAVAILABLE},
            "tripwire": tripwire if isinstance(tripwire, dict) else {"state": UNAVAILABLE},
        },
        "authorization_gates": _gates(receipt),
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
