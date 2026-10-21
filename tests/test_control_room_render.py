"""Render the shipped Control Room page under a minimal DOM stub in Node.

This is the only test that executes the page's own JavaScript. Source-text
assertions (CI safety checks) cannot catch a page that parses but renders
blank or drops a truth-state card; this test closes that gap by running the
real inline script against the real embedded data. Skipped when Node is not
installed (e.g. a minimal CI image) so the suite stays portable.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node runtime unavailable")


def _extract_page_script(html: str) -> str:
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    assert scripts, "control room page must ship an inline script"
    return scripts[-1]


def test_control_room_renders_truth_state_cards(tmp_path):
    html = (ROOT / "control_room" / "index.html").read_text(encoding="utf-8")
    page_js_path = tmp_path / "page.js"
    page_js_path.write_text(_extract_page_script(html), encoding="utf-8")

    syntax = subprocess.run(
        [NODE, "--check", str(page_js_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert syntax.returncode == 0, syntax.stderr

    harness = f"""
const fs = require("fs");
const vm = require("vm");
const dataSrc = fs.readFileSync({json.dumps(str(ROOT / "control_room" / "data.js"))}, "utf-8");
const pageSrc = fs.readFileSync({json.dumps(str(page_js_path))}, "utf-8");

const elements = {{}};
function fakeEl(id) {{
  return (elements[id] = elements[id] || {{
    id, innerHTML: "", textContent: "", className: "",
    addEventListener() {{}}, querySelectorAll() {{ return []; }},
    style: {{}}, dataset: {{}},
  }});
}}
const ctx = {{
  window: {{}},
  document: {{
    getElementById: (id) => fakeEl(id),
    querySelectorAll: () => [],
    addEventListener: () => {{}},
  }},
  console,
  setTimeout: (fn) => fn(),
}};
vm.createContext(ctx);
vm.runInContext(dataSrc, ctx);  // sets window.TERMIVANCE_DATA
vm.runInContext(pageSrc, ctx);  // runs the page script

