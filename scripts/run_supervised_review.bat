@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM Termivance — Supervised Retirement Review Live Execution Launcher (Scene 05)
REM 
REM This launcher executes the authentic read-only supervised investigation pipeline
REM against canonical Issue #5 (Session 9710085) and target disposable project 87785099.
REM
REM Safety Boundaries:
REM - Read-only GET requests only (GitLab REST API)
REM - Zero credentials exposed / required
REM - Personal spend target: $0.00
REM - Deterministic verdict BLOCKED is expected and safe-by-design
REM ==============================================================================

REM 1. Establish repository root working directory
cd /d "%~dp0\.."
if errorlevel 1 (
    echo [ERROR] Failed to establish repository working directory.
    exit /b 1
)

REM 2. Preflight: Check Python availability
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo ==============================================================================
    echo [PREFLIGHT FAILED] Python executable not found in PATH.
    echo.
    echo Setup Guidance:
    echo   1. Install Python 3.10 or newer from https://www.python.org/
    echo   2. Ensure "Add Python to PATH" is checked during installation.
    echo ==============================================================================
    exit /b 1
)

REM 3. Preflight: Verify Python version >= 3.10 and termivance package availability
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1); import termivance" >nul 2>nul
if errorlevel 1 (
    echo.
    echo ==============================================================================
    echo [PREFLIGHT FAILED] Python 3.10+ or 'termivance' package is not available.
    echo.
    echo Setup Guidance:
    echo   1. Verify Python version is 3.10+: python --version
    echo   2. Install termivance in editable mode:
    echo        pip install -e .[dev]
    echo ==============================================================================
    exit /b 1
)

REM 4. Present truthful runtime header distinguishing historical vs live sources
echo.
echo ==============================================================================
echo [TERMIVANCE] Supervised Retirement Review (Live Provider Execution)
echo.
echo Target Project:      87785099 (Disposable Pages Demo)
echo Historical Input:    GitLab Duo Session 9710085 (Catalog Item 1018562, Issue #5)
echo Live Operations:     Anonymous Read-Only Provider Checks (GitLab REST API)
echo Authority Boundary:  AI Proposes Obligations; Deterministic Code Enforces Verdict
echo Spending / Secrets:  $0.00 Incremental Spend; Zero Credentials Required
echo ==============================================================================
echo.

REM 5. Execute authentic supervised review command
python -m termivance.cli supervised-review --execute --issue 5
set CLI_EXIT=%ERRORLEVEL%

REM 6. Evaluate exit status truthfully
echo.
echo ==============================================================================
if %CLI_EXIT% equ 0 (
    echo [EXECUTION SUCCESS] Supervised review pipeline completed successfully.
    echo.
    echo Truthful Verdict: Deterministic SAFE_TO_RETIRE evaluates to BLOCKED.
    echo Safety Context:   This is an intentional fail-closed refusal. Redeployment
    echo                   risks are present and Pages administration rights are HTTP 403.
    echo Human Review:     Required before any retirement action can be authorized.
) else (
    echo [EXECUTION FAILED] Python process exited with non-zero status code: %CLI_EXIT%.
    echo Please review the trace output above for diagnostic errors.
)
echo ==============================================================================
echo.

if not "%1"=="--no-pause" (
    echo Press any key to close this terminal window...
    pause >nul
)

exit /b %CLI_EXIT%
