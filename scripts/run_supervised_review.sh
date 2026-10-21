#!/usr/bin/env bash
# ==============================================================================
# Termivance — Supervised Retirement Review Live Execution Launcher (Scene 05)
# 
# This launcher executes the authentic read-only supervised investigation pipeline
# against canonical Issue #5 (Session 9710085) and target disposable project 87785099.
#
# Safety Boundaries:
# - Read-only GET requests only (GitLab REST API)
# - Zero credentials exposed / required
# - Personal spend target: $0.00
# - Expected outcome: BLOCKED (intentional fail-closed refusal). The actual
#   verdict is read back from the structured execution output and confirmed
#   by scripts/launcher_verdict.py - never hard-coded, never assumed.
# - No retire-pages mutation and no issue-note publication is performed here.
# ==============================================================================

set -euo pipefail

# 1. Establish repository root working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# 2. Preflight: select a WORKING Python interpreter. The candidate is
#    validated (version >= 3.12 + termivance import), never trusted by name
#    alone: e.g. Windows Git Bash exposes a non-functional python3 stub
#    (WindowsApps alias) while the real interpreter is "python".
PYTHON_BIN=""
for candidate in python3 python; do
    if command -v "${candidate}" >/dev/null 2>&1; then
        if "${candidate}" -c "import sys; assert sys.version_info >= (3, 12); import termivance" >/dev/null 2>&1; then
            PYTHON_BIN="${candidate}"
            break
        fi
    fi
done
if [ -z "${PYTHON_BIN}" ]; then
    echo ""
    echo "=============================================================================="
    echo "[PREFLIGHT FAILED] No working Python 3.12+ interpreter with 'termivance'"
    echo "installed was found (tried python3 and python)."
    echo ""
    echo "Setup Guidance:"
    echo "  1. Install Python 3.12 or newer."
    echo "  2. Install termivance in editable mode from the repository root:"
    echo "       pip install -e .[dev]"
    echo "=============================================================================="
    exit 1
fi

# 4. Present truthful runtime header distinguishing historical vs live sources
echo ""
echo "=============================================================================="
echo "[TERMIVANCE] Supervised Retirement Review (Live Provider Execution)"
echo ""
echo "Target Project:      87785099 (Disposable Pages Demo)"
echo "Historical Input:    GitLab Duo Session 9710085 (Catalog Item 1018562, Issue #5)"
echo "Live Operations:     Anonymous Read-Only Provider Checks (GitLab REST API)"
echo "Authority Boundary:  AI Proposes Obligations; Deterministic Code Enforces Verdict"
echo "Spending / Secrets:  \$0.00 Incremental Spend; Zero Credentials Required"
echo "=============================================================================="
echo ""

# 5. Execute authentic supervised review command; structured result goes to a
#    temporary file so the ACTUAL verdict can be read back from the production
#    CLI's authoritative output (never a hard-coded expected result).
RESULT_FILE="${TMPDIR:-/tmp}/termivance_supervised_review_result.json"
rm -f "${RESULT_FILE}"
set +e
"${PYTHON_BIN}" -m termivance.cli supervised-review --execute --issue 5 --out "${RESULT_FILE}"
CLI_EXIT=$?
set -e

# 6. Classify the actual verdict from the structured execution output
set +e
"${PYTHON_BIN}" scripts/launcher_verdict.py --result-file "${RESULT_FILE}" --cli-exit ${CLI_EXIT}
VERDICT_STATUS=$?
set -e
rm -f "${RESULT_FILE}"

# 7. Report truthfully: only a classification-confirmed BLOCKED verdict from the
#    executed output is presented as the expected safe demonstration outcome.
echo ""
echo "=============================================================================="
if [ ${VERDICT_STATUS} -eq 0 ]; then
    echo "[VERDICT CONFIRMED FROM EXECUTION OUTPUT] The deterministic engine returned"
    echo "SAFE_TO_RETIRE = BLOCKED for target 87785099, confirmed from the structured"
    echo "result of THIS execution. Safety context: intentional fail-closed refusal -"
    echo "redeployment risk present, Pages administration denied (HTTP 403), no"
    echo "operator-signed authorization. Human review required before any retirement."
else
    echo "[VERDICT NOT CONFIRMED AS THE EXPECTED SAFE REFUSAL] This execution did not"
    echo "produce a confirmed BLOCKED outcome from verifiable structured output."
    echo "Do NOT treat this run as the expected demonstration result; see the"
    echo "LAUNCHER VERDICT REPORT above for the truthful classification."
fi
if [ ${CLI_EXIT} -ne 0 ]; then
    echo "[EXECUTION FAILED] Python process exited with non-zero status code: ${CLI_EXIT}."
    echo "Any verdict report above is unconfirmed; review the trace output for errors."
fi
echo "=============================================================================="
echo ""

exit ${CLI_EXIT}
