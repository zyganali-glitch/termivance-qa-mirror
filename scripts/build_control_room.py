#!/usr/bin/env python3
"""Build the static Control Room UI from recorded evidence artifacts.

The Control Room is a judge-facing single page generated *deterministically*
from files on disk. It performs no network fetch at view time: everything is
embedded into ``data.js`` (``window.TERMIVANCE_DATA``), so the page works from
``file://`` without any server, proxy or CDN.

Inputs (all optional; each missing input is rendered as an explicit
``NOT_OBSERVED`` section, never omitted or invented):

* ``--portfolio``   portfolio JSON record
* ``--risk-map``    risk map JSON record
* ``--decision``    deterministic decision JSON
* ``--receipt``     retirement receipt JSON (from the one real flow)
* ``--capsule``     proof capsule JSON
* ``--simulation``  simulation JSON record
* ``--workflow``    workflow assessment JSON
* ``--tripwire``    tripwire report JSON

The provenance label is honest: ``RECORDED_LIVE`` only when a live receipt or
live-observed decision is supplied; otherwise ``FIXTURE``.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

NOT_OBSERVED = "NOT_OBSERVED"


def _load(path: str | None) -> object:
    if path is None:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_data(args: argparse.Namespace) -> dict[str, object]:
    decision = _load(args.decision)
    receipt = _load(args.receipt)
    live_reads = isinstance(decision, dict) and (
        decision.get("evidence_classification") == "RECORDED_LIVE"
    )
    provenance = (
        "RECORDED_LIVE"
        if (receipt is not None or live_reads)
        else "FIXTURE"
    )
    data: dict[str, object] = {
        "schema": "termivance.control_room/v1",
        "provenance_label": provenance,
        # The B4 live state separates the two kinds of reality explicitly:
        # reads can be live-observed while the mutation stays NOT_RUN.
        "read_provenance": (
            "AUTHENTICATION_COMPLETE" if receipt is not None else "ANONYMOUS_PUBLIC_READ"
        ),
        "mutation_status": "LIVE_RECEIPT" if receipt is not None else "NOT_RUN",
        "built_at": datetime.now(tz=UTC).isoformat(),
        "sections": {
            "decision": decision if isinstance(decision, dict) else {"state": NOT_OBSERVED},
            "portfolio": _load(args.portfolio) or {"state": NOT_OBSERVED},
            "risk_map": _load(args.risk_map) or {"state": NOT_OBSERVED},
            "receipt": receipt or {"state": NOT_OBSERVED},
            "capsule": _load(args.capsule) or {"state": NOT_OBSERVED},
            "simulation": _load(args.simulation) or {"state": NOT_OBSERVED},
            "workflow": _load(args.workflow) or {"state": NOT_OBSERVED},
            "tripwire": _load(args.tripwire) or {"state": NOT_OBSERVED},
        },
        "boundaries": [
            "A successful mutation is not proof of retirement; absence is only "
            "claimed by the receipt-bound bounded-absence rules.",
            "NOT_RUN / BLOCKED / NOT_OBSERVED are first-class states and are "
            "never promoted to success.",
            "Unpublishing targets exactly one disposable Pages project; the "
            "canonical repository and every other project are out of scope.",
        ],
        "verify": {
            "command": (
                "python -m termivance.cli capsule-verify evidence/b4/proof_capsule.json"
            ),
            "note": "local integrity check only — it never re-observes GitLab",
        },
        "generated_by": "scripts/build_control_room.py (deterministic, from recorded files)",
    }
    return data


def write_data_js(data: dict[str, object], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "data.js"
    payload = json.dumps(data, indent=2, sort_keys=True)
    path.write_text(f"window.TERMIVANCE_DATA = {payload};\n", encoding="utf-8")
    return path


def ensure_index(out_dir: Path) -> Path:
    index = out_dir / "index.html"
    if index.exists():
        return index
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
    ):
        parser.add_argument(f"--{name}", dest=name.replace("-", "_"), default=None)
    parser.add_argument("--out-dir", default="control_room")
    parser.add_argument("--force-index", action="store_true", help="regenerate index.html")
    args = parser.parse_args()

    data = build_data(args)
    out_dir = Path(args.out_dir)
    data_path = write_data_js(data, out_dir)
    if args.force_index:
        (out_dir / "index.html").unlink(missing_ok=True)
    index_path = ensure_index(out_dir)
    print(f"control room built: {data_path} + {index_path}")
    print(f"provenance: {data['provenance_label']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
