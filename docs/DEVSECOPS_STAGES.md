# Termivance — Nine DevSecOps Stage Evidence Matrix

**Work item:** `WORK-B4-23` (final evidence-based reassessment, 2026-10-21)
**Purpose:** Judge-readable, evidence-bound audit of Termivance's coverage of the nine GitLab DevSecOps lifecycle stages defined by the GitLab Transcend *Life After Code* (October 2026) challenge.

## Official competition criterion

The official challenge states: *"The challenge is organized around nine GitLab DevSecOps stages: plan, create, verify, package, secure, release, configure, monitor, and govern. Participants do not need to use every feature within a stage, and touching a stage counts toward coverage."*

Termivance applies a **stricter internal standard** than "touching": each stage below is classified by what the finished product *actually, verifiably does*, with exact source and live-provider evidence, and every qualification is disclosed. Nothing on this page inflates a stage claim; nothing pretends that ordinary CI is agentic, that a discovery read is configuration control, or that a blocked mutation is a completed release.

## Summary matrix

| # | Stage | What genuinely happened | Automation class | Recommendation | Confidence |
|---|---|---|---|---|---|
| 1 | **Plan** | Real GitLab Duo Custom Flow (Catalog `1018562`, Session `9710085`) autonomously investigated a neutral retirement request on Issue #5, inspected the target repository, and proposed candidate obligations | Genuine agent automation (Duo) | **YES — core** | Highest |
| 2 | **Create** | Duo agent autonomously authored structured analysis notes on GitLab issues; deterministic publisher posted the outcome note (Note `4045409264`). No agent-generated source code or MRs | Agent-authored issue content (not code) | **Qualified — defensible with disclosure** | Medium |
| 3 | **Verify** | GitLab CI runs the full deterministic test suite (540 tests), `ruff`, and 40 network-free safety assertions on every pushed commit | Ordinary CI (deterministic, not agentic) | **YES — core** | Highest |
| 4 | **Package** | Tamper-evident Proof Capsule (`capsule-build` / `capsule-verify`) with SHA-256 integrity manifest binding decision, evidence, reconciliation and witness records | Deterministic application artifact (not GitLab Package Registry) | **Qualified — defensible with disclosure** | High |
| 5 | **Secure** | Fail-closed authorization preflights, HMAC operator approval, sealed single-use durable ledger, protected-target registry, endpoint-restricted mutation allowlist | Deterministic security core | **YES — core** | Highest |
| 6 | **Release** | Real GitLab Pages publication exists on the disposable target (served HTTP 200 with marker), but Termivance's own release action (bounded Pages unpublish) is fail-closed `BLOCKED_EXTERNAL` under the organizer's Maintainer denial | Implemented but not executed (permission-blocked) | **NO — leave unchecked** | Highest |
| 7 | **Configure** | GET-only discovery of environments, deployments, CI configuration and Pages state across four projects; resurrection monitor reads the target's own `.gitlab-ci.yml` at the exact observed commit | Read-only discovery (no configuration writes) | **Qualified — defensible with disclosure** | High |
| 8 | **Monitor** | On-demand exact-target resurrection monitor (12 fail-closed invariants) plus a scheduled (6-hour cron) independent GitHub Actions observer of live GitLab APIs; documented tripwire | Real monitoring automation (on-demand + external scheduled CI) | **Qualified — defensible with disclosure** | High |
| 9 | **Govern** | Protected-target registry, deterministic obligation-graph policy engine, immutable audit trail, non-authoritative AI boundary proven by counterfactual analysis | Deterministic governance core | **YES — core** | Highest |

**Recommended Devpost selections (subject to operator and auditor acceptance):**
- **Strongly recommended (core, unqualified):** Plan, Verify, Secure, Govern.
- **Defensible with one-line disclosure** (under the official "touching a stage counts" criterion): Create, Package, Configure, Monitor. If selected, the Devpost story must carry the qualifications below verbatim in spirit.
- **Not recommended:** Release — the one destructive release action is intentionally and verifiably blocked; claiming it would misrepresent the product's central safety property.

## Six-dimension attribution standard

Every stage is attributed across six dimensions so judges can see exactly who or what did what:

