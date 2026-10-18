import json

from conftest import make_snapshot

from termivance.cli import main
from termivance.discovery import save_snapshot
from termivance.graph import EvidenceClass


def test_status_json_reports_local_snapshot(capsys):
    assert main(["status", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["source"] == "local_snapshot_not_live"
    assert "B3_UNPUBLISH_NOT_RUN" in payload["retirement"]


def test_demo_blocked_from_record(tmp_path, capsys, canonical_target):
    snapshot = make_snapshot(canonical_target, classification=EvidenceClass.FIXTURE)
    path = tmp_path / "snap.json"
    save_snapshot(snapshot, path)
    rc = main(["demo-blocked", "--from-record", str(path), "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["verdict"] == "BLOCKED"
    assert out["read_only"] is True
    assert out["scenario"] == "canonical_project_as_protected_negative_control"
    assert out["evidence_classification"] == "FIXTURE"


def test_demo_blocked_human_output(tmp_path, capsys, canonical_target):
    snapshot = make_snapshot(canonical_target, classification=EvidenceClass.FIXTURE)
    path = tmp_path / "snap.json"
    save_snapshot(snapshot, path)
    assert main(["demo-blocked", "--from-record", str(path)]) == 0
    text = capsys.readouterr().out
    assert "Verdict: `BLOCKED`" in text
    assert "Destructive API operations performed: **0**" in text


def test_evaluate_from_record(tmp_path, capsys, pages_target):
    snapshot = make_snapshot(pages_target, classification=EvidenceClass.FIXTURE)
    path = tmp_path / "s.json"
    save_snapshot(snapshot, path)
    assert main(["evaluate", "--from-record", str(path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] in {"BLOCKED", "INCONCLUSIVE", "SAFE_TO_RETIRE"}
    assert payload["read_only"] is True
