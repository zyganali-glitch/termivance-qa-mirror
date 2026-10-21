# Termivance — Judge Demo Script (end-to-end, <3 minutes)

This is the canonical demonstration path for the GitLab Transcend *Life After Code* submission. Every step is labeled with its honest evidence class:

- `LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS` — observed live by the independent unauthenticated observer.
- `RECORDED_LIVE` — a real provider observation captured at a recorded time (freshness is evaluation-time only).
- `RECORDED_HISTORICAL` — a genuine archived session/note; bodies not anonymously readable.
- `FIXTURE` — offline replay data, clearly labeled, never presented as live.
- `NOT_OBSERVED` / `NOT_RUN` — honestly absent; never promoted.

**The chain is operator-initiated (Supervised).** A human retirement request → genuine Duo investigation → deterministic corroboration → BLOCKED decision → bounded repair guidance → proof decay boundary → human review. It is never narrated as a single-trigger autonomous flow: the Duo-to-Python continuation is an operator-run CLI command by documented platform constraint (`coding_environment: none`; no execution tools available to the flow agent).

## The end-to-end narrative (one pass)

1. **Human retirement request** — canonical Issue #5, a neutral unprimed prompt. `RECORDED_HISTORICAL` (issue identity observable live; note bodies 401 to anonymous reads).
2. **Genuine Duo multi-step investigation** — Catalog Item `1018562`, Session `9710085`: the agent inspected the target repository tree and `.gitlab-ci.yml`, discovered the surviving `create-pages` (`pages: true`) redeployment mechanism and the permission boundary, and posted candidate obligations (note `4045401991`). `RECORDED_HISTORICAL`.
3. **Identified obligations + source evidence** — 7 candidate claims: 4 corroborated, 2 unresolved, 1 contextual. `RECORDED_LIVE` corroboration against provider facts at commit `54fcc9ff`.
4. **Deterministic corroboration** — `termivance supervised-review --execute --target 87785099`: live anonymous provider reads, candidate reconciliation, counterfactual analysis (AI input does not alter the verdict). `EXECUTED_NOW` when run.
5. **Retirement Obligation Graph** — 8 obligations evaluated; 4 satisfied, 3 violated, 1 unknown. Control Room Graph tab. Recorded evidence.
6. **Fail-closed authorization decision** — `SAFE_TO_RETIRE = BLOCKED` (Pages administration 403; redeployment path active; no operator-signed ledger entry). Recorded + replayable live.
7. **Bounded candidate repair recommendations** — `termivance repair-sets`: topologically ordered remediation guidance; Maintainer role honestly classified `EXTERNALLY_UNAVAILABLE_UNDER_CONTEST_CONDITIONS`. Recorded evidence.
8. **Publication presence and redeployment risk** — the disposable target really serves HTTP 200 with marker `TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a` (5-level evidence, Level 2 honestly `NOT_OBSERVED_NOT_FOUND`); the surviving `create-pages` job can republish it. `RECORDED_LIVE` (regenerated 2026-10-21; present-tense narration requires a fresh live read at demonstration time — a historical HTTP 200 never automatically becomes a current observation).
9. **Evidence freshness / current-truth monitoring** — `termivance monitor-resurrection` + `check-decay`: 900s TTL, fail-closed staleness; the monitor requires fresh current observations for any positive present-tense verdict. `RECORDED_LIVE`.
10. **Proof Capsule and explicit limitations** — `capsule-build` + `capsule-verify`: SHA-256 manifest; mutation/absence sections `NOT_RUN`/`NOT_OBSERVED`. Local deterministic artifact.
11. **Human review** — the deterministic outcome is published back to Issue #5 (note `4045409264`) for human review. `RECORDED_HISTORICAL`.

**What is deliberately NOT shown as done:** a successful Pages retirement (blocked, `NOT_RUN / PERMISSION_BLOCKED`), `OBSERVED_ABSENT` (`NOT_CLAIMED`), `RESURRECTION_CONTROLLED` (`NOT_CLAIMED`), any simulated provider success, any green "current freshness" from historical data.

## Setup (pre-recorded, not in the video)

