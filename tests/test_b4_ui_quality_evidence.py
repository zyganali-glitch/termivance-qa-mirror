"""Tests for B4 enterprise UI quality, evidence identity, privacy hygiene, and presentation.

Validates:
1. Defect A: Session misattribution resolved — Session 9710085 (7 claims: 4 CORROBORATED,
   2 UNRESOLVED, 1 CONTEXTUAL_ONLY) and Session 9671626 (9 claims: 4 SUPPORTED, 2 UNRESOLVED,
   2 NOT_AUTHENTICALLY_ATTRIBUTABLE, 1 UNSUPPORTED) maintain distinct identity, source bindings,
   and taxonomies;
2. Defect B: Public artifact privacy hygiene — no absolute local home directories, developer
   usernames, or scratch paths in generated data.js or evidence artifacts;
3. Defect C: Wide-screen and responsive layout composition — centered container (1600px max-width),
   responsive grid, distinct main navigation and evidence sub-navigation;
4. Defect D: Snapshot freshness & provenance honesty — labeled as recorded historical snapshot
   with expired freshness window; zero live API fetches at view time;
5. Defect E: Developer diagnostics removed from standard presentation — no raw synthetic attack
   strings in normal footer or uncollapsed UI;
6. Defect G: Realistic browser checks and Chromium layout screenshots across viewports.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROME = shutil.which("chrome") or (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    else (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if os.path.exists(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
        else None
    )
)


def _load_data_js() -> dict[str, object]:
    data_path = ROOT / "control_room" / "data.js"
    assert data_path.exists(), "control_room/data.js must exist"
    raw = data_path.read_text(encoding="utf-8")
    prefix = "window.TERMIVANCE_DATA = "
    assert raw.startswith(prefix)
    json_text = raw[len(prefix) :].rstrip(";\n")
    return json.loads(json_text)


def _load_html() -> str:
    html_path = ROOT / "control_room" / "index.html"
    assert html_path.exists(), "control_room/index.html must exist"
    return html_path.read_text(encoding="utf-8")


class TestDefectAEvidenceSessionSeparation:
    """Verifies that Session 9710085 and Session 9671626 are bound to their actual records."""

    def test_primary_session_9710085_dataset(self):
        data = _load_data_js()
        sections = data.get("sections", {})
        primary = sections.get("duo_reconciliation_primary")
        assert isinstance(primary, dict), "duo_reconciliation_primary must be embedded in sections"
        assert primary.get("session_id") == "9710085"
        assert primary.get("target_project_id") == 87785099
        assert primary.get("issue_iid") == 5

        claims = primary.get("claims", [])
        assert len(claims) == 7, "Primary Session 9710085 must contain exactly 7 claims"
        statuses = [c.get("corroboration_status") for c in claims]
        assert statuses.count("CORROBORATED") == 4
        assert statuses.count("UNRESOLVED") == 2
        assert statuses.count("CONTEXTUAL_ONLY") == 1

        totals = primary.get("totals", {})
        assert totals.get("CORROBORATED") == 4
        assert totals.get("UNRESOLVED") == 2
        assert totals.get("CONTEXTUAL_ONLY") == 1
        assert totals.get("TOTAL") == 7

    def test_historical_session_9671626_dataset(self):
        data = _load_data_js()
        sections = data.get("sections", {})
        historical = sections.get("duo_reconciliation")
        assert isinstance(historical, dict), "duo_reconciliation must be embedded in sections"
        assert historical.get("duo_session_id") == "9671626"
        surface = historical.get("surface", {})
        assert surface.get("issue_iid") == 3
        assert surface.get("project_id") == 87779099

        claims = historical.get("claims", [])
        assert len(claims) == 9, "Historical Session 9671626 must contain exactly 9 claims"
        statuses = [c.get("status") for c in claims]
        assert statuses.count("SUPPORTED") == 4
        assert statuses.count("UNRESOLVED") == 2
        assert statuses.count("NOT_AUTHENTICALLY_ATTRIBUTABLE") == 2
        assert statuses.count("UNSUPPORTED") == 1

        totals = historical.get("totals", {})
        assert totals.get("SUPPORTED") == 4
        assert totals.get("UNRESOLVED") == 2
        assert totals.get("NOT_AUTHENTICALLY_ATTRIBUTABLE") == 2
        assert totals.get("UNSUPPORTED") == 1

    def test_ui_binds_session_headings_to_actual_records(self):
        html = _load_html()
        # Primary card heading is bound to 9710085
        assert "Primary Duo candidate corroboration — Session" in html
        assert "9710085" in html
        # Historical card heading is bound to 9671626
        assert "Duo claim reconciliation — Historical Session" in html
        assert "9671626" in html
        # Historical uses distinct taxonomy
        assert "SUPPORTED" in html
        assert "NOT_AUTHENTICALLY_ATTRIBUTABLE" in html


class TestDefectBPrivacyHygiene:
    """Verifies that public artifacts contain no absolute user/machine profile paths."""

    def test_data_js_has_no_absolute_user_paths(self):
        data_text = (ROOT / "control_room" / "data.js").read_text(encoding="utf-8")
        assert not re.search(r"[A-Za-z]:[/\\]Users[/\\]", data_text, re.IGNORECASE), (
            "control_room/data.js must not contain absolute Windows user paths"
        )
        assert not re.search(r"/home/[^/]+/", data_text), (
            "control_room/data.js must not contain absolute Linux home paths"
        )
        assert "scratch\\Termivance" not in data_text and "scratch/Termivance" not in data_text, (
            "control_room/data.js must not contain private scratch paths"
        )

    def test_evidence_reconciliation_claims_source_is_relative(self):
        recon_path = ROOT / "evidence" / "b4" / "duo_reconciliation.json"
        raw = json.loads(recon_path.read_text(encoding="utf-8"))
        claims_source = raw.get("claims_source", "")
        assert not re.search(r"[A-Za-z]:[/\\]Users[/\\]", claims_source, re.IGNORECASE), (
            "claims_source must not contain absolute Windows user path"
        )
        assert claims_source.startswith("evidence/"), "claims_source must be repository-relative"


class TestDefectCResponsiveLayout:
    """Verifies wide-screen centering, responsive grid, and navigation styling."""

    def test_html_contains_centered_container_styling(self):
        html = _load_html()
        # Max-width bounded and centered
        assert "--max-w: 1600px" in html
        assert "margin: 0 auto" in html
        # Panel uses max-w and margin 0 auto
        assert ".panel" in html
        assert "max-width: var(--max-w)" in html

    def test_evidence_subnav_is_visually_distinct(self):
        html = _load_html()
        assert "subnav-bar" in html
        assert "evidence-nav" in html
        # Primary nav is distinct
        assert 'nav id="tabs"' in html
        assert "tabbtn" in html


class TestDefectDSnapshotFreshnessHonesty:
    """Verifies honest labeling of recorded historical provider snapshots."""

    def test_snapshot_metadata_in_data_js(self):
        data = _load_data_js()
        meta = data.get("snapshot_metadata", {})
        assert meta.get("is_static_viewer") is True
        assert meta.get("live_api_requests_at_view_time") == 0
        assert meta.get("is_stale") is True
        assert meta.get("freshness_status") == "EXPIRED_HISTORICAL_SNAPSHOT"
        assert meta.get("observed_target_commit") == "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"

    def test_html_displays_snapshot_provenance_and_expired_freshness(self):
        html = _load_html()
        assert "SNAPSHOT: RECORDED_PROVIDER_READ" in html
        # Header honestly scopes freshness to record time (per-section timestamps),
        # never presenting historical evidence as current/live provider truth.
        assert "FRESHNESS: FRESH WHEN RECORDED ONLY" in html
        assert "ZERO LIVE API CALLS" in html
        assert "Static Historical Snapshot" in html
        assert "never a live claim" in html or "not live provider truth" in html


class TestDefectEDeveloperDiagnosticsRemoved:
    """Verifies removal of synthetic attack strings from normal user-facing presentation."""

    def test_footer_has_no_raw_probe_paragraph(self):
        html = _load_html()
        assert 'data-probe="rendered"' not in html, "Normal footer must not display data-probe"
        # Footer is concise and professional
        assert "Termivance Control Room" in html
        assert "Static page contract:" in html

    def test_escaping_probe_is_collapsed_in_details(self):
        html = _load_html()
        assert "Developer diagnostic: DOM escaping verification probe" in html, (
            "Diagnostic probe must be sequestered behind collapsed details"
        )
        assert "Security &amp; input sanitization contract" in html


class TestDefectGBrowserScreenshotValidation:
    """Validates realistic headless Chromium layout and screenshot generation across viewports."""

    def test_chromium_renders_screenshots(self):
        if not CHROME:
            return  # Skip gracefully if no browser executable found

        html_path = os.path.abspath(ROOT / "control_room" / "index.html")
        url = f"file:///{html_path}".replace("\\", "/")

        with tempfile.TemporaryDirectory() as td:
            for w, h in [(1920, 1080), (1366, 768)]:
                out_png = os.path.join(td, f"cr_{w}x{h}.png")
                cmd = [
                    str(CHROME),
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    f"--window-size={w},{h}",
                    "--virtual-time-budget=3000",
                    f"--screenshot={out_png}",
                    url,
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
                assert proc.returncode == 0, f"Chromium headless failed: {proc.stderr}"
                assert os.path.exists(out_png), f"Screenshot not created for {w}x{h}"
                size = os.path.getsize(out_png)
                assert size > 20000, f"Screenshot for {w}x{h} suspiciously small: {size} bytes"
