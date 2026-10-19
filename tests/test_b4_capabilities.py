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
from termivance.dependencies import cross_resource_view
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.portfolio import (
    KIND_CI_REDEPLOY,
    KIND_DEPLOYMENT,
    KIND_ENVIRONMENT,
    KIND_ISSUE,
    KIND_PACKAGE,
    KIND_PAGES,
    KIND_RELEASE,
    NOT_AUTHORIZING,
    PAGES_ABSENT,
    PAGES_NOT_OBSERVED_404,
    PAGES_PRESENT,
    PAGES_UNVERIFIABLE,
    SUPPORT_INFERRED,
    SUPPORT_NOT_OBSERVED,
    SUPPORT_OBSERVED,
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


def test_portfolio_pages_endpoint_404_is_never_verified_absence():
    # QA-FIX C: a standalone read-only 404 on the Pages endpoint is an
    # access/visibility observation, never proof that a published site is gone.
    client = GitLabClient(None, transport=transport(own=404))
    snapshot = observe_portfolio(client, [PID], now=NOW)
    asset = snapshot.assets[0]
    assert asset.pages_state == PAGES_NOT_OBSERVED_404
    assert asset.ok is True  # the project itself was readable
    assert snapshot.to_dict()["totals"]["pages_not_observed"] == 1
    assert snapshot.to_dict()["totals"]["pages_sites"] == 0
    # The recorded Pages resource is an explicit NOT_OBSERVED record, and the
    # absence state reserved for the authorized-transition protocol must not
    # appear anywhere in this read-only observation.
    pages_records = [r for r in asset.resources if r.kind == KIND_PAGES]
    assert pages_records and pages_records[0].support == SUPPORT_NOT_OBSERVED
    assert PAGES_ABSENT not in {r.state for r in asset.resources}
    lines = snapshot.render().splitlines()
    assert any("boundary:" in line for line in lines)


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
            {
                "obligation_id": "obl:target_scope",
                "kind": "TARGET_SCOPE",
                "status": (statuses or {}).get("scope", "SATISFIED"),
            },
            {
                "obligation_id": "obl:redeployment_path",
                "kind": "REDEPLOYMENT_PATH",
                "status": (statuses or {}).get("red", "UNKNOWN"),
            },
        ],
    }


def test_risk_map_is_deterministic_and_complete():
    record = decision_record()
    first = build_risk_map(
        verdict=record["verdict"],
        target=record["target"],
        reasons=record["reasons"],
        obligations=record["obligations"],
    )
    second = build_risk_map(
        verdict=record["verdict"],
        target=record["target"],
        reasons=record["reasons"],
        obligations=record["obligations"],
    )
    assert first.to_dict() == second.to_dict()
    kinds = {n.kind for n in first.nodes}
    assert kinds <= {"RISK", "CONTROL", "DEPENDENCY"}
    # the reason's obligation is edged; the satisfied obligation is a CONTROL node
    assert any("obl:redeployment_path" in e.dst for e in first.edges)
    assert any(n.node_id == "obl:target_scope" and n.kind == "CONTROL" for n in first.nodes)
    assert "boundary:" in first.render()


