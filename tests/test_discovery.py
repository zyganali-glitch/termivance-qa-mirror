from datetime import UTC, datetime, timedelta

from conftest import FakeTransport

from termivance.discovery import (
    detect_pages_mechanism,
    discover_live,
    graph_from_snapshot,
    is_retirement_related,
)
from termivance.gitlab_client import GitLabClient, HttpReply, RecordingTransport
from termivance.graph import EvidenceKind
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)

TARGET = TargetIdentity(1, "group/proj", "GITLAB_PAGES_SITE")


def responses(*, ci_body="stages: [verify]\nverify:\n  script: [true]\n", issues=None, pages=None):
    if pages is None:
        pages = HttpReply(403, "", "HTTP 403")
    return {
        ("GET", "/repository/branches/"): HttpReply(200, '{"name":"main","commit":{"id":"abc"}}'),
        ("GET", "/repository/files/.gitlab-ci.yml/raw"): HttpReply(200, ci_body),
        ("GET", "/issues"): HttpReply(200, issues if issues is not None else "[]"),
        ("GET", "/pages"): pages,
        ("GET", "/environments"): HttpReply(200, "[]"),
        ("GET", "/pipelines"): HttpReply(200, '[{"id": 7, "status": "success"}]'),
        ("GET", "/projects/1"): HttpReply(
            200,
            '{"id": 1, "path_with_namespace": "group/proj", "visibility": "public", '
            '"default_branch": "main", "namespace": {"full_path": "group"}}',
        ),
    }


def run_live(responses_map):
    recorder = RecordingTransport(inner=FakeTransport(responses_map))
    client = GitLabClient("t", transport=recorder)
    return discover_live(client, TARGET, now=NOW), recorder


def test_discovery_only_uses_get():
    snapshot, recorder = run_live(responses())
    assert snapshot.record(EvidenceKind.PROJECT_IDENTITY) is not None
    assert recorder.methods_used() == {"GET"}


def test_discovery_records_identity_and_no_pages_mechanism():
    snapshot, _ = run_live(responses())
    ci = snapshot.record(EvidenceKind.CI_CONFIG)
    assert ci is not None and ci.detail["pages_mechanism"] is False
    assert ci.detail["includes_present"] is False
    graph = graph_from_snapshot(snapshot)
    deps = {d.dependency_id: d for d in graph.dependencies.values()}
    assert deps["dep:active_redeployment"].active is False


def test_detect_pages_signal_agnostic_of_job_name():
    ci = "deploy_site:\n  script: [echo hi]\n  pages: true\n"
    detected, signals = detect_pages_mechanism(ci)
    assert detected is True and signals


def test_detect_top_level_pages_job():
    detected, _ = detect_pages_mechanism("pages:\n  script: [echo]\n")
    assert detected is True


def test_detect_nested_pages_keyword():
    ci = "deploy:\n  pages:\n    publish: dist\n  script: [echo]\n"
    detected, _ = detect_pages_mechanism(ci)
    assert detected is True


def test_detect_pages_stage():
    detected, _ = detect_pages_mechanism("site:\n  stage: pages\n  script: [echo]\n")
    assert detected is True


def test_plain_config_has_no_pages_signal():
    detected, signals = detect_pages_mechanism("stages: [verify]\nverify:\n  script: [true]\n")
    assert detected is False and signals == []


def test_arbitrary_pages_job_becomes_active_redeployment():
    ci = "publish_docs:\n  script: [echo]\n  pages: true\n"
    snapshot, _ = run_live(responses(ci_body=ci))
    graph = graph_from_snapshot(snapshot)
    deps = {d.dependency_id: d for d in graph.dependencies.values()}
    assert deps["dep:active_redeployment"].active is True


def test_include_is_flagged_as_incomplete():
    ci = "include:\n  - project: a/b\n    file: ci.yml\n"
    snapshot, _ = run_live(responses(ci_body=ci))
    ci_ev = snapshot.record(EvidenceKind.CI_CONFIG)
    assert ci_ev is not None and ci_ev.detail["includes_present"] is True


def test_discovery_detects_open_retirement_issue():
    issues = '[{"iid": 1, "title": "Please retire this site", "labels": ["retirement"]}]'
    snapshot, _ = run_live(responses(issues=issues))
    graph = graph_from_snapshot(snapshot)
    deps = {d.dependency_id: d for d in graph.dependencies.values()}
    assert deps["dep:open_work_item"].active is True


def test_generic_issue_is_not_a_retirement_obligation():
    assert is_retirement_related({"title": "fix a normal bug", "labels": ["bug"]}) is False
    assert is_retirement_related({"title": "cleanup", "labels": ["decommission"]}) is True
    assert is_retirement_related({"title": "Retire the demo Pages site"}) is True


def test_pages_403_is_recorded_not_fabricated():
    snapshot, _ = run_live(responses(pages=HttpReply(403, "", "HTTP 403")))
    pages = snapshot.record(EvidenceKind.PAGES)
    assert pages is not None and pages.error_kind == "AUTH_DENIED" and pages.status == 403


def test_snapshot_roundtrip_downgrades_live_to_recorded():
    from termivance.discovery import Snapshot

    snapshot, _ = run_live(responses())
    assert snapshot.classification.value == "LIVE"
    restored = Snapshot.from_dict(snapshot.to_dict())
    assert restored.classification.value == "RECORDED_LIVE"


def test_saved_snapshot_is_recorded_not_live(tmp_path):
    from termivance.discovery import Snapshot, load_snapshot, save_snapshot

    snapshot, _ = run_live(responses())
    path = save_snapshot(snapshot, tmp_path / "rec.json")
    restored = load_snapshot(path)
    assert restored.classification.value == "RECORDED_LIVE"
    assert Snapshot.from_dict(restored.to_dict()).classification.value == "RECORDED_LIVE"


def test_fresh_until_is_within_ttl():
    snapshot, _ = run_live(responses())
    for record in snapshot.records:
        assert record.fresh_until - record.observed_at == timedelta(seconds=900)
