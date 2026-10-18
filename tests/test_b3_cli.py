"""B3 CLI surface tests that never touch the network."""

from __future__ import annotations

import json

from conftest import make_snapshot

from termivance.cli import build_parser, main
from termivance.discovery import save_snapshot

B3_POLICY = "config/retirement_policy.b3_disposable.json"
EXAMPLE_AUTH = "config/authorization.example.json"


def test_retire_pages_parser_accepts_repair_flags():
    args = build_parser().parse_args(
        [
            "retire-pages",
            "--project-id",
            "87785099",
            "--url",
            "https://example.gitlab.io/demo/",
            "--marker",
            "MARKER",
            "--policy",
            B3_POLICY,
            "--authorization",
            EXAMPLE_AUTH,
            "--control-attestation",
            "control.json",
            "--ledger",
            "ledger.json",
            "--from-record",
            "snapshot.json",
        ]
    )
    assert args.control_attestation == "control.json"
    assert args.ledger == "ledger.json"
    assert args.marker == "MARKER"


def test_observe_absence_parser_requires_pre_state_flag():
    args = build_parser().parse_args(
        ["observe-absence", "--project-id", "87785099", "--url", "https://x/"]
    )
    assert args.pre_state is None
    assert args.action_accepted is False


def test_verify_publication_parser_has_marker():
    args = build_parser().parse_args(
        ["verify-publication", "--project-id", "87785099", "--url", "https://x/", "--marker", "M"]
    )
    assert args.marker == "M"


def test_retire_pages_from_record_with_example_authorization_is_blocked(tmp_path, capsys):
    from termivance.target import TargetIdentity

    target = TargetIdentity(
        87785099,
        "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
        "GITLAB_PAGES_SITE",
    )
    snapshot = make_snapshot(target, operator_control=True)
    path = tmp_path / "snap.json"
    save_snapshot(snapshot, path)
    rc = main(
        [
            "retire-pages",
            "--project-id",
            "87785099",
            "--from-record",
            str(path),
            "--policy",
            B3_POLICY,
            "--authorization",
            EXAMPLE_AUTH,
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert payload["mutation_attempted"] is False
    assert payload["verdict"] == "BLOCKED"
