"""Retirement policy loading.

Policy is configuration, not authorization. Loading the example policy must
never grant mutation. All parsing fails closed: a missing, malformed or
example-only policy permits no mutation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from termivance.target import TargetIdentity

EXAMPLE_MODE = "EXAMPLE_ONLY_NOT_AUTHORIZATION"


class PolicyError(ValueError):
    """Raised when a policy is missing, invalid, or would permit mutation unsafely."""


@dataclass(frozen=True, slots=True)
class Policy:
    schema_version: int
    mode: str
    mutation_enabled: bool
    provider: str
    allowed_target_project_ids: tuple[int, ...]
    allowed_target_full_paths: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    authorization_required: bool


def _require(data: object, key: str, types: tuple[type, ...]) -> object:
    if not isinstance(data, dict) or key not in data:
        raise PolicyError(f"policy is missing required field {key!r}")
    value = data[key]
    if not isinstance(value, types) or (isinstance(value, bool) and bool not in types):
        raise PolicyError(f"policy field {key!r} has invalid type {type(value).__name__}")
    return value


def load_policy(path: str | Path) -> Policy:
    """Load and validate a policy file, failing closed on any problem."""
    p = Path(path)
    if not p.is_file():
        raise PolicyError(f"policy file not found: {p}")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PolicyError(f"invalid policy JSON in {p}: {exc}") from exc

    schema_version = _require(raw, "schema_version", (int,))
    mode = _require(raw, "mode", (str,))
    mutation_enabled = _require(raw, "mutation_enabled", (bool,))
    provider = _require(raw, "provider", (str,))
    ids = _require(raw, "allowed_target_project_ids", (list,))
    paths = _require(raw, "allowed_target_full_paths", (list,))
    actions = _require(raw, "allowed_actions", (list,))
    auth_required = _require(raw, "authorization_required", (bool,))

    if mode == EXAMPLE_MODE and mutation_enabled:
        raise PolicyError("example policy must not enable mutation")
    for value in ids:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise PolicyError("allowed_target_project_ids must contain positive integers")

    return Policy(
        schema_version=int(schema_version),
        mode=str(mode),
        mutation_enabled=bool(mutation_enabled),
        provider=str(provider),
        allowed_target_project_ids=tuple(int(v) for v in ids),
        allowed_target_full_paths=tuple(str(v) for v in paths),
        allowed_actions=tuple(str(v) for v in actions),
        authorization_required=bool(auth_required),
    )


def assert_mutation_permitted(policy: Policy, target: TargetIdentity, action: str) -> None:
    """Fail closed unless a policy explicitly allows this exact target/action.

    In B1 this can never succeed: the shipped example policy has mutation
    disabled and no allowlisted targets or actions.
    """
    if policy.mode == EXAMPLE_MODE:
        raise PolicyError("example policy is not an authorization")
    if not policy.mutation_enabled:
        raise PolicyError("mutation is disabled by policy")
    if target.project_id not in policy.allowed_target_project_ids:
        raise PolicyError(f"target project_id {target.project_id} is not allowlisted")
    if target.full_path not in policy.allowed_target_full_paths:
        raise PolicyError(f"target full_path {target.full_path!r} is not allowlisted")
    if action not in policy.allowed_actions:
        raise PolicyError(f"action {action!r} is not allowlisted")
