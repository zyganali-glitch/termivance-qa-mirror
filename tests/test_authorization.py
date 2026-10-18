from datetime import UTC, datetime, timedelta

import pytest

from termivance.authorization import Authorization, AuthorizationError
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


def make_auth(pages_target) -> Authorization:
    return Authorization.issue(
        pages_target, "unpublish_pages", nonce="nonce-1", now=NOW, ttl=timedelta(minutes=10)
    )


def test_valid_within_bounds(pages_target):
    auth = make_auth(pages_target)
    assert auth.is_valid(NOW + timedelta(minutes=1), pages_target, "unpublish_pages")


def test_expired_is_invalid(pages_target):
    auth = make_auth(pages_target)
    assert not auth.is_valid(NOW + timedelta(minutes=11), pages_target, "unpublish_pages")


def test_wrong_action_is_invalid(pages_target):
    auth = make_auth(pages_target)
    assert not auth.is_valid(NOW, pages_target, "delete_project")


def test_wrong_target_is_invalid(pages_target):
    auth = make_auth(pages_target)
    other = TargetIdentity(999, "grp/other", "GITLAB_PAGES_SITE")
    assert not auth.is_valid(NOW, other, "unpublish_pages")


def test_one_time_use(pages_target):
    auth = make_auth(pages_target)
    auth.consume(NOW, pages_target, "unpublish_pages")
    assert not auth.is_valid(NOW, pages_target, "unpublish_pages")
    with pytest.raises(AuthorizationError):
        auth.consume(NOW, pages_target, "unpublish_pages")


def test_from_prose_always_refused(pages_target):
    with pytest.raises(AuthorizationError):
        Authorization.from_prose(pages_target, "unpublish_pages")


def test_invalid_ttl_refused(pages_target):
    with pytest.raises(AuthorizationError):
        Authorization.issue(pages_target, "unpublish_pages", nonce="n", now=NOW, ttl=timedelta(0))
