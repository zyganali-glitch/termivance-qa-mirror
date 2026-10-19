# Termivance

**Software retirement, proven within bounds.**

Termivance is a **Proof-Bounded Software Retirement Protocol** for GitLab Transcend — Life After Code (2026), **Path A / Start Fresh / Supervised**. One GitLab Duo Custom Flow agent assists with retirement context and orchestration, while a deterministic Python core controls exact targeting, obligation decisions, approval, mutation, evidence, and verdicts.

Core concepts: **Retirement Obligation Graph**, **Bounded Absence**, and **Retirement Reversal**. Independent verdicts: `SAFE_TO_RETIRE`, `OBSERVED_ABSENT`, and (only after actual detection/control evidence) `RESURRECTION_CONTROLLED`. We never claim universal absence.

## Status

**B4 implemented (2026-10-19); independent batch QA next.** B1 (live Duo Custom Flow) and B2 (deterministic BLOCKED gate) stand; B3's deterministic executor and bounded absence stand, with the live unpublish still **`BLOCKED` on a real access boundary**. B4 closes the P0 security defects (durable sealed-reservation ledger, GitLab-issue approval provenance, receipt-bound absence) and adds the six-capability **Retirement Control Plane**: read-only Portfolio, deterministic Risk Map, hypothetical Simulation, judge-facing Control Room, tamper-evident Proof Capsule with `capsule-verify`, and a 7-stage single-flow workflow orchestration. Suite: **238 tests**, ruff clean, **16/16** network-free CI safety assertions.

- Canonical repo: https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance
- QA bridge (non-canonical): https://github.com/zyganali-glitch/termivance-qa-mirror
- Live B1 session: https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9650440

**The live retirement remains `BLOCKED` on a real, verified access boundary**, not on
the engine: the operator holds only `Developer` on the competition subgroup, GitLab's
Pages lifecycle (deploy + `DELETE /projects/:id/pages`) requires `Maintainer`, and no
GitLab PAT is present on the machine — authenticated evidence stays `NOT_RUN`. No destructive call is made without an exact-target operator
authorization. See `docs/HANDOFF.md` and `docs/EVIDENCE_MATRIX.md`.

## Try the B4 capabilities (read-only)

```bash
python -m pip install -e ".[dev]"
# live anonymous portfolio over the two real projects (GET-only, no token):
termivance portfolio --project-ids 87785099,87779099 --anonymous --policy config/retirement_policy.b3_disposable.json
# deterministic risk map for a recorded decision:
termivance risk-map --decision evidence/b4/decision.json
# hypothetical what-if (never mutates):
termivance simulate --project-id 87785099 --from-record evidence/b4/snapshot.json
# single-flow workflow plan and artifact assessment:
termivance workflow-plan --project-id 87785099 --full-path gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo --out-dir evidence/b4
termivance workflow-status --project-id 87785099 --full-path gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo --out-dir evidence/b4
# judge control room (rebuild data, then open control_room/index.html in a browser):
python scripts/build_control_room.py --portfolio evidence/b4/portfolio.json --risk-map evidence/b4/risk_map.json --decision evidence/b4/decision.json --simulation evidence/b4/simulation.json --workflow evidence/b4/workflow_assessment.json
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
  `tripwire.py`, `provision.py` disposable site).
- `control_room/` — judge-facing static Control Room (`index.html` + generated `data.js`,
  built by `scripts/build_control_room.py`, no network at view time).
- `evidence/b4/` — committed live (anonymous, GET-only) portfolio/snapshot/decision/risk-map/
  simulation/workflow records with honest `NOT_RUN` rows.
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
