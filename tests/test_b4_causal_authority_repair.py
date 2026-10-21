"""B4 final causal-authority and proof-boundary closure repair tests.

Adversarial regressions for the five residual material integrity defects
identified by the independent source audit of canonical commit ``c8dbcc8``:

1. OFFLINE_REPLAY must never publish provider evidence (Defect 1):
   a command combining offline replay with ``--publish`` is rejected at the
   CLI boundary with a nonzero exit code and an explicit
   ``OFFLINE_PUBLICATION_REFUSED`` reason; the same prohibition is enforced
   inside ``run_supervised_continuation`` (not only argparse); a supplied
   publisher can never cause a mutation in offline mode. An actually
   injected publisher raises immediately if its write method is called and
   zero calls are asserted, both through direct Python invocation and real
   CLI dispatch.

2. The preflight-verified note must be the note executed (Defect 2):
   the exact provider-returned note body, note ID, author identity, target
   identity and provenance captured by the LIVE preflight are carried
   unchanged into the deterministic investigation; downstream candidate
   parsing is bound to those exact bytes and their digest; the validated
   note is never silently replaced by a second provider read or a local
   recorded fallback during LIVE continuation; a provider read failure is
   never rescued by a fixture. All tests exercise the real production
   function call chain (``validate_continuation_preflight`` →
   ``run_supervised_continuation`` → ``run_supervised_investigation``)
   through injected transports, never mocks that bypass the handoff.

3. The durable ledger must verify its execution owner (Defect 3):
   ``finalize()`` verifies the exact reserved execution identity before any
   state transition; a competing or stale execution cannot finalize another
   invocation's reservation; recovery transfers ownership to the verified
   recovering invocation; a duplicate complete record is never overwritten
   or recast; the durable recorded result and digest are verified after
   finalization.

4. Historical absence cannot override missing current observations
   (Defect 4): a verified historical receipt requires a nonempty exact
   current served URL matching the authenticated historical URL; the
   current CI configuration must be positively observed before claiming the
   redeployment mechanism absent; current-observation freshness is
   validated independently of the historical receipt's timestamp.

All tests are network-free.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime

import pytest
from conftest import FakeTransport, ScriptedTransport

from termivance.continuation_ledger import (
    COMPLETED_STATE,
    RESERVE_FIRST_EXECUTION,
    RESERVED_STATE,
    ContinuationLedger,
    ContinuationLedgerError,
)
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.resurrection_monitor import (
    CurrentTruthStatus,
    RedeploymentRisk,
    TargetCurrentObservation,
    monitor_resurrection,
)
from termivance.supervised_review import (
    DEFAULT_TARGET_FULL_PATH,
    DEFAULT_TARGET_PROJECT_ID,
    DUO_SERVICE_ACCOUNT_USERNAME,
    DUO_SESSION_ID_NEUTRAL,
    run_supervised_continuation,
    run_supervised_investigation,
    validate_continuation_preflight,
)
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 21, 12, 0, 0, tzinfo=UTC)
AUTHENTIC_COMMIT_SHA = "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
CANONICAL_PID = 87779099
NOTE_ID = 4045401991
AUTHENTIC_NOTE_BODY = (
    "### 1. Target Identity & Observed Scope\n"
    "- **Target project ID:** `87785099`\n"
    f"- **Default branch HEAD commit:** `{AUTHENTIC_COMMIT_SHA}`\n\n"
    "### 3. Candidate obligations\n"
    "1. **CI Redeployment Path**: create-pages in .gitlab-ci.yml with pages: true\n"
    "2. **Target Marker String**: TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a in site/index.html\n"
)
CHANGED_NOTE_BODY = (
    "### 1. Target Identity & Observed Scope\n"
    "- **Target project ID:** `87785099`\n"
    f"- **Default branch HEAD commit:** `{AUTHENTIC_COMMIT_SHA}`\n\n"
    "### 3. Candidate obligations\n"
    "1. **Injected impostor claim**: substituted content after preflight\n"
)
CI_CONTENT = (
    "create-pages:\n  stage: deploy\n  script:\n"
    "    - cp site/index.html public/index.html\n  pages: true\n"
)

TARGET = TargetIdentity(
    DEFAULT_TARGET_PROJECT_ID,
    DEFAULT_TARGET_FULL_PATH,
    "GITLAB_PAGES_SITE",
)


def _note_payload(
    *,
    body: str = AUTHENTIC_NOTE_BODY,
    note_id: int = NOTE_ID,
    author: str = DUO_SERVICE_ACCOUNT_USERNAME,
    issue_iid: int = 5,
) -> str:
    return json.dumps(
        {
            "id": note_id,
            "body": body,
            "noteable_iid": issue_iid,
            "noteable_type": "Issue",
            "author": {"username": author},
            "created_at": "2026-10-19T19:46:42Z",
        }
    )


def _base_replies() -> dict[tuple[str, str], HttpReply]:
    """A complete provider surface for the LIVE continuation path."""
    project_body = json.dumps(
        {
            "id": DEFAULT_TARGET_PROJECT_ID,
            "path_with_namespace": DEFAULT_TARGET_FULL_PATH,
            "default_branch": "main",
            "visibility": "public",
            "web_url": f"https://gitlab.com/{DEFAULT_TARGET_FULL_PATH}",
            "archived": False,
        }
    )
    return {
        ("GET", f"/projects/{CANONICAL_PID}/issues/5/notes/{NOTE_ID}"): HttpReply(
            200, _note_payload()
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/repository/files/"): HttpReply(
            200, CI_CONTENT
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/repository/branches/main"): (
            HttpReply(200, json.dumps({"name": "main", "commit": {"id": AUTHENTIC_COMMIT_SHA}}))
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/repository/commits"): HttpReply(
            200, json.dumps([{"id": AUTHENTIC_COMMIT_SHA}])
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/pipelines"): HttpReply(
            200, json.dumps([{"id": 2960507698, "sha": AUTHENTIC_COMMIT_SHA, "status": "success"}])
        ),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/issues"): HttpReply(200, "[]"),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/environments"): HttpReply(200, "[]"),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}/pages"): HttpReply(403, ""),
        ("GET", f"/projects/{CANONICAL_PID}/issues"): HttpReply(200, "[]"),
        ("GET", f"/projects/{CANONICAL_PID}"): HttpReply(200, "{}"),
        ("GET", "/projects/87777871"): HttpReply(200, "{}"),
        ("GET", "/projects/87786164"): HttpReply(200, "{}"),
        ("GET", f"/projects/{DEFAULT_TARGET_PROJECT_ID}"): HttpReply(200, project_body),
    }


class _TripwirePublisher:
    """An actually injected publisher that fails the test on ANY write call."""

    def __init__(self) -> None:
        self.calls = 0

    def create_issue_note(self, project_id, issue_iid, *, body):  # type: ignore[no-untyped-def]
        self.calls += 1
        raise AssertionError(
            "PROVIDER MUTATION ATTEMPTED: offline replay must never publish "
            f"(create_issue_note called with project {project_id}, issue {issue_iid})"
        )


# ---------------------------------------------------------------------------
# DEFECT 1 — OFFLINE_REPLAY must never publish provider evidence.
# ---------------------------------------------------------------------------


def test_offline_replay_with_publish_is_refused_and_publisher_never_called(tmp_path):
    """Direct Python invocation: offline replay + publish is categorically
    refused with OFFLINE_PUBLICATION_REFUSED; the injected publisher's write
    method is never called."""
    publisher = _TripwirePublisher()
    res = run_supervised_continuation(
        client=GitLabClient(None, transport=FakeTransport(_base_replies())),
        publisher=publisher,
        note_body=AUTHENTIC_NOTE_BODY,
        issue_iid=5,
        duo_session_id=DUO_SESSION_ID_NEUTRAL,
        duo_note_id=NOTE_ID,
        target_project_id=DEFAULT_TARGET_PROJECT_ID,
        expected_commit_sha=AUTHENTIC_COMMIT_SHA,
        publish_outcome=True,
        out_dir=tmp_path / "offline_publish",
        mode="OFFLINE_REPLAY",
        now=NOW,
    )
    assert res.status == "REFUSED_OFFLINE_PUBLICATION"
    assert res.deterministic_verdict == "NOT_DETERMINED"
    assert "OFFLINE_PUBLICATION_REFUSED" in res.summary
    assert res.supervised_review is None
    assert publisher.calls == 0
    # No review artifacts and no publication note were produced.
    assert not (tmp_path / "offline_publish" / "supervised_review.json").exists()
    assert not (tmp_path / "offline_publish" / "supervised_outcome_note.md").exists()


def test_offline_replay_supplied_publisher_cannot_mutate_even_without_publish(tmp_path):
    """A publisher supplied in offline mode can never cause a mutation even
    when publish_outcome is not requested (defense in depth)."""
    publisher = _TripwirePublisher()
    res = run_supervised_continuation(
        client=GitLabClient(None, transport=FakeTransport(_base_replies())),
        publisher=publisher,
        note_body=AUTHENTIC_NOTE_BODY,
        issue_iid=5,
        duo_session_id=DUO_SESSION_ID_NEUTRAL,
        duo_note_id=NOTE_ID,
        target_project_id=DEFAULT_TARGET_PROJECT_ID,
        expected_commit_sha=AUTHENTIC_COMMIT_SHA,
        publish_outcome=False,
        out_dir=tmp_path / "offline_nopublish",
        mode="OFFLINE_REPLAY",
        now=NOW,
    )
    assert res.status == "COMPLETED"
    assert res.mode == "OFFLINE_REPLAY"
    assert publisher.calls == 0
    assert not (tmp_path / "offline_nopublish" / "supervised_outcome_note.md").exists()


def test_cli_offline_replay_publish_rejected_at_boundary(tmp_path, capsys):
    """Real CLI dispatch: --mode offline-replay --publish exits nonzero with
    an explicit OFFLINE_PUBLICATION_REFUSED reason at the CLI boundary."""
    from termivance.cli import main

    cmd = [
        "supervised-review",
        "--continue",
        "--mode",
        "offline-replay",
        "--issue-iid",
        "5",
        "--session-id",
        DUO_SESSION_ID_NEUTRAL,
        "--note-id",
        str(NOTE_ID),
        "--target-id",
        str(DEFAULT_TARGET_PROJECT_ID),
        "--expected-sha",
        AUTHENTIC_COMMIT_SHA,
        "--note-body",
        AUTHENTIC_NOTE_BODY,
        "--publish",
        "--out-dir",
        str(tmp_path / "cli_offline_publish"),
        "--out",
        str(tmp_path / "cli_offline_publish.json"),
    ]
    exit_code = main(cmd)
    assert exit_code != 0
    assert exit_code == 2
    err = capsys.readouterr().err
    assert "OFFLINE_PUBLICATION_REFUSED" in err
    # Rejected before dispatch: no output artifacts were produced.
    assert not (tmp_path / "cli_offline_publish.json").exists()


def test_cli_live_mode_with_publish_is_not_rejected_at_boundary(tmp_path, monkeypatch):
    """The legitimate authorized live publication capability is preserved:
    LIVE mode with --publish is NOT rejected at the CLI boundary (it fails
    closed later on inaccessible provider prerequisites, not on the
    publication flag itself)."""
    import termivance.gitlab_client as glc
    from termivance.cli import main

    class _FailingClient:
        token = None

        def get_json(self, endpoint, params=None):  # type: ignore[no-untyped-def]
            from termivance.gitlab_client import ApiResult

            return ApiResult(False, 404, None, endpoint, "GET", "NOT_FOUND")

        def get_text(self, endpoint, params=None):  # type: ignore[no-untyped-def]
            from termivance.gitlab_client import ApiResult

            return ApiResult(False, 404, None, endpoint, "GET", "NOT_FOUND")

    monkeypatch.setattr(glc, "GitLabClient", lambda *a, **kw: _FailingClient())
    out_file = tmp_path / "cli_live_publish.json"
    cmd = [
        "supervised-review",
        "--continue",
        "--mode",
        "live",
        "--issue-iid",
        "5",
        "--session-id",
        DUO_SESSION_ID_NEUTRAL,
        "--note-id",
        str(NOTE_ID),
        "--target-id",
        str(DEFAULT_TARGET_PROJECT_ID),
        "--expected-sha",
        AUTHENTIC_COMMIT_SHA,
        "--note-body",
        AUTHENTIC_NOTE_BODY,
        "--publish",
        "--out-dir",
        str(tmp_path / "cli_live_publish"),
        "--out",
        str(out_file),
    ]
    exit_code = main(cmd)
    # The refusal comes from the fail-closed LIVE preflight (inaccessible
    # note), not from an offline-publication rejection.
    assert exit_code == 1
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["status"] == "REFUSED_PREFLIGHT"
    assert "OFFLINE_PUBLICATION_REFUSED" not in payload["summary"]


# ---------------------------------------------------------------------------
# DEFECT 2 — the preflight-verified note must be the note executed.
# ---------------------------------------------------------------------------


def _scripted_note_transport(
    second_reply: HttpReply,
) -> ScriptedTransport:
    """A transport whose note endpoint serves the authentic body on the first
    read (the preflight) and `second_reply` on every subsequent read of the
    same endpoint (a hypothetical second provider read)."""
    return ScriptedTransport(
        _base_replies(),
        scripted={
            f"/issues/5/notes/{NOTE_ID}": [
                HttpReply(200, _note_payload()),
                second_reply,
            ]
        },
    )


def _note_read_count(transport: ScriptedTransport) -> int:
    return sum(
        1
        for _m, url in transport.calls
        if f"/issues/5/notes/{NOTE_ID}" in url
    )


def _run_live_with_transport(tmp_path, transport, **overrides):
    params = {
        "client": GitLabClient(None, transport=transport),
        "issue_iid": 5,
        "duo_session_id": DUO_SESSION_ID_NEUTRAL,
        "duo_note_id": NOTE_ID,
        "target_project_id": DEFAULT_TARGET_PROJECT_ID,
        "expected_commit_sha": AUTHENTIC_COMMIT_SHA,
        "out_dir": tmp_path,
        "mode": "LIVE",
        "now": NOW,
    }
    params.update(overrides)
    return run_supervised_continuation(**params)


def test_preflight_captures_verified_handoff_with_exact_bytes():
    """The LIVE preflight captures the exact provider-returned note body,
    note ID, author identity, target identity and digest."""
    client = GitLabClient(None, transport=FakeTransport(_base_replies()))
    preflight, _pid, _sha, _cands = validate_continuation_preflight(
        client=client, note_body=AUTHENTIC_NOTE_BODY
    )
    assert preflight.passed is True
    handoff = preflight.verified_note
    assert handoff is not None
    assert handoff.body == AUTHENTIC_NOTE_BODY
    import hashlib

    assert handoff.body_sha256 == hashlib.sha256(
        AUTHENTIC_NOTE_BODY.encode("utf-8")
    ).hexdigest()
    assert handoff.note_id == NOTE_ID
    assert handoff.note_author == DUO_SERVICE_ACCOUNT_USERNAME
    assert handoff.issue_iid == 5
    assert handoff.canonical_project_id == CANONICAL_PID
    assert handoff.target_project_id == DEFAULT_TARGET_PROJECT_ID
    assert handoff.expected_commit_sha == AUTHENTIC_COMMIT_SHA
    assert handoff.provenance == "LIVE_ANONYMOUS_PROVIDER_NOTE"
    assert handoff.digest_ok() is True
    assert handoff.bindings_match(
        note_id=NOTE_ID,
        issue_iid=5,
        canonical_project_id=CANONICAL_PID,
        target_project_id=DEFAULT_TARGET_PROJECT_ID,
        expected_commit_sha=AUTHENTIC_COMMIT_SHA,
    )


def test_live_continuation_executes_the_preflight_verified_note_exactly(tmp_path):
    """Provider note accessible in preflight, inaccessible on a hypothetical
    second read: the continuation executes the verified handoff bytes and
    performs NO second provider note read (the preflight-verified note IS
    the note executed)."""
    transport = _scripted_note_transport(HttpReply(404, ""))
    res = _run_live_with_transport(tmp_path / "no_second_read", transport)
    assert res.status == "COMPLETED"
    assert res.preflight.passed is True
    # Exactly ONE note read happened (the preflight); the investigation
    # never re-read the provider note.
    assert _note_read_count(transport) == 1
    review = res.supervised_review
    assert review is not None
    duo_step = next(s for s in review.steps if s.step_id == "duo_candidate_analysis")
    assert duo_step.provenance == "LIVE_ANONYMOUS_PROVIDER_NOTE"
    handoff_step = next(s for s in review.steps if s.step_id == "operator_handoff")
    assert "candidate parsing bound to the exact preflight-verified" in handoff_step.detail
    # Candidates derive from the exact provider bytes (2 candidates), not
    # from a local recorded note or a failure fallback.
    from termivance.supervised_review import parse_duo_note

    _pid, _sha, expected_candidates = parse_duo_note(AUTHENTIC_NOTE_BODY)
    assert [c.text for c in review.candidate_claims] == [
        f"{c['topic']}: {c['detail']}" for c in expected_candidates
    ]


def test_provider_note_changed_after_preflight_is_not_substituted(tmp_path):
    """Provider note changed after preflight: the changed content is never
    substituted for the preflight-verified bytes (zero downstream candidate
    substitution)."""
    transport = _scripted_note_transport(HttpReply(200, _note_payload(body=CHANGED_NOTE_BODY)))
    res = _run_live_with_transport(tmp_path / "changed_note", transport)
    assert res.status == "COMPLETED"
    assert _note_read_count(transport) == 1
    review = res.supervised_review
    assert review is not None
    # The executed candidates come from the preflight-verified body (2
    # candidates), not from the changed post-preflight body (1 candidate).
    assert len(review.candidate_claims) == 2
    assert not any("Injected impostor claim" in c.text for c in review.candidate_claims)
    handoff_step = next(s for s in review.steps if s.step_id == "operator_handoff")
    import hashlib

    digest = hashlib.sha256(AUTHENTIC_NOTE_BODY.encode("utf-8")).hexdigest()
    assert digest[:16] in handoff_step.detail


def test_provider_read_failure_is_never_rescued_by_a_fixture(tmp_path):
    """A LIVE continuation whose provider note read fails inside the
    investigation window is never rescued by the local recorded note file
    (evidence/b4/duo_note_4045401991.json): the investigation keeps the
    preflight-verified provider bytes even when a direct provider read of
    the same note fails."""
    client = GitLabClient(None, transport=FakeTransport(_base_replies()))
    preflight, _, _, _ = validate_continuation_preflight(client=client)
    assert preflight.passed is True
    verified = preflight.verified_note
    assert verified is not None

    # A client whose note read now fails (404) for the investigation.
    failing_replies = dict(_base_replies())
    failing_replies[(("GET", f"/projects/{CANONICAL_PID}/issues/5/notes/{NOTE_ID}"))] = (
        HttpReply(404, "")
    )
    failing_client = GitLabClient(None, transport=FakeTransport(failing_replies))

    review = run_supervised_investigation(
        client=failing_client,
        target=TARGET,
        duo_note_id=NOTE_ID,
        verified_note=verified,
        issue_iid=5,
        out_dir=tmp_path / "failing_read",
        now=NOW,
    )
    # The verified handoff is the note executed: provider-read failure did
    # not trigger the local recorded fallback.
    duo_step = next(s for s in review.steps if s.step_id == "duo_candidate_analysis")
    assert duo_step.status == "COMPLETED"
    assert duo_step.provenance == "LIVE_ANONYMOUS_PROVIDER_NOTE"
    from termivance.supervised_review import parse_duo_note

    _pid, _sha, expected_candidates = parse_duo_note(AUTHENTIC_NOTE_BODY)
    assert len(review.candidate_claims) == len(expected_candidates)


def test_altered_verified_handoff_is_refused_not_rescued(tmp_path):
    """An altered verified handoff object (body no longer matching its
    recorded digest) is refused; the local recorded note is NOT used as a
    substitute."""
    client = GitLabClient(None, transport=FakeTransport(_base_replies()))
    preflight, _, _, _ = validate_continuation_preflight(client=client)
    verified = preflight.verified_note
    assert verified is not None
    tampered = dataclasses.replace(verified, body=CHANGED_NOTE_BODY)
    assert tampered.digest_ok() is False

    review = run_supervised_investigation(
        client=client,
        target=TARGET,
        duo_note_id=NOTE_ID,
        verified_note=tampered,
        issue_iid=5,
        out_dir=tmp_path / "tampered_handoff",
        now=NOW,
    )
    duo_step = next(s for s in review.steps if s.step_id == "duo_candidate_analysis")
    assert duo_step.status == "BLOCKED"
    assert "altered" in duo_step.detail.lower()
    assert review.target_validation.get("checks_passed") is False
    # No candidates were parsed from any substituted source.
    assert review.candidate_claims == ()


def test_live_continuation_without_verified_handoff_refuses(tmp_path):
    """If the verified handoff object is missing after a passing LIVE
    preflight, the continuation is refused (defense in depth)."""
    client = GitLabClient(None, transport=FakeTransport(_base_replies()))
    preflight, _, _, _ = validate_continuation_preflight(client=client)
    assert preflight.passed is True
    # Simulate a handoff lost between preflight and execution by stripping
    # it from the preflight object through the production result path.
    stripped = dataclasses.replace(preflight, verified_note=None)

    from unittest.mock import patch

    with patch(
        "termivance.supervised_review.validate_continuation_preflight",
        return_value=(stripped, None, None, []),
    ):
        res = run_supervised_continuation(
            client=client,
            issue_iid=5,
            duo_session_id=DUO_SESSION_ID_NEUTRAL,
            duo_note_id=NOTE_ID,
            target_project_id=DEFAULT_TARGET_PROJECT_ID,
            expected_commit_sha=AUTHENTIC_COMMIT_SHA,
            out_dir=tmp_path / "no_handoff",
            mode="LIVE",
            now=NOW,
        )
    assert res.status == "REFUSED_VERIFIED_NOTE_HANDOFF"
    assert res.deterministic_verdict == "NOT_DETERMINED"
    assert "VERIFIED_NOTE_HANDOFF_MISSING" in res.summary
    assert res.supervised_review is None


def test_contradictory_handoff_bindings_refuse_continuation(tmp_path):
    """A handoff whose identity bindings contradict the invocation's causal
    identity refuses the continuation."""
    client = GitLabClient(None, transport=FakeTransport(_base_replies()))
    preflight, _, _, _ = validate_continuation_preflight(client=client)
    verified = preflight.verified_note
    assert verified is not None
    contradictory = dataclasses.replace(verified, note_id=NOTE_ID + 1)

    from unittest.mock import patch

    with patch(
        "termivance.supervised_review.validate_continuation_preflight",
        return_value=(
            dataclasses.replace(preflight, verified_note=contradictory),
            None,
            None,
            [],
        ),
    ):
        res = run_supervised_continuation(
            client=client,
            issue_iid=5,
            duo_session_id=DUO_SESSION_ID_NEUTRAL,
            duo_note_id=NOTE_ID,
            target_project_id=DEFAULT_TARGET_PROJECT_ID,
            expected_commit_sha=AUTHENTIC_COMMIT_SHA,
            out_dir=tmp_path / "contradictory",
            mode="LIVE",
            now=NOW,
        )
    assert res.status == "REFUSED_VERIFIED_NOTE_HANDOFF"
    assert "VERIFIED_NOTE_HANDOFF_CONTRADICTORY" in res.summary


def test_offline_replay_retains_fixture_provenance_and_never_upgrades_to_live(tmp_path):
    """Offline replay must not upgrade a recorded result to a live
    authenticated outcome (FIXTURE_RECORDED_INPUT provenance preserved)."""
    res = run_supervised_continuation(
        client=GitLabClient(None, transport=FakeTransport(_base_replies())),
        note_body=AUTHENTIC_NOTE_BODY,
        issue_iid=5,
        duo_session_id=DUO_SESSION_ID_NEUTRAL,
        duo_note_id=NOTE_ID,
        target_project_id=DEFAULT_TARGET_PROJECT_ID,
        expected_commit_sha=AUTHENTIC_COMMIT_SHA,
        out_dir=tmp_path / "replay_provenance",
        mode="OFFLINE_REPLAY",
        now=NOW,
    )
    assert res.status == "COMPLETED"
    assert res.mode == "OFFLINE_REPLAY"
    assert res.preflight.provenance == "FIXTURE_RECORDED_INPUT"
    assert res.preflight.verified_note is None
    data = res.to_dict()
    assert "never a live authenticated Supervised continuation" in data["autonomy_classification"]
    # The note-authenticated LIVE session is never labelled independently
    # verified: the live classification keeps the NEEDS_REVIEW boundary.
    res_live = _run_live_with_transport(
        tmp_path / "live_provenance", _scripted_note_transport(HttpReply(404, ""))
    )
    assert res_live.status == "COMPLETED"
    live_data = res_live.to_dict()
    assert "NEEDS_REVIEW" in live_data["autonomy_classification"]
    assert "independently verified" not in live_data["autonomy_classification"]


# ---------------------------------------------------------------------------
# DEFECT 3 — the durable ledger must verify its execution owner.
# ---------------------------------------------------------------------------

CAUSAL_KEY = (
    f"{CANONICAL_PID}:5:{DUO_SESSION_ID_NEUTRAL}:{NOTE_ID}:"
    f"{DEFAULT_TARGET_PROJECT_ID}:{AUTHENTIC_COMMIT_SHA}"
)


def _fresh_ledger(tmp_path, name: str) -> ContinuationLedger:
    ledger = ContinuationLedger(tmp_path / name / ".continuation_executions.json")
    ledger.health_check()
    return ledger


def test_finalize_rejects_wrong_execution_owner(tmp_path):
    """A competing execution cannot finalize another invocation's
    reservation."""
    ledger = _fresh_ledger(tmp_path, "wrong_owner")
    reservation = ledger.reserve(CAUSAL_KEY, execution_id="cont-owner-a", now=NOW)
    assert reservation.outcome == RESERVE_FIRST_EXECUTION

    with pytest.raises(ContinuationLedgerError, match="EXECUTION_OWNER_MISMATCH"):
        ledger.finalize(
            CAUSAL_KEY,
            execution_id="cont-owner-b",
            status="COMPLETED",
            verdict="BLOCKED",
            now=NOW,
        )
    # The reservation is untouched and still owned by the first execution.
    record = ledger.lookup(CAUSAL_KEY)
    assert record is not None
    assert record["state"] == RESERVED_STATE
    assert record["execution_id"] == "cont-owner-a"

    # The rightful owner can still finalize.
    finalized = ledger.finalize(
        CAUSAL_KEY, execution_id="cont-owner-a", status="COMPLETED", verdict="BLOCKED", now=NOW
    )
    assert finalized["state"] == COMPLETED_STATE


def test_recovery_transfers_ownership_and_stale_owner_is_refused(tmp_path):
    """Recovery transfers the reservation to the verified recovering
    invocation; the stale original invocation cannot finalize afterwards."""
    ledger = _fresh_ledger(tmp_path, "recovery_owner")
    ledger.reserve(CAUSAL_KEY, execution_id="cont-original", now=NOW)

    recovered = ledger.reserve(
        CAUSAL_KEY, execution_id="cont-recovering", now=NOW, allow_recovery=True
    )
    assert recovered.outcome == RESERVE_FIRST_EXECUTION
    assert recovered.record is not None
    assert recovered.record["execution_id"] == "cont-recovering"
    assert recovered.record.get("recovery_attempts")

    # The stale original invocation is refused.
    with pytest.raises(ContinuationLedgerError, match="EXECUTION_OWNER_MISMATCH"):
        ledger.finalize(
            CAUSAL_KEY,
            execution_id="cont-original",
            status="COMPLETED",
            verdict="BLOCKED",
            now=NOW,
        )
    record = ledger.lookup(CAUSAL_KEY)
    assert record is not None
    assert record["state"] == RESERVED_STATE
    assert record["execution_id"] == "cont-recovering"

    # The recovering invocation finalizes successfully.
    finalized = ledger.finalize(
        CAUSAL_KEY,
        execution_id="cont-recovering",
        status="COMPLETED",
        verdict="BLOCKED",
        now=NOW,
    )
    assert finalized["state"] == COMPLETED_STATE
    assert finalized["execution_id"] == "cont-recovering"


def test_duplicate_complete_record_is_never_refinalized_or_recast(tmp_path):
    """A duplicate complete record is not overwritten, re-finalized or
    silently recast; contradictory follow-ups are audit-only."""
    ledger = _fresh_ledger(tmp_path, "duplicate_complete")
    ledger.reserve(CAUSAL_KEY, execution_id="cont-first", now=NOW)
    finalized = ledger.finalize(
        CAUSAL_KEY, execution_id="cont-first", status="COMPLETED", verdict="BLOCKED", now=NOW
    )
    assert finalized["state"] == COMPLETED_STATE

    # A contradictory follow-up from another execution is recorded as an
    # audit-only ambiguous outcome; the authoritative first verdict stands.
    after = ledger.finalize(
        CAUSAL_KEY,
        execution_id="cont-second",
        status="COMPLETED",
        verdict="SAFE_TO_RETIRE",
        now=NOW,
    )
    assert after["state"] == COMPLETED_STATE
    assert after["verdict"] == "BLOCKED"
    assert after["status"] == "COMPLETED"
    assert after["execution_id"] == "cont-first"
    ambiguous = after.get("ambiguous_outcomes")
    assert isinstance(ambiguous, list) and len(ambiguous) == 1
    assert ambiguous[0]["execution_id"] == "cont-second"
    assert ambiguous[0]["verdict"] == "SAFE_TO_RETIRE"

    # The idempotent duplicate path still retrieves the authentic record.
    reservation = ledger.reserve(CAUSAL_KEY, execution_id="cont-third", now=NOW)
    assert reservation.outcome == "DUPLICATE_OF_COMPLETED"
    assert reservation.record is not None
    assert reservation.record["verdict"] == "BLOCKED"


def test_finalize_verifies_durable_result_and_digest_after_writing(tmp_path):
    """After finalization the durable recorded result and its integrity
    digest are verified (independent read-back)."""
    ledger = _fresh_ledger(tmp_path, "readback")
    ledger.reserve(CAUSAL_KEY, execution_id="cont-readback", now=NOW)
    finalized = ledger.finalize(
        CAUSAL_KEY, execution_id="cont-readback", status="COMPLETED", verdict="BLOCKED", now=NOW
    )
    assert finalized["state"] == COMPLETED_STATE
    assert finalized["execution_id"] == "cont-readback"
    assert finalized["verdict"] == "BLOCKED"

    # A fresh ledger instance (simulated restart) reads the same verified
    # record; any tampering with it fails the integrity digest.
    restarted = ContinuationLedger(ledger.path)
    record = restarted.lookup(CAUSAL_KEY)
    assert record is not None
    assert record["state"] == COMPLETED_STATE

    raw = json.loads(ledger.path.read_text(encoding="utf-8"))
    key = next(iter(raw["executions"]))
    raw["executions"][key]["verdict"] = "SAFE_TO_RETIRE"
    ledger.path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ContinuationLedgerError, match="integrity digest"):
        restarted.lookup(CAUSAL_KEY)


def test_concurrent_reservations_single_owner_finalize(tmp_path):
    """Concurrent reservations yield exactly one first execution; only that
    owner may finalize (exercised through the production ledger path)."""
    from concurrent.futures import ThreadPoolExecutor

    ledger = _fresh_ledger(tmp_path, "concurrent_owner")

    def _reserve(i: int) -> tuple[str, str]:
        led = ContinuationLedger(ledger.path)
        outcome = led.reserve(
            CAUSAL_KEY, execution_id=f"cont-conc-{i}", now=NOW
        ).outcome
        return outcome, f"cont-conc-{i}"

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(_reserve, range(4)))

    first_owners = [owner for outcome, owner in results if outcome == RESERVE_FIRST_EXECUTION]
    assert len(first_owners) == 1
    winner = first_owners[0]
    for _outcome, owner in results:
        if owner != winner:
            with pytest.raises(ContinuationLedgerError, match="EXECUTION_OWNER_MISMATCH"):
                ledger.finalize(
                    CAUSAL_KEY, execution_id=owner, status="COMPLETED", verdict="BLOCKED", now=NOW
                )
    finalized = ledger.finalize(
        CAUSAL_KEY, execution_id=winner, status="COMPLETED", verdict="BLOCKED", now=NOW
    )
    assert finalized["state"] == COMPLETED_STATE
    assert finalized["execution_id"] == winner


# ---------------------------------------------------------------------------
# DEFECT 4 — historical absence cannot override missing current observations.
# ---------------------------------------------------------------------------


SERVED_URL = "https://termivance-b3-disposable-pages-demo-42a1a9.gitlab.io/"
MONITOR_TARGET = TARGET


def _genuine_receipt(tmp_path) -> tuple[dict[str, object], object]:
    """A genuine bounded historical receipt built through the real
    Authorization/AuthorizationLedger contracts (as in the B4 suite)."""
    from datetime import timedelta

    from termivance.authorization import Authorization, OperatorApproval
    from termivance.ledger import AuthorizationLedger

    ledger_file = tmp_path / "durable_ledger_monitor.json"
    ledger = AuthorizationLedger(ledger_file)
    ledger.health_check()

    auth = Authorization.issue(MONITOR_TARGET, "unpublish_pages", nonce="nonce-ca-1", now=NOW)
    auth.approval = OperatorApproval(
        operator="op",
        statement=(
            "I authorize exactly one unpublish_pages using "
            f"/projects/{MONITOR_TARGET.project_id}/pages"
        ),
        approved_at=NOW,
        channel="web_ui",
        binding=auth.binding(),
    )
    consumption = ledger.consume(auth, operation_id="op-ca-1", now=NOW)
    ledger.finalize(consumption.binding, outcome="ACCEPTED")

    eligibility_at = NOW - timedelta(seconds=100)
    requested_at = NOW - timedelta(seconds=50)
    absence_at = NOW - timedelta(seconds=40)

    receipt: dict[str, object] = {
        "schema": "termivance.retirement_receipt/v3",
        "target": MONITOR_TARGET.to_dict(),
        "action": "unpublish_pages",
        "authorization_binding": auth.binding(),
        "authorization_record": {
            "binding": auth.binding(),
            "nonce": "nonce-ca-1",
            "action": "unpublish_pages",
            "target_key": MONITOR_TARGET.key_string(),
        },
        "operation_id": "op-ca-1",
        "mutation_attempted": True,
        "verdict": "OBSERVED_ABSENT",
        "eligibility": {
            "established_at": eligibility_at.isoformat(),
            "pre_state": {
                "served_url": SERVED_URL,
                "marker": "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a",
                "marker_observed": True,
                "marker_sha256": "a" * 64,
                "deployment_present": True,
                "observed_at": eligibility_at.isoformat(),
                "genuinely_published": True,
            },
        },
        "mutation": {
            "accepted": True,
            "status": 204,
            "method": "DELETE",
            "endpoint": f"/projects/{MONITOR_TARGET.project_id}/pages",
            "requested_at": requested_at.isoformat(),
        },
        "absence": {
            "verdict": "OBSERVED_ABSENT",
            "pages_api": {"status": 404, "error": None},
            "served_url": {"http_status": 404, "error": None},
            "observation": {
                "served_url": SERVED_URL,
                "marker": "TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a",
                "marker_observed": False,
                "deployment_present": False,
                "observed_at": absence_at.isoformat(),
            },
            "notes": ["post-action read-backs of the same exact URL"],
        },
        "observed_at": absence_at.isoformat(),
        "preflight": {"observed_at": absence_at.isoformat(), "commit_sha": AUTHENTIC_COMMIT_SHA},
        "commit_sha": AUTHENTIC_COMMIT_SHA,
    }
    return receipt, ledger_file


def _make_obs(
    *,
    served_url: str | None = SERVED_URL,
    served_status: int | None = 404,
    marker_observed: bool = False,
    ci_config_present: bool = True,
    has_mechanism: bool = False,
    pages_api_status: int = 404,
    observed_at: datetime = NOW,
) -> TargetCurrentObservation:
    return TargetCurrentObservation(
        project_id=MONITOR_TARGET.project_id,
        full_path=MONITOR_TARGET.full_path,
        default_branch="main",
        commit_sha=AUTHENTIC_COMMIT_SHA,
        ci_config_present=ci_config_present,
        redeployment_mechanism=has_mechanism,
        redeployment_signals=("pages_true", "pages_keyword") if has_mechanism else (),
        pages_api_status=pages_api_status,
        pages_api_accessible=(pages_api_status < 400),
        served_url=served_url,
        served_http_status=served_status,
        served_marker_observed=marker_observed,
        observed_at=observed_at,
        pages_api_deployment_count=0,
    )


def _monitor(tmp_path, obs, receipt=None, **overrides):
    from termivance.ledger import AuthorizationLedger

    history, ledger_file = (
        _genuine_receipt(tmp_path) if receipt is None else (receipt, None)
    )
    ledger = AuthorizationLedger(ledger_file) if ledger_file else None
    params = {
        "target": MONITOR_TARGET,
        "current_observation": obs,
        "historical_truth": history,
        "ledger": ledger,
        "now": NOW,
    }
    params.update(overrides)
    return monitor_resurrection(**params)


def test_valid_receipt_with_missing_current_url_is_refused(tmp_path):
    """Valid prior receipt plus missing current served URL: never continued
    absence — the current observation is unbound (CURRENT_OBSERVATION_MISMATCH)."""
    report = _monitor(
        tmp_path,
        _make_obs(served_url=None, served_status=404, pages_api_status=404),
    )
    assert report.current_truth == CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH
    assert report.current_truth != CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED
    assert any("CURRENT_SERVED_URL_MISSING" in d for d in report.diff_reasons)


def test_valid_receipt_with_wrong_current_url_is_refused(tmp_path):
    """Valid prior receipt plus wrong current URL: refused, never continued
    absence."""
    report = _monitor(
        tmp_path,
        _make_obs(served_url="https://unrelated-site.gitlab.io/other/"),
    )
    assert report.current_truth == CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH
    assert report.current_truth != CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED


def test_served_200_marker_on_unbound_url_is_not_resurrection(tmp_path):
    """Served HTTP 200 and marker on an unbound URL: never inferred to come
    from the authorized URL, never RESURRECTED_NOT_ABSENT."""
    report = _monitor(
        tmp_path,
        _make_obs(
            served_url="https://impostor-site.gitlab.io/",
            served_status=200,
            marker_observed=True,
        ),
    )
    assert report.current_truth == CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH
    assert report.current_truth != CurrentTruthStatus.RESURRECTED_NOT_ABSENT


def test_synthetic_served_200_without_current_url_is_not_resurrection(tmp_path):
    """A synthetic served_http_status=200 with NO current served URL can
    never be attributed to the authorized URL."""
    report = _monitor(
        tmp_path,
        _make_obs(served_url=None, served_status=200, marker_observed=True),
    )
    assert report.current_truth == CurrentTruthStatus.CURRENT_OBSERVATION_MISMATCH
    assert report.current_truth != CurrentTruthStatus.RESURRECTED_NOT_ABSENT


def test_valid_receipt_with_missing_ci_configuration_is_inconclusive(tmp_path):
    """Valid prior receipt, Pages 404 and served 404, but CI inaccessible:
    uncertainty is reported, never continued absence."""
    report = _monitor(
        tmp_path,
        _make_obs(ci_config_present=False, pages_api_status=404, served_status=404),
    )
    assert report.current_truth == CurrentTruthStatus.INCONCLUSIVE_PROBE_FAILED
    assert report.current_truth != CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED
    assert report.redeployment_risk == RedeploymentRisk.CONFIG_INACCESSIBLE
    assert any("CURRENT_CI_CONFIGURATION_NOT_OBSERVED" in d for d in report.diff_reasons)


def test_stale_current_observation_never_awards_continued_absence(tmp_path):
    """Stale current observation with an otherwise valid historical receipt:
    never continued absence (current-observation freshness is validated
    independently of the historical receipt's timestamp)."""
    from datetime import timedelta

    report = _monitor(
        tmp_path,
        _make_obs(observed_at=NOW - timedelta(seconds=1200)),
    )
    assert report.current_truth == CurrentTruthStatus.STALE_REVALIDATION_REQUIRED
    assert report.current_truth != CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED
    assert any("CURRENT_OBSERVATION_STALE" in d for d in report.diff_reasons)


def test_continued_absence_requires_bound_url_observed_ci_and_fresh_observation(tmp_path):
    """Real target-bound negative read-backs with verified current CI and a
    fresh, URL-bound current observation do award continued absence."""
    report = _monitor(
        tmp_path,
        _make_obs(
            served_url=SERVED_URL,
            served_status=404,
            marker_observed=False,
            ci_config_present=True,
            has_mechanism=False,
            pages_api_status=404,
            observed_at=NOW,
        ),
    )
    assert report.current_truth == CurrentTruthStatus.CONTINUED_ABSENCE_OBSERVED
    assert report.current_observation.served_url == SERVED_URL
    assert report.current_observation.ci_config_present is True


def test_protected_targets_are_refused(tmp_path):
    """Protected projects are refused regardless of observation quality."""
    from termivance.resurrection_monitor import monitor_resurrection as _mr

    for pid in (87779099, 87777871, 87786164):
        tgt = TargetIdentity(pid, f"group/project-{pid}", "GITLAB_PAGES_SITE")
        obs = TargetCurrentObservation(
            project_id=pid,
            full_path=f"group/project-{pid}",
            default_branch="main",
            commit_sha=AUTHENTIC_COMMIT_SHA,
            ci_config_present=True,
            redeployment_mechanism=False,
            redeployment_signals=(),
            pages_api_status=404,
            pages_api_accessible=True,
            served_url=SERVED_URL,
            served_http_status=404,
            served_marker_observed=False,
            observed_at=NOW,
            pages_api_deployment_count=0,
        )
        report = _mr(tgt, current_observation=obs, now=NOW)
        assert report.current_truth == CurrentTruthStatus.TARGET_MUTATION_BLOCKED
