# Termivance — Evidence Matrix

This starter pack contains **no live evidence**. `NOT_RUN` != `PASS`. Record evidence with immutable project/resource IDs, exact commit SHA, invocation/run IDs, source, UTC time, and sanitized URLs. Separate local fixture, CI test, live GitLab Duo session, live GitLab Pages mutation, independent API observation, and unauthenticated HTTP observation.

**B1 access blocker (2026-10-18):** the execution environment had no valid GitLab credential (stored `git:https://gitlab.com` token expired; no browser session; no GitLab CLI/MCP), so every live B1 row below remains `NOT_RUN`. Local-only rows (install, lint, tests, fail-closed CLI) were verified locally but are not substitutes for the live rows.

| Claim / gate | Required real evidence | Starter status | Boundaries |
|---|---|---|---|
| B1: canonical new repository | Public GitLab URL, license, remote SHA | NOT_RUN | GitHub repository is not substitute |
| B1: CI works | Passing pipeline URL and job/test logs | NOT_RUN | Local tests insufficient |
| B1: actual Duo agent | Custom Flow definition + actual session/run URL + independent GitLab result | NOT_RUN | YAML alone != integration; Chat alone != Custom Flow |
| B1: local foundation | `pip install -e .`, `ruff check .`, `pytest`, CLI exit codes | LOCAL_PASS (38 tests, ruff clean) | Local-only; never a substitute for remote CI or the live repo |
| B2: SAFE_TO_RETIRE | Fresh graph/obligation checks + bound authority and exact target | NOT_RUN | Deterministic verdict, not model prose |
| B2: real BLOCKED | Actual GitLab read evidence, forbidden/unsatisfied edge, zero delete API calls | NOT_RUN | Fixture tests cannot replace live gate |
| B3: existing target | Exact disposable GitLab Pages project ID/path, Pages API `200`, live served site | NOT_RUN | NOT the canonical repo |
| B3: authorized unpublish | Bound operator approval, exact project ID, DELETE result | NOT_RUN | Successful DELETE not proof of absence |
| B3: OBSERVED_ABSENT | Fresh independent Pages API GET and served URL HTTP observation, scoped receipt | NOT_RUN | GitLab-only scope; no claim about Cloudflare, AWS or general external resources |
| B3: environment state | Separate environment API or GitLab read | NOT_RUN | `stopped` does not prove Pages site deletion |
| B3 optional: resurrection | Subsequent same-target observed redeploy + state downgrade | NOT_RUN | Do not claim `RESURRECTION_CONTROLLED` without control proof |
| B4: judge package | Public evidence UI, integrated pipeline, YouTube <3m, Devpost submission | NOT_RUN | Video must depict actual product |

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
