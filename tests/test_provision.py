"""Tests for disposable Pages site provisioning (non-destructive)."""

from __future__ import annotations

from termivance.provision import SITE_MARKER, site_files


def test_site_files_include_ci_and_marker():
    files = site_files()
    assert ".gitlab-ci.yml" in files
    assert "site/index.html" in files
    assert "site/marker.txt" in files
    assert SITE_MARKER in files["site/index.html"]
    assert SITE_MARKER in files["site/marker.txt"]


def test_ci_uses_arbitrary_job_name_with_pages_true():
    ci = site_files()[".gitlab-ci.yml"]
    # The publishing job must not be named "pages"; participation is via pages: true.
    assert "pages: true" in ci
    assert "\npages:\n" not in ci


def test_unique_marker_is_stable_and_distinctive():
    assert SITE_MARKER.startswith("TERMIVANCE-B3-DISPOSABLE")
    assert SITE_MARKER == site_files()["site/marker.txt"].strip()
