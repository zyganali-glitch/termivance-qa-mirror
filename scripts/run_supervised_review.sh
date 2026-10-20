#!/usr/bin/env bash
# ==============================================================================
# Termivance — Supervised Retirement Review Live Execution Launcher (Scene 05)
# This script runs the authentic read-only supervised investigation pipeline against
# canonical Issue #5 (Session 9710085) and target disposable project 87785099.
# Zero credentials exposed. Read-only GET requests only. Personal spend: $0.00.
# ==============================================================================

set -euo pipefail

echo ""
echo "=============================================================================="
echo "[TERMIVANCE] Running Supervised Retirement Review (Live Provider Execution)"
echo "Target Project: 87785099 (Disposable Pages Project)"
echo "Duo Discovery: Canonical Issue #5 (Session 9710085)"
echo "Mode: Live Read-Only Deterministic Evaluation"
echo "=============================================================================="
echo ""

python -m termivance.cli supervised-review --execute --issue 5

echo ""
echo "=============================================================================="
echo "[TERMIVANCE] Supervised Review Execution Complete."
echo "=============================================================================="
