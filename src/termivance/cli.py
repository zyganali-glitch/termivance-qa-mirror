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
from datetime import datetime
from pathlib import Path

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

    run = live_run(args.project_id, kind=args.kind, anonymous=args.anonymous)
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


def _resolve_target(project_id: int, kind: str, *, anonymous: bool = False):
    from termivance.gitlab_client import GitLabClient, load_local_token
    from termivance.runtime import resolve_target

    if anonymous:
        return resolve_target(GitLabClient(None), project_id, kind)
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
    from termivance.capsule import ReceiptValidationError, validate_mutation_receipt
    from termivance.evidence import PagesPreState
    from termivance.gitlab_client import GitLabClient, load_local_token
    from termivance.ledger import AuthorizationLedger

    target = _resolve_target(args.project_id, "GITLAB_PAGES_SITE")
    client = GitLabClient(load_local_token())
    pre_state = None
    if args.pre_state:
        with open(args.pre_state, encoding="utf-8") as handle:
            pre_state = PagesPreState.from_dict(_json.load(handle))
    receipt_binding = None
    if args.receipt:
        if not args.ledger:
            print(
                "refusing: --receipt also requires --ledger; a durable, sealed "
                "operation record is mandatory to bind an absence claim (P0-C)",
                file=sys.stderr,
            )
            return 2
        with open(args.receipt, encoding="utf-8") as handle:
            receipt_data = _json.load(handle)
        try:
            receipt_binding = validate_mutation_receipt(
                receipt_data, target, ledger=AuthorizationLedger(args.ledger)
            )
        except ReceiptValidationError as exc:
            print(f"receipt refused: {exc}", file=sys.stderr)
            return 2
    probe = observe_absence(
        client,
        target,
        args.url,
        pre_state=pre_state,
        mutation_receipt=receipt_binding,
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


def _cmd_approval_template(args: argparse.Namespace) -> int:
    import os

    from termivance.approval_source import approval_statement_template
    from termivance.authorization import APPROVAL_KEY_ENV, load_authorization

    approval_key = os.environ.get(APPROVAL_KEY_ENV) or None
    authorization = load_authorization(
        args.authorization, approval_key=approval_key, require_approval=False
    )
    print(approval_statement_template(authorization))
    print()
    print(
        "next step (operator, in the GitLab web UI): create a NEW issue in project "
        f"{authorization.target.project_id}, paste the statement above as the issue "
        "description, keep the issue OPEN; verify with "
        f"--approval-project-id {authorization.target.project_id} --approval-issue-iid <iid>"
    )
    return 0


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
    operator_trust = None
    trust_path = getattr(args, "operator_trust", None)
    if trust_path:
        from termivance.approval_source import load_operator_trust

        operator_trust = load_operator_trust(trust_path)
    elif args.execute:
        from termivance.approval_source import TRUST_SCHEMA

        print(
            "refusing --execute: an independent operator trust policy is required "
            f"for a real mutation (pass --operator-trust PATH pointing at a "
            f"{TRUST_SCHEMA} document)",
            file=sys.stderr,
        )
        return 2
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
        approval_project_id=args.approval_project_id,
        approval_issue_iid=args.approval_issue_iid,
        operator_trust=operator_trust,
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


def _read_json(path: str | None) -> dict[str, object] | None:
    if path is None:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_out(payload: object, out: str | None, plain: str) -> None:
    if out:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"saved: {path}")
    if not out:
        print(plain)


def _cmd_portfolio(args: argparse.Namespace) -> int:
    from termivance.gitlab_client import GitLabClient, TokenUnavailable, load_local_token
    from termivance.policy import load_policy
    from termivance.portfolio import observe_portfolio

    if args.anonymous:
        client = GitLabClient(None)
    else:
        try:
            client = GitLabClient(load_local_token())
        except TokenUnavailable as exc:
            print(f"no GitLab token ({exc}); use --anonymous for public reads", file=sys.stderr)
            return 2
    policy = load_policy(args.policy) if args.policy else None
    ids = [int(x) for x in str(args.project_ids).split(",") if x.strip()]
    snapshot = observe_portfolio(client, ids, policy=policy)
    payload = snapshot.to_dict()
    if args.out:
        _write_out(payload, args.out, "")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(snapshot.render())
    return 0 if all(asset.ok for asset in snapshot.assets) else 1


