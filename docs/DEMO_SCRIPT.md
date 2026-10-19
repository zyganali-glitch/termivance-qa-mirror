# Termivance — Judge Demo Script (<3 minutes)

Every step below was executed and verified on 2026-10-19 against the real
canonical repository. The only not-possible live legs are called out honestly:
GitLab Pages unpublication (requires Maintainer; recorded 403) and any step
needing a GitLab PAT — those stay `NOT_RUN` and are *shown as NOT_RUN in the
demo*, which is itself a product feature (honest evidence states).

## 0 · Setup (pre-recorded, not in the video)

```bash
python -m pip install -e ".[dev]"
ruff check . && python -m pytest -q   # 238 passed
```

Open `control_room/index.html` in a browser (final shot).

## 1 · The problem (≈20 s)

"Software retirement without proof is just downtime. Termivance makes retirement
an auditable protocol: a deterministic obligation graph decides, one narrowly
authorized action executes, and absence is proven with explicit boundaries."

## 2 · Portfolio — read-only discovery (≈30 s)

```bash
termivance portfolio --project-ids 87785099,87779099 --anonymous \
  --policy config/retirement_policy.b3_disposable.json
```

Show the live GitLab read: `87779099` labelled **PROTECTED** (canonical repo —
expressly excluded), `87785099` labelled **APPROVED_RETIREMENT_TARGET**;
both `/pages` reads honest `PAGES_UNVERIFIABLE_403`. Say: "a 403 is an *access*
observation — we never turn it into a deployment claim."

## 3 · Decision + Risk map + Simulation (≈50 s)

```bash
termivance simulate --project-id 87785099 --from-record evidence/b4/snapshot.json
termivance risk-map --decision evidence/b4/decision.json
```

Explain the deterministic `BLOCKED` (target outside anonymous-verifiable scope,
pages publication unverifiable without a credential, observed redeployment
mechanism) and the simulation's `PROJECTED_NOT_OBSERVED` labels: "same rules as
the real engine, zero mutation dispatch — a hypothesis can never mint a verdict."

## 4 · Control Room (≈40 s)

Open `control_room/index.html`: verdict **BLOCKED**, provenance
`RECORDED_LIVE` with `mutation_status: NOT_RUN`, portfolio strip, risk map,
workflow stage chips (`COMPLETE` / `NOT_RUN` — nothing hidden).

## 5 · Proof Capsule + verify-receipt (≈30 s)

```bash
termivance capsule-build --decision evidence/b4/decision.json \
  --target-project-id 87785099 \
  --target-full-path gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo \
  --out evidence/b4/proof_capsule.json
termivance capsule-verify evidence/b4/proof_capsule.json
```

This is the *no-mutation-yet* capsule over the real BLOCKED decision:
mutation/absence sections are explicit `NOT_RUN`/`NOT_OBSERVED`, never invented.
Say plainly: "integrity verification is a hash check, not a provider
re-observation. When a real receipt exists, the capsule carries the mutation
receipt, authorization provenance and independence observations instead."

## 6 · Single-flow workflow (≈25 s)

```bash
termivance workflow-plan --project-id 87785099 --full-path \
  gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo --out-dir evidence/b4
```

Point at stage 5: "the destructive step exists exactly once — `retire-pages
--execute` — wrapped by the GitLab-issued operator approval, a durable
single-use ledger and independent read-back. There is no second mutation code
path."

## 7 · Honest NOT_RUN close (≈15 s)

"With today's access, the live unpublish and a role-dependent 403 re-check stay
`NOT_RUN` — GitLab's own safety gates. The protocol fails closed, and that is
the point."

**NOT shown as done (never claim):** live unpublication footage,
`OBSERVED_ABSENT`, `RESURRECTION_CONTROLLED`, a live capsule, a new Duo session.
The B1 Duo session (`9650440`) remains the deployed-flow evidence.
