import json

import pytest

from termivance.policy import PolicyError, assert_mutation_permitted, load_policy
from termivance.target import TargetIdentity


def write(tmp_path, data):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def valid(**over):
    data = {
        "schema_version": 1,
        "mode": "EXAMPLE_ONLY_NOT_AUTHORIZATION",
        "mutation_enabled": False,
        "provider": "GITLAB_PAGES",
        "allowed_target_project_ids": [],
        "allowed_target_full_paths": [],
        "allowed_actions": [],
        "authorization_required": True,
    }
    data.update(over)
    return data


def test_example_policy_loads_disabled(tmp_path):
    policy = load_policy(write(tmp_path, valid()))
    assert policy.mutation_enabled is False


def test_missing_file_fails_closed(tmp_path):
    with pytest.raises(PolicyError):
        load_policy(tmp_path / "missing.json")


def test_invalid_json_fails_closed(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(PolicyError):
        load_policy(p)


def test_missing_field_fails_closed(tmp_path):
    data = valid()
    del data["mode"]
    with pytest.raises(PolicyError):
        load_policy(write(tmp_path, data))


def test_example_cannot_enable_mutation(tmp_path):
    with pytest.raises(PolicyError):
        load_policy(write(tmp_path, valid(mutation_enabled=True)))


def test_mutation_refused_even_when_flag_set(tmp_path):
    # Real (non-example) mode but empty allowlists: still refused.
    policy = load_policy(
        write(
            tmp_path,
            valid(mode="OPERATOR_APPROVED", mutation_enabled=True),
        )
    )
    target = TargetIdentity(5, "a/b", "GITLAB_PAGES_SITE")
    with pytest.raises(PolicyError):
        assert_mutation_permitted(policy, target, "unpublish_pages")