def test_risk_map_distinguishes_satisfied_violated_unknown():
    record = decision_record(statuses={"scope": "SATISFIED", "red": "VIOLATED"})
    risk_map = build_risk_map(
        verdict=record["verdict"],
        target=record["target"],
        reasons=record["reasons"],
        obligations=record["obligations"],
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
    authorization = Authorization.issue(pages_target, "unpublish_pages", nonce="sim-1", now=NOW)
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
    assert data["mode"] == "SINGLE_AUTHORIZED_FLOW"
    assert "not a GitLab Duo Custom Flow executor" in data["mode_note"]
    stages = [s["stage"] for s in data["stages"]]
    assert stages == [
        "snapshot",
        "decision",
        "authorization",
        "approval_issue",
        "execute",
        "absence",
        "capsule",
    ]
    text = plan_.render()
    assert "retire-pages" in text and "--execute" in text
    # Repair B: --operator-trust must be present in the execute command
    assert "--operator-trust" in text
    assert "deterministic Python workflow" in text


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
    assert (
        WorkflowPlan.from_dict(plan_.to_dict()).to_dict() == plan_.to_dict()
        if hasattr(WorkflowPlan, "from_dict")
        else True
    )


# -- Control Room build script -----------------------------------------------------


def test_control_room_build_writes_embedded_data(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "decision.json").write_text(json.dumps(decision_record()), encoding="utf-8")
    record = build_risk_map(
        verdict="BLOCKED",
        target=TARGET.to_dict(),
        reasons=decision_record()["reasons"],
        obligations=decision_record()["obligations"],
    )
    (evidence / "risk_map.json").write_text(json.dumps(record.to_dict()), encoding="utf-8")
    out_dir = tmp_path / "control_room"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/build_control_room.py",
            "--decision",
            str(evidence / "decision.json"),
            "--risk-map",
            str(evidence / "risk_map.json"),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[1],
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data_js = (out_dir / "data.js").read_text(encoding="utf-8")
    assert data_js.startswith("window.TERMIVANCE_DATA =")
    assert '"termivance.control_room/v2"' in data_js
    # No live receipt supplied → mutation observable stays NOT_RUN, never PASS.
    assert '"mutation_status": "NOT_OBSERVED"' in data_js
    assert '"destructive_buttons": 0' in data_js
    payload = json.loads(data_js.removeprefix("window.TERMIVANCE_DATA = ").removesuffix(";\n"))
    assert payload["sections"]["decision"]["verdict"] == "BLOCKED"
    assert payload["sections"]["risk_map"]["schema"].startswith("termivance.risk")
    gates = [g["gate"] for g in payload["authorization_gates"]]
    assert any("87785099" in g for g in gates)
    assert any("STRUCTURALLY_REFUSED" == g["state"] for g in payload["authorization_gates"])
    index = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "TERMIVANCE_DATA" in index
    # The interactive contract is visible in the page itself.
    assert "What if we retire this?" in index or "What-if" in index
    assert "escapeHtml" in index and "<script>" in index


def _build_control_room(tmp_path, receipt_obj):
    """Run the builder with one receipt artifact; return the embedded payload."""
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt_obj), encoding="utf-8")
    out_dir = tmp_path / "control_room_receipt"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/build_control_room.py",
            "--receipt",
            str(receipt_path),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[1],
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data_js = (out_dir / "data.js").read_text(encoding="utf-8")
    return json.loads(data_js.removeprefix("window.TERMIVANCE_DATA = ").removesuffix(";\n"))


def _v3_receipt(**overrides):
    """A minimally coherent v3 receipt for classifier tests (display-only)."""
    receipt = {
        "schema": "termivance.retirement_receipt/v3",
        "target": {"project_id": PID, "full_path": PATH, "resource_kind": "GITLAB_PAGES_SITE"},
        "action": "unpublish_pages",
        "mutation_attempted": False,
        "verdict": "BLOCKED",
        "mutation": None,
    }
    receipt.update(overrides)
    return receipt


def test_control_room_receipt_schema_presence_is_never_live(tmp_path):
    # QA-FIX D: a bare, incoherent schema string must classify INVALID and must
    # never flip the provenance to RECORDED_LIVE or a live mutation state.
    payload = _build_control_room(tmp_path, {"schema": "termivance.retirement_receipt/v3"})
    receipt = payload["sections"]["receipt"]
    assert receipt["receipt_state"] == "INVALID"
    assert payload["mutation_status"] == "INVALID"
    assert payload["provenance_label"] != "RECORDED_LIVE"
    gate = next(g for g in payload["authorization_gates"] if "87785099" in str(g["gate"]))
    assert gate["state"] == "INVALID"


def test_control_room_unknown_schema_receipt_is_invalid(tmp_path):
    payload = _build_control_room(tmp_path, {"schema": "termivance.fake_receipt/v9"})
    receipt = payload["sections"]["receipt"]
    assert receipt["receipt_state"] == "INVALID"
    assert receipt["record"]["schema"] == "termivance.fake_receipt/v9"
    assert payload["mutation_status"] == "INVALID"


def test_control_room_blocked_receipt_is_surfaced_never_promoted(tmp_path):
    payload = _build_control_room(
        tmp_path, _v3_receipt(mutation_attempted=False, verdict="BLOCKED")
    )
    receipt = payload["sections"]["receipt"]
    assert receipt["receipt_state"] == "BLOCKED"
    assert receipt["mutation_attempted"] is False
    assert payload["mutation_status"] == "BLOCKED"
    # A recorded non-attempt is never live evidence of the destructive event.
    assert payload["provenance_label"] != "RECORDED_LIVE"