def _cmd_risk_map(args: argparse.Namespace) -> int:
    from termivance.riskmap import risk_map_from_record

    decision = _read_json(args.decision)
    if decision is None:
        print("--decision is required", file=sys.stderr)
        return 2
    cross_nodes, cross_edges = (), ()
    portfolio_path = getattr(args, "portfolio", None)
    if portfolio_path:
        from termivance.dependencies import cross_resource_view
        from termivance.portfolio import portfolio_from_data

        portfolio_data = _read_json(portfolio_path)
        if portfolio_data is None:
            print(f"portfolio snapshot unreadable: {portfolio_path}", file=sys.stderr)
            return 2
        view = cross_resource_view(portfolio_from_data(portfolio_data))
        cross_nodes = view.as_risk_nodes(decision.get("target") or {})
        cross_edges = view.as_risk_edges()
    try:
        risk_map = risk_map_from_record(decision, cross_nodes=cross_nodes, cross_edges=cross_edges)
    except ValueError as exc:
        print(f"decision record unusable: {exc}", file=sys.stderr)
        return 2
    payload = risk_map.to_dict()
    if args.out:
        _write_out(payload, args.out, "")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(risk_map.render())
    return 0


def _cmd_simulate(args: argparse.Namespace) -> int:
    from termivance.discovery import discover_live, graph_from_snapshot, load_snapshot
    from termivance.gitlab_client import GitLabClient, TokenUnavailable, load_local_token
    from termivance.policy import load_policy
    from termivance.simulation import simulate_retirement

    policy = load_policy(args.policy) if args.policy else None
    if args.from_record:
        snapshot = load_snapshot(args.from_record)
        graph = graph_from_snapshot(snapshot)
    else:
        if args.anonymous:
            client = GitLabClient(None)
        else:
            try:
                client = GitLabClient(load_local_token())
            except TokenUnavailable as exc:
                print(f"no GitLab token ({exc}); use --from-record or --anonymous", file=sys.stderr)
                return 2
        from termivance.discovery import discover_live

        target = _resolve_target(args.project_id, "GITLAB_PAGES_SITE")
        snapshot = discover_live(client, target)
        graph = graph_from_snapshot(snapshot)
    policy = policy or load_policy("config/retirement_policy.b3_disposable.json")
    cross = None
    portfolio_path = getattr(args, "portfolio", None)
    if portfolio_path:
        from termivance.dependencies import cross_resource_view
        from termivance.portfolio import portfolio_from_data

        portfolio_data = _read_json(portfolio_path)
        if portfolio_data is None:
            print(f"portfolio snapshot unreadable: {portfolio_path}", file=sys.stderr)
            return 2
        cross = cross_resource_view(portfolio_from_data(portfolio_data))
    result = simulate_retirement(graph, policy=policy, cross=cross)
    payload = result.to_dict()
    payload["target_project_id"] = args.project_id
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(result.render())
    return 0


def _cmd_reconcile_duo(args: argparse.Namespace) -> int:
    from termivance.duo_reconciliation import (
        ReconciliationError,
        load_claims,
        observe_duo_surface,
        probe_web_status,
        reconcile_duo,
    )
    from termivance.gitlab_client import GitLabClient

    try:
        claims_data, claims = load_claims(args.claims)
    except ReconciliationError as exc:
        print(f"claims record unusable: {exc}", file=sys.stderr)
        return 2
    # Reconciliation is anonymous by construction: the Duo evidence surface is
    # public, and no credential may ever enter this read-only path.
    client = GitLabClient(None)
    surface = observe_duo_surface(
        client,
        project_id=args.project_id,
        issue_iid=args.issue_iid,
        session_url=args.session_url or "",
        web_probe=probe_web_status,
    )
    reconciliation = reconcile_duo(
        claims_data,
        claims,
        surface,
        claims_source=args.claims,
        ttl_seconds=args.ttl,
    )
    payload = reconciliation.to_dict()
    if args.out:
        _write_out(payload, args.out, "")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(reconciliation.render())
    return 0


