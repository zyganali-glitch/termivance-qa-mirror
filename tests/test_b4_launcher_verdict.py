"""Adversarial tests for the demo launcher verdict semantics (W23-W25 repair).

The launchers (``scripts/run_supervised_review.bat`` / ``.sh``) must report the
ACTUAL deterministic verdict obtained from the production CLI's structured
``--out`` record — never a hard-coded expected result. These tests exercise
``scripts/launcher_verdict.py`` (the shared classifier both launchers call)
with controlled CLI outputs, plus the launcher scripts' contract, without any
network access or provider mutation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLASSIFIER = REPO_ROOT / "scripts" / "launcher_verdict.py"
BAT = REPO_ROOT / "scripts" / "run_supervised_review.bat"
SH = REPO_ROOT / "scripts" / "run_supervised_review.sh"


def _run(result_file: str, cli_exit: int) -> tuple[int, dict[str, str]]:
    """Run the classifier as a real subprocess and parse its key: value report."""
    env = dict(os.environ)
    # Force deterministic UTF-8 child output independent of the host codepage.
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [
            sys.executable,
            str(CLASSIFIER),
            "--result-file",
            result_file,
            "--cli-exit",
            str(cli_exit),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        timeout=60,
        env=env,
    )
    report: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if ": " in line:
            key, _, value = line.partition(": ")
            report[key.strip()] = value.strip()
    return proc.returncode, report


def _valid_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schema": "termivance.supervised_review/v1",
        "execution_id": "inv-20261021TEST-000001",
        "investigation_mode": "EXECUTED_NOW",
        "deterministic_verdict": "BLOCKED",
        "observed_at": "2026-10-21T12:00:00+00:00",
        "target": {"project_id": 87785099, "full_path": "x/termivance-b3-disposable-pages-demo"},
        "steps": [
            {
                "step_id": "duo_analysis",
                "status": "COMPLETED",
                "execution_mode": "RECORDED_HISTORICAL",
            },
            {
                "step_id": "deterministic_decision",
                "status": "COMPLETED",
                "execution_mode": "EXECUTED_NOW",
            },
            {
                "step_id": "risk_map",
                "status": "COMPLETED",
                "execution_mode": "EXECUTED_NOW",
            },
        ],
    }
    record.update(overrides)
    return record


def _write(tmp_path: Path, record: object, name: str = "result.json") -> str:
    p = tmp_path / name
    p.write_text(json.dumps(record), encoding="utf-8")
    return str(p)


class TestConfirmedBlocked:
    def test_blocked_verdict_with_live_evidence_confirms(self, tmp_path):
        result = _write(tmp_path, _valid_record())
        code, report = _run(result, 0)
        assert code == 0
        assert report["CLASSIFICATION"] == "VERDICT_CONFIRMED_BLOCKED"
        assert report["DETERMINISTIC_VERDICT"] == "BLOCKED"
        assert report["INVESTIGATION_MODE"] == "EXECUTED_NOW"
        assert report["STEPS_COMPLETED"] == "3/3"
        assert report["LIVE_PROVIDER_STEPS"] == "2"
        assert report["EXECUTION_ID"] == "inv-20261021TEST-000001"

    def test_extra_completed_steps_still_confirm(self, tmp_path):
        record = _valid_record(
            steps=[
                {"step_id": f"s{i}", "status": "COMPLETED", "execution_mode": "EXECUTED_NOW"}
                for i in range(7)
            ]
        )
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 0
        assert report["CLASSIFICATION"] == "VERDICT_CONFIRMED_BLOCKED"
        assert report["STEPS_COMPLETED"] == "7/7"


class TestUnexpectedVerdicts:
    def test_inconclusive_verdict_is_displayed_not_converted(self, tmp_path):
        record = _valid_record(deterministic_verdict="INCONCLUSIVE")
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "VERDICT_INCONCLUSIVE"
        assert report["DETERMINISTIC_VERDICT"] == "INCONCLUSIVE"

    def test_safe_to_retire_is_never_a_confirmed_demo_outcome(self, tmp_path):
        record = _valid_record(deterministic_verdict="SAFE_TO_RETIRE")
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "UNEXPECTED_VERDICT_SAFE"
        assert report["DETERMINISTIC_VERDICT"] == "SAFE_TO_RETIRE"
        assert "never" in report["SUMMARY"].lower()

    def test_unknown_verdict_is_surfaced_as_unexpected(self, tmp_path):
        record = _valid_record(deterministic_verdict="SOMETHING_ELSE")
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "UNEXPECTED_VERDICT"
        assert report["DETERMINISTIC_VERDICT"] == "SOMETHING_ELSE"

    def test_missing_verdict_field_reports_not_determined(self, tmp_path):
        record = _valid_record()
        del record["deterministic_verdict"]
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "VERDICT_NOT_DETERMINED"

    def test_null_verdict_reports_not_determined(self, tmp_path):
        record = _valid_record(deterministic_verdict=None)
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "VERDICT_NOT_DETERMINED"
        assert report["DETERMINISTIC_VERDICT"] == "NOT_DETERMINED"


class TestMissingStructuredFields:
    def test_wrong_schema_is_malformed(self, tmp_path):
        record = _valid_record(schema="termivance.other/v9")
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "RESULT_MALFORMED"

    def test_missing_schema_is_malformed(self, tmp_path):
        record = _valid_record()
        del record["schema"]
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "RESULT_MALFORMED"

    def test_non_object_result_is_malformed(self, tmp_path):
        code, report = _run(_write(tmp_path, [1, 2, 3]), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "RESULT_MALFORMED"

    def test_malformed_json_file_is_explicit_failure(self, tmp_path):
        p = tmp_path / "broken.json"
        p.write_text("{ not valid json !!", encoding="utf-8")
        code, report = _run(str(p), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "RESULT_MALFORMED"
        assert "not valid JSON" in report["SUMMARY"]

    def test_missing_result_file_is_explicit_failure(self, tmp_path):
        code, report = _run(str(tmp_path / "does-not-exist.json"), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "RESULT_FILE_MISSING"

    def test_empty_steps_is_execution_incomplete(self, tmp_path):
        code, report = _run(_write(tmp_path, _valid_record(steps=[])), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "EXECUTION_INCOMPLETE"


class TestExecutionTruth:
    def test_nonzero_cli_exit_is_execution_failed_even_with_valid_file(self, tmp_path):
        result = _write(tmp_path, _valid_record())
        code, report = _run(result, 1)
        assert code == 1
        assert report["CLASSIFICATION"] == "EXECUTION_FAILED"
        # The verdict from a failed execution is never confirmed.
        assert report["DETERMINISTIC_VERDICT"] == "NOT_DETERMINED"

    def test_nonzero_cli_exit_with_missing_file_reports_execution_failed(self, tmp_path):
        code, report = _run(str(tmp_path / "nope.json"), 2)
        assert code == 1
        assert report["CLASSIFICATION"] == "EXECUTION_FAILED"

    def test_recorded_input_mode_is_not_a_live_execution(self, tmp_path):
        record = _valid_record(investigation_mode="RECORDED_INPUT_USED")
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "NOT_EXECUTED_NOW"

    def test_step_not_run_is_execution_incomplete(self, tmp_path):
        record = _valid_record(
            steps=[
                {
                    "step_id": "duo_analysis",
                    "status": "COMPLETED",
                    "execution_mode": "RECORDED_HISTORICAL",
                },
                {
                    "step_id": "deterministic_decision",
                    "status": "NOT_RUN",
                    "execution_mode": "NOT_RUN",
                },
            ]
        )
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "EXECUTION_INCOMPLETE"
        assert "deterministic_decision" in report["SUMMARY"]

    def test_zero_live_provider_steps_is_no_live_evidence(self, tmp_path):
        record = _valid_record(
            steps=[
                {
                    "step_id": "duo_analysis",
                    "status": "COMPLETED",
                    "execution_mode": "RECORDED_HISTORICAL",
                },
                {
                    "step_id": "deterministic_decision",
                    "status": "COMPLETED",
                    "execution_mode": "RECORDED_INPUT_USED",
                },
            ]
        )
        code, report = _run(_write(tmp_path, record), 0)
        assert code == 1
        assert report["CLASSIFICATION"] == "NO_LIVE_PROVIDER_EVIDENCE"


class TestLauncherScriptContract:
    """Both launcher entry points must use the classifier and preserve the CLI exit code."""

    @staticmethod
    def _read(path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")

    def test_no_hard_coded_verdict_summary_remains(self):
        for path in (BAT, SH):
            text = self._read(path)
            assert "evaluates to BLOCKED" not in text, f"{path.name} still hard-codes the verdict"
            assert "EXECUTION SUCCESS] Supervised review pipeline completed" not in text

    def test_both_launchers_invoke_the_verdict_classifier(self):
        bat = self._read(BAT)
        sh = self._read(SH)
        assert "launcher_verdict.py" in bat and "launcher_verdict.py" in sh
        assert "--result-file" in bat and "--result-file" in sh
        assert "--cli-exit" in bat and "--cli-exit" in sh

    def test_both_launchers_preserve_the_original_cli_exit_code(self):
        bat = self._read(BAT)
        sh = self._read(SH)
        assert "exit /b %CLI_EXIT%" in bat
        assert "exit ${CLI_EXIT}" in sh

    def test_both_launchers_use_the_production_cli_structured_output(self):
        bat = self._read(BAT)
        sh = self._read(SH)
        for text in (bat, sh):
            assert "supervised-review --execute --issue 5" in text
            assert "--out" in text
            # The launcher must not invoke any mutation or publication command.
            assert "retire-pages --execute" not in text
            assert "--publish" not in text
            assert "--token" not in text

    def test_both_launchers_report_unconfirmed_verdicts_truthfully(self):
        for path in (BAT, SH):
            text = self._read(path)
            assert "VERDICT NOT CONFIRMED" in text
            assert "VERDICT CONFIRMED FROM EXECUTION OUTPUT" in text
