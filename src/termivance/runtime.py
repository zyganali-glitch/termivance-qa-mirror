"""Wiring for live read-only discovery and evaluation.

Keeps credential loading, transport wiring and snapshot handling out of the CLI
so both can be tested independently. The transport is wrapped in a recorder so a
run can prove it performed only read-only methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from termivance.authorization import Authorization
from termivance.discovery import (
    DEFAULT_TTL_SECONDS,
    Snapshot,
    discover_live,
    graph_from_snapshot,
    load_snapshot,
)
from termivance.engine import Decision, evaluate
from termivance.gitlab_client import (
    GitLabClient,
    RecordingTransport,
    UrllibTransport,
    load_local_token,
)
from termivance.graph import Graph
from termivance.policy import Policy, load_policy
from termivance.target import TargetIdentity

DEFAULT_POLICY_PATH = "config/retirement_policy.example.json"
DEFAULT_KIND = "GITLAB_PAGES_SITE"
CANONICAL_PROJECT_ID = 87779099


@dataclass(slots=True)
class LiveRun:
    snapshot: Snapshot
    transport: RecordingTransport

    def methods_used(self) -> set[str]:
        return self.transport.methods_used()

    def non_read_only_calls(self) -> list[str]:
        return [c.method for c in self.transport.calls if c.method.upper() != "GET"]


def resolve_target(
    client: GitLabClient, project_id: int, kind: str = DEFAULT_KIND
) -> TargetIdentity:
    """Resolve a project's exact full path read-only, then build the target."""
    result = client.get_json(f"/projects/{project_id}")
    if not result.ok or not isinstance(result.data, dict):
        raise RuntimeError(f"cannot resolve project {project_id}: {result.error_text()}")
    full_path = str(result.data.get("path_with_namespace") or "")
    if not full_path:
        raise RuntimeError(f"project {project_id} has no path_with_namespace")
    return TargetIdentity(project_id, full_path, kind)


def live_run(
    project_id: int,
    *,
    kind: str = DEFAULT_KIND,
    now: datetime | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    anonymous: bool = False,
) -> LiveRun:
    """Perform a live, read-only discovery run for one project.

    ``anonymous=True`` never sends a token: only public reads happen and every
    observation carries the honest error kinds (mostly 403) that anonymous
    access produces. The recording transport still proves GET-only behaviour.
    """
    if anonymous:
        token = None
    else:
        token = load_local_token()
    transport = RecordingTransport(inner=UrllibTransport())
    client = GitLabClient(token, transport=transport)
    target = resolve_target(client, project_id, kind)
    snapshot = discover_live(client, target, now=now, ttl_seconds=ttl_seconds)
    return LiveRun(snapshot=snapshot, transport=transport)


def load_policy_file(path: str | Path | None = None) -> Policy:
    return load_policy(path or DEFAULT_POLICY_PATH)


def load_recorded(path: str | Path) -> Snapshot:
    return load_snapshot(path)


def decide(
    snapshot: Snapshot,
    policy: Policy,
    *,
    now: datetime | None = None,
    authorization: Authorization | None = None,
) -> tuple[Decision, Graph]:
    graph = graph_from_snapshot(snapshot)
    decision = evaluate(
        graph,
        policy=policy,
        action=snapshot.action,
        now=now or datetime.now(tz=UTC),
        authorization=authorization,
    )
    return decision, graph