def _cmd_witness_build(args: argparse.Namespace) -> int:
    from termivance.gitlab_client import GitLabClient
    from termivance.target import TargetIdentity
    from termivance.witness import build_witness

    client = GitLabClient(None)
    full_path = args.full_path
    if not full_path:
        project = client.get_json(f"/projects/{args.project_id}")
        if project.ok and isinstance(project.data, dict):
            full_path = str(project.data.get("path_with_namespace") or "")
        if not full_path:
            print(
                "could not resolve the project full path anonymously; pass --full-path",
                file=sys.stderr,
            )
            return 2
    target = TargetIdentity(args.project_id, full_path, args.kind)
    witness = build_witness(client, target)
    payload = witness.to_dict()
    if args.out:
        _write_out(payload, args.out, "")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(witness.render())
    return 0


def _cmd_supervised_review(args: argparse.Namespace) -> int:
    if getattr(args, "execute", False):
        from termivance.gitlab_client import GitLabClient, load_local_token
        from termivance.publish import GitLabPublisher
        from termivance.supervised_review import run_supervised_investigation
        from termivance.target import TargetIdentity

        target = TargetIdentity(args.project_id, args.full_path, "GITLAB_PAGES_SITE")
        client = GitLabClient(None)
        publisher = None
        if getattr(args, "publish", False):
            try:
                publisher = GitLabPublisher(load_local_token())
            except Exception:
                pass
        review = run_supervised_investigation(
            client=client,
            publisher=publisher,
            target=target,
            policy_path=getattr(args, "policy", None),
            duo_claims_path=args.duo_claims,
            issue_iid=getattr(args, "issue_iid", None),
            publish_outcome=getattr(args, "publish", False),
            out_dir=getattr(args, "out_dir", None) or (Path(args.out).parent if args.out else None),
        )
    else:
        from termivance.supervised_review import build_supervised_review

        review = build_supervised_review(
            duo_claims_path=args.duo_claims,
            duo_reconciliation_path=args.duo_reconciliation,
            witness_path=args.witness,
            decision_path=args.decision,
            risk_map_path=args.risk_map,
            capsule_path=args.capsule,
            target_project_id=args.project_id,
            target_full_path=args.full_path,
        )
    payload = review.to_dict()
    if args.out:
        _write_out(payload, args.out, "")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(review.render())
    return 0