```bash
python -m pip install -e ".[dev]"
ruff check . && python -m pytest -q        # 563 passed
# optional fresh read-only evidence refresh (anonymous, GET-only, $0.00):
termivance verify-pages-publication --project-id 87785099 --json --out evidence/b4/disposable_pages_publication.json
termivance monitor-resurrection --project-id 87785099 --receipt evidence/b4/decision.json --json --out evidence/b4/resurrection_monitoring.json
python scripts/build_control_room.py --portfolio evidence/b4/portfolio.json --risk-map evidence/b4/risk_map.json --decision evidence/b4/decision.json --simulation evidence/b4/simulation.json --workflow evidence/b4/workflow_assessment.json --capsule evidence/b4/proof_capsule.json --duo-external evidence/b4/duo_session_9671626_readback.json --duo-reconciliation evidence/b4/duo_reconciliation.json --duo-reconciliation-primary evidence/b4/duo_reconciliation_issue_5.json --witness evidence/b4/witness_87785099.json --supervised-review evidence/b4/supervised_review.json --pages-publication evidence/b4/disposable_pages_publication.json --resurrection-monitoring evidence/b4/resurrection_monitoring.json --repair-sets evidence/b4/bounded_repair_sets.json --freshness-decay evidence/b4/freshness_decay_record.json
```

Open `control_room/index.html` in a browser (works from `file://`, zero network at view time).

## Filming sequence (matches the video runbook in the Master Plan, Section 11)

| Scene | Screen | What to show | Evidence label |
|---|---|---|---|
| SC-01 | Control Room — Overview | First-screen explainer; `RETIREMENT BLOCKED` hero; why (403 + redeployment + no authorization) | Recorded snapshot, `FRESH WHEN RECORDED` |
| SC-02 | Control Room — Overview | Three independent claims: `SAFE_TO_RETIRE: BLOCKED`, `OBSERVED_ABSENT: NOT_CLAIMED`, `RESURRECTION_CONTROLLED: NOT_CLAIMED` | Recorded |
| SC-03 | GitLab browser — Issue #5 + Duo session URL | The neutral request and the agent's investigation (fallback: Control Room Evidence tab, since session UI is 404 to non-members) | `RECORDED_HISTORICAL` |
| SC-04 | Control Room — Evidence & Audit → Candidate corroboration | Session `9710085`: 4 corroborated / 2 unresolved / 1 contextual; row `duo-9710085-cand-01` (`create-pages` @ `54fcc9ff`) | Recorded |
| SC-05 | Terminal | `scripts/run_supervised_review.bat --no-pause` (or `termivance supervised-review --execute --target 87785099`) — live deterministic evaluation; the launcher's `LAUNCHER VERDICT REPORT` must show `CLASSIFICATION: VERDICT_CONFIRMED_BLOCKED` before narrating the BLOCKED result | `EXECUTED_NOW` (live, read-only) |
| SC-06 | Browser — disposable Pages URL | FRESH browser read of the URL during filming: if it loads, show the marker live (LIVE narration); if not, show the Control Room Pages-publication card (HISTORICAL, past-tense narration). A recorded HTTP 200 never automatically becomes a current observation. | `LIVE` when freshly read during filming, else `RECORDED_LIVE` fallback |
| SC-07 | Control Room — Graph | Click `resource:ci_redeployment:87785099`; edges highlight to the BLOCKED decision | Recorded |
| SC-08 | Control Room — What-if + Evidence & Audit → "Deterministic decision" | `PROJECTED_NOT_OBSERVED` factors; bounded repair-set card; 900s decay/freshness card | Recorded |
| SC-09 | GitLab CI + GitHub Actions | Green verification pipeline; independent observer `PASS / IN_SYNC` | `LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS` |
| SC-10 | Control Room — Overview (final) | Tagline close: "Software retirement, proven within bounds." | Recorded |

Duration budget, complete voice-over and the timed narration-matching subtitle track: see Master Plan Section 11 (target 174 s, hard limit 180 s) and [`assets/demo/subtitles/termivance_demo_en.srt`](assets/demo/subtitles/termivance_demo_en.srt).

## Honest boundary lines (say these on camera)

- "A real Duo Custom Flow investigated the target — its candidates are advisory; deterministic Python alone decides."
- "The target's Pages site is genuinely published — that's presence, not retirement. (Say 'is serving' only after a fresh live read during filming; otherwise say 'was independently observed serving'.) Unpublishing stays blocked: the operator lacks Maintainer, and the organizer denied it. Termivance refuses to mutate without proof and permission."
- "Evidence has a freshness window — 900 seconds. Older observations are historical, never current truth."
- "The what-if page is clearly hypothetical — a projection can never mint a verdict."

## Negative controls (read-only, safe to run live)

```bash
# real mutations require an independent operator trust policy → refused (exit 2):
termivance retire-pages --execute --project-id 87785099 --policy config/retirement_policy.b3_disposable.json
# (with a full trust document, protected targets such as 87779099 remain
#  structurally refused — proven by the test suite and the 40 CI safety assertions)
# offline replay can never publish (exit 2, OFFLINE_PUBLICATION_REFUSED):
termivance supervised-review --continue --issue-iid 5 --session-id 9710085 --note-id 4045401991 --target-id 87785099 --expected-sha 54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d --mode offline-replay --publish
```

Both refusals are product features: fail-closed safety, demonstrated live.
