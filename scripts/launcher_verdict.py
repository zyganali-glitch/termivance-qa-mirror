#!/usr/bin/env python3
"""Launcher verdict classifier — reports the ACTUAL deterministic verdict of a
supervised-review execution from the production CLI's structured output.

Used by ``scripts/run_supervised_review.bat`` and ``scripts/run_supervised_review.sh``
so the demo launchers never print a hard-coded expected result. This module adds
no authority of its own: it only reads the ``termivance.supervised_review/v1``
record that ``termivance supervised-review --execute --json --out <file>``
produced and classifies, truthfully, what that record establishes.

Contract:
* Exit 0  — the expected safe demonstration outcome is CONFIRMED from the
  structured output: execution genuinely completed now, live provider evidence
  was observed, and the deterministic verdict is ``BLOCKED`` (intentional
  fail-closed refusal).
* Exit 1  — truthful failure classification: unsuccessful execution, missing /
  malformed / contradictory / unreadable result, verdict not determined,
  execution not live, incomplete steps, no live provider evidence, or an
  unexpected / inconclusive verdict. Unexpected results are displayed as such
  and are NEVER converted into a successful BLOCKED result.
* Exit 2  — usage error.

The classifier never mutates anything, never contacts a provider, and never
prints credentials. The LAUNCHER preserves the original CLI exit code; this
helper's exit code only signals whether the expected safe outcome was
confirmed from the record.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REVIEW_SCHEMA = "termivance.supervised_review/v1"
EXPECTED_SAFE_VERDICT = "BLOCKED"
#: Step statuses that mean the step did not complete successfully.
FAILED_STEP_STATUSES = {"BLOCKED", "NOT_RUN", "STRUCTURALLY_REFUSED"}


def classify(record: object, cli_exit: int) -> dict[str, object]:
    """Classify an execution result. Returns a report dict; never raises on bad input."""
    report: dict[str, object] = {
        "classification": "",
        "deterministic_verdict": "NOT_DETERMINED",
        "investigation_mode": "UNKNOWN",
        "execution_id": "UNKNOWN",
        "observed_at": "UNKNOWN",
        "steps_completed": "0/0",
        "live_provider_steps": 0,
        "summary": "",
        "exit_code": 1,
    }

    def finish(classification: str, summary: str, exit_code: int) -> dict[str, object]:
        report["classification"] = classification
        report["summary"] = summary
        report["exit_code"] = exit_code
        return report

    # 1. Unsuccessful execution is authoritative regardless of any file content.
    if cli_exit != 0:
        return finish(
            "EXECUTION_FAILED",
            f"the review process exited with non-zero status {cli_exit}; "
            "no verdict is confirmed from a failed execution",
            1,
        )

    # 2. The record must exist and be readable structured output.
    if not isinstance(record, dict):
        return finish("RESULT_MALFORMED", "the result is not a JSON object", 1)
    schema = record.get("schema")
    if schema != REVIEW_SCHEMA:
        return finish(
            "RESULT_MALFORMED",
            f"unexpected or missing schema {schema!r} (expected {REVIEW_SCHEMA})",
            1,
        )

    verdict = record.get("deterministic_verdict")
    mode = record.get("investigation_mode")
    steps = record.get("steps")
    report["deterministic_verdict"] = (
        verdict if isinstance(verdict, str) and verdict else "NOT_DETERMINED"
    )
    report["investigation_mode"] = mode if isinstance(mode, str) else "UNKNOWN"
    report["execution_id"] = record.get("execution_id") or "UNKNOWN"
    report["observed_at"] = record.get("observed_at") or "UNKNOWN"

    # 3. Steps must be present, complete and genuinely live.
    if not isinstance(steps, list) or not steps:
        return finish(
            "EXECUTION_INCOMPLETE",
            "the record carries no review steps; execution cannot be confirmed complete",
            1,
        )
    completed = 0
    live_steps = 0
    failed_step = None
    for step in steps:
        if not isinstance(step, dict):
            return finish("RESULT_MALFORMED", "a review step is not a JSON object", 1)
        status = step.get("status")
        if status == "COMPLETED":
            completed += 1
        elif status in FAILED_STEP_STATUSES:
            failed_step = f"{step.get('step_id', '?')} ({status})"
        if step.get("execution_mode") == "EXECUTED_NOW":
            live_steps += 1
    report["steps_completed"] = f"{completed}/{len(steps)}"
    report["live_provider_steps"] = live_steps
    if failed_step:
        return finish(
            "EXECUTION_INCOMPLETE",
            f"review step {failed_step} did not complete; "
            "the pipeline result is not a completed execution",
            1,
        )

    # 4. The execution must be a live, now-executed investigation with provider evidence.
    if mode != "EXECUTED_NOW":
        return finish(
            "NOT_EXECUTED_NOW",
            f"investigation mode is {mode!r}, not EXECUTED_NOW; recorded-input assembly "
            "is not a live provider execution",
            1,
        )
    if live_steps == 0:
        return finish(
            "NO_LIVE_PROVIDER_EVIDENCE",
            "no step was executed against live provider evidence in this run",
            1,
        )

    # 5. The verdict itself must be determined.
    if not isinstance(verdict, str) or not verdict:
        return finish(
            "VERDICT_NOT_DETERMINED",
            "the executed review produced no deterministic verdict "
            "(no deterministic decision step completed)",
            1,
        )

    # 6. Classify the actual verdict. Only BLOCKED is the expected safe demo outcome.
    if verdict == EXPECTED_SAFE_VERDICT:
        return finish(
            "VERDICT_CONFIRMED_BLOCKED",
            "execution completed with live provider evidence and the deterministic "
            "engine returned SAFE_TO_RETIRE = BLOCKED (intentional fail-closed refusal)",
            0,
        )
    if verdict == "SAFE_TO_RETIRE":
        return finish(
            "UNEXPECTED_VERDICT_SAFE",
            "the deterministic engine returned SAFE_TO_RETIRE - this is NOT the expected "
            "safe demonstration outcome and must never be presented as a confirmed BLOCKED "
            "refusal; verify the target and evidence before any further use",
            1,
        )
    if verdict == "INCONCLUSIVE":
        return finish(
            "VERDICT_INCONCLUSIVE",
            "the deterministic engine returned INCONCLUSIVE; the execution completed but "
            "no retirement decision could be determined",
            1,
        )
    return finish(
        "UNEXPECTED_VERDICT",
        f"the deterministic engine returned an unrecognized verdict {verdict!r}; "
        "it is displayed as-is and never converted into a successful BLOCKED result",
        1,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--result-file", required=True, help="structured --out result of the executed review"
    )
    parser.add_argument(
        "--cli-exit", required=True, type=int, help="the review process's real exit code"
    )
    args = parser.parse_args(argv)

    record: object = None
    file_state = "ok"
    read_error: str | None = None
    try:
        text = Path(args.result_file).read_text(encoding="utf-8")
    except OSError as exc:
        file_state = "missing"
        read_error = f"result file unreadable: {exc.__class__.__name__}"
    else:
        try:
            record = json.loads(text)
        except json.JSONDecodeError as exc:
            file_state = "malformed"
            read_error = f"result file is not valid JSON: {exc.msg}"

    if file_state != "ok":
        if args.cli_exit != 0:
            # An unsuccessful execution is the authoritative failure; the missing or
            # unreadable file is secondary detail in that case.
            report = classify(None, args.cli_exit)
        else:
            classification = (
                "RESULT_FILE_MISSING" if file_state == "missing" else "RESULT_MALFORMED"
            )
            report = {
                "classification": classification,
                "deterministic_verdict": "NOT_DETERMINED",
                "investigation_mode": "UNKNOWN",
                "execution_id": "UNKNOWN",
                "observed_at": "UNKNOWN",
                "steps_completed": "0/0",
                "live_provider_steps": 0,
                "summary": (
                    f"{read_error}; a zero exit code without a readable structured "
                    "result cannot confirm any verdict"
                ),
                "exit_code": 1,
            }
    else:
        report = classify(record, args.cli_exit)

    print("LAUNCHER VERDICT REPORT (from structured execution output)")
    print(f"CLASSIFICATION: {report['classification']}")
    print(f"DETERMINISTIC_VERDICT: {report['deterministic_verdict']}")
    print(f"INVESTIGATION_MODE: {report['investigation_mode']}")
    print(f"EXECUTION_ID: {report['execution_id']}")
    print(f"OBSERVED_AT: {report['observed_at']}")
    print(f"STEPS_COMPLETED: {report['steps_completed']}")
    print(f"LIVE_PROVIDER_STEPS: {report['live_provider_steps']}")
    print(f"SUMMARY: {report['summary']}")
    return int(report["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