def _cmd_capsule_build(args: argparse.Namespace) -> int:
    from termivance.capsule import build_capsule, save_capsule
    from termivance.target import TargetIdentity

    receipt = _read_json(args.receipt)
    decision = _read_json(args.decision)
    if receipt is not None:
        target_data = receipt.get("target")
    elif decision is not None:
        # Honest no-mutation-yet capsule: assembled from the recorded BLOCKED
        # decision; no mutation/absence section can exist without a real receipt.
        target_data = {
            "project_id": args.target_project_id,
            "full_path": args.target_full_path,
            "resource_kind": args.target_kind,
        }
    else:
        print(
            "--receipt is required, or --decision with --target-* flags to "
            "assemble a no-mutation-yet capsule over recorded BLOCKED evidence",
            file=sys.stderr,
        )
        return 2
    if not isinstance(target_data, dict):
        print("receipt or decision carries no usable target", file=sys.stderr)
        return 2
    target = TargetIdentity.from_dict(target_data)
    mutation = (
        receipt.get("mutation")
        if (receipt is not None and isinstance(receipt.get("mutation"), dict))
        else None
    )
    # Authorization provenance: read back the approval checks recorded in the
    # receipt's preflight (never invented here).
    preflight_data = receipt.get("preflight") if receipt is not None else None
    authorization_section: dict[str, object] | None = None
    if isinstance(preflight_data, dict):
        checks = preflight_data.get("checks")
        if isinstance(checks, list):
            authorization_section = {
                "present": True,
                "binding": receipt.get("authorization_binding"),
                "approval_checks": [
                    {"check": c.get("check"), "ok": c.get("ok"), "detail": c.get("detail")}
                    for c in checks
                    if isinstance(c, dict)
                    and str(c.get("check"))
                    in {
                        "operator_approval_verified",
                        "approval_provenance_gitlab",
                        "gitlab_approval_record_verified",
                    }
                ],
            }
    notes = tuple(note.strip() for note in str(args.notes or "").split(";") if note.strip())
    duo_reconciliation = _read_json(getattr(args, "duo_reconciliation", None))
    if (
        duo_reconciliation is not None
        and duo_reconciliation.get("schema") != "termivance.duo_reconciliation/v1"
    ):
        print(
            "--duo-reconciliation must be a termivance.duo_reconciliation/v1 record",
            file=sys.stderr,
        )
        return 2
    witness = _read_json(getattr(args, "witness", None))
    if witness is not None:
        if witness.get("schema") != "termivance.resurrection_witness/v1":
            print(
                "--witness must be a termivance.resurrection_witness/v1 record",
                file=sys.stderr,
            )
            return 2
        witness_target = witness.get("target")
        if not isinstance(witness_target, dict) or (
            TargetIdentity.from_dict(witness_target).key() != target.key()
        ):
            print(
                "the witness record targets a different resource than the capsule; "
                "a capsule never adopts another target's witness",
                file=sys.stderr,
            )
            return 2
    if receipt is None:
        default_notes = (
            "no-mutation-yet capsule: assembled from a recorded deterministic "
            "decision only; no Pages unpublication is claimed",
            "mutation and absence sections are NOT_OBSERVED by design until a "
            "real authorized receipt exists",
        )
    else:
        default_notes = (
            "built from recorded artifacts only; no section was invented",
            "Pages unpublication claim status is carried verbatim from the receipt",
        )
    capsule = build_capsule(
        target=target,
        decision=decision,
        mutation=mutation,
        absence=None if receipt is None else _read_json(args.absence),
        authorization=authorization_section,
        duo_reconciliation=duo_reconciliation,
        witness=witness,
        notes=tuple(dict.fromkeys(notes + default_notes)),
    )
    path = save_capsule(capsule, args.out)
    if args.json:
        print(json.dumps({"saved": str(path), "manifest_digest": capsule["manifest_digest"]}))
    else:
        print(f"capsule saved: {path}")
        print(f"manifest: sha256 {capsule['manifest_digest'][:32]}…")
    return 0


