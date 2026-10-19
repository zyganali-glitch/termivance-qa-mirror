"""B4 enhancement acceptance tests — evidence-bound Duo reconciliation and the
resurrection counterexample witness. All network-free (fake transports)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from conftest import NOW, FakeTransport

from termivance.capsule import CapsuleError, build_capsule, verify_capsule
from termivance.cli import main
from termivance.duo_reconciliation import (
    DUO_CLAIMS_SCHEMA,
    ClaimStatus,
    DuoClaim,
    DuoSurfaceObservation,
    ReconciliationError,
    load_claims,
    reconcile_duo,
    reconciliation_from_data,
)
from termivance.gitlab_client import ApiResult, GitLabClient, HttpReply
from termivance.target import TargetIdentity
from termivance.witness import (
    ABSENCE_CLAIM_NEVER,
    RESURRECTION_CONTROLLED_NOT_CLAIMED,
    ResurrectionPossibility,
    build_witness,
)

ROOT = Path(__file__).parents[1]
PID = 87785099
CANONICAL = 87779099
PATH = "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"


# -- Duo reconciliation --------------------------------------------------------


def _surface(**overrides) -> DuoSurfaceObservation:
    base: dict = {
        "observed_at": NOW,
        "project_id": CANONICAL,
        "issue_iid": 3,
        "session_url": "https://gitlab.com/x/-/automate/agent-sessions/9671626",
        "project_read_status": 200,
        "issue_read_status": 200,
        "issue_metadata": {
            "state": "opened",
            "labels": ["retirement-decision", "termivance::b3"],
            "user_notes_count": 3,
            "updated_at": "2026-10-19T08:57:41.500Z",
            "author": {"username": "zyganali", "id": 39306908},
        },
        "notes_read_status": 401,
        "discussions_read_status": 401,
        "session_ui_status": 404,
    }
    base.update(overrides)
    return DuoSurfaceObservation(**base)


def _claims() -> tuple[dict, tuple[DuoClaim, ...]]:
    claims = (
        DuoClaim("c1", "project readable", "ANONYMOUS_API_OBSERVATION", "PROJECT_READ", {}),
        DuoClaim(
            "c2",
            "issue opened by zyganali",
            "ANONYMOUS_API_OBSERVATION",
            "ISSUE_METADATA",
            {"fields": {"state": "opened", "author": {"username": "zyganali"}}},
        ),
        DuoClaim(
            "c3",
            "consistent with the comment window",
            "ANONYMOUS_API_OBSERVATION",
            "CONSISTENCY_INFERENCE",
            {"fields": {"user_notes_count": 3}},
        ),
        DuoClaim("c4", "session Finished", "OPERATOR_CONFIRMED_UI", "SESSION_UI_PROBE", {}),
        DuoClaim(
            "c5",
            "note attributed to the service account",
            "OPERATOR_CONFIRMED_NOTE_CONTENT",
            "ISSUE_NOTE_READ",
            {"note_id": 4040776241},
        ),
        DuoClaim("c6", "flow internals", "OPERATOR_CONFIRMED_UI", "FLOW_INTERNALS", {}),
        DuoClaim(
            "c7",
            "notes 401 to anonymous",
            "ANONYMOUS_API_OBSERVATION",
            "OBSERVABILITY_PROBE",
            {"surface": "notes", "status": 401},
        ),
        DuoClaim(
            "c8",
            "session UI 404 to anonymous",
            "ANONYMOUS_API_OBSERVATION",
            "OBSERVABILITY_PROBE",
            {"surface": "session_ui", "status": 404},
        ),
    )
    return {"schema": DUO_CLAIMS_SCHEMA, "duo_session_id": "9671626"}, claims


def _reconcile(surface: DuoSurfaceObservation, *, now: datetime | None = None):
    data, claims = _claims()
    return reconcile_duo(data, claims, surface, claims_source="test", now=now or NOW)


def test_reconciliation_assigns_fail_closed_statuses():
    result = _reconcile(_surface())
    by_id = {r.claim_id: r for r in result.results}
    assert by_id["c1"].status == ClaimStatus.SUPPORTED
    assert by_id["c2"].status == ClaimStatus.SUPPORTED
    # "consistent with, but not proof" is never promoted to SUPPORTED.
    assert by_id["c3"].status == ClaimStatus.UNRESOLVED
    # an authenticated-only surface can never be verified anonymously.
    assert by_id["c4"].status == ClaimStatus.UNRESOLVED
    # a 401 note read is an access observation: not absence, not attribution.
    assert by_id["c5"].status == ClaimStatus.NOT_AUTHENTICALLY_ATTRIBUTABLE
    assert by_id["c6"].status == ClaimStatus.UNSUPPORTED
    assert by_id["c7"].status == ClaimStatus.SUPPORTED
    assert by_id["c8"].status == ClaimStatus.SUPPORTED
    payload = result.to_dict()
    assert payload["authority"] == "NON_AUTHORITATIVE"
    assert payload["totals"]["SUPPORTED"] == 4
    assert payload["totals"]["NOT_AUTHENTICALLY_ATTRIBUTABLE"] == 1
    assert payload["totals"]["UNSUPPORTED"] == 1
    # The reconciler can never award an authoritative verdict.
    forbidden = {"SAFE_TO_RETIRE", "RETIRED", "OBSERVED_ABSENT", "RESURRECTION_CONTROLLED"}
    assert not ({r.status for r in result.results} & forbidden)


def test_issue_metadata_conflict_is_contradicted_not_silently_matched():
    result = _reconcile(_surface(issue_metadata={"state": "closed"}))
    by_id = {r.claim_id: r for r in result.results}
    assert by_id["c2"].status == ClaimStatus.CONTRADICTED
    assert "conflicts" in by_id["c2"].detail
    # the consistency claim's observable core conflicts too.
    assert by_id["c3"].status == ClaimStatus.CONTRADICTED


def test_unreadable_issue_leaves_metadata_claims_unresolved():
    result = _reconcile(_surface(issue_read_status=403, issue_metadata={}))
    by_id = {r.claim_id: r for r in result.results}
    assert by_id["c2"].status == ClaimStatus.UNRESOLVED
    assert by_id["c3"].status == ClaimStatus.UNRESOLVED


def test_anonymous_project_read_failure_is_unresolved_never_absence():
    result = _reconcile(_surface(project_read_status=403))
    by_id = {r.claim_id: r for r in result.results}
    assert by_id["c1"].status == ClaimStatus.UNRESOLVED
    assert "access observation" in by_id["c1"].detail


def test_stale_surface_demotes_supported_and_contradicted_to_stale():
    result = _reconcile(_surface(), now=NOW + timedelta(hours=2))
    by_id = {r.claim_id: r for r in result.results}
    assert by_id["c1"].status == ClaimStatus.STALE
    assert "provisional finding was SUPPORTED" in by_id["c1"].detail
    # attribution impossibility is not a factual conclusion; it stays explicit.
    assert by_id["c5"].status == ClaimStatus.NOT_AUTHENTICALLY_ATTRIBUTABLE


def test_observability_boundary_change_contradicts_the_probe_claim():
    result = _reconcile(_surface(notes_read_status=200))
    by_id = {r.claim_id: r for r in result.results}
    assert by_id["c7"].status == ClaimStatus.CONTRADICTED
    assert "HTTP 200" in by_id["c7"].detail


def test_readable_note_stays_unresolved_and_never_attributes_authorship():
    result = _reconcile(_surface(notes_read_status=200))
    by_id = {r.claim_id: r for r in result.results}
    assert by_id["c5"].status == ClaimStatus.UNRESOLVED
    assert "never awarded" in by_id["c5"].detail


def test_reconciliation_round_trip():
    original = _reconcile(_surface())
    rebuilt = reconciliation_from_data(original.to_dict())
    assert rebuilt.to_dict() == original.to_dict()


def test_load_claims_refuses_duplicates_and_unknown_kinds(tmp_path):
    duplicate = {
        "schema": DUO_CLAIMS_SCHEMA,
        "claims": [
            {
                "claim_id": "x",
                "text": "a",
                "origin": "OPERATOR_CONFIRMED_UI",
                "check_kind": "FLOW_INTERNALS",
            },
            {
                "claim_id": "x",
                "text": "b",
                "origin": "OPERATOR_CONFIRMED_UI",
                "check_kind": "FLOW_INTERNALS",
            },
        ],
    }
    path = tmp_path / "claims.json"
    path.write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(ReconciliationError, match="ambiguous"):
        load_claims(path)
    unknown = {
        "schema": DUO_CLAIMS_SCHEMA,
        "claims": [
            {"claim_id": "x", "text": "a", "origin": "OPERATOR_CONFIRMED_UI", "check_kind": "MAGIC"}
        ],
    }
    path.write_text(json.dumps(unknown), encoding="utf-8")
    with pytest.raises(ReconciliationError, match="unknown check kind"):
        load_claims(path)
    wrong = {"schema": "termivance.other/v1", "claims": []}
    path.write_text(json.dumps(wrong), encoding="utf-8")
    with pytest.raises(ReconciliationError, match="unsupported claims schema"):
        load_claims(path)


def test_shipped_claims_record_loads_and_reconciles_live_surface():
    path = ROOT / "evidence" / "b4" / "duo_claims.json"
    data, claims = load_claims(path)
    assert data["duo_session_id"] == "9671626"
    assert len(claims) == 9
    result = reconcile_duo(data, claims, _surface(), claims_source=str(path), now=NOW)
    statuses = {r.status for r in result.results}
    assert ClaimStatus.SUPPORTED in statuses
    assert ClaimStatus.NOT_AUTHENTICALLY_ATTRIBUTABLE in statuses
    assert "SAFE_TO_RETIRE" not in json.dumps(result.to_dict())


class _FakeClient:
    """Stand-in anonymous client: only the endpoints the reconciliation reads."""

    def __init__(self, token, **kwargs):  # type: ignore[no-untyped-def]
        assert token is None  # reconciliation is anonymous by construction

    def get_json(self, endpoint, params=None):  # type: ignore[no-untyped-def]
        if "/notes" in endpoint:
            return ApiResult(False, 401, None, endpoint, "GET", "AUTH_DENIED")
        if "/discussions" in endpoint:
            return ApiResult(False, 401, None, endpoint, "GET", "AUTH_DENIED")
        if endpoint.endswith("/issues/3"):
            return ApiResult(
                True,
                200,
                {"state": "opened", "author": {"username": "zyganali"}},
                endpoint,
                "GET",
            )
        return ApiResult(True, 200, {"id": CANONICAL}, endpoint, "GET")


def test_cli_reconcile_duo_writes_record(tmp_path, monkeypatch):
    monkeypatch.setattr("termivance.gitlab_client.GitLabClient", _FakeClient)
    monkeypatch.setattr("termivance.duo_reconciliation.probe_web_status", lambda url, **kw: 404)
    out = tmp_path / "duo_reconciliation.json"
    rc = main(
        [
            "reconcile-duo",
            "--claims",
            str(ROOT / "evidence" / "b4" / "duo_claims.json"),
            "--project-id",
            str(CANONICAL),
            "--issue-iid",
            "3",
            "--session-url",
            "https://gitlab.com/x/-/automate/agent-sessions/9671626",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "termivance.duo_reconciliation/v1"
    assert payload["authority"] == "NON_AUTHORITATIVE"
    assert payload["totals"]["SUPPORTED"] >= 3


# -- Resurrection counterexample witness ---------------------------------------

WITNESS_CONFIG_WITH_SIGNAL = "stages:\n  - deploy\npages:\n  script:\n    - echo hi\n"
WITNESS_CONFIG_CLEAN = "stages:\n  - test\n"
WITNESS_CONFIG_INCLUDE = "include:\n  - local: /other.yml\nstages:\n  - test\n"
SHA = "b" * 40


def _witness_transport(
    pid: int = PID,
    *,
    config: str = WITNESS_CONFIG_WITH_SIGNAL,
    config_status: int = 200,
    pages_status: int = 403,
    branch: str | None = "main",
    sha: str | None = SHA,
):  # type: ignore[no-untyped-def]
    responses = {}
    if branch:
        responses[("GET", f"/projects/{pid}/repository/commits")] = HttpReply(
            200, json.dumps([{"id": sha or SHA}])
        )
    responses[("GET", f"/projects/{pid}/repository/files/")] = HttpReply(
        config_status, config if config_status == 200 else ""
    )
    responses[("GET", f"/projects/{pid}/pages")] = HttpReply(
        pages_status, json.dumps({"url": "https://x.example/"}) if pages_status == 200 else ""
    )
    responses[("GET", f"/projects/{pid}")] = HttpReply(
        200,
        json.dumps(
            {
                "id": pid,
                "path_with_namespace": PATH,
                "default_branch": branch,
            }
        ),
    )
    return FakeTransport(responses)


def _target() -> TargetIdentity:
    return TargetIdentity(PID, PATH, "GITLAB_PAGES_SITE")


def test_witness_reads_target_own_config_at_exact_commit():
    client = GitLabClient(None, transport=_witness_transport())
    witness = build_witness(client, _target(), now=NOW)
    payload = witness.to_dict()
    assert payload["config"]["ref"] == SHA  # exact observed commit, not the branch
    assert f"ref={SHA}" in payload["config"]["endpoint"]
    assert payload["config"]["signals"] == ["pages_job_key"]
    assert (
        payload["resurrection_possible"]
        == ResurrectionPossibility.MECHANISM_PRESENT_IN_OBSERVED_CONFIG.value
    )
    assert payload["absence_claim"] == ABSENCE_CLAIM_NEVER
    assert payload["resurrection_controlled"] == RESURRECTION_CONTROLLED_NOT_CLAIMED
    assert payload["target"]["project_id"] == PID
    joined = " ".join(payload["counterexamples"])
    assert SHA in joined and "pages_job_key" in joined
    without_boundary = {k: v for k, v in payload.items() if k != "boundary"}
    assert "RESURRECTION_CONTROLLED" not in json.dumps(without_boundary)


def test_witness_pages_403_phrase_never_claims_absence():
    client = GitLabClient(None, transport=_witness_transport(pages_status=403))
    witness = build_witness(client, _target(), now=NOW)
    phrase = witness.to_dict()["pages_administration"]["phrase"]
    assert "cannot verify this Pages administration surface" in phrase
    assert "site may be present or absent" in phrase


def test_witness_no_signal_in_complete_config_still_witnesses_counterexamples():
    client = GitLabClient(None, transport=_witness_transport(config=WITNESS_CONFIG_CLEAN))
    witness = build_witness(client, _target(), now=NOW)
    payload = witness.to_dict()
    assert (
        payload["resurrection_possible"]
        == ResurrectionPossibility.NO_MECHANISM_IN_OBSERVED_CONFIG.value
    )
    assert payload["config"]["configuration_complete"] is True
    joined = " ".join(payload["counterexamples"])
    assert "pages-administration action" in joined
    assert "not verifiable" in joined


def test_witness_included_config_cannot_prove_completeness():
    client = GitLabClient(None, transport=_witness_transport(config=WITNESS_CONFIG_INCLUDE))
    witness = build_witness(client, _target(), now=NOW)
    payload = witness.to_dict()
    assert (
        payload["resurrection_possible"]
        == ResurrectionPossibility.MECHANISM_NOT_FOUND_CONFIG_INCOMPLETE.value
    )
    joined = " ".join(payload["counterexamples"])
    assert "include:" in joined


def test_witness_unreadable_config_is_unknown_never_safe():
    client = GitLabClient(None, transport=_witness_transport(config_status=403))
    witness = build_witness(client, _target(), now=NOW)
    payload = witness.to_dict()
    assert payload["resurrection_possible"] == ResurrectionPossibility.CONFIG_NOT_OBSERVED.value
    joined = " ".join(payload["counterexamples"])
    assert "cannot be excluded" in joined


def test_witness_pages_404_is_access_observation_not_absence():
    client = GitLabClient(None, transport=_witness_transport(pages_status=404))
    witness = build_witness(client, _target(), now=NOW)
    phrase = witness.to_dict()["pages_administration"]["phrase"]
    assert "access observation, never absence" in phrase


# -- Capsule embedding ---------------------------------------------------------


def _witness_record(project_id: int) -> dict:
    client = GitLabClient(None, transport=_witness_transport(pid=project_id))
    target = TargetIdentity(project_id, PATH, "GITLAB_PAGES_SITE")
    return build_witness(client, target, now=NOW).to_dict()


def test_capsule_embeds_reconciliation_and_witness():
    data, claims = _claims()
    reconciliation = reconcile_duo(
        data, claims, _surface(), claims_source="test", now=NOW
    ).to_dict()
    witness = _witness_record(PID)
    capsule = build_capsule(
        target=_target(),
        decision={"verdict": "BLOCKED"},
        duo_reconciliation=reconciliation,
        witness=witness,
        now=NOW,
    )
    report = verify_capsule(capsule)
    assert "duo_reconciliation" in report["sections_verified"]
    assert "witness" in report["sections_verified"]
    assert capsule["sections"]["duo_reconciliation"]["state"] == "RECONCILED"
    assert capsule["sections"]["witness"]["state"] == "RECORDED"
    assert capsule["sections"]["duo_reconciliation"]["authority"] == "NON_AUTHORITATIVE"


def test_capsule_refuses_a_witness_for_a_different_target():
    witness = _witness_record(CANONICAL)  # witness for the canonical repo
    capsule = build_capsule(
        target=_target(),  # capsule for the disposable target
        decision={"verdict": "BLOCKED"},
        witness=witness,
        now=NOW,
    )
    with pytest.raises(CapsuleError, match="different target"):
        verify_capsule(capsule)


def test_cli_capsule_build_refuses_cross_target_witness(tmp_path):
    witness_path = tmp_path / "witness_other.json"
    witness_path.write_text(json.dumps(_witness_record(CANONICAL)), encoding="utf-8")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps({"verdict": "BLOCKED"}), encoding="utf-8")
    rc = main(
        [
            "capsule-build",
            "--decision",
            str(decision_path),
            "--target-project-id",
            str(PID),
            "--target-full-path",
            PATH,
            "--witness",
            str(witness_path),
            "--out",
            str(tmp_path / "capsule.json"),
        ]
    )
    assert rc == 2


def test_cli_capsule_build_embeds_matching_records(tmp_path):
    witness_path = tmp_path / "witness.json"
    witness_path.write_text(json.dumps(_witness_record(PID)), encoding="utf-8")
    data, claims = _claims()
    reconciliation = reconcile_duo(
        data, claims, _surface(), claims_source="test", now=NOW
    ).to_dict()
    reconciliation_path = tmp_path / "duo_reconciliation.json"
    reconciliation_path.write_text(json.dumps(reconciliation), encoding="utf-8")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps({"verdict": "BLOCKED"}), encoding="utf-8")
    out = tmp_path / "capsule.json"
    rc = main(
        [
            "capsule-build",
            "--decision",
            str(decision_path),
            "--target-project-id",
            str(PID),
            "--target-full-path",
            PATH,
            "--duo-reconciliation",
            str(reconciliation_path),
            "--witness",
            str(witness_path),
            "--out",
            str(out),
            "--json",
        ]
    )
    assert rc == 0
    capsule = json.loads(out.read_text(encoding="utf-8"))
    assert verify_capsule(capsule)["ok"] is True


# -- Control room rendering ----------------------------------------------------


def test_control_room_embeds_reconciliation_and_witness(tmp_path):
    import subprocess
    import sys

    data, claims = _claims()
    reconciliation = reconcile_duo(
        data, claims, _surface(), claims_source="test", now=NOW
    ).to_dict()
    reconciliation_path = tmp_path / "duo_reconciliation.json"
    reconciliation_path.write_text(json.dumps(reconciliation), encoding="utf-8")
    witness_path = tmp_path / "witness.json"
    witness_path.write_text(json.dumps(_witness_record(PID)), encoding="utf-8")
    out_dir = tmp_path / "control_room"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/build_control_room.py",
            "--duo-reconciliation",
            str(reconciliation_path),
            "--witness",
            str(witness_path),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data_js = (out_dir / "data.js").read_text(encoding="utf-8")
    payload = json.loads(data_js.removeprefix("window.TERMIVANCE_DATA = ").removesuffix(";\n"))
    assert payload["sections"]["duo_reconciliation"]["schema"] == (
        "termivance.duo_reconciliation/v1"
    )
    assert payload["sections"]["witness"]["schema"] == "termivance.resurrection_witness/v1"
    index = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "duoReconciliationCard" in index and "witnessCard" in index