1. **Genuine Duo agent action** — autonomous analysis/tool invocation by the one real Custom Flow agent.
2. **Deterministic Python action** — graph evaluation, ledger sealing, corroboration, capsule hashing.
3. **Ordinary GitLab CI execution** — runner executing pytest/linter/safety assertions (never agentic).
4. **External GitHub QA** — the independent, unauthenticated observer of live GitLab APIs.
5. **Operator-triggered action** — issue mentions, CLI launches, approvals.
6. **Historical recorded evidence** — archived sessions and previous snapshots.

## Per-stage detail

### 1. Plan — YES (core)

- **Official interpretation:** planning, context analysis, and work-item driven investigation.
- **What happened:** a human filed a neutral, unprimed retirement request on canonical Issue #5. The genuine Duo Custom Flow (Catalog Item `1018562`, Session `9710085`, agent note `4045401991`) autonomously inspected the disposable target `87785099` repository tree and `.gitlab-ci.yml`, discovered the surviving `create-pages` redeployment mechanism, and proposed candidate retirement obligations.
- **Duo (agent):** autonomous repository inspection (`list_repository_tree`, `get_repository_file`) and candidate formulation.
- **Deterministic Python:** `supervised_review.py` ingests and corroborates the candidates against independent provider facts; `engine.py` evaluates the obligation graph.
- **Ordinary CI / external QA:** none for this stage.
- **Operator-triggered:** the initial issue mention (the human "single request" of the Supervised pattern).
- **Genuinely automated:** yes — the investigation itself is agent-autonomous.
- **Evidence:** Issue #5 note `4045401991`; `evidence/b4/duo_session_9710085_readback.json`; `evidence/b4/duo_reconciliation_issue_5.json` (4 CORROBORATED / 2 UNRESOLVED / 1 CONTEXTUAL_ONLY).
- **Observation class:** `RECORDED_HISTORICAL` (session) + `LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS` (issue identity) — session UI is 404 to non-members; artifacts are inspectable in the Control Room.
- **Limitations:** candidates are advisory only; the deterministic engine never promotes AI text to fact.
- **Recommendation:** **YES.**

### 2. Create — Qualified

- **Official interpretation:** source code / merge request creation and authoring.
- **What happened:** the Duo agent authored structured markdown analysis (candidate obligations, observed facts, non-authority disclaimers) posted as issue notes; the deterministic publisher (`publisher.py`) created the outcome note `4045409264` on Issue #5 via the GitLab REST API.
- **Duo (agent):** authored the candidate-obligation note content autonomously.
- **Deterministic Python:** `GitLabPublisher.create_issue_note` publishes the deterministic outcome note with SHA-256 read-back verification.
- **Ordinary CI / external QA:** none.
- **Operator-triggered:** issue mention that started the flow.
- **Genuinely automated:** the *content authoring and note creation* is automated; **no source code or merge requests are agent-generated**.
- **Evidence:** Issue #5 notes `4045401991` (agent) and `4045409264` (outcome); `evidence/b4/duo_note_4045401991.json`.
- **Observation class:** `RECORDED_HISTORICAL` (note bodies; anonymous note reads return 401).
- **Limitations:** Create-stage credit here means agent-authored issue content, not code generation — this must be disclosed if the box is checked.
- **Recommendation:** **Qualified YES with disclosure** ("agent-authored analysis notes, not code/MRs").

### 3. Verify — YES (core)

- **Official interpretation:** automated testing and quality gates.
- **What happened:** every push to canonical `main` runs the GitLab CI `verification` job: `ruff check`, the full **540-test** pytest suite, CLI smoke checks, and **40 network-free CI safety assertions** (`scripts/ci_safety_assertions.py`).
- **Ordinary CI:** yes — this is deterministic CI, not agentic verification, and is presented as such.
- **Genuinely automated:** yes.
- **Evidence:** verified pipeline history on `main` (e.g. pipeline `2971888764`, job `17348108462` `SUCCESS` at `b59735f`; every batch push has a verified pipeline); `.gitlab-ci.yml`.
- **Observation class:** `LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS` (pipeline and job status via public API); raw job traces are 401 to anonymous reads — honestly `NOT_OBSERVED`.
- **Limitations:** none material; suite size grows per batch (historical milestones: 381 → 437 → 505 → 530 → 540).
- **Recommendation:** **YES.**

