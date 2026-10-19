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
  tabs: ["tab-portfolio", "tab-graph", "tab-whatif", "tab-proof"].map((id) => {{
    const el = elements[id];
    return {{ id, length: el ? el.innerHTML.length : -1 }};
  }}),
  proofHtml: elements["tab-proof"] ? elements["tab-proof"].innerHTML : "",
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
    # Initial render populates portfolio/what-if/proof; the graph tab is
    # rendered lazily on click and is not exercised by this smoke render.
    rendered = {tab["id"]: tab["length"] for tab in out["tabs"]}
    for tab_id in ("tab-portfolio", "tab-whatif", "tab-proof"):
        assert rendered[tab_id] > 0, f"{tab_id} rendered blank"

    proof = out["proofHtml"]
    assert len(proof) > 1000, "proof tab rendered suspiciously little"
    assert "Duo claim reconciliation" in proof
    assert "NOT_AUTHENTICALLY_ATTRIBUTABLE" in proof
    assert "Resurrection counterexample witness" in proof
    assert "MECHANISM_PRESENT_IN_OBSERVED_CONFIG" in proof
    assert "cannot verify this Pages administration surface" in proof
    assert "Retirement receipt" in proof
    assert "No live mutation receipt exists" in proof
    assert "(live)" not in proof
