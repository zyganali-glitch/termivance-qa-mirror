import pytest

from termivance.target import TargetError, TargetIdentity


def test_valid_target_key():
    t = TargetIdentity(7, "grp/proj", "GITLAB_PAGES_SITE")
    assert t.key() == (7, "grp/proj", "GITLAB_PAGES_SITE")


@pytest.mark.parametrize(
    "project_id, full_path, kind",
    [
        (0, "grp/proj", "GITLAB_PAGES_SITE"),
        (-3, "grp/proj", "GITLAB_PAGES_SITE"),
        (True, "grp/proj", "GITLAB_PAGES_SITE"),
        (4, "", "GITLAB_PAGES_SITE"),
        (4, " grp/proj", "GITLAB_PAGES_SITE"),
        (4, "/grp/proj", "GITLAB_PAGES_SITE"),
        (4, "grp/proj/", "GITLAB_PAGES_SITE"),
        (4, "grp/proj", "UNKNOWN_KIND"),
    ],
)
def test_invalid_targets_refused(project_id, full_path, kind):
    with pytest.raises(TargetError):
        TargetIdentity(project_id, full_path, kind)


def test_from_dict_missing_field():
    with pytest.raises(TargetError):
        TargetIdentity.from_dict({"project_id": 1, "full_path": "a/b"})


def test_roundtrip():
    t = TargetIdentity(9, "a/b", "GITLAB_PROJECT")
    assert TargetIdentity.from_dict(t.to_dict()).key() == t.key()
