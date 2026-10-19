# Termivance — Judge Demo Script (<3 minutes)

Every step below was executed and verified on 2026-10-19 against the real
canonical repository. The only not-possible live legs are called out honestly:
GitLab Pages unpublication (requires Maintainer; recorded 403) and any step
needing a GitLab PAT — those stay `NOT_RUN` and are *shown as NOT_RUN in the
demo*, which is itself a product feature (honest evidence states).

## 0 · Setup (pre-recorded, not in the video)

```bash
python -m pip install -e ".[dev]"
ruff check . && python -m pytest -q   # 306 passed
python scripts/refresh_b4_evidence.py  # anonymous live refresh (GET-only, $0)
python scripts/build_control_room.py --portfolio evidence/b4/portfolio.json --risk-map evidence/b4/risk_map.json --decision evidence/b4/decision.json --simulation evidence/b4/simulation.json --workflow evidence/b4/workflow_assessment.json --capsule evidence/b4/proof_capsule.json --duo-external evidence/b4/duo_session_9671626_readback.json --duo-reconciliation evidence/b4/duo_reconciliation.json --witness evidence/b4/witness_87785099.json --out-dir control_room
```

Open `control_room/index.html` in a browser (final shot).

## 1 · The problem (≈20 s)

"Software retirement without proof is just downtime. Termivance makes retirement
an auditable protocol: a deterministic obligation graph decides, one narrowly
authorized action executes, and absence is proven with explicit boundaries."

## 2 · Portfolio — multi-resource discovery (≈35 s)

```bash
termivance portfolio --project-ids 87785099,87779099,87777871,87786164 --anonymous \
  --policy config/retirement_policy.b3_disposable.json
```

Show the live GitLab read: `87779099` labelled **PROTECTED** (canonical repo —
expressly excluded), `87785099` labelled **APPROVED_RETIREMENT_TARGET**; per-resource
records (environments, deployments, issues, CI Pages mechanism, Pages), each with
exact IDs, endpoint, timestamp, freshness, provenance and `NOT_AUTHORIZING`.
This pass `/pages` honest `PAGES_UNVERIFIABLE_403` on all visible projects. Say:
"a 403 is an *access* observation — we never turn it into a deployment claim."

## 3 · Decision + Risk map + Simulation (≈50 s)

```bash
termivance simulate --project-id 87785099 --from-record evidence/b4/snapshot.json --portfolio evidence/b4/portfolio.json
termivance risk-map --decision evidence/b4/decision.json --portfolio evidence/b4/portfolio.json
```

Explain the deterministic `BLOCKED` (target outside anonymous-verifiable scope,
pages publication unverifiable without a credential, observed redeployment
mechanism) and the simulation's `PROJECTED_NOT_OBSERVED` labels: "same rules as
the real engine, zero mutation dispatch — a hypothesis can never mint a verdict."
Point out the shared portfolio evidence: the same snapshot feeds risk map and
simulation, `INFERRED` edges are context, never decision facts.

## 4 · Control Room v2, interactive (≈50 s)

Open `control_room/index.html` and *use it live*:

1. Header chips: **EVIDENCE: LIVE_ANONYMOUS** · **MUTATION: NOT_OBSERVED/NOT RUN**.
2. Portfolio tab: click `87785099` → 4 resource records with endpoint/timestamp/freshness;
   click a resource → selection highlights.
3. Graph tab: **"independently observed" — the graph is drawn from the recorded
   risk map only.** Click `resource:ci_redeployment:87785099` → edges highlight,
   detail pane shows the full recorded payload; click a `not-observed:…` node →
   the 403-with-context fact. Zoom in/out.
4. What-if tab: pick the CI mechanism → its precomputed `PROJECTED_NOT_OBSERVED`
   factor; pick the Pages resource → honest `NOT_RUN` card. "This page runs no
   engine and observes nothing — it is a viewer of records."
5. Proof tab: authorization gates (`STRUCTURALLY_REFUSED` for project deletion,
   the receipt card showing the fail-closed truth state — `NOT_RUN` today, never
   a "live" label from mere schema presence), capsule sections, the Duo session
   `9671626` evidence ladder (independently observed 200s vs operator-confirmed
   contents vs 401/404 unobservable leg), the **claim reconciliation** table
   (4 SUPPORTED / 2 UNRESOLVED / 2 NOT_AUTHENTICALLY_ATTRIBUTABLE / 1 UNSUPPORTED
   — "consistency is never promoted; a 401 is not attribution") and the
   **resurrection witness** card (target 87785099's *own* CI config at the exact
   observed commit carries Pages redeployment signals; its Pages administration
   surface answers 403 → "the observing identity cannot verify this surface";
   absence claim `NEVER`, control `NOT_CLAIMED`) — plus the escaping self-test
   rendering as inert text.

## 5 · Proof Capsule + verify-receipt (≈25 s)

```bash
termivance capsule-build --decision evidence/b4/decision.json \
  --target-project-id 87785099 \
  --target-full-path gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo \
  --out evidence/b4/proof_capsule.json
termivance capsule-verify evidence/b4/proof_capsule.json
```

This is the *no-mutation-yet* capsule over the real BLOCKED decision:
mutation/absence sections are explicit `NOT_RUN`/`NOT_OBSERVED`, never invented.
The shipped `evidence/b4/proof_capsule.json` additionally embeds the
non-authoritative Duo reconciliation and the resurrection witness verbatim (or
explicit `NOT_OBSERVED` when not supplied). Say plainly: "integrity verification
is a hash check, not a provider re-observation. When a real receipt exists, the
capsule carries the mutation receipt, authorization provenance and independence
observations instead."

## 6 · Single-flow workflow (≈20 s)

```bash
termivance workflow-plan --project-id 87785099 --full-path \
  gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo --out-dir evidence/b4
```

Point at stage 5: "the destructive step exists exactly once — `retire-pages
--execute` — wrapped by the operator trust policy (`--operator-trust`), a GitLab-issued
operator approval, a durable single-use ledger and independent read-back. There is
no second mutation code path."

## 7 · Honest NOT_RUN close (≈15 s)

"With today's access, the live unpublish and a role-dependent 403 re-check stay
`NOT_RUN` — GitLab's own safety gates. The protocol fails closed, and that is
the point."

**NOT shown as done (never claim):** live unpublication footage,
`OBSERVED_ABSENT`, `RESURRECTION_CONTROLLED`, a live capsule.
The B1 Duo session (`9650440`) remains the deployed-flow evidence; the B4 session
`9671626` on issue #3 is shown from its **evidence ladder**: issue metadata read
anonymously (HTTP 200), while the comment contents are operator-confirmed only
(notes endpoint returned 401 to anonymous reads — an access observation, never
proof either way). The deterministic executor issued no verdict from either.
