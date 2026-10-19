# Termivance

**Software retirement, proven within bounds.**

Termivance is a **Proof-Bounded Software Retirement Protocol** for GitLab Transcend — Life After Code (2026), **Path A / Start Fresh / Supervised**. One GitLab Duo Custom Flow agent assists with retirement context and orchestration, while a deterministic Python core controls exact targeting, obligation decisions, approval, mutation, evidence, and verdicts.

Core concepts: **Retirement Obligation Graph**, **Bounded Absence**, and **Retirement Reversal**. Independent verdicts: `SAFE_TO_RETIRE`, `OBSERVED_ABSENT`, and (only after actual detection/control evidence) `RESURRECTION_CONTROLLED`. We never claim universal absence.

## Status

**B4 consolidated QA repair completed (2026-10-19)** after independent batch QA, followed by the **final consolidated closure** the same day (four mandatory QA correctness fixes A–D + evidence-bound Duo reconciliation + resurrection witness; final push/bridge recorded in the closure report; independent QA of the closure commit remains the external next step). B1 (live Duo Custom Flow) and B2 (deterministic BLOCKED gate) stand; B3's deterministic executor and bounded absence stand, with the live unpublish still **`BLOCKED` on a real access boundary**; a genuine operator-triggered B4 Duo session (`9671626`, judge-facing analysis, read-only) exists on canonical issue #3. The repair closes the QA's material defects:

- **Trust-bound approvals** — approval identity must match an operator-held trust policy (username **and** provider-issued user ID, project allowlist, freshness, revocation, operator-held HMAC); `retire-pages --execute` refuses without `--operator-trust`. The operator HMAC cannot be disabled by a policy field (`signature_required=false` is refused at construction and load; verification is unconditional), and duplicate/conflicting approval-binding statements are refused as ambiguous.
- **One-contract ledger** — every mutating ledger operation is consolidated under the exclusive lock with per-entry digests and a one-way `RESERVED_BEFORE_MUTATION → CONSUMED_<outcome>` state machine; consumed/ambiguous authorizations can never be re-enabled; legacy v1 ledgers and locally edited entries are refused on load.
- **Receipts that cross-check** — receipts fail closed unless they match a durable ledger entry (binding, nonce, action, target, `CONSUMED_ACCEPTED`, 2xx, pre-state marker); unsigned SHA-256 is local tamper evidence, never authentication. The Control Room renders receipt truth states through a fail-closed classifier (`NOT_RUN`/`INVALID`/recorded verdict/`ATTEMPT_NOT_ACCEPTED`/`MUTATION_ACCEPTED`) — bare schema presence is never labeled live.
- **Multi-resource Portfolio + shared evidence** — v2 observes environments, deployments, releases, packages, issues, CI Pages mechanisms and Pages per project (each record `mutation_capability: NOT_AUTHORIZING`); a Pages-endpoint `404` is recorded as `PAGES_NOT_OBSERVED_404` and never promoted to absence; one `CrossResourceView` feeds both the risk map and the simulation, `INFERRED` edges never satisfy obligations, and a single interactive **Control Room v2** renders it (clickable graph + resource drilldown + read-only "What if", zero network/destructive controls).
- **Evidence-bound Duo reconciliation + resurrection witness** — `reconcile-duo` classifies the operator-confirmed Duo session's candidate claims against anonymous live evidence (4 `SUPPORTED` / 2 `UNRESOLVED` / 2 `NOT_AUTHENTICALLY_ATTRIBUTABLE` / 1 `UNSUPPORTED`; never authoritative; "consistent with, but not proof" stays `UNRESOLVED`); `witness-build` records the disposable target's **own** CI redeployment mechanism at the exact observed commit (`MECHANISM_PRESENT_IN_OBSERVED_CONFIG`) while explicitly never claiming absence or `RESURRECTION_CONTROLLED`. Both are bound into the proof capsule.

Suite: **306 tests**, ruff clean, **40/40** network-free CI safety assertions.

B4 also closes the P0 security defects (durable sealed-reservation ledger, GitLab-issue approval provenance, receipt-bound absence) and adds the six-capability **Retirement Control Plane**: read-only Portfolio, deterministic Risk Map, hypothetical Simulation, judge-facing Control Room, tamper-evident Proof Capsule with `capsule-verify`, and a 7-stage single-flow workflow orchestration.