const out = {{
  tabs: ["tab-overview", "tab-portfolio", "tab-graph", "tab-whatif", "tab-proof"].map((id) => {{
    const el = elements[id];
    return {{ id, length: el ? el.innerHTML.length : -1 }};
  }}),
  proofHtml: elements["tab-proof"] ? elements["tab-proof"].innerHTML : "",
  overviewHtml: elements["tab-overview"] ? elements["tab-overview"].innerHTML : "",
}};
console.log(JSON.stringify(out));
"""
    harness_path = tmp_path / "harness.js"
    harness_path.write_text(harness, encoding="utf-8")
    proc = subprocess.run(
        [NODE, str(harness_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr

    out = json.loads(proc.stdout)
    # Initial render populates overview/portfolio/what-if/proof; the graph tab
    # is rendered lazily on click and is not exercised by this smoke render.
    rendered = {tab["id"]: tab["length"] for tab in out["tabs"]}
    for tab_id in ("tab-overview", "tab-portfolio", "tab-whatif", "tab-proof"):
        assert rendered[tab_id] > 0, f"{tab_id} rendered blank"

    proof = out["proofHtml"]
    assert len(proof) > 1000, "proof tab rendered suspiciously little"
    assert "Duo claim reconciliation" in proof
    assert "NOT_AUTHENTICALLY_ATTRIBUTABLE" in proof
    assert "Resurrection counterexample witness" in proof
    assert "MECHANISM_PRESENT_IN_OBSERVED_CONFIG" in proof
    assert "cannot verify this Pages administration surface" in proof
    assert "Supervised retirement review" in proof
    assert (
        "AI proposes candidate claims; deterministic engine owns authorization and verdicts"
        in proof
    )
    assert "Multi-step causal review pipeline" in proof
    assert "Counterfactual analysis" in proof
    assert "Retirement receipt" in proof
    assert "No live mutation receipt exists" in proof
    assert "(live)" not in proof

    # B4 integrity correction: historical freshness must be displayed as
    # FRESH WHEN RECORDED, never as current/live freshness.
    assert "FRESH WHEN RECORDED" in proof
    assert "freshness: FRESH<" not in proof
    assert "AT RECORDED EVALUATION TIME" in proof or "WHEN RECORDED" in proof
    # Level 2 must display the honest NOT_OBSERVED status, not a
    # success-looking fallback.
    assert "NOT_OBSERVED_NOT_FOUND" in proof
    assert "DEPLOYMENTS_FOUND" not in proof
    # Level 5 source corroboration is displayed explicitly.
    assert "VERIFIED IN REPOSITORY SOURCE AT OBSERVED COMMIT" in proof
    # The resurrection monitor truth state is surfaced.
    assert "HISTORICAL_RECEIPT_UNVERIFIED" in proof


def test_control_room_generated_data_matches_corrected_evidence():
    """The generated data.js must carry the corrected evidence values with
    complete data/schema parity to the real generated records."""
    text = (ROOT / "control_room" / "data.js").read_text(encoding="utf-8")
    assert text.startswith("window.TERMIVANCE_DATA = ")
    data = json.loads(text[len("window.TERMIVANCE_DATA = ") :].rstrip().rstrip(";"))

    assert data["schema"] == "termivance.control_room/v2"
    assert data["interactive_contract"]["page_is_static"] is True
    assert data["interactive_contract"]["network_fetches_at_view_time"] == 0
    assert data["interactive_contract"]["destructive_buttons"] == 0

    pp = data["sections"]["pages_publication"]
    assert pp["schema"] == "termivance.pages_publication_evidence/v1"
    assert pp["target"]["project_id"] == 87785099
    assert (
        pp["target"]["full_path"]
        == "gitlab-ai-hackathon/transcend-october-2026/39306908/"
        "termivance-b3-disposable-pages-demo"
    )
    assert pp["status"] == "VERIFIED_LIVE_SERVED"
    assert pp["commit_sha"] == "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
    assert (
        pp["served_url"]
        == "https://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/"
    )
    assert pp["observed_at"].startswith("2026-10-21")
    # Level 2 is honestly NOT_OBSERVED (Pages deployments API inaccessible).
    assert pp["levels"]["level2_deployment_created"] is False
    assert pp["levels"]["level2_deployment_status"].startswith("NOT_OBSERVED")
    # Level 5 separates served presence from the source-bound claim.
    assert pp["levels"]["level5_marker_independently_observed"] is True
    assert pp["levels"]["level5_source_corroborated"] is True
    assert pp["freshness_scope"].startswith("EVALUATION_TIME_ONLY")

    rm = data["sections"]["resurrection_monitoring"]
    assert rm["schema"] == "termivance.resurrection_monitor/v1"
    assert rm["current_truth"] == "HISTORICAL_RECEIPT_UNVERIFIED"
    assert rm["resurrection_control"] == "NOT_CLAIMED"

    fd = data["sections"]["freshness_decay"]
    assert fd["schema"] == "termivance.proof_decay/v1"
    assert fd["state"] in ("FRESH", "EXPIRING", "EXPIRED", "NOT_OBSERVED")

    # No secret, token, absolute personal path or unescaped provider HTML.
    assert "glpat-" not in text
    assert "PRIVATE-TOKEN" not in text
    assert "Dell 24" not in text
    assert "C:\\\\Users" not in text
    assert "/home/" not in text


def test_control_room_page_ships_five_functional_tabs():
    """All five existing tabs (Overview, Portfolio, Obligation Graph, What-if,
    Evidence & Audit) remain present and wired in the shipped page."""
    html = (ROOT / "control_room" / "index.html").read_text(encoding="utf-8")
    for tab in ("overview", "portfolio", "graph", "whatif", "proof"):
        assert f'data-tab="{tab}"' in html, f"tab button {tab} missing"
        assert f'id="tab-{tab}"' in html, f"tab panel {tab} missing"