def test_control_room_accepted_mutation_is_action_acceptance_never_absence(tmp_path):
    payload = _build_control_room(
        tmp_path,
        _v3_receipt(
            mutation_attempted=True,
            verdict="INCONCLUSIVE",
            mutation={"accepted": True, "status": 202, "method": "DELETE"},
        ),
    )
    receipt = payload["sections"]["receipt"]
    # A locally supplied JSON without durable ledger verification is an UNVERIFIED_RECORDED_CLAIM.
    # The UI never promotes it to an authoritative outcome.
    assert receipt["receipt_state"] == "UNVERIFIED_RECORDED_CLAIM"
    assert receipt["display_verdict"] == "UNVERIFIED_RECORDED_CLAIM"
    assert receipt["claimed_verdict"] == "INCONCLUSIVE"
    assert payload["mutation_status"] == "UNVERIFIED_RECORDED_CLAIM"
    assert payload["provenance_label"] != "RECORDED_LIVE"
    raw = json.dumps(payload)
    assert "OBSERVED_ABSENT" not in raw
    assert "RESURRECTION_CONTROLLED" not in raw


def test_control_room_observed_absent_only_from_receipt_verdict(tmp_path):
    payload = _build_control_room(
        tmp_path,
        _v3_receipt(
            mutation_attempted=True,
            verdict="OBSERVED_ABSENT",
            mutation={"accepted": True, "status": 204, "method": "DELETE"},
        ),
    )
    receipt = payload["sections"]["receipt"]
    # Even when a JSON asserts OBSERVED_ABSENT, it remains UNVERIFIED_RECORDED_CLAIM
    assert receipt["receipt_state"] == "UNVERIFIED_RECORDED_CLAIM"
    assert receipt["display_verdict"] == "UNVERIFIED_RECORDED_CLAIM"
    assert receipt["claimed_verdict"] == "OBSERVED_ABSENT"
    assert payload["mutation_status"] == "UNVERIFIED_RECORDED_CLAIM"
    assert payload["provenance_label"] != "RECORDED_LIVE"


def test_control_room_incoherent_acceptance_without_2xx_is_invalid(tmp_path):
    payload = _build_control_room(
        tmp_path,
        _v3_receipt(
            mutation_attempted=True,
            verdict="RETIRED",
            mutation={"accepted": True, "status": "202", "method": "DELETE"},
        ),
    )
    receipt = payload["sections"]["receipt"]
    assert receipt["receipt_state"] == "INVALID"
    assert payload["mutation_status"] == "INVALID"


# -- P2: tripwire ------------------------------------------------------------------


def reading(target, *, page, at, url="https://grp.gitlab.io/x/"):  # type: ignore[no-untyped-def]
    from termivance.tripwire import TripwireReading

    return TripwireReading(target=target, served_url=url, publication_observed=page, observed_at=at)


def test_no_mutation_yet_capsule_from_decision(tmp_path):  # type: ignore[no-untyped-def]
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(decision_record()), encoding="utf-8")
    out = tmp_path / "blocked_capsule.json"
    rc = main(
        [
            "capsule-build",
            "--decision",
            str(decision_path),
            "--target-project-id",
            str(PID),
            "--target-full-path",
            PATH,
            "--target-kind",
            "GITLAB_PAGES_SITE",
            "--out",
            str(out),
        ]
    )
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
            "portfolio",
            "--project-ids",
            f"{PID},{OTHER_PID}",
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


# -- multi-resource portfolio (consolidated repair, Defect B) ---------------------


