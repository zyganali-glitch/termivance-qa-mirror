#!/usr/bin/env python3
"""Anonymous live refresh of the recorded B4 evidence artifacts.

Runs the full read-only capability chain against the *actual* GitLab endpoints
with no credential (``GitLabClient(None)``):

1. ``snapshot.json``        — discovery observation record for the one approved
                              disposable target ``87785099`` (graph evidence);
2. ``decision.json``        — the deterministic engine verdict from that graph;
3. ``portfolio.json``       — v2 multi-resource portfolio for the four
                              explicitly selected project ids;
4. ``risk_map.json``        — risk map built from the *same* decision record,
                              with cross-resource nodes/edges from the *same*
                              portfolio snapshot;
5. ``simulation.json``      — hypothetical analysis reusing the same cross view;
6. ``workflow_assessment.json`` — shipped-plan posture assessment.

Every artifact embeds its provenance label (``ANONYMOUS_PUBLIC_READ``),
observation timestamps and freshness. 401/403/404 responses are recorded as
``NOT_OBSERVED`` facts — never absence, never presence. The script performs no
mutation of any kind and never touches a secret: it is anonymous and read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Explicitly selected project ids only — no recursive discovery, no surprises.
DISPOSABLE = 87785099  # the sole approved destructive demo target
CANONICAL = 87779099  # protected: never touched by mutation paths
SHOWCASE = 87777871  # protected
DIAGNOSTIC = 87786164  # protected
PROJECT_IDS = [DISPOSABLE, CANONICAL, SHOWCASE, DIAGNOSTIC]


def _write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    print(f"  wrote {path.name}  sha256={digest[:16]}…")


def main() -> int:  # type: ignore[no-untyped-def]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(ROOT / "evidence" / "b4"))
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    from termivance.dependencies import cross_resource_view
    from termivance.discovery import discover_live, graph_from_snapshot
    from termivance.engine import evaluate
    from termivance.gitlab_client import GitLabClient
    from termivance.policy import load_policy
    from termivance.portfolio import observe_portfolio
    from termivance.riskmap import risk_map_from_record
    from termivance.simulation import simulate_retirement
    from termivance.target import TargetIdentity
    from termivance.workflow import assess, plan

    client = GitLabClient(None)
    policy = load_policy(str(ROOT / "config" / "retirement_policy.b3_disposable.json"))
    observed = datetime.now(tz=UTC)

    target = TargetIdentity(
        DISPOSABLE,
        "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
        "GITLAB_PAGES_SITE",
    )
    print("1/6 discovery snapshot (anonymous) …")
    snapshot = discover_live(client, target, now=observed)
    _write(out_dir / "snapshot.json", snapshot.to_dict())

    print("2/6 deterministic decision …")
    graph = graph_from_snapshot(snapshot)
    decision = evaluate(graph, policy=policy, action="unpublish_pages", now=observed)
    _write(out_dir / "decision.json", decision.to_dict(graph=graph))

    print("3/6 multi-resource portfolio (four explicitly selected ids) …")
    portfolio = observe_portfolio(
        client,
        PROJECT_IDS,
        policy=policy,
        now=observed,
    )
    _write(out_dir / "portfolio.json", portfolio.to_dict())

    print("4/6 risk map (same decision, same portfolio evidence) …")
    view = cross_resource_view(portfolio)
    risk_map = risk_map_from_record(
        decision.to_dict(graph=graph),
        cross_nodes=view.as_risk_nodes(target.to_dict()),
        cross_edges=view.as_risk_edges(),
    )
    _write(out_dir / "risk_map.json", risk_map.to_dict())

    print("5/6 simulation (same cross view) …")
    simulation = simulate_retirement(graph, policy=policy, now=observed, cross=view)
    sim_payload = simulation.to_dict()
    sim_payload["target_project_id"] = DISPOSABLE
    _write(out_dir / "simulation.json", sim_payload)

    print("6/6 workflow assessment …")
    artifact_paths: dict[str, Path] = {
        "decision": out_dir / "decision.json",
        "snapshot": out_dir / "snapshot.json",
        "portfolio": out_dir / "portfolio.json",
        "risk_map": out_dir / "risk_map.json",
        "simulation": out_dir / "simulation.json",
    }
    shipping_plan = plan(
        project_id=DISPOSABLE,
        full_path=target.full_path,
        out_dir=str(out_dir),
    )
    assessment = assess(artifact_paths, shipping_plan)
    _write(out_dir / "workflow_assessment.json", dict(assessment))  # type: ignore[arg-type]

    print("done — all reads anonymous; zero mutations; zero spend")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
