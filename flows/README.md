# Termivance Duo Custom Flow assets

**Status: DEPLOYED and verified live (B1, 2026-10-18).**

`termivance_retirement_analyst.yaml` is the single GitLab Duo Agent Platform
**Custom Flow** used by Termivance. It contains exactly one `AgentComponent`.

Live identities:

| Thing | Value |
|---|---|
| AI Catalog item (FLOW) | `gid://gitlab/Ai::Catalog::Item/1018562` |
| Consumer (enabled in project) | `gid://gitlab/Ai::Catalog::ItemConsumer/12750509` |
| Mention trigger | `gid://gitlab/Ai::FlowTrigger/3071665` (`eventTypes: [0]`) |
| Service account | `ai-termivance-retirement-analyst-gitlab-ai-hackathon` |
| Live session (FINISHED) | `9650440` |
| Session URL | `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9650440` |
| Produced artifact | issue #1 comment `4037535804` (independently read back via REST) |

The flow was created and enabled through the GitLab GraphQL API
(`aiCatalogFlowCreate`, `aiCatalogItemConsumerCreate`, `aiFlowTriggerCreate`),
not by committing YAML. Triggering was a real mention of the service account on
issue #1; the flow then read project context with real tools
(`get_issue`, `list_repository_tree`, `get_repository_file`) and published a
structured **non-authoritative** assessment whose final status line is
`NON-AUTHORITATIVE / DETERMINISTIC VERDICT: NOT_RUN`.

The agent performs **no** mutation and awards **no** authoritative verdict; a
deterministic Python core owns target identity, authorization, mutation,
read-back and verdicts.