### 4. Package — Qualified

- **Official interpretation:** packaging artifacts (GitLab Package Registry, container registry, release assets).
- **What happened:** `capsule-build` assembles a tamper-evident JSON **Proof Capsule** binding target identity, decision, evidence receipts, Duo reconciliation, and resurrection witness under a SHA-256 integrity manifest; `capsule-verify` fails closed on any tampering.
- **Deterministic Python:** `capsule.py`.
- **Genuinely automated:** yes, as an application-level artifact pipeline.
- **Evidence:** `evidence/b4/proof_capsule.json`; capsule-verify PASS in CI and locally.
- **Observation class:** local/CI deterministic artifact (recorded in repo).
- **Limitations:** this is **not** GitLab Package Registry automation — disclosed if checked.
- **Recommendation:** **Qualified YES with disclosure** ("tamper-evident proof capsule, not Package Registry").

### 5. Secure — YES (core)

- **Official interpretation:** security policy, vulnerability and access control enforcement.
- **What happened:** fail-closed authorization preflights (exact target identity, immutable numeric ID, full path, endpoint, action, expiry); HMAC-SHA256 operator approval verification; atomic fsync-backed single-use ledger (no replay); endpoint-restricted mutation allowlist (`DELETE /projects/:id/pages` only — project deletion structurally refused); protected-target registry (`87779099`, `87777871`, `87786164`).
- **Deterministic Python:** `ledger.py`, `approval_source.py`, `retirement.py`, `protected.py`, `pages.py`.
- **Ordinary CI:** 40 network-free safety assertions re-prove these contracts in the pipeline.
- **Genuinely automated:** yes.
- **Evidence:** `scripts/ci_safety_assertions.py` (40/40 PASS in CI); adversarial suites `tests/test_b4_regression_integrity.py`, `tests/test_b4_causal_authority_repair.py`, `tests/test_b4_resurrection_monitoring.py`.
- **Observation class:** deterministic contracts verified in CI.
- **Limitations:** the HMAC key is optional in unconfigured environments (approval then *attributed*, not cryptographically proven — the durable ledger is what prevents replay); disclosed in code and docs.
- **Recommendation:** **YES.**

### 6. Release — NO

- **Official interpretation:** deployment/release automation.
- **What happened:** the disposable target `87785099` really serves a published GitLab Pages site (HTTP 200 with unique marker `TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a`, source-corroborated at commit `54fcc9ff`) — deployed by the **target's own CI** (`create-pages` job), which is precisely the resurrection risk Termivance detects. Termivance's own release-stage action — the bounded, authorized Pages unpublish (`DELETE /projects/87785099/pages`) — is implemented, tested, and **fail-closed BLOCKED**: the operator holds Developer (403 on the Pages API) and the hackathon organizer formally denied Maintainer access.
- **Genuinely automated:** the refusal is deterministic and real; the mutation itself is `NOT_RUN / PERMISSION_BLOCKED`.
- **Evidence:** `evidence/b4/disposable_pages_publication.json` (5-level evidence: Level 1 CI job success, Level 2 `NOT_OBSERVED_NOT_FOUND`, Level 3 403, Level 4 served 200, Level 5 marker + source corroboration); organizer decision on Showcase Work Item #1; `evidence/b4/decision.json` (`BLOCKED`).
- **Observation class:** live served-URL observation (`RECORDED_LIVE`, regenerated 2026-10-21) + recorded permission boundary.
- **Limitations:** claiming the Release stage would misrepresent a deliberately blocked destructive action as a completed release.
- **Recommendation:** **NO — leave unchecked.** The fail-closed refusal is presented as a product strength, not as release automation.

### 7. Configure — Qualified

