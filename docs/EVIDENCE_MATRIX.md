# Termivance — Evidence Matrix

This starter pack contains **no live evidence**. `NOT_RUN` != `PASS`. Record evidence with immutable project/resource IDs, exact commit SHA, invocation/run IDs, source, UTC time, and sanitized URLs. Separate local fixture, CI test, live GitLab Duo session, live GitLab Pages mutation, independent API observation, and unauthenticated HTTP observation.

**B1 live status (2026-10-18):** executed end-to-end with an operator-issued scoped GitLab PAT (`api`, `write_repository`) read privately from Git Credential Manager. Canonical project created, pipeline green, one real Duo Custom Flow created/enabled and executed live, artifact independently read back. Every B2/B3 row remains `NOT_RUN`.

| Claim / gate | Required real evidence | Starter status | Boundaries |
|---|---|---|---|
| B1: canonical new repository | Public GitLab URL, license, remote SHA | PASS (see log) | GitHub repository is not substitute |
| B1: CI works | Passing pipeline URL and job/test logs | PASS (see log) | Local tests insufficient |
| B1: actual Duo agent | Custom Flow definition + actual session/run URL + independent GitLab result | PASS (see log) | YAML alone != integration; Chat alone != Custom Flow |
| B1: local foundation | `pip install -e .`, `ruff check .`, `pytest`, CLI exit codes | LOCAL_PASS (38 tests, ruff clean) | Local-only; never a substitute for remote CI or the live repo |
| B2: SAFE_TO_RETIRE | Fresh graph/obligation checks + bound authority and exact target | ENGINE_PASS (synthetic safe case tested) | Deterministic verdict, not model prose |
| B2: real BLOCKED | Actual GitLab read evidence, forbidden/unsatisfied edge, zero delete API calls | PASS (see B2 log) | Fixture tests cannot replace live gate |
| B3: existing target | Exact disposable GitLab Pages project ID/path, Pages API `200`, live served site | NOT_RUN | NOT the canonical repo |
| B3: authorized unpublish | Bound operator approval, exact project ID, DELETE result | NOT_RUN | Successful DELETE not proof of absence |
| B3: OBSERVED_ABSENT | Fresh independent Pages API GET and served URL HTTP observation, scoped receipt | NOT_RUN | GitLab-only scope; no claim about Cloudflare, AWS or general external resources |
| B3: environment state | Separate environment API or GitLab read | NOT_RUN | `stopped` does not prove Pages site deletion |
| B3 optional: resurrection | Subsequent same-target observed redeploy + state downgrade | NOT_RUN | Do not claim `RESURRECTION_CONTROLLED` without control proof |
| B4: judge package | Public evidence UI, integrated pipeline, YouTube <3m, Devpost submission | NOT_RUN | Video must depict actual product |

## B1 evidence log (2026-10-18, all times UTC)

