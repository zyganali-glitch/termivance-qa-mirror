# termivance-qa-mirror

**Independent QA bridge for [Termivance](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance).**

This repository is **non-canonical**. It is **not** a competition submission and
**not** the product. GitLab remains the only canonical source of Termivance
development and evidence. Nothing here is synchronised back to GitLab.

The purpose of this repository is to give a reviewer an *independently executed*
view of the GitLab system of record, through normal chat-based inspection of this
repository.

## What runs here

A single GitHub Actions workflow (`.github/workflows/gitlab-qa.yml`) has two jobs:

1. **mirror** — clones the canonical public GitLab repository and pushes its
   `main` commit onto the `gitlab-main` branch of this repository, preserving the
   exact GitLab commit SHA. No credentials are required to read a public repo.
2. **observe** — runs `observer/observe.py`, which contacts real GitLab REST API
   endpoints with its **own read-only, unauthenticated network calls** (it never
   trusts JSON authored by any executor), compares the live GitLab `main` commit
   against the `gitlab-main` mirror, and commits the resulting sanitized evidence.

## Provenance classifications

These labels have distinct, non-interchangeable meanings:

| Label | Meaning |
|---|---|
| `LIVE_GITLAB_OBSERVED_BY_GITHUB_ACTIONS` | A successful read-only GitLab API response observed by a GitHub Actions run, at its recorded UTC timestamp. |
| `RECORDED_LIVE` | An archived observation. It is a record, not a fresh live read, and is not perpetual proof of current state. |
| `FIXTURE` | Synthetic data. Never provider evidence. |
| `NOT_OBSERVED` | The endpoint was not successfully observed (401/403/timeout/other). The real status is preserved; nothing is invented. |

## Latest observation

`evidence/latest/manifest.json` is refreshed on every run and contains, for each
endpoint: the HTTP method, exact endpoint, HTTP status, acquisition time (UTC),
the exact project/resource ID, the artifact SHA-256, the workflow run id/URL, the
provenance classification and the limitations. The sanitized original provider
bodies are stored alongside it as `evidence/latest/<name>.json`.

`evidence/history/` keeps one record per run.

## Drift

Every run compares the live GitLab `main` commit with the `gitlab-main` mirror
branch. If they differ, `manifest.json.drift.status` is `DRIFT`. `IN_SYNC` means
the mirrored tree is the exact canonical commit.

## Security

* No GitLab credentials are used or stored here. All reads are public/unauthenticated.
* Only GitHub's built-in repository-scoped `GITHUB_TOKEN` is used (workflow
  `permissions: contents: write`, needed to push the mirror and evidence).
* Responses are sanitized (emails, avatars, human names and token fields are
  redacted) before being published. The redacted key list is recorded per artifact.
* No private project data, personal data or secret-bearing logs are published.

## Limitations

Public API access cannot read some records (for example private GitLab Pages
state, issue notes and environment details on some projects). Those endpoints are
reported as `NOT_OBSERVED` with the real HTTP status; they are never fabricated.
