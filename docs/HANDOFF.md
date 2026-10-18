# Termivance — Active Handoff

- **Active batch:** B1 — Eligible GitLab foundation and real Duo integration.
- **Canonical GitLab repository:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance` — created 2026-10-18, **public**, project ID `87779099`, namespace `full_path` `gitlab-ai-hackathon/transcend-october-2026/39306908` (group ID `145090697`, parent `142538134`). Distinct from the organizer `showcase` project (`87777871`), which is untouched.
- **Canonical branch:** `main`.
- **Last independently verified remote SHA:** `cc11f445478972ce8772b2db8859537776d26594` (verified via `git ls-remote` + GitLab API). Full push history in `docs/EVIDENCE_MATRIX.md`.
- **Operator role:** GitLab `Developer` (access_level 30) on the subgroup and inherited on the project — **not** Maintainer/Owner. This did **not** block B1: custom-flow creation, enablement, trigger, and a live session all succeeded through the GraphQL API under the Developer role.
- **Completed batches:** `NONE` (B1 executed; awaiting independent QA).
- **Actual blockers:** `NONE VERIFIED` for B1. Open B3 risk: the Developer role gets HTTP 403 on the Pages API (`GET /projects/:id/pages`), so B3's disposable Pages project likely needs Maintainer/Owner — recheck live.
- **Architecture:** one real GitLab Duo Custom Flow agent (item `1018562`, exactly one `AgentComponent`); deterministic Python; GitLab-native only; disposable separate GitLab Pages site for B3. No Cloudflare or other external provider.
- **Safety:** $0 personal spending; never delete a GitLab project; never mutate existing/shared targets; B3 unpublish only after exact-target operator approval.
- **Evidence truth:** B1 now has a real live Duo session (`Workflow/9650440`, FINISHED) whose non-authoritative assessment is independently read back (issue #1, note `4037535804`). B2/B3 and all retirement/bounded-absence claims remain `NOT_RUN`.
- **Verified schema facts (2026-10-18, GitLab.com 19.6.0-pre):** custom flows support only `environment: ambient` and reject top-level `name`/`description`/`product_group`; `default:variables` is rejected by CI; a Developer can create/enable a custom flow, create an `aiFlowTriggerCreate` trigger (needs `projectPath` as a **path string**, `description`, `eventTypes: [Int]`, `aiCatalogItemConsumerId`). See `docs/EVIDENCE_MATRIX.md`.
- **Next full executor prompt:** independent whole-B1 QA; on `BATCH PASS`, the B2 full prompt.
- **Rules-source discrepancy:** `/rules` may show the prior June 2026 hackathon; October Devpost schedule gives 13:00 UTC (16:00 Türkiye), while organizer contributor page has displayed 14:00 UTC. Use earlier 13:00 UTC as hard deadline; B1 must verify applicable current event requirements.
- **Deadline:** 2026-10-27 16:00 Türkiye; leave final day to video and submission.

Update only critical facts here: active batch, actual blocker, independently checked SHA, eligibility, security/cost/evidence-boundary changes. Reconcile cosmetic documentation once in B4.