- **Repository:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance` — project ID `87779099`, namespace `gitlab-ai-hackathon/transcend-october-2026/39306908` (group `145090697`), public, default branch `main`, license detected MIT. Organizer `showcase` project (`87777871`) untouched.
- **SHAs:** first pushed `ebfae4173da0a0adefea0e953502f70dc9777d11`; CI fix `0d9be1b59a3f473195855e27a4ffd0fb54024cf4`; B1 completion `cc11f445478972ce8772b2db8859537776d26594`. Remote HEAD verified with `git ls-remote` and the GitLab API.
- **CI:** pipeline `2960123673` SUCCESS (job `verification`, shared runner) — ruff clean, **38 tests passed**, CLI smoke exit 0. First pipeline `2960120304` FAILED (GitLab 19.6 rejects `default:variables`); root cause found via API and fixed in the same batch.
- **Duo Custom Flow:** created via GraphQL `aiCatalogFlowCreate` → `Ai::Catalog::Item/1018562` (type `FLOW`, exactly one `AgentComponent`); enabled via `aiCatalogItemConsumerCreate` → `ItemConsumer/12750509`; mention trigger via `aiFlowTriggerCreate` → `Ai::FlowTrigger/3071665` (`eventTypes: [0]`). Service account `ai-termivance-retirement-analyst-gitlab-ai-hackathon`.
- **Live session:** `Ai::DuoWorkflows::Workflow/9650440`, status `FINISHED`, triggered by a real issue mention — `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9650440`.
- **Artifact:** issue #1 (`.../-/work_items/1`) comment `4037535804` by the flow service account — a structured NON-AUTHORITATIVE assessment (Reference / Observed / Candidate obligations / Missing proof / Authorization / `NON-AUTHORITATIVE / DETERMINISTIC VERDICT: NOT_RUN`), produced with real tools `get_issue`, `list_repository_tree`, `get_repository_file`. Independently read back via `GET /projects/87779099/issues/1/notes`.
- **No mutation:** no project/resource deleted or unpublished; only additive creates (project, flow, consumer, trigger, issue, comments).

## B2 evidence log (2026-10-18, all times UTC)

- **Deterministic core:** typed Retirement Obligation Graph (`graph.py`), read-only GitLab client (`gitlab_client.py`, GET-only, raises `ReadOnlyViolation` otherwise), discovery (`discovery.py`), fail-closed engine (`engine.py`), protected-target registry (`protected.py`), report renderer (`report.py`) and a separate publisher (`publish.py`). 94 tests pass; ruff clean.
- **Live read-only BLOCKED:** target canonical project `87779099` (`GITLAB_PAGES_SITE`, action `unpublish_pages`). Verdict **`BLOCKED`**; reasons **`PROTECTED_PROJECT`**, **`TARGET_NOT_AUTHORIZED`**, **`UNRESOLVED_OBLIGATION`**. `RecordingTransport` observed **only GET** — `non_GET_calls = []` (zero destructive operations).
- **Real blocking facts:** project identity (id `87779099`, path `gitlab-ai-hackathon/transcend-october-2026/39306908/termivance`, visibility `public`, branch `main`); CI config has **no `pages:` job** so `REDEPLOYMENT_PATH` is satisfied, not fabricated; **1 open retirement-related work item** (issue #1) → active `OPEN_WORK_ITEM`; `GET /projects/87779099/pages` → **403** (recorded, not stored as fact).
- **Recorded snapshot:** `config/recorded/canonical_project.json` (classification `RECORDED_LIVE`) — replayable offline; stale replay fails closed.
- **Published artifact:** B2 issue #2 `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/work_items/2`; independently read back via API (`GET /projects/87779099/issues/2`).
- **Duo explanation (reused single flow):** issue #2 note `4037739173` by `ai-termivance-retirement-analyst-gitlab-ai-hackathon`, explicitly non-authoritative; deterministic verdict unchanged.



## B3 feasibility notes (B2 observation, not evidence of absence)

- GitLab Pages exists on this GitLab.com namespace (`pages_access_level=private`) but the **Developer** role receives **HTTP 403** on `GET /projects/:id/pages` and `/pages/domains`. A disposable Pages project for B3 therefore likely needs the operator to be **Maintainer/Owner**, or the Pages API read will 403. Re-check live in B3; do not assume.
- No Pages site, environment, or served URL exists for the canonical project — nothing was published or unpublished in B1.



## Minimal bounded-absence receipt fields

`provider=GITLAB_PAGES`, `exact_project_id`, `exact_project_path`, `resource_kind=PAGES_SITE`, `observed_scope`, `observation_time_utc`, `api_request_identity`, `api_status`, `deployment_state`, `served_url`, `http_observation`, `freshness_or_expiry`, `source_sha`, `authorization_binding`, `verdict`.

A `404` from a misaddressed URL, authentication error, unavailable API, cached site, or absent scope does not prove negative state. Contradictions yield `INCONCLUSIVE` until resolved. Reappearance changes **current** truth while preserving historical evidence.

## Authoritative references (checked 2026-10-18)

- October 2026 overview: https://gitlab-transcend.devpost.com/
- October schedule (conservative deadline 13:00 UTC): https://gitlab-transcend.devpost.com/details/dates
- Rules page (may currently serve prior June 2026 event; do not blindly treat as October rules): https://gitlab-transcend.devpost.com/rules
- Custom flows: https://docs.gitlab.com/user/duo_agent_platform/flows/custom/
- Schema: https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows_schema/
- Flow triggering/credits: https://docs.gitlab.com/user/duo_agent_platform/triggers/
- Pages API: https://docs.gitlab.com/api/pages/
- Pages deployment lifecycle: https://docs.gitlab.com/user/project/pages/
