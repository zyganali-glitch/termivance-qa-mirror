# Termivance

**Software retirement, proven within bounds.**

Termivance is a **Proof-Bounded Software Retirement Protocol** for GitLab. It answers a question every platform team eventually faces — *"can we safely turn this off?"* — with an auditable, deterministic lifecycle instead of a decommissioning checklist and a leap of faith.

One real **GitLab Duo Custom Flow agent** investigates a retirement request and proposes candidate obligations. A **deterministic Python authority** independently corroborates every claim against provider facts, evaluates the complete obligation graph, and alone owns targeting, authorization, mutation, and verdicts. AI proposes; deterministic code decides.

> Built for [GitLab Transcend — Life After Code (October 2026)](https://gitlab-transcend.devpost.com/), Path A / Start Fresh / **Supervised** autonomy.
> Canonical repository: <https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance> (MIT).

---

## Why deleting code is not retiring software

Teams "retire" a service by deleting a DNS entry or stopping a server — and assume it's gone. But retirement without proof is just downtime with paperwork:

- **Resurrection.** The repository still contains a CI job like `create-pages` with `pages: true`. Weeks later, a dependency bot or unrelated push triggers the pipeline, and the "retired" site silently republishes — re-exposing vulnerabilities and cost.
- **Unverified absence.** "It 404s for me" is not proof a resource is gone; an access error is not an absence observation.
- **Unbounded claims.** "The service is deleted" says nothing about *which* surfaces were checked, *when*, and *how fresh* that evidence is.

Termivance treats retirement as a proof problem: every prerequisite — target identity, provider observations, permissions, redeployment paths, operator authorization, evidence freshness — must be **satisfied and verifiable** before anything destructive may happen, and every claim it makes is explicitly bounded.

## The protocol, and what actually happened in this repository

$$\text{DISCOVER} \rightarrow \text{ANALYZE} \rightarrow \text{AUTHORIZE} \rightarrow \text{RETIRE} \rightarrow \text{PROVE} \rightarrow \text{WATCH}$$

The demonstrated end-to-end run (all evidence committed under [`evidence/b4/`](evidence/b4/)):

1. A human filed a **neutral retirement request** on [Issue #5](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/issues/5).
2. The genuine **Duo Custom Flow** (Catalog Item `1018562`, Session `9710085`) autonomously inspected the target repository and discovered the surviving `create-pages` redeployment mechanism.
3. Deterministic Python **corroborated the candidates** against live provider facts (4 corroborated, 2 unresolved, 1 contextual — unobservable claims stay `UNRESOLVED`, never promoted).
4. The **Retirement Obligation Graph** evaluated 8 obligations → 3 violated, 1 unknown → **`SAFE_TO_RETIRE: BLOCKED`**.
5. The real disposable target — a GitLab Pages site that genuinely serves HTTP 200 with marker `TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a` — **remains published**, because the only authorized unpublish path is fail-closed: the operator holds `Developer` (GitLab returns 403 on the Pages admin API), the hackathon organizer formally denied Maintainer access, and no operator-signed single-use ledger entry exists.
6. Termivance published the deterministic outcome back to Issue #5 for **human review**, with bounded repair guidance, freshness boundaries, and a tamper-evident proof capsule.

**A correctly blocked unsafe retirement is the product working**, not failing: the same engine that would execute a fully proven, fully authorized retirement refuses this one — on exactly the evidence boundaries it discovered.

## Architecture and trust boundaries

```
┌─────────────────────────────── GitLab (canonical) ───────────────────────────────┐
│                                                                                  │
│  Human request        GitLab Duo Custom Flow            Deterministic Python     │
│  (Issue #5)   ─────▶  Catalog 1018562 / Session 9710085 ─────▶  Termivance core   │
│                        • list_repository_tree               • GET-only client    │
│                        • get_repository_file               • obligation graph    │
│                        • candidate obligations  ──(advisory)─▶ • corroboration   │
│                                                          • authorization gates │
│  Outcome note ◀─────────────────────────────────────  • sealed ledger           │
│  (human review)                                        • verdicts & capsule     │
│                                                                                  │
│  GitLab CI (every push): ruff + 563 tests + 40 safety assertions                 │
└──────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼ (one-way mirror, SHA-exact)
┌───────────────────── GitHub (QA-only mirror, non-canonical) ─────────────────────┐
│  Independent observer (6-hour cron + dispatch): 21+ live GitLab API reads,       │
│  source/evidence SHA-256 manifests, fail-closed drift detection (PASS / IN_SYNC) │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**The authority contract is absolute:** model text can never grant permissions, mutate providers, or award verdicts. The counterfactual is proven in the codebase — with identical provider facts, the deterministic verdict is `BLOCKED` whether or not Duo's candidates are present.

## Three core innovations

1. **Retirement Obligation Graph (ROG).** Retirement modeled as an auditable directed graph: target identity, provider observations, open work items, redeployment paths, required permissions, and operator approvals must all evaluate to satisfied before retirement proceeds.
2. **Bounded Absence.** Absence is negative evidence bound to an explicit target, checked surfaces, exact timestamps, and a contractual freshness window (TTL ≤ 900 s). Termivance proves verified state transitions — it refuses universal or perpetual absence claims.
3. **Retirement Reversal.** Neutralizing a service doesn't keep it gone. Termivance witnesses surviving deployment mechanisms (e.g. `create-pages` with `pages: true`) and distinguishes *resurrection risk*, *observed reappearance*, and *proven resurrection control*.

## Three independent verdicts — never merged into one status

| Verdict | Meaning | Demonstrated result |
|---|---|---|
| `SAFE_TO_RETIRE` | Deterministic eligibility from provider facts and satisfied obligations | **`BLOCKED`** (permissions + active redeployment path + no authorization) |
| `OBSERVED_ABSENT` | Empirical post-mutation verification across independent surfaces (API + served URL) | **`NOT_CLAIMED`** (no mutation was run) |
| `RESURRECTION_CONTROLLED` | Proven neutralization or active control of redeployment mechanisms | **`NOT_CLAIMED`** (mechanism present; monitoring ≠ control) |

## What the GitLab Duo agent does — and doesn't

The one deployed agent ([`flows/termivance_retirement_analyst.yaml`](flows/termivance_retirement_analyst.yaml), Catalog Item `1018562`, mention-triggered on issues) genuinely and autonomously:

- inspects repository trees and configuration files with real tools (`list_repository_tree`, `get_repository_file`);
- formulates structured, non-authoritative candidate obligations and posts them to the issue.

It does **not** execute code, mutate anything, or decide anything. The supervised continuation from a Duo note into deterministic Python is a real CLI command (`supervised-review --continue`) whose LIVE mode fails closed on every unobserved prerequisite (note read-back, author, issue ownership, target path, commit drift); a fully automatic single-request handoff is constrained by the GitLab Duo Agent Platform today (`coding_environment: none`, no execution tools) and is honestly documented as such — never narrated as autonomous.

## The deterministic authority

- **GET-only provider transport** that raises on any non-GET call.
- **Fail-closed preflights**: exact immutable target ID, full path, resource kind, endpoint, action, expiry; ambiguity is refused.
- **Authorization**: operator approval with provenance and HMAC; an atomic, fsync-backed **single-use sealed ledger** makes replay structurally impossible.
- **The only mutation capability** is `retire-pages --execute` → `DELETE /projects/:id/pages` on the single approved disposable target — graph-gated (`SAFE_TO_RETIRE` required), revalidated immediately before dispatch, read back on both channels afterward. Project deletion is structurally unreachable (allowlist + protected registry + tests).
- **Evidence decay**: a 6-state temporal machine (fresh → expiring → expired → revalidation-required → not-observed → inconclusive) — stale evidence can never authorize anything, and expiration can never improve a verdict.
- **Tamper-evident Proof Capsule** with SHA-256 manifest; `capsule-verify` fails closed on any alteration.

## Real disposable GitLab Pages demonstration

The retirement target is a real, isolated, operator-approved disposable project (`87785099`, `termivance-b3-disposable-pages-demo`) — never the canonical repository, never any shared resource. Its Pages site **is genuinely published and publicly served** (HTTP 200 with a unique marker, corroborated against repository source bytes at the observed commit — 5-level evidence record in [`evidence/b4/disposable_pages_publication.json`](evidence/b4/disposable_pages_publication.json)). That same project's surviving `create-pages` CI job is the demonstrated resurrection risk.

Its retirement is intentionally **not** executed: `BLOCKED_EXTERNAL` under the organizer's Maintainer denial. Unpublish remains `NOT_RUN / PERMISSION_BLOCKED`; absence and resurrection control remain `NOT_CLAIMED`. No simulated success, no environment-stop substitute, ever.

## Control Room (judge-facing viewer)

The **Control Room** ([`control_room/index.html`](control_room/index.html)) is a polished, enterprise-style, five-tab static viewer — Overview, Portfolio, Obligation Graph, What-if, Evidence & Audit — rendered entirely from recorded evidence:

- zero network requests at view time (works from `file://`; verified: empty resource entries, zero console errors, Lighthouse accessibility 100);
- every historical observation labeled `FRESH WHEN RECORDED`, never presented as live;
- interactive obligation graph, clearly-hypothetical what-if factors (`PROJECTED_NOT_OBSERVED`), full corroboration matrix, resurrection witness, repair sets, and the 7-step supervised review pipeline.

It is deliberately **not deployed on public hosting**: GitLab Pages on the canonical project would default to members-only visibility, and making it public requires a Maintainer setting change that the organizer has denied for this namespace (see the feasibility study in the [Master Plan §10.3](plans/TERMIVANCE_MASTER_EXECUTION_PLAN.md)). The local `file://` experience is the verified, guaranteed path — and public deployment is optional for Path A eligibility.

## Try It Out

```bash
git clone https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance.git
cd termivance
python -m pip install -e ".[dev]"        # Python 3.12+
```

**Open the Control Room** (no network needed):

```bash
# Windows: just double-click control_room\index.html, or:
start control_room\index.html
# POSIX:
open control_room/index.html   # or xdg-open
```

**Read-only CLI tour** (all safe; anonymous GET-only provider reads, $0.00):

```bash
termivance status                            # truthful local status snapshot
termivance doctor                            # environment sanity checks
# live multi-resource portfolio over the four real projects (GET-only, no token):
termivance portfolio --project-ids 87785099,87779099,87777871,87786164 --anonymous --policy config/retirement_policy.b3_disposable.json
# the real demonstrated chain:
termivance supervised-review --execute --target 87785099            # live 7-step investigation → BLOCKED
termivance verify-pages-publication --project-id 87785099 --json    # 5-level publication evidence
termivance monitor-resurrection --project-id 87785099 --receipt evidence/b4/decision.json --json
termivance repair-sets --project-id 87785099 --from-record evidence/b4/snapshot.json --json
termivance check-decay --timestamp 2026-10-21T06:08:09Z --expected-sha 54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d --json
termivance capsule-verify evidence/b4/proof_capsule.json
```

**See the safety refusals** (negative controls — both must fail closed):

```bash
# real mutations require an independent operator trust policy → refused (exit 2):
termivance retire-pages --execute --project-id 87785099 --policy config/retirement_policy.b3_disposable.json
# (and even with a full trust document, protected targets like the canonical repo
#  87779099 are structurally refused — proven by the test suite and CI assertions)
# offline replay can never publish → exit 2, OFFLINE_PUBLICATION_REFUSED:
termivance supervised-review --continue --issue-iid 5 --session-id 9710085 --note-id 4045401991 --target-id 87785099 --expected-sha 54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d --mode offline-replay --publish
```

**Full local verification:**

```bash
ruff check .     # clean
pytest -q        # 563 passed
python scripts/ci_safety_assertions.py   # 40/40 PASS, network-free
```

Interpretation guide: every command prints explicit verdicts and `NOT_RUN`/`NOT_OBSERVED` states — a refusal is a correct result, and no output ever claims more than was observed. The complete command reference (risk map, simulation, workflow, reconciliation, witness, continuation) is in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) and the [Master Plan](plans/TERMIVANCE_MASTER_EXECUTION_PLAN.md).

## Tests, CI, and independent QA

- **563 deterministic tests** (`pytest -q`), `ruff` clean, **40 network-free safety-contract assertions** — all green in GitLab CI on every push to `main` (visible pipeline history on the canonical repository).
- An independent **GitHub Actions observer** (non-canonical QA mirror, [termivance-qa-mirror](https://github.com/zyganali-glitch/termivance-qa-mirror)) runs on a 6-hour schedule and on demand: 21+ live GitLab API observations, SHA-exact one-way mirror, source and evidence SHA-256 manifests, and fail-closed drift detection. Latest verified runs are recorded in [`docs/HANDOFF.md`](docs/HANDOFF.md).
- Claim/proof separation for every batch is maintained in [`docs/EVIDENCE_MATRIX.md`](docs/EVIDENCE_MATRIX.md); the nine-stage DevSecOps coverage audit is [`docs/DEVSECOPS_STAGES.md`](docs/DEVSECOPS_STAGES.md).

## Limitations, security, and zero-cost posture — stated plainly

- **Not executed:** the destructive Pages unpublish (`NOT_RUN / PERMISSION_BLOCKED`), `OBSERVED_ABSENT` and `RESURRECTION_CONTROLLED` (both `NOT_CLAIMED`). These are honest boundaries, not gaps in implementation — the full authorized-execution path is implemented and adversarially tested.
- **Supervised autonomy boundary:** the Duo→Python continuation is operator-triggered; a single-request automatic handoff is not currently supported by the GitLab Duo Agent Platform for this flow configuration and is never claimed.
- **Protected targets:** the canonical repository (`87779099`), the organizer showcase (`87777871`), and the diagnostic project (`87786164`) are on the protected registry and structurally untargetable.
- **Privacy & secrets:** no tokens, personal paths, or credentials in the repository, Control Room, or CI; the QA bridge uses unauthenticated public reads only; no GitLab credential is ever exported to GitHub.
- **Cost:** **$0.00 incremental personal spend** — GitLab-native free tier only; no paid APIs, no cloud accounts, no third-party hosting.

## Competition context

- **Event:** [GitLab Transcend — Life After Code](https://gitlab-transcend.devpost.com/), October 2026 · Path A (Start Fresh) · Supervised autonomy level.
- **DevSecOps stage coverage:** evidence-bound audit with per-stage qualifications in [`docs/DEVSECOPS_STAGES.md`](docs/DEVSECOPS_STAGES.md) (core: Plan, Verify, Secure, Govern; qualified: Create, Package, Configure, Monitor; Release honestly unchecked).
- **Demo video:** a public YouTube demonstration under three minutes is part of the submission (operator-produced; this repository contains the runbook in [Master Plan §11](plans/TERMIVANCE_MASTER_EXECUTION_PLAN.md)).
- Deadline: 2026-10-27 13:00 UTC / 16:00 Türkiye.

## License

MIT — see [LICENSE](LICENSE).
