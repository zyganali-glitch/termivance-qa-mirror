# Termivance — Active Handoff

- **Active batch:** B3 — authorized real GitLab Pages retirement + permanent independent GitHub QA bridge.
- **Canonical GitLab repository:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance` — public, project ID `87779099`, namespace `gitlab-ai-hackathon/transcend-october-2026/39306908` (subgroup `145090697`). Organizer `showcase` project `87777871` untouched.
- **Canonical branch:** `main`.
- **Operator role:** GitLab `Developer` (access_level 30, custom role `Developer+`) on the subgroup and inherited on projects. **Not** Maintainer/Owner.
- **B3 disposable target (operator-approved scope):** project ID **`87785099`**, `gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo`. Created 2026-10-18.
- **Completed batches:** `B1` (independent `BATCH PASS ✅`). `B2` implemented and verified live. `B3` implemented; awaiting independent QA.
- **Actual B3 blocker (verified live 2026-10-18):** the GitLab Pages lifecycle requires `Maintainer`. On `87785099` (Developer) `GET /pages`, `DELETE /pages` and `PUT pages_access_level` all return **403**. A Pages deployment is **not** created for the disposable project even though the identical CI config deploys under an owner-controlled namespace — i.e. Pages is gated by Maintainer in this namespace. No destructive call is made without an exact-target operator authorization. **Required action:** hackathon organizer grants the operator `Maintainer` (40) on `87785099` (or performs the exact unpublish).
- **B3 GitHub QA bridge (operational):** non-canonical `https://github.com/zyganali-glitch/termivance-qa-mirror` (repo ID `1424459128`). Workflow `gitlab-qa.yml` mirrors GitLab `main` to branch `gitlab-main` (exact SHA preserved) and runs an independent unauthenticated GitLab API observer. First run: `39143542346` — drift `IN_SYNC`, B2 pipeline↔commit binding matched, 11/18 endpoints `LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS`, 7 `NOT_OBSERVED` with real statuses. No GitLab credential is exported to GitHub.
- **Architecture:** ONE real GitLab Duo Custom Flow agent (item `1018562`); deterministic Python authority. B3 adds `pages.py` (endpoint-restricted mutation), `retirement.py` (exact-target authorization + executor), `absence.py` (bounded-absence), `provision.py` (disposable site).
- **Safety:** $0 personal spending; never delete a GitLab project; never mutate existing/shared targets; canonical project `87779099` and showcase `87777871` are on the protected registry.
- **Evidence truth:** B3 unpublish and bounded-absence remain `NOT_RUN`/`BLOCKED`; no absence is claimed. See `docs/EVIDENCE_MATRIX.md`.
- **Rules-source discrepancy:** Devpost October schedule gives 13:00 UTC; use earlier conservative deadline. Deadline: 2026-10-27 16:00 Türkiye.

Update only critical facts here. Reconcile cosmetic documentation once in B4.