def _cmd_capsule_verify(args: argparse.Namespace) -> int:
    from termivance.capsule import CapsuleError, load_capsule, verify_capsule

    try:
        capsule = load_capsule(args.path)
        report = verify_capsule(capsule)
    except (CapsuleError, KeyError, ValueError) as exc:
        print(f"CAPSULE INVALID: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("CAPSULE VALID (local integrity only — no GitLab re-observation)")
        print(f"manifest: sha256 {report['manifest_sha256'][:32]}…")
        print(f"sections: {', '.join(report['sections_verified'])}")
    return 0


def _cmd_capsule_render(args: argparse.Namespace) -> int:
    from termivance.capsule import load_capsule, render_capsule

    try:
        capsule = load_capsule(args.path)
    except (ValueError, KeyError) as exc:
        print(f"capsule unreadable: {exc}", file=sys.stderr)
        return 2
    print(render_capsule(capsule))
    return 0


def _cmd_workflow_plan(args: argparse.Namespace) -> int:
    from termivance.workflow import plan as build_plan

    plan_ = build_plan(project_id=args.project_id, full_path=args.full_path, out_dir=args.out_dir)
    payload = plan_.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(plan_.render())
    return 0


def _cmd_workflow_status(args: argparse.Namespace) -> int:
    from termivance.workflow import assess, render_assessment
    from termivance.workflow import plan as build_plan

    plan_ = build_plan(project_id=args.project_id, full_path=args.full_path, out_dir=args.out_dir)
    out_dir = Path(args.out_dir)
    artifacts = {
        "snapshot": out_dir / args.snapshot,
        "decision": out_dir / args.decision,
        "receipt": out_dir / args.receipt,
        "absence": out_dir / args.absence,
        "capsule": out_dir / args.capsule,
    }
    if args.authorization:
        artifacts["authorization"] = Path(args.authorization)
    if args.approval:
        artifacts["approval_issue"] = Path(args.approval)
    assessment = assess(artifacts, plan_)
    if args.out:
        _write_out(assessment, args.out, "")
    if args.json:
        print(json.dumps(assessment, indent=2, sort_keys=True))
    else:
        print(render_assessment(assessment))
    return 0


def _cmd_tripwire(args: argparse.Namespace) -> int:
    from termivance.target import TargetIdentity
    from termivance.tripwire import TripwireReading, check_tripwire

    def reading(path: str) -> TripwireReading:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return TripwireReading(
            target=TargetIdentity.from_dict(dict(data["target"])),
            served_url=str(data["served_url"]),
            publication_observed=bool(data["publication_observed"]),
            observed_at=datetime.fromisoformat(str(data["observed_at"])),
        )

    report = check_tripwire(reading(args.earlier), reading(args.later))
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(report.render())
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
    discover.add_argument("--anonymous", action="store_true", help="unauthenticated public reads")
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
        help="recorded pre-retirement publication proof (context only)",
    )
    absence.add_argument(
        "--receipt",
        default=None,
        help="recorded retirement receipt JSON binding the claim to the real mutation",
    )
    absence.add_argument(
        "--ledger",
        default=None,
        help="durable authorization ledger JSON (mandatory with --receipt)",
    )
    absence.add_argument("--json", action="store_true")

    approval_tpl = sub.add_parser(
        "approval-template",
        help="print the exact operator approval statement for a GitLab approval issue",
    )
    approval_tpl.add_argument("--authorization", required=True, help="authorization JSON")

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
    retire.add_argument("--approval-project-id", type=int, default=None)
    retire.add_argument("--approval-issue-iid", type=int, default=None)
    retire.add_argument(
        "--operator-trust",
        default=None,
        dest="operator_trust",
        help="path to the operator-owned trust policy "
        "(termivance.operator_trust/v1) required for --execute",
    )
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

    portfolio = sub.add_parser("portfolio", help="read-only multi-asset portfolio overview")
    portfolio.add_argument("--project-ids", required=True, help="comma-separated project ids")
    portfolio.add_argument("--policy", default=None, help="policy used only to label targets")
    portfolio.add_argument("--anonymous", action="store_true", help="unauthenticated public reads")
    portfolio.add_argument("--out", default=None, help="write the portfolio JSON record")
    portfolio.add_argument("--json", action="store_true")

    risk_map = sub.add_parser("risk-map", help="deterministic risk map for a recorded decision")
    risk_map.add_argument("--decision", required=True, help="recorded decision JSON")
    risk_map.add_argument(
        "--portfolio",
        default=None,
        help="observed portfolio snapshot JSON: its resource records are appended "
        "as cross-resource dependency/risk context (never decision facts)",
    )
    risk_map.add_argument("--out", default=None)
    risk_map.add_argument("--json", action="store_true")

    simulate = sub.add_parser(
        "simulate", help='hypothetical "what if we retire this?" analysis (never mutates)'
    )
    simulate.add_argument("--project-id", type=int, required=True)
    simulate.add_argument("--policy", default=None)
    simulate.add_argument("--from-record", default=None, help="recorded snapshot to analyze")
    simulate.add_argument("--anonymous", action="store_true", help="unauthenticated live reads")
    simulate.add_argument(
        "--portfolio",
        default=None,
        help="observed portfolio snapshot JSON: resource-level projection factors "
        "are appended from the same evidence (never observations)",
    )
    simulate.add_argument("--json", action="store_true")

    capsule_build = sub.add_parser(
        "capsule-build", help="assemble the tamper-evident proof capsule from recorded artifacts"
    )
    capsule_build.add_argument("--receipt", default=None, help="retirement receipt JSON")
    capsule_build.add_argument("--absence", default=None, help="recorded absence probe JSON")
    capsule_build.add_argument("--decision", default=None, help="recorded decision JSON")
    capsule_build.add_argument(
        "--target-project-id",
        type=int,
        default=None,
        help="with --decision: target identity for a no-mutation-yet capsule",
    )
    capsule_build.add_argument(
        "--target-full-path", default=None, help="with --decision: full path"
    )
    capsule_build.add_argument(
        "--target-kind",
        default="GITLAB_PAGES_SITE",
        help="resource kind for a no-mutation-yet capsule",
    )
    capsule_build.add_argument("--notes", default=None, help="semicolon-separated limitation notes")
    capsule_build.add_argument(
        "--duo-reconciliation",
        dest="duo_reconciliation",
        default=None,
        help="recorded termivance.duo_reconciliation/v1 record (embedded verbatim, "
        "always NON_AUTHORITATIVE)",
    )
    capsule_build.add_argument(
        "--witness",
        default=None,
        help="recorded termivance.resurrection_witness/v1 record for this exact target",
    )
    capsule_build.add_argument("--out", required=True)
    capsule_build.add_argument("--json", action="store_true")

    capsule_verify = sub.add_parser(
        "capsule-verify", help="integrity-verify a proof capsule (local check only)"
    )
    capsule_verify.add_argument("path", help="capsule JSON path")
    capsule_verify.add_argument("--json", action="store_true")

    capsule_render = sub.add_parser(
        "capsule-render", help="render a proof capsule as judge-facing text"
    )
    capsule_render.add_argument("path", help="capsule JSON path")

    workflow_plan = sub.add_parser("workflow-plan", help="the single-flow retirement stage plan")
    workflow_plan.add_argument("--project-id", type=int, required=True)
    workflow_plan.add_argument("--full-path", required=True)
    workflow_plan.add_argument("--out-dir", required=True)
    workflow_plan.add_argument("--json", action="store_true")

    workflow_status = sub.add_parser(
        "workflow-status", help="classify workflow stages from recorded artifacts"
    )
    workflow_status.add_argument("--project-id", type=int, required=True)
    workflow_status.add_argument("--full-path", required=True)
    workflow_status.add_argument("--out-dir", required=True)
    workflow_status.add_argument("--snapshot", default="snapshot.json")
    workflow_status.add_argument("--decision", default="decision.json")
    workflow_status.add_argument("--authorization", default=None)
    workflow_status.add_argument("--approval", default=None, help="JSON holding issue_iid")
    workflow_status.add_argument("--receipt", default="receipt.json")
    workflow_status.add_argument("--absence", default="absence.json")
    workflow_status.add_argument("--capsule", default="proof_capsule.json")
    workflow_status.add_argument(
        "--out", default=None, help="save the assessment JSON (beware: --out-dir also exists)"
    )
    workflow_status.add_argument("--json", action="store_true")

    tripwire = sub.add_parser(
        "tripwire-check", help="compare two recorded passes for resurrection (P2)"
    )
    tripwire.add_argument("--earlier", required=True, help="earlier tripwire reading JSON")
    tripwire.add_argument("--later", required=True, help="later tripwire reading JSON")
    tripwire.add_argument("--json", action="store_true")

    reconcile_duo = sub.add_parser(
        "reconcile-duo",
        help="reconcile recorded Duo candidate claims against anonymous read-only evidence",
    )
    reconcile_duo.add_argument(
        "--claims", required=True, help="termivance.duo_claims/v1 claims record"
    )
    reconcile_duo.add_argument("--project-id", type=int, required=True)
    reconcile_duo.add_argument("--issue-iid", type=int, required=True)
    reconcile_duo.add_argument(
        "--session-url", default=None, help="recorded agent-session UI URL (probed anonymously)"
    )
    reconcile_duo.add_argument(
        "--ttl", type=int, default=900, help="freshness window in seconds (default 900)"
    )
    reconcile_duo.add_argument("--out", default=None)
    reconcile_duo.add_argument("--json", action="store_true")

    witness_build = sub.add_parser(
        "witness-build",
        help="resurrection counterexample witness: the target's own CI config at "
        "the exact observed commit, plus its Pages administration surface",
    )
    witness_build.add_argument("--project-id", type=int, required=True)
    witness_build.add_argument(
        "--full-path", default=None, help="exact full path (resolved anonymously when omitted)"
    )
    witness_build.add_argument("--kind", default="GITLAB_PAGES_SITE")
    witness_build.add_argument("--out", default=None)
    witness_build.add_argument("--json", action="store_true")

    supervised_review = sub.add_parser(
        "supervised-review",
        help="build the evidence-bound supervised retirement review from "
        "recorded Duo claims, reconciliation, witness and decision artifacts",
    )
    supervised_review.add_argument(
        "--duo-claims",
        dest="duo_claims",
        default=None,
        help="recorded termivance.duo_claims/v1 record",
    )
    supervised_review.add_argument(
        "--duo-reconciliation",
        dest="duo_reconciliation",
        default=None,
        help="recorded termivance.duo_reconciliation/v1 record",
    )
    supervised_review.add_argument("--witness", default=None, help="resurrection witness record")
    supervised_review.add_argument("--decision", default=None, help="recorded decision JSON")
    supervised_review.add_argument("--risk-map", dest="risk_map", default=None)
    supervised_review.add_argument("--capsule", default=None, help="proof capsule JSON")
    supervised_review.add_argument("--project-id", type=int, default=87785099)
    supervised_review.add_argument(
        "--target", dest="project_id", type=int, help="alias for --project-id"
    )
    supervised_review.add_argument(
        "--full-path",
        default="gitlab-ai-hackathon/transcend-october-2026/39306908/"
        "termivance-b3-disposable-pages-demo",
    )
    supervised_review.add_argument(
        "--execute",
        action="store_true",
        help="actually execute the 7-step read-only investigation pipeline live (anonymous)",
    )
    supervised_review.add_argument(
        "--issue",
        dest="issue_iid",
        type=int,
        default=None,
        help="GitLab issue IID (e.g. 5) containing the Duo analysis",
    )
    supervised_review.add_argument(
        "--publish",
        action="store_true",
        help="publish deterministic supervised review outcome back to the GitLab issue",
    )
    supervised_review.add_argument(
        "--out-dir",
        dest="out_dir",
        default=None,
        help="directory to write all refreshed investigation artifacts",
    )
    supervised_review.add_argument(
        "--policy",
        default=None,
        help="custom retirement policy JSON path",
    )
    supervised_review.add_argument("--out", default=None)
    supervised_review.add_argument("--json", action="store_true")

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
    if args.command == "approval-template":
        return _cmd_approval_template(args)
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
    if args.command == "portfolio":
        return _cmd_portfolio(args)
    if args.command == "risk-map":
        return _cmd_risk_map(args)
    if args.command == "simulate":
        return _cmd_simulate(args)
    if args.command == "capsule-build":
        return _cmd_capsule_build(args)
    if args.command == "capsule-verify":
        return _cmd_capsule_verify(args)
    if args.command == "capsule-render":
        return _cmd_capsule_render(args)
    if args.command == "workflow-plan":
        return _cmd_workflow_plan(args)
    if args.command == "workflow-status":
        return _cmd_workflow_status(args)
    if args.command == "tripwire-check":
        return _cmd_tripwire(args)
    if args.command == "reconcile-duo":
        return _cmd_reconcile_duo(args)
    if args.command == "witness-build":
        return _cmd_witness_build(args)
    if args.command == "supervised-review":
        return _cmd_supervised_review(args)
    return 1  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