- Canonical repo: https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance
- QA bridge (non-canonical): https://github.com/zyganali-glitch/termivance-qa-mirror
- Live B1 session: https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9650440
- Operator-confirmed B4 Duo session (read-only, non-authoritative): https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9671626 (agent comment on issue #3; contents not independently observable anonymously — see evidence ladder)

**The live retirement remains `BLOCKED` on a real, verified access boundary**, not on
the engine: the operator holds only `Developer` on the competition subgroup, GitLab's
Pages lifecycle (deploy + `DELETE /projects/:id/pages`) requires `Maintainer`, and no
GitLab PAT is present on the machine — authenticated evidence stays `NOT_RUN`. No destructive call is made without an exact-target operator
authorization. See `docs/HANDOFF.md` and `docs/EVIDENCE_MATRIX.md`.

## Try the B4 capabilities (read-only)

```bash
python -m pip install -e ".[dev]"
# live anonymous multi-resource portfolio over the four real projects (GET-only, no token):
termivance portfolio --project-ids 87785099,87779099,87777871,87786164 --anonymous --policy config/retirement_policy.b3_disposable.json
# deterministic risk map for a recorded decision, with the same portfolio evidence as context:
termivance risk-map --decision evidence/b4/decision.json --portfolio evidence/b4/portfolio.json
# hypothetical what-if (never mutates), sharing the portfolio snapshot as projection factors:
termivance simulate --project-id 87785099 --from-record evidence/b4/snapshot.json --portfolio evidence/b4/portfolio.json
# single-flow workflow plan and artifact assessment:
termivance workflow-plan --project-id 87785099 --full-path gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo --out-dir evidence/b4
termivance workflow-status --project-id 87785099 --full-path gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo --out-dir evidence/b4
# reconcile the Duo session's recorded candidate claims against anonymous live evidence (never authoritative):
termivance reconcile-duo --claims evidence/b4/duo_claims.json --project-id 87779099 --issue-iid 3 --session-url https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9671626 --out evidence/b4/duo_reconciliation.json
# resurrection counterexample witness for the exact disposable target (its own CI config at the exact commit):
termivance witness-build --project-id 87785099 --full-path gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo --out evidence/b4/witness_87785099.json
# judge control room v2 (rebuild data, then open control_room/index.html in a browser):
python scripts/build_control_room.py --portfolio evidence/b4/portfolio.json --risk-map evidence/b4/risk_map.json --decision evidence/b4/decision.json --simulation evidence/b4/simulation.json --workflow evidence/b4/workflow_assessment.json --capsule evidence/b4/proof_capsule.json --duo-external evidence/b4/duo_session_9671626_readback.json --duo-reconciliation evidence/b4/duo_reconciliation.json --witness evidence/b4/witness_87785099.json
# proof capsule (local integrity only):
termivance capsule-build --receipt <receipt.json> --out proof_capsule.json
termivance capsule-verify proof_capsule.json
```

Every command above is read-only or operates purely on recorded files.

## GitLab-native demo target

The retirement target is **one new, separate disposable GitLab Pages project**: a real static site published through GitLab CI/CD, then un-published using the exact-target GitLab Pages API after explicit bounded authorization. GitLab Pages API and publicly served URL are independently read back. GitLab environment status is checked separately and must not be confused with site removal. This verifies scoped GitLab-hosted absence, **not** absence of any resource on unrelated providers or infrastructure.

**Never unpublish the canonical Termivance GitLab project. Never delete any GitLab project.**

## Bootstrap development

Requires Python 3.12+:

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest -q
termivance status             # truthful status (Duo=NOT_RUN, retirement=NOT_RUN)
termivance status --json
termivance doctor             # environment sanity checks
termivance policy-check config/retirement_policy.example.json
```

On Windows PowerShell, use `python -m pip install -e ".[dev]"` if single-quote handling differs.

The CLI deliberately reports `NOT_RUN` and performs no API mutation; it has no
mutation-capable command. The GitLab Duo Custom Flow definition lives in
`flows/termivance_retirement_analyst.yaml` (a **source artifact only** — a YAML
file in a repository is not an active GitLab flow). GitLab CI configuration is
in `.gitlab-ci.yml`.

## Structure

- `AGENTS.md` — tool-independent execution and evidence guardrails.
- `plans/MASTER_PLAN.md` — four batches; no microphases.
- `docs/HANDOFF.md` — current critical project facts.
- `docs/EVIDENCE_MATRIX.md` — claim/proof separation.
- `src/termivance/` and `tests/` — minimal runnable baseline and deterministic contracts
  (`pages.py` endpoint-restricted mutation, `retirement.py` authorized executor,
  `absence.py` receipt-bound bounded-absence observation, `authorization.py` provenance,
  `ledger.py` durable single use, `approval_source.py` GitLab-issue approval provenance,
  `capsule.py` proof capsule, `portfolio.py`, `riskmap.py`, `simulation.py`, `workflow.py`,
  `duo_reconciliation.py`, `witness.py`, `tripwire.py`, `provision.py` disposable site).
- `control_room/` — judge-facing static Control Room (`index.html` + generated `data.js`,
  built by `scripts/build_control_room.py`, no network at view time).
- `evidence/b4/` — committed live (anonymous, GET-only) portfolio/snapshot/decision/risk-map/
  simulation/workflow records with honest `NOT_RUN` rows, plus Duo reconciliation, the
  resurrection witness and the capsule embedding both.
- `flows/termivance_retirement_analyst.yaml` — GitLab Duo Custom Flow source definition (`DEPLOYED`, live session `9650440`).
- `config/retirement_policy.example.json` — non-authorizing sample, destructive operations off by default.
- `config/retirement_policy.b3_disposable.json` — permits retirement of ONLY the disposable project `87785099`.
- `config/authorization.example.json` — non-authorizing example of an operator-issued authorization record.
- `deploy/disposable-pages/` — the disposable B3 Pages site template.

## Competition

Submission requires the new public MIT-licensed GitLab repository, real CI history, working Duo integration, and a public YouTube demo shorter than three minutes. Deadline: **2026-10-27 13:00 UTC / 16:00 Türkiye**. No paid services or unapproved mutations.

October contest: https://gitlab-transcend.devpost.com/ | Current schedule: https://gitlab-transcend.devpost.com/details/dates

**Source caution (2026-10-18):** The `/rules` URL has returned a June 2026 event text in some views. Verify the applicable October event requirements; for the deadline, follow the earlier 13:00 UTC Devpost schedule rather than the 14:00 UTC stated elsewhere.

## License

MIT — see `LICENSE`.
