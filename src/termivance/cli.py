"""Termivance deterministic CLI.

Read-only by default. The evaluator path can only perform ``GET`` requests; the
only writing command is ``demo-blocked --issue`` which publishes a report and is
kept separate from evaluation.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections.abc import Sequence

from termivance import __version__
from termivance.engine import Decision
from termivance.policy import PolicyError, load_policy
from termivance.report import render_decision_report

CANONICAL_URL = "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance"

#: Disposable B3 retirement demonstration target (never the canonical project).
DISPOSABLE_PAGES_PROJECT_ID = 87785099

#: Truthful local snapshot. Live GitLab state is verified separately (docs/).
STATUS = {
    "product": "Termivance",
    "source": "local_snapshot_not_live",
    "remote": CANONICAL_URL,
    "ci": "NOT_VERIFIED_LOCALLY",
    "duo_flow": "DEPLOYED item 1018562",
    "duo_session": "9650440 FINISHED (B1)",
    "retirement": "B3_ENGINE_READY; B3_UNPUBLISH_NOT_RUN",
    "disposable_pages_project": DISPOSABLE_PAGES_PROJECT_ID,
}


def _emit(payload: dict[str, object], as_json: bool, human: str) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True) if as_json else human)


def _cmd_version() -> int:
    print(__version__)
    return 0


def _cmd_status(as_json: bool) -> int:
    payload = {"version": __version__, **STATUS}
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Termivance {__version__} - deterministic retirement engine (read-only)")
        print(f"source={STATUS['source']} remote={STATUS['remote']}")
        print(
            f"ci={STATUS['ci']}  Duo={STATUS['duo_flow']}  "
            f"session={STATUS['duo_session']}  retirement={STATUS['retirement']}"
        )
    return 0


def _cmd_policy_check(path: str, as_json: bool) -> int:
    try:
        policy = load_policy(path)
    except PolicyError as exc:
        print(f"policy-error: {exc}", file=sys.stderr)
        return 2
    result = {
        "mode": policy.mode,
        "mutation_enabled": policy.mutation_enabled,
        "authorization_required": policy.authorization_required,
        "targets": list(policy.allowed_target_project_ids),
        "actions": list(policy.allowed_actions),
        "safe_read_only": not policy.mutation_enabled,
    }
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        state = "DISABLED" if not policy.mutation_enabled else "ENABLED"
        print(f"policy mode={policy.mode} mutation={state} targets={len(result['targets'])}")
    return 0 if not policy.mutation_enabled else 3


def _cmd_doctor(as_json: bool) -> int:
    checks = {
        "python": platform.python_version(),
        "python_ok": sys.version_info >= (3, 12),
        "platform": platform.platform(),
        "package_version": __version__,
    }
    if as_json:
        print(json.dumps(checks, indent=2, sort_keys=True))
    else:
        print(f"python={checks['python']} ok={checks['python_ok']} version={__version__}")
    return 0 if checks["python_ok"] else 1


def _cmd_discover(args: argparse.Namespace) -> int:
    from termivance.discovery import graph_from_snapshot, save_snapshot
    from termivance.runtime import live_run

    run = live_run(args.project_id, kind=args.kind)
    snapshot = run.snapshot
    if args.save:
        save_snapshot(snapshot, args.save)
    graph = graph_from_snapshot(snapshot)
    if args.json:
        print(graph.to_json())
    else:
        print(
            f"discovered project {snapshot.target.project_id} "
            f"{snapshot.target.full_path} ({snapshot.target.resource_kind})"
        )
        print(f"classification={snapshot.classification.value} records={len(snapshot.records)}")
        print(f"read_only_methods={sorted(run.methods_used())}")
        print(f"nodes: obligations={len(graph.obligations)} evidence={len(graph.evidence)}")
        if args.save:
            print(f"saved snapshot: {args.save}")
    return 0


def _cmd_evaluate(args: argparse.Namespace) -> int:
    from termivance.discovery import load_snapshot
    from termivance.runtime import decide, load_policy_file

    if args.from_record:
        snapshot = load_snapshot(args.from_record)
    else:
        from termivance.runtime import live_run

        snapshot = live_run(args.project_id, kind=args.kind).snapshot
    decision, graph = decide(snapshot, load_policy_file(args.policy))
    payload = decision.to_dict(graph=graph)
    payload["evidence_classification"] = snapshot.classification.value
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_decision(decision)
    return 0


def _print_decision(decision: Decision) -> None:
    print(f"target={decision.target.project_id} {decision.target.full_path}")
    print(
        f"action={decision.action} verdict={decision.verdict.value} read_only={decision.read_only}"
    )
    for reason in decision.reasons:
        print(f"  - {reason.code.value}: {reason.detail}")


def _cmd_demo_blocked(args: argparse.Namespace) -> int:
    from termivance.discovery import load_snapshot
    from termivance.runtime import CANONICAL_PROJECT_ID, decide, live_run, load_policy_file

    if args.from_record:
        snapshot = load_snapshot(args.from_record)
    else:
        snapshot = live_run(CANONICAL_PROJECT_ID, kind="GITLAB_PAGES_SITE").snapshot
    decision, graph = decide(snapshot, load_policy_file(args.policy))
    payload = decision.to_dict(graph=graph)
    payload["evidence_classification"] = snapshot.classification.value
    payload["scenario"] = "canonical_project_as_protected_negative_control"

    if args.issue:
        from termivance.gitlab_client import load_local_token
        from termivance.publish import GitLabPublisher

        body = render_decision_report(decision, snapshot, list(graph.evidence.values()))
        publisher = GitLabPublisher(load_local_token())
        result = publisher.create_issue(
            snapshot.target.project_id,
            title="B2 retirement decision: BLOCKED (deterministic, read-only)",
            description=body,
            labels="termivance::b2,retirement-decision",
        )
        if result.ok and isinstance(result.data, dict):
            payload["published_issue_url"] = result.data.get("web_url")
            payload["published_issue_iid"] = result.data.get("iid")
        else:
            payload["publish_error"] = result.error or f"HTTP {result.status}"

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_decision_report(decision, snapshot, list(graph.evidence.values())))
        print()
        if "published_issue_url" in payload:
            print(f"published issue: {payload['published_issue_url']}")
    return 0 if decision.verdict.value == "BLOCKED" else 1


def _resolve_target(project_id: int, kind: str):
    from termivance.gitlab_client import GitLabClient, load_local_token
    from termivance.runtime import resolve_target

    return resolve_target(GitLabClient(load_local_token()), project_id, kind)


def _cmd_pages_state(args: argparse.Namespace) -> int:
    from termivance.gitlab_client import GitLabClient, load_local_token
    from termivance.pages import read_pages_state

    target = _resolve_target(args.project_id, "GITLAB_PAGES_SITE")
    client = GitLabClient(load_local_token())
    state = read_pages_state(client, target)
    if args.json:
        print(json.dumps(state.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"pages target={target.project_id} {target.full_path}")
        print(f"api_status={state.status} error={state.error_kind} present={state.present}")
        print(f"url={state.url}")
    return 0 if state.accessible else 2


def _cmd_observe_absence(args: argparse.Namespace) -> int:
    import json as _json

    from termivance.absence import observe_absence
    from termivance.evidence import PagesPreState
    from termivance.gitlab_client import GitLabClient, load_local_token

    target = _resolve_target(args.project_id, "GITLAB_PAGES_SITE")
    client = GitLabClient(load_local_token())
    pre_state = None
    if args.pre_state:
        with open(args.pre_state, encoding="utf-8") as handle:
            pre_state = PagesPreState.from_dict(_json.load(handle))
    probe = observe_absence(
        client,
        target,
        args.url,
        pre_state=pre_state,
        action_accepted=bool(args.action_accepted),
        action_endpoint=args.action_endpoint,
    )
    if args.json:
        print(json.dumps(probe.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"target={target.project_id} {target.full_path}")
        print(f"pages_api={probe.pages_api_status} ({probe.pages_api_error})")
        print(f"served_url={args.url} http={probe.served_http_status}")
        for note in probe.notes:
            print(f"note: {note}")
        print(f"verdict={probe.verdict.value}")
    return 0 if probe.verdict.value == "OBSERVED_ABSENT" else 1


def _cmd_verify_publication(args: argparse.Namespace) -> int:
    from termivance.absence import publication_pre_state
    from termivance.gitlab_client import GitLabClient, load_local_token
    from termivance.pages import observe_publication

    target = _resolve_target(args.project_id, "GITLAB_PAGES_SITE")
    client = GitLabClient(load_local_token())
    probe = observe_publication(client, target, args.url, args.marker)
    payload = probe.to_dict()
    payload["pre_state"] = publication_pre_state(probe).to_dict()
    if args.json_out:
        from pathlib import Path

        Path(args.json_out).write_text(
            json.dumps(payload["pre_state"], indent=2, sort_keys=True), encoding="utf-8"
        )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"target={target.project_id} {target.full_path}")
        print(
            f"pages_api={probe.api_status} ({probe.api_error}) deployments={probe.deployment_count}"
        )
        print(f"served_url={probe.served_url} http={probe.http_status}")
        print(f"marker_observed={probe.marker_observed}")
        print(f"genuinely_published={probe.genuinely_published}")
    return 0 if probe.genuinely_published else 1


def _cmd_retire_pages(args: argparse.Namespace) -> int:
    import os

    from termivance.attestation import ControlAttestation
    from termivance.authorization import APPROVAL_KEY_ENV, load_authorization
    from termivance.discovery import load_snapshot
    from termivance.gitlab_client import GitLabClient, load_local_token
    from termivance.ledger import AuthorizationLedger
    from termivance.pages import PagesMutationClient
    from termivance.retirement import retire_pages
    from termivance.runtime import load_policy_file

    # A recorded snapshot already carries the exact bound target, so a replay
    # needs no provider access at all. A live run always resolves the target from
    # the provider itself: the identity is never taken from local input.
    snapshot = load_snapshot(args.from_record) if args.from_record else None
    live_run = args.execute or snapshot is None
    token = load_local_token() if live_run else None
    if not live_run and snapshot is not None and snapshot.target.project_id == args.project_id:
        target = snapshot.target
    else:
        target = _resolve_target(args.project_id, "GITLAB_PAGES_SITE")

    policy = load_policy_file(args.policy)
    approval_key = os.environ.get(APPROVAL_KEY_ENV) or None
    authorization = (
        load_authorization(args.authorization, approval_key=approval_key)
        if args.authorization
        else None
    )
    control_attestation = None
    if args.control_attestation:
        with open(args.control_attestation, encoding="utf-8") as handle:
            control_attestation = ControlAttestation.from_dict(json.load(handle))
        control_attestation.verify(target, key=approval_key)
    ledger = AuthorizationLedger(args.ledger) if args.ledger else None
    if args.execute and not token:
        print("refusing --execute: no local GitLab token is available", file=sys.stderr)
        return 2
    mutation_client = PagesMutationClient(token) if (args.execute and token) else None
    read_client = GitLabClient(token) if (live_run and token) else None
    receipt = retire_pages(
        target,
        policy,
        authorization,
        mutation_client=mutation_client,
        read_client=read_client,
        snapshot=snapshot,
        served_url=args.url,
        marker=args.marker,
        control_attestation=control_attestation,
        ledger=ledger,
        approval_key=approval_key,
    )
    payload = receipt.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"target={target.project_id} {target.full_path} action={receipt.action}")
        print(
            f"preflight_ok={receipt.preflight.ok} mutation_attempted={receipt.mutation_attempted}"
        )
        for check in receipt.preflight.checks:
            print(f"  - {check['check']}: {check['ok']} ({check['detail']})")
        if receipt.eligibility is not None:
            print(
                f"decision={receipt.eligibility.decision.verdict.value} "
                f"snapshot_digest={receipt.eligibility.snapshot_digest[:16]}…"
            )
            for obligation in receipt.eligibility.decision.obligations:
                print(f"  - {obligation['kind']}: {obligation['status']}")
        for note in receipt.notes:
            print(f"note: {note}")
        if receipt.mutation is not None:
            print(f"mutation HTTP {receipt.mutation.status} accepted={receipt.mutation.accepted}")
        if receipt.absence is not None:
            print(
                f"read-back: pages_api={receipt.absence.pages_api_status} "
                f"served={receipt.absence.served_http_status}"
            )
        print(f"verdict={receipt.verdict.value}")
        if not args.execute:
            print("(dry run: no mutation performed; pass --execute to attempt the real call)")
    return 0 if receipt.verdict.value in {"SAFE_TO_RETIRE", "OBSERVED_ABSENT", "RETIRED"} else 1


def _cmd_provision_pages(args: argparse.Namespace) -> int:
    from termivance.gitlab_client import load_local_token
    from termivance.provision import create_disposable_project, site_files

    project = create_disposable_project(
        load_local_token(),
        namespace_id=args.namespace_id,
        name=args.name,
        path=args.path,
        description=args.description,
    )
    payload = project.to_dict()
    payload["site_files"] = sorted(site_files())
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"created disposable project {project.project_id} {project.full_path}")
        print(f"web_url={project.web_url}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="termivance",
        description="Proof-bounded software retirement (B2 read-only decision engine).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="print the package version")

    status = sub.add_parser("status", help="print the local status snapshot")
    status.add_argument("--json", action="store_true", help="emit JSON")

    policy_check = sub.add_parser("policy-check", help="validate a policy file (fail closed)")
    policy_check.add_argument("path", help="path to a retirement policy JSON file")
    policy_check.add_argument("--json", action="store_true", help="emit JSON")

    doctor = sub.add_parser("doctor", help="report environment sanity checks")
    doctor.add_argument("--json", action="store_true", help="emit JSON")

    discover = sub.add_parser("discover", help="read-only GitLab discovery for a project")
    discover.add_argument("--project-id", type=int, required=True)
    discover.add_argument("--kind", default="GITLAB_PAGES_SITE")
    discover.add_argument("--save", default=None, help="save the raw snapshot JSON")
    discover.add_argument("--json", action="store_true")

    evaluate = sub.add_parser("evaluate", help="deterministic retirement decision")
    evaluate.add_argument("--project-id", type=int, default=0)
    evaluate.add_argument("--kind", default="GITLAB_PAGES_SITE")
    evaluate.add_argument("--from-record", default=None, help="replay a recorded snapshot")
    evaluate.add_argument("--policy", default=None)
    evaluate.add_argument("--json", action="store_true")

    demo = sub.add_parser("demo-blocked", help="canonical blocked negative-control scenario")
    demo.add_argument("--from-record", default=None, help="replay a recorded snapshot")
    demo.add_argument("--policy", default=None)
    demo.add_argument("--issue", action="store_true", help="publish the report as an issue")
    demo.add_argument("--json", action="store_true")

    pages_state = sub.add_parser("pages-state", help="read-only GitLab Pages state")
    pages_state.add_argument("--project-id", type=int, required=True)
    pages_state.add_argument("--json", action="store_true")

    absence = sub.add_parser("observe-absence", help="independent bounded-absence read-back")
    absence.add_argument("--project-id", type=int, required=True)
    absence.add_argument("--url", required=True, help="exact previously-served Pages URL")
    absence.add_argument(
        "--pre-state",
        default=None,
        help="recorded pre-retirement publication proof (required to claim OBSERVED_ABSENT)",
    )
    absence.add_argument("--action-endpoint", default=None)
    absence.add_argument("--action-accepted", action="store_true")
    absence.add_argument("--json", action="store_true")

    publication = sub.add_parser(
        "verify-publication", help="prove a Pages site is genuinely published before retiring it"
    )
    publication.add_argument("--project-id", type=int, required=True)
    publication.add_argument("--url", required=True, help="exact served Pages URL")
    publication.add_argument("--marker", required=True, help="distinctive content marker")
    publication.add_argument("--json-out", default=None, help="write the pre-state record")
    publication.add_argument("--json", action="store_true")

    retire = sub.add_parser(
        "retire-pages", help="authorized Pages unpublish (dry run unless --execute)"
    )
    retire.add_argument("--project-id", type=int, required=True)
    retire.add_argument("--url", default=None, help="exact served URL for read-back")
    retire.add_argument("--marker", default=None, help="distinctive content marker")
    retire.add_argument("--policy", default=None)
    retire.add_argument("--authorization", default=None, help="operator authorization JSON")
    retire.add_argument(
        "--control-attestation",
        default=None,
        help="operator-supplied redeployment-control attestation JSON",
    )
    retire.add_argument(
        "--ledger", default=None, help="durable single-use authorization ledger path"
    )
    retire.add_argument("--from-record", default=None, help="replay a recorded snapshot")
    retire.add_argument("--execute", action="store_true", help="attempt the real DELETE call")
    retire.add_argument("--json", action="store_true")

    provision = sub.add_parser("provision-pages", help="create a disposable Pages project")
    provision.add_argument("--namespace-id", type=int, required=True)
    provision.add_argument("--name", required=True)
    provision.add_argument("--path", required=True)
    provision.add_argument("--description", default="Disposable Termivance B3 Pages demo target")
    provision.add_argument("--json", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "version":
        return _cmd_version()
    if args.command == "status":
        return _cmd_status(args.json)
    if args.command == "policy-check":
        return _cmd_policy_check(args.path, args.json)
    if args.command == "doctor":
        return _cmd_doctor(args.json)
    if args.command == "discover":
        return _cmd_discover(args)
    if args.command == "evaluate":
        return _cmd_evaluate(args)
    if args.command == "demo-blocked":
        return _cmd_demo_blocked(args)
    if args.command == "pages-state":
        return _cmd_pages_state(args)
    if args.command == "observe-absence":
        return _cmd_observe_absence(args)
    if args.command == "verify-publication":
        return _cmd_verify_publication(args)
    if args.command == "retire-pages":
        return _cmd_retire_pages(args)
    if args.command == "provision-pages":
        return _cmd_provision_pages(args)
    return 1  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
