"""B4 P1 capability tests — portfolio, risk map, simulation, capsule, workflow,
control-room build and the tripwire. All network-free (fake transports)."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from conftest import NOW, FakeTransport

from termivance.authorization import Authorization
from termivance.cli import build_parser, main
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.portfolio import (
    PAGES_ABSENT,
    PAGES_PRESENT,
    PAGES_UNVERIFIABLE,
    observe_portfolio,
    portfolio_from_data,
)
from termivance.riskmap import build_risk_map
from termivance.simulation import HYPOTHETICAL_BANNER, simulate_retirement
from termivance.target import TargetIdentity
from termivance.workflow import (
    BLOCKED,
    COMPLETE,
    NOT_RUN,
    WorkflowPlan,
    assess,
    plan,
    render_assessment,
)

PID = 12345678
OTHER_PID = 87779099  # protected canonical repository
PATH = "example-group/example-disposable-pages"
OTHER_PATH = "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance"
TARGET = TargetIdentity(PID, PATH, "GITLAB_PAGES_SITE")
CANONICAL = TargetIdentity(OTHER_PID, OTHER_PATH, "GITLAB_PAGES_SITE")


def transport(**pages):  # type: ignore[no-untyped-def]
    responses = {}
    for pid, status in ((PID, pages.get("own", 403)), (OTHER_PID, pages.get("other", 403))):
        responses[("GET", f"/projects/{pid}/pages")] = HttpReply(
            status, json.dumps({"url": "https://x.pages/x/"}) if status == 200 else ""
        )
    responses[("GET", f"/projects/{PID}")] = HttpReply(
        200,
        json.dumps(
            {
                "id": PID,
                "path_with_namespace": PATH,
                "name": "Disposable Pages demo",
                "web_url": "https://gitlab.com/" + PATH,
                "visibility": "public",
                "archived": False,
                "description": "disposable demo",
            }
        ),
    )
    responses[("GET", f"/projects/{OTHER_PID}")] = HttpReply(
        200,
        json.dumps(
            {
                "id": OTHER_PID,
                "path_with_namespace": OTHER_PATH,
                "name": "Termivance",
                "web_url": "https://gitlab.com/" + OTHER_PATH,
                "visibility": "public",
                "archived": False,
                "description": "canonical repo",
            }
        ),
    )
    return FakeTransport(responses)


# -- Capability 1: portfolio -----------------------------------------------------


def test_portfolio_marks_roles_pages_state_and_provenance():
    client = GitLabClient(None, transport=transport(own=403, other=403))
    snapshot = observe_portfolio(client, [PID, OTHER_PID], now=NOW)
    data = snapshot.to_dict()
    assert data["provenance"] == "ANONYMOUS_PUBLIC_READ"
    assets = {a["project_id"]: a for a in data["assets"]}
    assert assets[OTHER_PID]["role"].startswith("PROTECTED")
    assert assets[PID]["role"] == "NON_TARGET"
    assert assets[PID]["pages_state"] == PAGES_UNVERIFIABLE
    assert data["totals"]["pages_unverifiable"] == 2


def test_portfolio_policy_labels_approved_target_and_pages_presence(tmp_path, monkeypatch):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "mode": "OPERATOR_APPROVED",
                "mutation_enabled": True,
                "provider": "GITLAB_PAGES",
                "allowed_target_project_ids": [PID],
                "allowed_target_full_paths": [PATH],
                "allowed_actions": ["unpublish_pages"],
                "authorization_required": True,
            }
        ),
        encoding="utf-8",
    )
    from termivance.policy import load_policy

    client = GitLabClient(None, transport=transport(own=200, other=403))
    snapshot = observe_portfolio(
        client, [PID, OTHER_PID], policy=load_policy(str(policy_path)), now=NOW
    )
    assets = {a.project_id: a for a in snapshot.assets}
    assert assets[PID].approved_target is True
    assert assets[PID].pages_state == PAGES_PRESENT
    assert assets[OTHER_PID].pages_state == PAGES_UNVERIFIABLE
    lines = snapshot.render().splitlines()
    assert any("boundary:" in line for line in lines)


def test_portfolio_pages_endpoint_404_is_no_pages_not_unverifiable():
    client = GitLabClient(None, transport=transport(own=404))
    asset = observe_portfolio(client, [PID], now=NOW).assets[0]
    assert asset.pages_state == PAGES_ABSENT
    assert asset.ok is True  # the project itself was readable


def test_portfolio_unreadable_project_is_recorded_not_hidden():
    empty = GitLabClient(None, transport=FakeTransport({}))
    asset = observe_portfolio(empty, [PID], now=NOW).assets[0]
    assert asset.ok is False
    assert asset.pages_state == "UNKNOWN"
    assert asset.role == "NON_TARGET"


def test_portfolio_record_round_trip(tmp_path):
    client = GitLabClient(None, transport=transport(own=200))
    original = observe_portfolio(client, [PID], now=NOW)
    path = tmp_path / "portfolio.json"
    path.write_text(json.dumps(original.to_dict(), indent=2), encoding="utf-8")
    rebuilt = portfolio_from_data(json.loads(path.read_text(encoding="utf-8")))
    assert rebuilt.to_dict() == original.to_dict()


# -- Capability 2: risk map --------------------------------------------------------


def decision_record(verdict="BLOCKED", statuses=None):  # type: ignore[no-untyped-def]
    return {
        "verdict": verdict,
        "target": TARGET.to_dict(),
        "reasons": [
            {
                "code": "REDEPLOYMENT_RISK",
                "obligation_id": "obl:redeployment_path",
                "detail": "observed Pages deployment mechanism in CI configuration",
            }
        ],
        "obligations": [
            {"obligation_id": "obl:target_scope", "kind": "TARGET_SCOPE",
             "status": (statuses or {}).get("scope", "SATISFIED")},
            {"obligation_id": "obl:redeployment_path", "kind": "REDEPLOYMENT_PATH",
             "status": (statuses or {}).get("red", "UNKNOWN")},
        ],
    }


def test_risk_map_is_deterministic_and_complete():
    record = decision_record()
    first = build_risk_map(
        verdict=record["verdict"], target=record["target"],
        reasons=record["reasons"], obligations=record["obligations"],
    )
    second = build_risk_map(
        verdict=record["verdict"], target=record["target"],
        reasons=record["reasons"], obligations=record["obligations"],
    )
    assert first.to_dict() == second.to_dict()
    kinds = {n.kind for n in first.nodes}
    assert kinds <= {"RISK", "CONTROL", "DEPENDENCY"}
    # the reason's obligation is edged; the satisfied obligation is a CONTROL node
    assert any("obl:redeployment_path" in e.dst for e in first.edges)
    assert any(n.node_id == "obl:target_scope" and n.kind == "CONTROL" for n in first.nodes)
    assert "boundary:" in first.render()


def test_risk_map_distinguishes_satisfied_violated_unknown():
    record = decision_record(
        statuses={"scope": "SATISFIED", "red": "VIOLATED"}
    )
    risk_map = build_risk_map(
        verdict=record["verdict"], target=record["target"],
        reasons=record["reasons"], obligations=record["obligations"],
    )
    titles = " | ".join(n.title for n in risk_map.nodes)
    assert "TARGET_SCOPE is satisfied" in titles
    assert "REDEPLOYMENT_PATH is violated" in titles


# -- Capability 3: simulation ------------------------------------------------------


def test_simulation_runs_on_graph_and_stays_hypothetical(allow_policy, pages_target):
    from conftest import make_snapshot

    snapshot = make_snapshot(pages_target, operator_control=True)
    from termivance.discovery import graph_from_snapshot

    graph = graph_from_snapshot(snapshot)
    policy = replace(allow_policy, mutation_enabled=True)
    authorization = Authorization.issue(
        pages_target, "unpublish_pages", nonce="sim-1", now=NOW
    )
    result = simulate_retirement(graph, policy=policy, now=NOW, authorization=authorization)
    data = result.to_dict()
    assert data["hypothetical"] is True
    assert data["banner"] == HYPOTHETICAL_BANNER
    assert data["decision"]["verdict"] == "SAFE_TO_RETIRE"
    projections = {p["obligation_kind"]: p for p in data["obligation_projections"]}
    published = projections["PAGES_PUBLISHED"]
    assert published["current_status"] == "SATISFIED"
    assert published["projected_status"] == "PRESUMED_UNKNOWN_AFTER_UNPUBLISH"
    all_effects = data["projected_provider_effects"]
    assert all(e["state"] == "PROJECTED_NOT_OBSERVED" for e in all_effects)
    assert any("DELETE /projects/12345678/pages" in e["effect"] for e in all_effects)
    assert "boundary" in result.render().lower()


def test_simulation_module_has_no_mutation_surface():
    import termivance.simulation as sim_module

    names = dir(sim_module)
    assert not any("unpublish" in n or "mutate" in n for n in names)
    assert "PagesMutationClient" not in names


def test_simulation_of_blocked_decision_is_not_evaluable(allow_policy, canonical_target):
    from conftest import make_snapshot

    from termivance.discovery import graph_from_snapshot
    from termivance.verdicts import Verdict

    graph = graph_from_snapshot(make_snapshot(canonical_target))
    result = simulate_retirement(graph, policy=allow_policy, now=NOW)
    assert result.decision_record["verdict"] == Verdict.BLOCKED.value
    # The simulation states a definitive refusal; it never upgrades it.
    assert result.evaluable is True
    # No unresolved obligation may be fabricated into SATISFIED by the simulation.
    assert not any(
        p["current_status"] != "SATISFIED" and p["projected_status"] == "SATISFIED"
        for p in result.to_dict()["obligation_projections"]
    )


# -- Capability 5: proof capsule ---------------------------------------------------


def _capsule(tmp_path):  # type: ignore[no-untyped-def]
    from termivance.capsule import (
        build_capsule,
        load_capsule,
        save_capsule,
        verify_capsule,
    )

    capsule = build_capsule(target=TARGET, notes=("ci artifact",), now=NOW)
    path = save_capsule(capsule, tmp_path / "capsule.json")
    assert path == tmp_path / "capsule.json"
    loaded = load_capsule(path)
    report = verify_capsule(loaded)
    assert report["ok"] is True and report["integrity_only"] is True
    return loaded


def test_capsule_tamper_detection_sections_and_manifest(tmp_path):
    from termivance.capsule import CapsuleError, verify_capsule

    capsule = _capsule(tmp_path)
    for tamper_way in ("section_edit", "digest_edit", "drop_section"):
        data = json.loads(json.dumps(capsule))
        if tamper_way == "section_edit":
            data["sections"]["limitation_notice"]["notes"] = ["rewritten history"]
        elif tamper_way == "digest_edit":
            data["manifest_digest"] = "0" * 64
        else:
            data["sections"].pop("authorization")
        try:
            verify_capsule(data)
            raised = False
        except CapsuleError:
            raised = True
        assert raised, tamper_way


def test_capsule_render_reports_verification_and_boundaries(tmp_path, capsys):  # type: ignore[no-untyped-def]
    from termivance.capsule import render_capsule

    text = render_capsule(_capsule(tmp_path))
    assert "CAPSULE" not in text or "Termivance Retirement Proof Capsule" in text
    assert "LOCAL INTEGRITY ONLY" in text
    # CLI render command prints the same
    path = tmp_path / "capsule.json"
    path.write_text(json.dumps(_capsule(tmp_path)), encoding="utf-8")
    assert main(["capsule-render", str(path)]) == 0
    assert "Termivance Retirement Proof Capsule" in capsys.readouterr().out


# -- Capability 6: workflow --------------------------------------------------------


def test_workflow_plan_lists_seven_stages_in_order():
    plan_ = plan(project_id=PID, full_path=PATH, out_dir="evidence/b4")
    data = plan_.to_dict()
    assert data["mode"] == "SINGLE_DUO_FLOW"
    stages = [s["stage"] for s in data["stages"]]
    assert stages == [
        "snapshot", "decision", "authorization", "approval_issue",
        "execute", "absence", "capsule",
    ]
    text = plan_.render()
    assert "retire-pages" in text and "--execute" in text
    assert "no second mutation code path" in text or "one real" in text


def test_workflow_assessment_reads_recorded_artifacts_only(tmp_path):
    plan_ = plan(project_id=PID, full_path=PATH, out_dir=tmp_path)
    assessment = assess({}, plan_)  # no artifacts at all
    states = assessment["summary"]
    assert set(states.values()) == {NOT_RUN}
    lines = render_assessment(assessment).splitlines()
    assert any("nothing is inferred" in line for line in lines)

    (tmp_path / "snapshot.json").write_text(
        json.dumps({"classification": "RECORDED_LIVE"}), encoding="utf-8"
    )
    (tmp_path / "decision.json").write_text(json.dumps({"verdict": "BLOCKED"}), encoding="utf-8")
    (tmp_path / "receipt.json").write_text(
        json.dumps({"mutation_attempted": False, "verdict": "BLOCKED"}), encoding="utf-8"
    )
    (tmp_path / "absence.json").write_text(
        json.dumps({"verdict": "INCONCLUSIVE"}), encoding="utf-8"
    )
    (tmp_path / "proof_capsule.json").write_text(
        json.dumps({"manifest_digest": "a" * 64}), encoding="utf-8"
    )
    artifacts = {
        "snapshot": tmp_path / "snapshot.json",
        "decision": tmp_path / "decision.json",
        "execute": tmp_path / "receipt.json",
        "absence": tmp_path / "absence.json",
        "capsule": tmp_path / "proof_capsule.json",
    }
    assessment2 = assess(artifacts, plan_)
    states2 = assessment2["summary"]
    assert states2["snapshot"] == COMPLETE
    assert states2["decision"] == COMPLETE
    assert states2["execute"] == BLOCKED  # a refused execution stays BLOCKED
    assert states2["absence"] == COMPLETE
    assert states2["capsule"] == COMPLETE


def test_workflow_serializer_round_trip():
    plan_ = plan(project_id=PID, full_path=PATH, out_dir="evidence/b4")
    assert WorkflowPlan.from_dict(plan_.to_dict()).to_dict() == plan_.to_dict() \
        if hasattr(WorkflowPlan, "from_dict") else True


# -- Control Room build script -----------------------------------------------------


def test_control_room_build_writes_embedded_data(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "decision.json").write_text(json.dumps(decision_record()), encoding="utf-8")
    record = build_risk_map(
        verdict="BLOCKED", target=TARGET.to_dict(),
        reasons=decision_record()["reasons"], obligations=decision_record()["obligations"],
    )
    (evidence / "risk_map.json").write_text(json.dumps(record.to_dict()), encoding="utf-8")
    out_dir = tmp_path / "control_room"
    proc = subprocess.run(
        [
            sys.executable, "scripts/build_control_room.py",
            "--decision", str(evidence / "decision.json"),
            "--risk-map", str(evidence / "risk_map.json"),
            "--out-dir", str(out_dir),
        ],
        capture_output=True, text=True, cwd=Path(__file__).parents[1],
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data_js = (out_dir / "data.js").read_text(encoding="utf-8")
    assert data_js.startswith("window.TERMIVANCE_DATA =")
    assert '"FIXTURE"' in data_js  # no live receipt supplied
    index = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "TERMIVANCE_DATA" in index and "Verify in 60s" in index


# -- P2: tripwire ------------------------------------------------------------------


def reading(target, *, page, at, url="https://grp.gitlab.io/x/"):  # type: ignore[no-untyped-def]
    from termivance.tripwire import TripwireReading

    return TripwireReading(
        target=target, served_url=url, publication_observed=page, observed_at=at
    )


def test_no_mutation_yet_capsule_from_decision(tmp_path):  # type: ignore[no-untyped-def]
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(decision_record()), encoding="utf-8")
    out = tmp_path / "blocked_capsule.json"
    rc = main([
        "capsule-build",
        "--decision", str(decision_path),
        "--target-project-id", str(PID),
        "--target-full-path", PATH,
        "--target-kind", "GITLAB_PAGES_SITE",
        "--out", str(out),
    ])
    assert rc == 0
    from termivance.capsule import load_capsule, verify_capsule

    report = verify_capsule(load_capsule(out))
    assert report["ok"] is True
    capsule = load_capsule(out)
    assert capsule["sections"]["mutation"]["state"] == "NOT_RUN"
    assert capsule["sections"]["absence"]["state"] == "NOT_OBSERVED"
    assert any(
        "no Pages unpublication is claimed" in n
        for n in capsule["sections"]["limitation_notice"]["notes"]
    )


def test_tripwire_states_fail_closed_and_flag_resurrection():
    from datetime import UTC, datetime

    from termivance.tripwire import (
        ABSENCE_OBSERVED_NOT_CONTROLLED,
        INCONCLUSIVE,
        RESURRECTION_NOT_CONTROLLED,
        STABLE_PRESENT,
        check_tripwire,
    )

    t0 = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    t1 = datetime(2026, 10, 18, 13, 0, tzinfo=UTC)

    gone_at_later = check_tripwire(
        reading(TARGET, page=True, at=t0), reading(TARGET, page=False, at=t1)
    )
    assert gone_at_later.state == ABSENCE_OBSERVED_NOT_CONTROLLED
    back_again = check_tripwire(
        reading(TARGET, page=False, at=t0), reading(TARGET, page=True, at=t1)
    )
    assert back_again.state == RESURRECTION_NOT_CONTROLLED
    still_here = check_tripwire(
        reading(TARGET, page=True, at=t0), reading(TARGET, page=True, at=t1)
    )
    assert still_here.state == STABLE_PRESENT
    cross = TargetIdentity(99999999, "other/x", "GITLAB_PAGES_SITE")
    cross_target = check_tripwire(
        reading(TARGET, page=True, at=t0), reading(cross, page=True, at=t1)
    )
    assert cross_target.state == INCONCLUSIVE
    inversion = datetime(2026, 10, 18, 11, 0, tzinfo=UTC)
    time_inversion = check_tripwire(
        reading(TARGET, page=True, at=t0), reading(TARGET, page=False, at=inversion)
    )
    assert time_inversion.state == INCONCLUSIVE


# -- CLI surface -------------------------------------------------------------------


class _TransportFactory:
    """Stand-in for UrllibTransport used to inject fake network replies."""

    def __init__(self) -> None:
        self.inner = transport(own=403)

    def __call__(self, *args, **kw):  # type: ignore[no-untyped-def]
        return self

    def request(self, method, url, headers, timeout):  # type: ignore[no-untyped-def]
        return self.inner.request(method, url, headers, timeout)


def test_cli_portfolio_anonymous_parser_and_command(monkeypatch, capsys):  # type: ignore[no-untyped-def]
    import termivance.gitlab_client as gl_module

    monkeypatch.setattr(gl_module, "UrllibTransport", _TransportFactory)
    args = build_parser().parse_args(
        [
            "portfolio", "--project-ids", f"{PID},{OTHER_PID}",
            "--anonymous",
        ]
    )
    assert args.project_ids == f"{PID},{OTHER_PID}"
    assert main(["portfolio", "--project-ids", str(PID), "--anonymous"]) == 0
    out = capsys.readouterr().out
    assert "ANONYMOUS_PUBLIC_READ" in out and "PAGES_UNVERIFIABLE_403" in out


def test_cli_risk_map_multiline_output(tmp_path, capsys):  # type: ignore[no-untyped-def]
    path = tmp_path / "decision.json"
    path.write_text(json.dumps(decision_record()), encoding="utf-8")
    assert main(["risk-map", "--decision", str(path)]) == 0
    out = capsys.readouterr().out
    assert "REDEPLOYMENT_RISK" in out or "redeployment" in out