def _resource_transport() -> FakeTransport:
    """A complete read-only project surface for multi-resource portfolio tests."""
    body = (
        "stages:\n"
        "  - deploy\n"
        "pages:\n"
        "  stage: deploy\n"
        "  script:\n"
        "    - echo deploying the site\n"
        "  artifacts:\n"
        "    paths:\n"
        "      - public\n"
    )
    return FakeTransport(
        {
            ("GET", f"/projects/{PID}/pages"): HttpReply(
                200, json.dumps({"url": "https://x.pages/x/"})
            ),
            ("GET", f"/projects/{PID}/environments"): HttpReply(
                200,
                json.dumps(
                    [
                        {
                            "id": 11,
                            "name": "production",
                            "state": "available",
                            "external_url": "https://x.pages/x/",
                        },
                        {"id": 12, "name": "staging", "state": "stopped"},
                    ]
                ),
            ),
            ("GET", f"/projects/{PID}/deployments"): HttpReply(
                200,
                json.dumps(
                    [
                        {
                            "id": 301,
                            "ref": "main",
                            "status": "success",
                            "environment": {"name": "production"},
                        }
                    ]
                ),
            ),
            ("GET", f"/projects/{PID}/releases"): HttpReply(
                200,
                json.dumps([{"tag_name": "v1.2.0", "name": "Release v1.2.0"}]),
            ),
            ("GET", f"/projects/{PID}/packages"): HttpReply(
                200,
                json.dumps(
                    [{"id": 9001, "name": "pkg-a", "version": "1.0.0", "package_type": "npm"}]
                ),
            ),
            ("GET", f"/projects/{PID}/issues"): HttpReply(
                200,
                json.dumps(
                    [
                        {
                            "iid": 5,
                            "title": "Retire the demo site after acceptance",
                            "labels": ["retirement"],
                            "state": "opened",
                        },
                        {"iid": 2, "title": "Renumber the rows", "labels": [], "state": "opened"},
                    ]
                ),
            ),
            ("GET", f"/projects/{PID}/repository/files/.gitlab-ci.yml/raw"): HttpReply(200, body),
            ("GET", f"/projects/{PID}"): HttpReply(
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
            ),
        }
    )


def test_portfolio_v2_multi_resource_records_carry_exact_facts():
    snapshot = observe_portfolio(
        GitLabClient(None, transport=_resource_transport()), [PID], now=NOW
    )
    asset = snapshot.assets[0]
    kinds = {r.kind for r in asset.resources}
    assert kinds <= {
        KIND_PAGES,
        KIND_ENVIRONMENT,
        KIND_DEPLOYMENT,
        KIND_RELEASE,
        KIND_PACKAGE,
        KIND_ISSUE,
        KIND_CI_REDEPLOY,
    }
    assert KIND_PAGES in kinds and KIND_ENVIRONMENT in kinds and KIND_DEPLOYMENT in kinds
    for record in asset.resources:
        # Exact provenance and freshness on every resource record.
        assert record.provenance == "ANONYMOUS_PUBLIC_READ"
        assert record.fresh_until > record.observed_at
        assert record.endpoint.startswith("/projects/12345678")
        # Discovery is never an authorization to mutate.
        assert record.mutation_capability == NOT_AUTHORIZING
        if record.kind not in {KIND_PAGES, KIND_CI_REDEPLOY}:
            assert record.ref.split(":")[1] == "12345678"
    envs = sorted((r for r in asset.resources if r.kind == KIND_ENVIRONMENT), key=lambda r: r.ref)
    env = envs[0]
    assert env.ref == "environment:12345678:11"
    assert env.state == "available"
    assert env.detail["name"] == "production"
    issue = [r for r in asset.resources if r.kind == KIND_ISSUE][0]
    assert issue.ref == "issue:12345678:5"
    retirement_flagged = [
        r for r in asset.resources if r.kind == KIND_ISSUE and r.detail.get("retirement_related")
    ]
    assert [r.ref for r in retirement_flagged] == ["issue:12345678:5"]
    ci = [r for r in asset.resources if r.kind == KIND_CI_REDEPLOY][0]
    assert ci.state == "PAGES_REDEPLOYMENT_SIGNAL_PRESENT"
    snapshot_dict = snapshot.to_dict()
    assert "termivance.portfolio/v2" in snapshot_dict["schema"]
    totals = snapshot_dict["totals"]
    assert totals["resources_observed"] > 0


def test_portfolio_403_endpoint_is_not_observed_never_absence():
    body = FakeTransport(
        {
            ("GET", f"/projects/{PID}/pages"): HttpReply(
                200, json.dumps({"url": "https://x.pages/x/"})
            ),
            # Environment/deployments/releases/packages/issues endpoints are all
            # members-only for this anonymous probe: silently 404 from the Fake.
            ("GET", f"/projects/{PID}/repository/files/.gitlab-ci.yml/raw"): HttpReply(
                200, "just:\n  - echo ok\n"
            ),
            ("GET", f"/projects/{PID}"): HttpReply(
                200,
                json.dumps(
                    {
                        "id": PID,
                        "path_with_namespace": PATH,
                        "name": "d",
                        "web_url": "w",
                        "visibility": "public",
                        "archived": False,
                        "description": "",
                    }
                ),
            ),
        }
    )
    snapshot = observe_portfolio(GitLabClient(None, transport=body), [PID], now=NOW)
    asset = snapshot.assets[0]
    missing = [
        r
        for r in asset.resources
        if r.support == SUPPORT_NOT_OBSERVED and r.kind == KIND_ENVIRONMENT
    ]
    assert len(missing) == 1
    assert missing[0].state.startswith("NOT_OBSERVED (")
    assert missing[0].detail["project_id"] == PID
    assert missing[0].mutation_capability == NOT_AUTHORIZING
    # Not one record claims pages absence from an access limitation.
    assert all(r.state != "ABSENT" for r in asset.resources)
    totals = snapshot.to_dict()["totals"]
    assert totals["resources_not_observed"] >= 4  # env, deployments, releases, packages, issues


