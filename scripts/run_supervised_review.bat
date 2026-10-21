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
REM - Expected outcome: BLOCKED (intentional fail-closed refusal). The actual
REM   verdict is read back from the structured execution output and confirmed
REM   by scripts\launcher_verdict.py - never hard-coded, never assumed.
REM - No retire-pages mutation and no issue-note publication is performed here.
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
    echo   1. Install Python 3.12 or newer from https://www.python.org/
    echo   2. Ensure "Add Python to PATH" is checked during installation.
    echo ==============================================================================
    exit /b 1
)

REM 3. Preflight: Verify Python version >= 3.12 and termivance package availability
python -c "import sys; assert sys.version_info >= (3, 12); import termivance" >nul 2>nul
if errorlevel 1 (
    echo.
    echo ==============================================================================
    echo [PREFLIGHT FAILED] Python 3.12+ or 'termivance' package is not available.
    echo.
    echo Setup Guidance:
    echo   1. Verify Python version is 3.12+: python --version
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

REM 5. Execute authentic supervised review command; structured result goes to a
REM    temporary file so the ACTUAL verdict can be read back from the production
REM    CLI's authoritative output (never a hard-coded expected result).
set "RESULT_FILE=%TEMP%\termivance_supervised_review_result.json"
if exist "%RESULT_FILE%" del "%RESULT_FILE%" >nul 2>nul
python -m termivance.cli supervised-review --execute --issue 5 --out "%RESULT_FILE%"
set CLI_EXIT=%ERRORLEVEL%

REM 6. Classify the actual verdict from the structured execution output
python scripts\launcher_verdict.py --result-file "%RESULT_FILE%" --cli-exit %CLI_EXIT%
set VERDICT_STATUS=%ERRORLEVEL%
if exist "%RESULT_FILE%" del "%RESULT_FILE%" >nul 2>nul

REM 7. Report truthfully: only a classification-confirmed BLOCKED verdict from the
REM    executed output is presented as the expected safe demonstration outcome.
echo.
echo ==============================================================================
if %VERDICT_STATUS% equ 0 (
    echo [VERDICT CONFIRMED FROM EXECUTION OUTPUT] The deterministic engine returned
    echo SAFE_TO_RETIRE = BLOCKED for target 87785099, confirmed from the structured
    echo result of THIS execution. Safety context: intentional fail-closed refusal -
    echo redeployment risk present, Pages administration denied ^(HTTP 403^), no
    echo operator-signed authorization. Human review required before any retirement.
) else (
    echo [VERDICT NOT CONFIRMED AS THE EXPECTED SAFE REFUSAL] This execution did not
    echo produce a confirmed BLOCKED outcome from verifiable structured output.
    echo Do NOT treat this run as the expected demonstration result; see the
    echo LAUNCHER VERDICT REPORT above for the truthful classification.
)
if not %CLI_EXIT% equ 0 (
    echo [EXECUTION FAILED] Python process exited with non-zero status code: %CLI_EXIT%.
    echo Any verdict report above is unconfirmed; review the trace output for errors.
)
echo ==============================================================================
echo.

if not "%1"=="--no-pause" (
    echo Press any key to close this terminal window...
    pause >nul
)

exit /b %CLI_EXIT%
