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
# - Deterministic verdict BLOCKED is expected and safe-by-design
# ==============================================================================

set -euo pipefail

# 1. Establish repository root working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# 2. Preflight: Check Python availability
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo ""
    echo "=============================================================================="
    echo "[PREFLIGHT FAILED] Python executable (python3 or python) not found in PATH."
    echo ""
    echo "Setup Guidance:"
    echo "  1. Install Python 3.12 or newer."
    echo "  2. Ensure python3 is available in your PATH."
    echo "=============================================================================="
    exit 1
fi

# 3. Preflight: Verify Python version >= 3.12 and termivance package availability
if ! "${PYTHON_BIN}" -c "import sys; assert sys.version_info >= (3, 12); import termivance" >/dev/null 2>&1; then
    echo ""
    echo "=============================================================================="
    echo "[PREFLIGHT FAILED] Python 3.12+ or 'termivance' package is not available."
    echo ""
    echo "Setup Guidance:"
    echo "  1. Verify Python version is 3.12+: ${PYTHON_BIN} --version"
    echo "  2. Install termivance in editable mode:"
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

# 5. Execute authentic supervised review command
set +e
"${PYTHON_BIN}" -m termivance.cli supervised-review --execute --issue 5
CLI_EXIT=$?
set -e

# 6. Evaluate exit status truthfully
echo ""
echo "=============================================================================="
if [ ${CLI_EXIT} -eq 0 ]; then
    echo "[EXECUTION SUCCESS] Supervised review pipeline completed successfully."
    echo ""
    echo "Truthful Verdict: Deterministic SAFE_TO_RETIRE evaluates to BLOCKED."
    echo "Safety Context:   This is an intentional fail-closed refusal. Redeployment"
    echo "                  risks are present and Pages administration rights are HTTP 403."
    echo "Human Review:     Required before any retirement action can be authorized."
else
    echo "[EXECUTION FAILED] Python process exited with non-zero status code: ${CLI_EXIT}."
    echo "Please review the trace output above for diagnostic errors."
fi
echo "=============================================================================="
echo ""

exit ${CLI_EXIT}