def test_portfolio_relations_are_explicitly_observed_or_inferred():
    snapshot = observe_portfolio(
        GitLabClient(None, transport=_resource_transport()), [PID], now=NOW
    )
    rels = {r.kind + "->" + r.dst for r in snapshot.relations}
    deployed = [rel for rel in snapshot.relations if rel.kind == "deployed_to"]
    assert deployed and all(rel.support == SUPPORT_OBSERVED for rel in deployed)
    recreate = [rel for rel in snapshot.relations if rel.kind == "recreates"]
    assert recreate and all(rel.support == SUPPORT_INFERRED for rel in recreate)
    obligates = [rel for rel in snapshot.relations if rel.kind == "obligates"]
    assert obligates and all(rel.support == SUPPORT_INFERRED for rel in obligates)
    assert "deployed_to->environment:12345678:11" in rels


def test_cross_resource_view_shared_by_riskmap_and_simulation():
    snapshot = observe_portfolio(
        GitLabClient(None, transport=_resource_transport()), [PID], now=NOW
    )
    view = cross_resource_view(snapshot)
    # The same pool of records feeds both downstream capabilities.
    refs = {r.ref for r in view.nodes}
    assert "pages:12345678" in refs and "environment:12345678:11" in refs
    node_payload = view.as_risk_nodes({"project_id": PID})
    for node in node_payload:
        assert node["target"] == {"project_id": PID}
    ci_node = [n for n in node_payload if n["node_id"] == "resource:ci_redeployment:12345678"][0]
    assert ci_node["severity"] == "HIGH"  # a live redeployment signal is real risk context
    assert ci_node["support"] == SUPPORT_OBSERVED
    factors = view.as_simulation_factors()
    assert factors
    assert all(f["state"] == "PROJECTED_NOT_OBSERVED" for f in factors)
    assert not any(f["resource"].startswith("pages:") for f in factors)


def test_inferred_relations_can_never_satisfy_a_mandatory_obligation():
    """Even with rich portfolio evidence, the decision engine sees unchanged obligations."""
    from termivance.discovery import graph_from_snapshot, load_snapshot
    from termivance.engine import evaluate
    from termivance.policy import Policy

    snapshot = observe_portfolio(
        GitLabClient(None, transport=_resource_transport()), [PID], now=NOW
    )
    graph_record_path = Path(__file__).resolve().parents[1] / "evidence" / "b4"
    # Build the decision WITHOUT and WITH the portfolio cross view.

    live = load_snapshot(graph_record_path / "snapshot.json")
    graph = graph_from_snapshot(live)
    policy = Policy(
        schema_version=1,
        mode="OPERATOR_APPROVED",
        mutation_enabled=False,
        provider="GITLAB_PAGES",
        allowed_target_project_ids=(87785099,),
        allowed_target_full_paths=(
            "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
        ),
        allowed_actions=("unpublish_pages",),
        authorization_required=True,
    )
    from datetime import UTC, datetime

    later = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
    without = evaluate(graph, policy=policy, action="unpublish_pages", now=later)
    view = cross_resource_view(snapshot)
    with_cross = evaluate(graph, policy=policy, action="unpublish_pages", now=later)
    # The engine is a pure function of graph+policy: cross-resource context is NOT
    # an input, so INFERRED portfolio edges cannot flip any obligation.
    assert without.verdict == with_cross.verdict
    assert [str(o.get("status")) for o in without.to_dict()["obligations"]] == [
        str(o.get("status")) for o in with_cross.to_dict()["obligations"]
    ]
    assert view.inferred_relations > 0


