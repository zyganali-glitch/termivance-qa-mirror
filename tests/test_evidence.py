from datetime import UTC, datetime, timedelta

from termivance.evidence import PagesObservation, PagesPreState, bounded_absence
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
URL = "https://example.pages.example/"


def pre_state(**kw) -> PagesPreState:
    base = {
        "served_url": URL,
        "marker": "MARKER",
        "marker_observed": True,
        "deployment_present": True,
        "observed_at": NOW - timedelta(minutes=5),
    }
    base.update(kw)
    return PagesPreState(**base)  # type: ignore[arg-type]


def obs(pages_target, **kw) -> PagesObservation:
    base = {
        "target": pages_target,
        "observed_scope": frozenset({"pages_api", "served_url"}),
        "observation_time_utc": NOW,
        "source": "GET /projects/:id/pages + GET served url",
        "api_status": 404,
        "served_url": URL,
        "http_status": 404,
        "fresh_until": NOW + timedelta(minutes=5),
        "pre_state": pre_state(),
        "action_accepted": True,
        "action_endpoint": "/projects/12345678/pages",
    }
    base.update(kw)
    return PagesObservation(**base)  # type: ignore[arg-type]


def test_proven_transition_is_observed_absent(pages_target):
    assert bounded_absence(obs(pages_target), NOW) == Verdict.OBSERVED_ABSENT


def test_two_unrelated_404_without_pre_state_are_not_absent(pages_target):
    assert bounded_absence(obs(pages_target, pre_state=None), NOW) == Verdict.INCONCLUSIVE


def test_never_published_site_is_not_absent(pages_target):
    o = obs(pages_target, pre_state=pre_state(deployment_present=False, marker_observed=False))
    assert bounded_absence(o, NOW) == Verdict.INCONCLUSIVE


def test_marker_never_observed_is_not_absent(pages_target):
    o = obs(pages_target, pre_state=pre_state(marker_observed=False))
    assert bounded_absence(o, NOW) == Verdict.INCONCLUSIVE


def test_mismatched_pre_state_url_is_not_absent(pages_target):
    o = obs(pages_target, pre_state=pre_state(served_url="https://other.pages.example/"))
    assert bounded_absence(o, NOW) == Verdict.INCONCLUSIVE


def test_unaccepted_action_is_not_absent(pages_target):
    assert bounded_absence(obs(pages_target, action_accepted=False), NOW) == Verdict.INCONCLUSIVE


def test_still_served_is_blocked(pages_target):
    assert bounded_absence(obs(pages_target, api_status=200), NOW) == Verdict.BLOCKED


def test_error_status_is_inconclusive(pages_target):
    assert bounded_absence(obs(pages_target, api_status=500), NOW) == Verdict.INCONCLUSIVE


def test_unknown_status_is_inconclusive(pages_target):
    o = obs(pages_target, api_status=None, http_status=None)
    assert bounded_absence(o, NOW) == Verdict.INCONCLUSIVE


def test_missing_scope_is_inconclusive(pages_target):
    o = obs(pages_target, observed_scope=frozenset({"pages_api"}))
    assert bounded_absence(o, NOW) == Verdict.INCONCLUSIVE


def test_stale_evidence_is_inconclusive(pages_target):
    assert bounded_absence(obs(pages_target), NOW + timedelta(minutes=6)) == Verdict.INCONCLUSIVE


def test_api_404_but_url_still_served_is_inconclusive(pages_target):
    assert bounded_absence(obs(pages_target, http_status=200), NOW) == Verdict.INCONCLUSIVE


def test_cloudflare_challenge_is_inconclusive(pages_target):
    assert bounded_absence(obs(pages_target, http_status=403), NOW) == Verdict.INCONCLUSIVE


def test_redirect_to_login_is_inconclusive(pages_target):
    assert bounded_absence(obs(pages_target, http_status=302), NOW) == Verdict.INCONCLUSIVE


def test_non_pages_target_refused():
    from termivance.evidence import EvidenceError

    try:
        obs(TargetIdentity(1, "a/b", "GITLAB_PROJECT"))
    except EvidenceError:
        return
    raise AssertionError("expected EvidenceError")
