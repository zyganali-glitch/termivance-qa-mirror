"""Termivance deterministic CLI.

B1 foundation only: this CLI never performs a GitLab mutation and offers no
mutation-capable command. It reports truthful status and validates the
deterministic boundaries that the rest of the protocol depends on.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections.abc import Sequence

from termivance import __version__
from termivance.policy import PolicyError, load_policy

STATUS = {
    "product": "Termivance",
    "remote": "NOT_CREATED_OR_NOT_VERIFIED",
    "ci": "NOT_RUN",
    "duo_flow": "NOT_RUN",
    "duo_session": "NOT_RUN",
    "retirement": "NOT_RUN",
}


def _cmd_version() -> int:
    print(__version__)
    return 0


def _cmd_status(as_json: bool) -> int:
    payload = {"version": __version__, **STATUS}
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Termivance {__version__} - B1 foundation (no mutation)")
        print(
            f"remote={STATUS['remote']}  ci={STATUS['ci']}  "
            f"Duo={STATUS['duo_flow']}  retirement={STATUS['retirement']}"
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
        "safe_for_b1": not policy.mutation_enabled,
    }
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        state = "DISABLED" if not policy.mutation_enabled else "ENABLED"
        print(f"policy mode={policy.mode} mutation={state} targets={len(result['targets'])}")
    # Exit non-zero if a policy would permit mutation during B1.
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="termivance",
        description="Proof-bounded software retirement (B1 foundation; no mutation).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="print the package version")

    status = sub.add_parser("status", help="print truthful project status")
    status.add_argument("--json", action="store_true", help="emit JSON")

    policy_check = sub.add_parser("policy-check", help="validate a policy file (fail closed)")
    policy_check.add_argument("path", help="path to a retirement policy JSON file")
    policy_check.add_argument("--json", action="store_true", help="emit JSON")

    doctor = sub.add_parser("doctor", help="report environment sanity checks")
    doctor.add_argument("--json", action="store_true", help="emit JSON")

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
    return 1  # pragma: no cover - argparse guarantees a known command


if __name__ == "__main__":
    raise SystemExit(main())