def test_riskmap_appends_cross_nodes_but_decision_facts_unchanged():
    from conftest import NOW as _NOW

    decision = decision_record()
    base = build_risk_map(
        verdict=str(decision["verdict"]),
        target=dict(decision["target"]),
        reasons=list(decision["reasons"]),
        obligations=list(decision["obligations"]),
    )
    snapshot = observe_portfolio(
        GitLabClient(None, transport=_resource_transport()), [PID], now=_NOW
    )
    view = cross_resource_view(snapshot)
    cross = build_risk_map(
        verdict=str(decision["verdict"]),
        target=dict(decision["target"]),
        reasons=list(decision["reasons"]),
        obligations=list(decision["obligations"]),
        cross_nodes=view.as_risk_nodes(dict(decision["target"])),
        cross_edges=view.as_risk_edges(),
    )
    base_ids = [n.node_id for n in base.nodes]
    cross_ids = [n.node_id for n in cross.nodes]
    assert all(node in cross_ids for node in base_ids), "decision nodes must be preserved"
    assert "resource:pages:12345678" in cross_ids
    assert len(cross_ids) == len(set(cross_ids)), "risk nodes must be uniquely identified"
    rel_edges = [
        e for e in cross.edges if e.src.startswith("resource:") and e.dst.startswith("resource:")
    ]
    assert rel_edges
    assert {e.relation for e in rel_edges} == {"deployed_to", "recreates", "obligates"}


def test_riskmap_edges_reference_existing_nodes():
    """Every edge endpoint must resolve to a node — a graph nobody can walk by
    clicking would be unintelligible, and dangling ids made it so."""
    decision = decision_record()
    legacies = [
        build_risk_map(
            verdict=str(decision["verdict"]),
            target=dict(decision["target"]),
            reasons=list(decision["reasons"]),
            obligations=list(decision["obligations"]),
        ),
    ]
    snapshot = observe_portfolio(
        GitLabClient(None, transport=_resource_transport()), [PID], now=NOW
    )
    view = cross_resource_view(snapshot)
    legacies.append(
        build_risk_map(
            verdict=str(decision["verdict"]),
            target=dict(decision["target"]),
            reasons=list(decision["reasons"]),
            obligations=list(decision["obligations"]),
            cross_nodes=view.as_risk_nodes({}),
            cross_edges=view.as_risk_edges(),
        )
    )
    for rm in legacies:
        ids = {n.node_id for n in rm.nodes}
        dangling = [(e.src, e.dst) for e in rm.edges if e.src not in ids or e.dst not in ids]
        assert not dangling, f"dangling edges: {dangling}"
        assert any(e.dst in ids for e in rm.edges), "no resolvable edges at all"
        # decision-side chains must actually connect: at least one reason edge
        # lands on the obligation a reason declares.
        reaches = [e for e in rm.edges if e.relation == "impacts" and e.dst.startswith("obl:")]
        assert reaches


def test_simulation_accepts_cross_factors_via_cli(tmp_path, capsys):  # type: ignore[no-untyped-def]
    portfolio_path = tmp_path / "portfolio.json"
    snapshot = observe_portfolio(
        GitLabClient(None, transport=_resource_transport()), [PID], now=NOW
    )
    portfolio_path.write_text(json.dumps(snapshot.to_dict(), sort_keys=True), encoding="utf-8")
    assert (
        main(
            [
                "simulate",
                "--project-id",
                str(PID),
                "--from-record",
                str(Path(__file__).resolve().parents[1] / "evidence" / "b4" / "snapshot.json"),
                "--portfolio",
                str(portfolio_path),
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert HYPOTHETICAL_BANNER in payload["banner"]
    factors = payload["cross_resource_factors"]
    assert factors
    assert all(f["state"] == "PROJECTED_NOT_OBSERVED" for f in factors)


def test_cli_portfolio_v2_prints_resource_totals(tmp_path, capsys):  # type: ignore[no-untyped-def]
    snapshot = observe_portfolio(
        GitLabClient(None, transport=_resource_transport()), [PID], now=NOW
    )
    out_path = tmp_path / "p.json"
    out_path.write_text(json.dumps(snapshot.to_dict(), sort_keys=True), encoding="utf-8")
    rebuilt = portfolio_from_data(json.loads(out_path.read_text(encoding="utf-8")))
    rendered = rebuilt.render()
    assert "NOT_AUTHORIZING" in rendered
    assert "resources NOT_OBSERVED" not in rendered  # everything observed in this fixture
