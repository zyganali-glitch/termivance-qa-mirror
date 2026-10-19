#!/usr/bin/env python3
"""Network-free safety-contract assertions executed by GitLab CI.

This script never contacts any provider. It proves, in the pipeline itself, that
the deterministic safety contract is enforced by the shipped code — not merely
described in documentation:

1. the single mutation allowlist can never match a project-deletion path;
2. a provenance-free authorization record cannot be loaded;
3. a durable-ledger authorization cannot be spent twice;
4. bounded absence cannot be awarded from two unrelated 404 responses;
5. a retirement attempt without a discovery source or recorded snapshot refuses;
6. an uploaded operator approval must reference the exact endpoint and action;
7. a real-mutation preflight without a durable ledger refuses;
8. non-durable ledger paths are refused;
9. only a GitLab-authenticated approval channel can authorize a real mutation;
10. a malformed ledger is refused rather than guessed;
11. a forged receipt without a durable record cannot bind an absence claim;
12. capsule integrity verification fails closed on any tampering;
13. cross-target receipts are refused; and
14. concurrent ledger reservations are serialized by the lock file.

Exits non-zero on any violation.
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from termivance.authorization import (
    Authorization,
    AuthorizationError,
    OperatorApproval,
    load_authorization,
)
from termivance.capsule import (
    CapsuleError,
    build_capsule,
    validate_mutation_receipt,
    verify_capsule,
)
from termivance.evidence import PagesObservation, PagesPreState, bounded_absence
from termivance.ledger import AuthorizationLedger, LedgerError
from termivance.pages import mutation_is_structurally_safe
from termivance.policy import load_policy
from termivance.retirement import preflight, retire_pages
from termivance.target import TargetIdentity
from termivance.verdicts import Verdict

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
TARGET = TargetIdentity(
    87785099,
    "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
    "GITLAB_PAGES_SITE",
)
ACTION = "unpublish_pages"
URL = "https://termivance-b3-disposable-pages-demo.pages.example/"

failures: list[str] = []


def check(name: str, ok: bool) -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(name)


def build_auth() -> Authorization:
    authorization = Authorization.issue(TARGET, ACTION, nonce="ci-assertion", now=NOW)
    authorization.approval = OperatorApproval(
        operator="ci",
        statement=f"I authorize exactly one {ACTION} using {authorization.exact_endpoint}",
        approved_at=NOW,
        channel="ci",
        binding=authorization.binding(),
    )
    return authorization


def main() -> int:
    check("mutation allowlist excludes project deletion", mutation_is_structurally_safe())

    # 2. provenance gate
    example = json.loads(Path("config/authorization.example.json").read_text(encoding="utf-8"))
    example["operator_approval"] = None
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "auth.json"
        path.write_text(json.dumps(example), encoding="utf-8")
        try:
            load_authorization(path)
            check("provenance-free authorization is refused", False)
        except AuthorizationError:
            check("provenance-free authorization is refused", True)

        # 3. durable single use across invocations
        ledger = AuthorizationLedger(Path(tmp) / "ledger.json")
        authorization = build_auth()
        ledger.consume(authorization, operation_id="ci-1", now=NOW)
        try:
            ledger.consume(authorization, operation_id="ci-2", now=NOW)
            check("durable ledger refuses a second consumption", False)
        except LedgerError:
            check("durable ledger refuses a second consumption", True)

    # 4. two unrelated 404s prove nothing
    observation = PagesObservation(
        target=TARGET,
        observed_scope=frozenset({"pages_api", "served_url"}),
        observation_time_utc=NOW,
        source="ci",
        api_status=404,
        served_url=URL,
        http_status=404,
        fresh_until=NOW + timedelta(minutes=5),
    )
    check(
        "two unrelated 404 responses cannot award OBSERVED_ABSENT",
        bounded_absence(observation, NOW) == Verdict.INCONCLUSIVE,
    )
    proven = PagesPreState(
        served_url=URL,
        marker="M",
        marker_observed=True,
        deployment_present=True,
        observed_at=NOW,
    )
    observation_with_pre_state = PagesObservation(
        target=TARGET,
        observed_scope=frozenset({"pages_api", "served_url"}),
        observation_time_utc=NOW,
        source="ci",
        api_status=404,
        served_url=URL,
        http_status=404,
        fresh_until=NOW + timedelta(minutes=5),
        pre_state=proven,
        action_accepted=True,
    )
    check(
        "a proven transition can award OBSERVED_ABSENT",
        bounded_absence(observation_with_pre_state, NOW) == Verdict.OBSERVED_ABSENT,
    )

    # 5. no discovery source => no mutation
    policy = load_policy("config/retirement_policy.b3_disposable.json")
    receipt = retire_pages(TARGET, policy, build_auth(), now=NOW)
    check(
        "retirement without a discovery source or record is BLOCKED",
        receipt.verdict == Verdict.BLOCKED and receipt.mutation_attempted is False,
    )

    # 6. a generic approval statement cannot unlock the exact endpoint
    generic = build_auth()
    generic.approval = OperatorApproval(
        operator="ci",
        statement="please retire this thing",
        approved_at=NOW,
        channel="ci",
        binding=generic.binding(),
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "generic.json"
        path.write_text(json.dumps(generic.to_dict()), encoding="utf-8")
        try:
            load_authorization(path)
            check("a non-specific approval statement is refused", False)
        except AuthorizationError:
            check("a non-specific approval statement is refused", True)

    # 7. a real-mutation preflight without a durable ledger refuses
    pre = preflight(TARGET, policy, build_auth(), mutation_intent=True, now=NOW)
    rejected = [str(c["detail"]) for c in pre.checks if not c["ok"]]
    check(
        "live mutation without a durable ledger is refused",
        pre.ok is False and any("ledger" in d.lower() for d in rejected),
    )

    # 8. non-durable ledger paths are refused
    pre_nul = preflight(
        TARGET,
        policy,
        build_auth(),
        ledger=AuthorizationLedger("NUL"),
        mutation_intent=True,
        now=NOW,
    )
    nondurable = {c["check"]: c for c in pre_nul.checks}
    check(
        "non-durable ledger paths are refused",
        nondurable["durable_ledger_required"]["ok"] is False,
    )

    # 9. only a GitLab-authenticated approval channel can authorize a real mutation
    with tempfile.TemporaryDirectory() as tmp:
        pre_channel = preflight(
            TARGET,
            policy,
            build_auth(),  # channel="ci" — not GitLab-authenticated
            ledger=AuthorizationLedger(Path(tmp) / "ledger.json"),
            mutation_intent=True,
            now=NOW,
        )
    channel_checks = {c["check"]: c for c in pre_channel.checks}
    check(
        "untrusted approval channels cannot authorize real mutations",
        channel_checks["approval_provenance_gitlab"]["ok"] is False,
    )

    # 10. a malformed ledger is refused rather than guessed
    with tempfile.TemporaryDirectory() as tmp:
        corrupt = Path(tmp) / "corrupt.json"
        corrupt.write_text("{{ not json", encoding="utf-8")
        try:
            AuthorizationLedger(corrupt).health_check()
            check("a malformed ledger is refused, never guessed", False)
        except LedgerError:
            check("a malformed ledger is refused, never guessed", True)

    # 11. a forged receipt without a durable record cannot bind an absence claim
    with tempfile.TemporaryDirectory() as tmp:
        authorization = build_auth()
        binding = authorization.binding()
        receipt = {
            "schema": "termivance.retirement_receipt/v2",
            "target": TARGET.to_dict(),
            "action": ACTION,
            "operation_id": "op-ci",
            "authorization_binding": binding,
            "mutation_attempted": True,
            "mutation": {
                "accepted": True,
                "method": "DELETE",
                "endpoint": f"/projects/{TARGET.project_id}/pages",
                "status": 204,
                "requested_at": NOW.isoformat(),
            },
            "eligibility": {
                "established_at": NOW.isoformat(),
                "pre_state": {
                    "served_url": URL,
                    "marker": "M",
                    "marker_observed": True,
                    "deployment_present": True,
                    "observed_at": NOW.isoformat(),
                    "genuinely_published": True,
                },
            },
        }
        fresh = AuthorizationLedger(Path(tmp) / "fresh.json")
        fresh.health_check()
        forged = Path(tmp) / "forged_receipt.json"
        forged.write_text(json.dumps(receipt), encoding="utf-8")
        try:
            validate_mutation_receipt(receipt, TARGET, ledger=fresh)
            check("forged receipt without a durable record is refused", False)
        except Exception:  # noqa: BLE001 - CapsuleError expected
            check("forged receipt without a durable record is refused", True)

        # 12. capsule integrity fails closed on tampering
        capsule = build_capsule(target=TARGET, now=NOW)
        tampered = json.loads(json.dumps(capsule))
        tampered["sections"]["identity"]["generated_at"] = "2020-01-01T00:00:00+00:00"
        try:
            verify_capsule(tampered)
            check("capsule tampering fails closed", False)
        except CapsuleError:
            check("capsule tampering fails closed", True)
        check(
            "untampered capsule verifies (local integrity only)",
            verify_capsule(capsule).get("integrity_only") is True,
        )

        # 13. cross-target receipts are refused
        durable = AuthorizationLedger(Path(tmp) / "durable.json")
        durable.health_check()
        durable.consume(authorization, operation_id="op-ci", now=NOW)
        other_target = TargetIdentity(
            87779099, "gitlab-ai-hackathon/canonical-repo", "GITLAB_PAGES_SITE"
        )
        try:
            validate_mutation_receipt(receipt, other_target, ledger=durable)
            check("cross-target receipts are refused", False)
        except Exception:  # noqa: BLE001 - CapsuleError expected
            check("cross-target receipts are refused", True)

    # 14. concurrent reservations are serialized by the lock file
    with tempfile.TemporaryDirectory() as tmp:
        ledger = AuthorizationLedger(Path(tmp) / "ledger.json")
        ledger.health_check()
        lock = Path(str(Path(tmp) / "ledger.json") + ".lock")
        lock.write_text("999999", encoding="utf-8")
        try:
            ledger.consume(build_auth(), operation_id="op-ci", now=NOW)
            check("concurrent reservations are serialized (lock honoured)", False)
        except LedgerError as exc:
            check("concurrent reservations are serialized (lock honoured)", "lock" in str(exc))
        finally:
            lock.unlink(missing_ok=True)

    if failures:
        print(f"\nSAFETY CONTRACT FAILED: {len(failures)} assertion(s)")
        return 1
    print("\nSAFETY CONTRACT VERIFIED (network-free)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