- **Official interpretation:** configuration of environments, deployments, and runtime configuration.
- **What happened:** GET-only discovery across four projects (`portfolio`): environments, deployments, releases, packages, CI Pages mechanisms, Pages state — every record carrying endpoint, timestamp, freshness and `NOT_AUTHORIZING`; the resurrection witness and monitor read the target's own `.gitlab-ci.yml` at the exact observed commit.
- **Deterministic Python:** `portfolio.py`, `gitlab_client.py` (GET-only transport that raises on any non-GET), `witness.py`, `resurrection_monitor.py`.
- **Genuinely automated:** yes — as **read-only discovery**.
- **Evidence:** `evidence/b4/portfolio.json`, `evidence/b4/witness_87785099.json`, `evidence/b4/resurrection_monitoring.json`.
- **Observation class:** `LIVE_ANONYMOUS` recorded reads (access-limited surfaces honestly `NOT_OBSERVED` with 401/403/404 preserved).
- **Limitations:** Termivance never writes configuration — discovery, not configuration management; disclosed if checked.
- **Recommendation:** **Qualified YES with disclosure** ("read-only configuration discovery").

### 8. Monitor — Qualified

- **Official interpretation:** monitoring of deployed software and runtime state.
- **What happened:** (a) an on-demand exact-target **resurrection monitor** (`monitor-resurrection`) with 12 fail-closed invariants — exact URL binding, positively-observed CI configuration, independent current-observation freshness, current-freshness precedence for any positive present-tense verdict; (b) an independent **GitHub Actions observer** on a 6-hour cron (plus on-demand dispatch) that reads 21+ live GitLab API endpoints, verifies mirror/source parity and fails closed on drift; (c) a documented tripwire (`tripwire.py`) for comparing recorded passes.
- **Deterministic Python + external CI:** yes.
- **Genuinely automated:** yes — scheduled independent observation is real recurring monitoring; the product monitor is on-demand.
- **Evidence:** `evidence/b4/resurrection_monitoring.json` (regenerated live 2026-10-21T15:15Z: `HISTORICAL_RECEIPT_UNVERIFIED`, `MECHANISM_PRESENT`, served marker observed); verified GitHub observer runs (e.g. run `39599023519` `PASS / IN_SYNC` at `b59735f`).
- **Observation class:** `LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS` (observer) + `RECORDED_LIVE` (monitor records).
- **Limitations:** the scheduled observer is external QA CI (not GitLab-native agentic monitoring) and the product monitor is on-demand rather than continuous; no `RESURRECTION_CONTROLLED` is claimed. Disclosed if checked.
- **Recommendation:** **Qualified YES with disclosure** ("on-demand monitor + independent scheduled observer").

### 9. Govern — YES (core)

- **Official interpretation:** compliance, policy enforcement, audit, and access governance.
- **What happened:** protected-target registry (canonical, showcase and diagnostic projects structurally untargetable); deterministic obligation-graph policy engine where no policy or authorization success can override an inconclusive graph; immutable audit trail (historical receipts preserved without rewriting; tampered ledgers fail closed); the non-authoritative AI boundary is *proven* by counterfactual analysis (identical provider facts yield the same `BLOCKED` verdict with or without Duo candidates).
- **Deterministic Python:** `protected.py`, `engine.py`, `counterfactual.py`, `continuation_ledger.py`.
- **Genuinely automated:** yes.
- **Evidence:** `evidence/b4/supervised_review.json` (counterfactual section); protected-target refusal tests; ledger corruption/recovery adversarial tests.
- **Observation class:** deterministic contracts verified by the 540-test suite and 40 CI safety assertions.
- **Limitations:** none material.
- **Recommendation:** **YES.**

## Reconciliation notes

- This matrix supersedes the historical four-stage default (Plan, Verify, Secure, Govern) recorded before `WORK-B4-18`–`22` completed. The four core stages are unchanged; the reassessment upgrades Create, Package, Configure and Monitor from "Lean NO" to "defensible with disclosure" **only because the official criterion explicitly counts touching a stage**, and each of these stages is now touched by real, evidenced, automated capability with its qualification stated.
- The deterministic boundary between "genuine automation" and "touching" is preserved: no stage recommendation on this page relies on conflating ordinary CI with agentic action, discovery with control, or a blocked mutation with a release.
- Final checkbox selections remain an operator decision subject to independent auditor acceptance (`WORK-B4-26` Checkpoint A/B).
