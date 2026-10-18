"""Tests for the shipped B3 disposable configuration and safe defaults."""

from __future__ import annotations

from datetime import UTC, datetime

from termivance.authorization import load_authorization
from termivance.pages import mutation_is_structurally_safe
from termivance.policy import load_policy
from termivance.retirement import preflight
from termivance.target import TargetIdentity

B3_POLICY = "config/retirement_policy.b3_disposable.json"
EXAMPLE_AUTH = "config/authorization.example.json"
DISPOSABLE_ID = 87785099
DISPOSABLE_PATH = (
    "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
)


def test_b3_policy_allows_only_the_disposable_target():
    policy = load_policy(B3_POLICY)
    assert policy.mutation_enabled is True
    assert policy.allowed_target_project_ids == (DISPOSABLE_ID,)
    assert policy.allowed_target_full_paths == (DISPOSABLE_PATH,)
    assert policy.allowed_actions == ("unpublish_pages",)
    assert DISPOSABLE_ID not in (87779099, 87777871)


def test_shipped_example_authorization_is_expired_and_unusable():
    auth = load_authorization(EXAMPLE_AUTH)
    now = datetime(2026, 10, 18, tzinfo=UTC)
    assert auth.is_valid(now, auth.target, "unpublish_pages") is False


def test_example_authorization_cannot_unlock_the_disposable_target():
    policy = load_policy(B3_POLICY)
    target = TargetIdentity(DISPOSABLE_ID, DISPOSABLE_PATH, "GITLAB_PAGES_SITE")
    auth = load_authorization(EXAMPLE_AUTH)
    result = preflight(target, policy, auth, now=datetime(2026, 10, 18, tzinfo=UTC))
    assert result.ok is False


def test_mutation_allowlist_excludes_project_deletion():
    assert mutation_is_structurally_safe() is True
