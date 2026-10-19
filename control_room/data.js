window.TERMIVANCE_DATA = {
  "authorization_gates": [
    {
      "detail": "anonymous public reads are permitted; authenticated reads require operator-supplied credentials (none stored on the executor machine)",
      "gate": "READ-ONLY GITLAB API (GET)",
      "state": "AVAILABLE"
    },
    {
      "detail": "bound to immutable numeric project id, exact endpoint, one-time operator-signed approval + trust policy, durable single-use ledger, fresh SAFE_TO_RETIRE decision and operator-provided credential; GitHub-namespace approvals and API-key possession never equal consent. Receipt truth state: no receipt artifact was supplied; the runtime records no mutation attempt and this page will not pretend otherwise",
      "gate": "DELETE /projects/87785099/pages (the sole approved destructive action)",
      "state": "NOT_RUN"
    },
    {
      "detail": "the mutation client can only ever issue DELETE /projects/<positive-int>/pages; project deletion is unreachable by construction",
      "gate": "Project deletion / any other project's mutation",
      "state": "STRUCTURALLY_REFUSED"
    },
    {
      "detail": "personal spend target 0.00 USD; no paid plan may be enabled without explicit operator authorization",
      "gate": "Paid plans / on-demand credits / token transfer",
      "state": "AUTHORIZED_FALSE"
    }
  ],
  "boundaries": [
    "A successful mutation is not proof of retirement; absence is only claimed by the receipt-bound bounded-absence rules.",
    "NOT_RUN / BLOCKED / NOT_OBSERVED are first-class states and are never promoted to success.",
    "Unpublishing targets exactly one disposable Pages project; the canonical repository and every other project are out of scope.",
    "Unsigned SHA-256 digests in the ledger are local tamper evidence, never cryptographic authentication of provider events."
  ],
  "built_at": "2026-10-19T20:48:07.640382+00:00",
  "demo_target_discovery": {
    "candidates": [
      {
        "agent_claim": ".gitlab-ci.yml at 87785099 (create-pages, pages: true) can republish the site on any pipeline run against the default branch. Candidate obligation: neutralize or control this path, or show that no pipeline can run. This is the main resurrection risk.",
        "candidate_id": "duo-9710085-cand-01",
        "classification": "CORROBORATED",
        "engine_obligation_mapping": "REDEPLOYMENT_PATH (Violated: active pages: true mechanism exists without ControlAttestation)",
        "independent_content_digest_sha256": "fe895004ba37081c95f893bc9025a5fb24b3fc3cb51da5655d566f69a0b20620",
        "independent_findings": "Confirmed: job create-pages defines stage deploy, image alpine:3.20, script copying site/index.html and site/marker.txt into public/, and pages: true.",
        "independent_source_read": "GET /projects/87785099/repository/files/.gitlab-ci.yml?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
        "session_id": "9710085",
        "tool_used_by_duo": "get_repository_file(87785099, '.gitlab-ci.yml', ref='HEAD')",
        "topic": "CI Redeployment Path (Target .gitlab-ci.yml)"
      },
      {
        "agent_claim": "site/index.html and site/marker.txt contain the marker TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a. The marker could be used by a later deterministic check.",
        "candidate_id": "duo-9710085-cand-02",
        "classification": "CORROBORATED",
        "engine_obligation_mapping": "IDENTITY_BINDING (Marker verifies exact target identity and content)",
        "independent_findings": "Confirmed: marker string TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a exists verbatim at target commit 54fcc9ff…",
        "independent_source_read": "GET /projects/87785099/repository/files/site%2Fmarker.txt?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
        "session_id": "9710085",
        "tool_used_by_duo": "get_repository_file on target 87785099 (site/marker.txt, site/index.html)",
        "topic": "Target Marker String Direct Discovery"
      },
      {
        "agent_claim": "The header comment says 'DISPOSABLE B3 demonstration site (temporary; safe to retire)'. That is only a repository comment. It is not authorization. A bound, valid, single-use authorization is still required.",
        "candidate_id": "duo-9710085-cand-03",
        "classification": "CORROBORATED",
        "engine_obligation_mapping": "OWNERSHIP_AUTHORIZATION (Refused: prose/comment never satisfies operator authorization contract)",
        "independent_findings": "Confirmed: in-code comment exists. Deterministic core strictly refuses prose/comments as authorization.",
        "independent_source_read": "Inspected line 1 of target .gitlab-ci.yml: '# DISPOSABLE B3 demonstration site (temporary; safe to retire).'",
        "session_id": "9710085",
        "tool_used_by_duo": "get_repository_file(87785099, '.gitlab-ci.yml')",
        "topic": "In-Code Comment Not Operator Authorization"
      },
      {
        "agent_claim": "The acting identity needs Maintainer/Owner Pages administration on the target. The recorded evidence shows only anonymous read, with a 403 on the Pages endpoint.",
        "candidate_id": "duo-9710085-cand-04",
        "classification": "CORROBORATED",
        "engine_obligation_mapping": "RETIREMENT_PERMISSION (Violated: Maintainer role required on namespace to unpublish Pages)",
        "independent_findings": "Confirmed access boundary: GET /projects/87785099/pages returns HTTP 403 (AUTH_DENIED). Proves anonymous observing identity is denied Pages access; does not authenticate operator's effective role.",
        "independent_source_read": "GET /projects/87785099/pages",
        "session_id": "9710085",
        "tool_used_by_duo": "Recorded witness inspection and boundary evaluation",
        "topic": "Pages Administration Access Boundary (403)"
      },
      {
        "agent_claim": "Out-of-repo resurrection vectors (schedules, trigger tokens, manual runs) and cached content edge replicas may stay reachable after a provider change.",
        "candidate_id": "duo-9710085-cand-05",
        "classification": "UNRESOLVED",
        "engine_obligation_mapping": "ABSENCE_VERIFICATION (Bound: absence requires live transition proof, never cached/negative assumption)",
        "independent_findings": "Unobservable anonymously: pipeline schedules, trigger tokens, and edge CDN cache retention cannot be observed via anonymous GitLab read; preserved as unverified candidate risk hypothesis.",
        "independent_source_read": "UNOBSERVABLE_ANONYMOUSLY (Requires Maintainer authentication or external edge CDN telemetry)",
        "session_id": "9710085",
        "tool_used_by_duo": "Systemic risk reasoning based on GitLab architecture",
        "topic": "Out-of-Repo Resurrection Vectors & Caches"
      }
    ],
    "canonical_project": {
      "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance",
      "project_id": 87779099
    },
    "deterministic_reconciliation": {
      "engine_verdict": "BLOCKED",
      "observed_absent": "NOT_CLAIMED",
      "resurrection_controlled": "NOT_CLAIMED",
      "safe_to_retire": "BLOCKED",
      "summary": "GitLab Duo independently discovered the exact CI redeployment risk (create-pages with pages: true) on disposable project 87785099 from a neutral, unprimed issue request (#5). Termivance independently verified this source fact via public GitLab API (sha256 fe895004ba37081c95f893bc9025a5fb24b3fc3cb51da5655d566f69a0b20620) and bound it to REDEPLOYMENT_PATH obligation, while preserving unobservable schedules and edge caches as UNRESOLVED. The deterministic decision remains strictly BLOCKED because AI cannot authorize mutation or award verdicts, and no operator authorization or Maintainer unpublish permission was granted."
    },
    "duo_flow": {
      "agent_note_id": 4045401991,
      "catalog_item_id": 1018562,
      "flow_name": "Termivance Retirement Analyst",
      "issue_iid": 5,
      "primary_agent_note_id": 4045401991,
      "primary_deterministic_outcome_note_id": 4045409264,
      "primary_issue_iid": 5,
      "primary_issue_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/issues/5",
      "primary_session_id": "9710085",
      "primary_session_status": "Finished",
      "primary_session_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9710085",
      "secondary_issue_iid": 4,
      "secondary_session_id": "9704855",
      "session_id": "9710085",
      "session_status": "Finished"
    },
    "generated_at_utc": "2026-10-19T19:50:00.000000+00:00",
    "inspection_preferences_and_provenance": {
      "contextual_discovery_session_9704855": {
        "details": "Issue #4 description contained a fallback source snapshot snippet and witness reference. Duo verified that target repository files matched the snapshot and differed from canonical templates.",
        "issue_iid": 4,
        "status": "SUCCEEDED_WITH_SNAPSHOT_CONTEXT"
      },
      "neutral_unprimed_discovery_session_9710085": {
        "details": "Issue #5 contained NO source snapshot, NO YAML snippet, NO pages: true hint, and NO pre-calculated hashes. Duo used list_repository_tree (found 4 files) and get_repository_file on target 87785099 to directly and independently discover the CI redeployment mechanism (create-pages / pages: true), marker string, and permission boundaries.",
        "issue_iid": 5,
        "status": "SUCCEEDED_UNPRIMED"
      }
    },
    "schema": "termivance.demo_duo_target_discovery/v2",
    "spend_usd": "0.00",
    "status": "EVIDENCE_STRENGTHENING_SUCCESSFUL",
    "target": {
      "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
      "observed_commit": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
      "project_id": 87785099,
      "resource_kind": "GITLAB_PAGES_SITE"
    }
  },
  "escape_probe": "<img src=x onerror=alert(1)>&\"'",
  "external_evidence": {
    "duo_session": {
      "captured_at_utc": "2026-10-19T09:55:24.858411+00:00",
      "determinism_boundary": "the Duo analysis is read-only and non-authoritative; no mutation, no verdict, no SAFE_TO_RETIRE/OBSERVED_ABSENT/RESURRECTION_CONTROLLED claim can originate from it — the deterministic executor remains the only decision authority",
      "duo_session": {
        "independent_probe_note": "agent-sessions UI requires authenticated access; 404 to anonymous clients is an access observation, never evidence about the session state",
        "independent_web_page_probe_status_anonymous": 404,
        "session_id": "9671626",
        "status": "Finished",
        "status_source": "OPERATOR_VISUAL_CONFIRMATION (authenticated browser session)",
        "url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9671626"
      },
      "evidence_ladder": {
        "independently_observed_anonymous_api": [
          "project 87779099 is publicly readable (HTTP 200)",
          "issue #3 exists, state opened, title/labels/author match the recorded B3 retirement status thread",
          "issue user_notes_count=3 and issue updated_at=2026-10-19T08:57:41.500Z — consistent with, but not proof of, the operator-reported new comment window"
        ],
        "not_independently_observable_and_never_promoted": [
          "note/discussion contents (HTTP 401 to anonymous readers; 401 is an access observation, never absence, never authenticity)",
          "flow-execution internals behind the agent-sessions UI (HTTP 404 to anonymous clients)"
        ],
        "operator_confirmed_only": [
          "session id 9671626 exists and Finished in the authenticated automate/agent-sessions UI",
          "the agent-authored comment note id 4040776241 was published on issue #3 by the GitLab Duo service account",
          "the six-section analysis content itself and its read-only, non-authoritative character",
          "the agent used genuine GitLab tools and stated it did NOT directly query disposable project 87785099"
        ]
      },
      "flow_catalog_item_id": 1018562,
      "issue_binding": {
        "independent_api_readback": {
          "discussions_list_status_anonymous": 401,
          "issue_author": "zyganali",
          "issue_metadata_status_anonymous": 200,
          "issue_state": "opened",
          "issue_title": "[B3] Retirement status: BLOCKED (deterministic) - graph-bound authority, proven-transition absence, durable single-use authorization",
          "issue_updated_at": "2026-10-19T08:57:41.500Z",
          "labels": [
            "retirement-decision",
            "termivance::b3"
          ],
          "notes_list_status_anonymous": 401,
          "user_notes_count": 3
        },
        "issue_iid": 3,
        "note_id_reported": 4040776241,
        "project_id": 87779099,
        "project_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance"
      },
      "schema": "termivance.external_evidence_record/v1",
      "spend": "0.00 USD (anonymous unsigned reads only; no PAT requested, no session triggered by the executor)",
      "subject": "genuine B4 GitLab Duo Custom Flow execution (Termivance Retirement Analyst)"
    }
  },
  "generated_by": "scripts/build_control_room.py (deterministic, from recorded files)",
  "interactive_contract": {
    "destructive_buttons": 0,
    "network_fetches_at_view_time": 0,
    "note": "this page embeds recorded facts and can trigger nothing; every mutation path is CLI-gated by the operator trust chain",
    "page_is_static": true
  },
  "mutation_status": "NOT_OBSERVED",
  "provenance_label": "LIVE_ANONYMOUS",
  "read_provenance": "LIVE_ANONYMOUS",
  "schema": "termivance.control_room/v2",
  "sections": {
    "capsule": {
      "manifest": {
        "sections": {
          "absence": "39eeab2a4f3f78cd4f0282f33bf7b190571ec528c74b01fbfe65e4a57ab9dad6",
          "authorization": "31067f2c9a69e8451fc5a278856f3929c0703aa7132301423f0cce564637e48c",
          "decision": "d3d7f3224fecec5e9b37880a7b728e6b778ba44c0468543da74a3c528cb6c668",
          "duo_reconciliation": "b29585014165873c51a099953d8983ebd27ffd252417460707ba9d373cc96967",
          "identity": "08d6d83421fcd9a4a27899eebc904c21a86ac3d112699d265a8f60b176d2977d",
          "limitation_notice": "1f45038b36918e0d5acd11e991b0a33fab3f955e3ff92a6453c092cb65627f88",
          "mutation": "8233bc272138a9c113143e1842426f82c3412faede769c095d7ee9bb74ad004e",
          "source_evidence": "58227fbfa8e806878a27d5fca70d4a1e96b2ca8b98c1d80739dffa7bb35dcbc0",
          "witness": "5dd7a64d9efe2f683102d30af58a4a9d4cd2407cb0b2084cf384000756d26fa2"
        }
      },
      "manifest_digest": "15ea45e1cde3defaf5f05a031eeb9d3437ad6641ee4a9875702ff4bf89fd612f",
      "schema": "termivance.proof_capsule/v1",
      "sections": {
        "absence": {
          "claimed": false,
          "state": "NOT_OBSERVED"
        },
        "authorization": {
          "present": false,
          "state": "NOT_RUN"
        },
        "decision": {
          "action": "unpublish_pages",
          "authoritative": false,
          "evaluated_at": "2026-10-19T20:47:44.867015+00:00",
          "graph": {
            "dependencies": [
              {
                "active": true,
                "dependency_id": "dep:active_redeployment",
                "description": "observed Pages deployment mechanism in CI configuration",
                "evidence_id": "ev:ci_config",
                "kind": "ACTIVE_REDEPLOYMENT"
              },
              {
                "active": false,
                "dependency_id": "dep:open_work_item",
                "description": "0 open retirement-related work item(s)",
                "evidence_id": "ev:open_issues",
                "kind": "OPEN_WORK_ITEM"
              }
            ],
            "edges": [
              {
                "from": "target:87785099:GITLAB_PAGES_SITE",
                "relation": "HAS_OBLIGATION",
                "to": "obl:target_scope"
              },
              {
                "from": "target:87785099:GITLAB_PAGES_SITE",
                "relation": "HAS_OBLIGATION",
                "to": "obl:ownership_authorization"
              },
              {
                "from": "target:87785099:GITLAB_PAGES_SITE",
                "relation": "HAS_OBLIGATION",
                "to": "obl:retirement_permission"
              },
              {
                "from": "target:87785099:GITLAB_PAGES_SITE",
                "relation": "HAS_OBLIGATION",
                "to": "obl:pages_published"
              },
              {
                "from": "target:87785099:GITLAB_PAGES_SITE",
                "relation": "HAS_OBLIGATION",
                "to": "obl:identity_binding"
              },
              {
                "from": "target:87785099:GITLAB_PAGES_SITE",
                "relation": "HAS_OBLIGATION",
                "to": "obl:provider_observation"
              },
              {
                "from": "target:87785099:GITLAB_PAGES_SITE",
                "relation": "HAS_OBLIGATION",
                "to": "obl:unresolved_work"
              },
              {
                "from": "target:87785099:GITLAB_PAGES_SITE",
                "relation": "HAS_OBLIGATION",
                "to": "obl:redeployment_path"
              },
              {
                "from": "obl:provider_observation",
                "relation": "REQUIRES_EVIDENCE",
                "to": "ev:project_identity"
              },
              {
                "from": "obl:identity_binding",
                "relation": "REQUIRES_EVIDENCE",
                "to": "ev:project_identity"
              },
              {
                "from": "obl:identity_binding",
                "relation": "REQUIRES_EVIDENCE",
                "to": "ev:branch"
              },
              {
                "from": "obl:redeployment_path",
                "relation": "REQUIRES_EVIDENCE",
                "to": "ev:ci_config"
              },
              {
                "from": "obl:unresolved_work",
                "relation": "REQUIRES_EVIDENCE",
                "to": "ev:open_issues"
              },
              {
                "from": "obl:retirement_permission",
                "relation": "REQUIRES_EVIDENCE",
                "to": "ev:effective_permission"
              },
              {
                "from": "obl:identity_binding",
                "relation": "REQUIRES_EVIDENCE",
                "to": "ev:effective_permission"
              },
              {
                "from": "obl:pages_published",
                "relation": "REQUIRES_EVIDENCE",
                "to": "ev:pages_deployment"
              },
              {
                "from": "obl:identity_binding",
                "relation": "REQUIRES_EVIDENCE",
                "to": "ev:pages_deployment"
              },
              {
                "from": "obl:unresolved_work",
                "relation": "BLOCKED_BY",
                "to": "dep:open_work_item"
              },
              {
                "from": "obl:redeployment_path",
                "relation": "BLOCKED_BY",
                "to": "dep:active_redeployment"
              }
            ],
            "evidence": [
              {
                "classification": "LIVE",
                "detail": {
                  "branch": "main",
                  "commit_id": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
                },
                "digest": "11688fd09e0d06312ba2934b2b5aad899e1dc1b71e254639310c8b1cb9714aba",
                "endpoint": "/projects/87785099/repository/branches/main",
                "error_kind": null,
                "evidence_id": "ev:branch",
                "fresh_until": "2026-10-19T21:02:44.867015+00:00",
                "kind": "BRANCH",
                "method": "GET",
                "observed_at": "2026-10-19T20:47:44.867015+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "LIVE",
                "detail": {
                  "bytes": 320,
                  "file": ".gitlab-ci.yml",
                  "includes_present": false,
                  "pages_mechanism": true,
                  "pages_signals": [
                    "pages_true",
                    "pages_keyword"
                  ],
                  "present": true,
                  "ref": "main",
                  "refs_examined": [
                    "main"
                  ]
                },
                "digest": "ff9ca84d2117058681353e234a6cda441b6831cd9e8b3540a22cf02595a32b37",
                "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
                "error_kind": null,
                "evidence_id": "ev:ci_config",
                "fresh_until": "2026-10-19T21:02:44.867015+00:00",
                "kind": "CI_CONFIG",
                "method": "GET",
                "observed_at": "2026-10-19T20:47:44.867015+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "LIVE",
                "detail": {
                  "can_manage_pages": false,
                  "effective_access_level": null,
                  "pages_api_error": "AUTH_DENIED",
                  "pages_api_status": 403
                },
                "digest": "034fcec2a8deeee99eadeac6496228730fa29905e4d807d8a8487d96b8dd7ec5",
                "endpoint": "/projects/87785099",
                "error_kind": null,
                "evidence_id": "ev:effective_permission",
                "fresh_until": "2026-10-19T21:02:44.867015+00:00",
                "kind": "EFFECTIVE_PERMISSION",
                "method": "GET",
                "observed_at": "2026-10-19T20:47:44.867015+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "LIVE",
                "detail": {
                  "error": "AUTH_DENIED"
                },
                "digest": "be458994bf4fae39544bf92130b1d29908c0c918ca5515468d47e326bb9406df",
                "endpoint": "/projects/87785099/environments",
                "error_kind": "AUTH_DENIED",
                "evidence_id": "ev:environment",
                "fresh_until": "2026-10-19T21:02:44.867015+00:00",
                "kind": "ENVIRONMENT",
                "method": "GET",
                "observed_at": "2026-10-19T20:47:44.867015+00:00",
                "status": 401,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "LIVE",
                "detail": {
                  "open_count": 0,
                  "retirement_related": []
                },
                "digest": "e53888a5d945e88f379bf5b2d42b12de6b07f7eb50a01a60d7182ba9d8dbd941",
                "endpoint": "/projects/87785099/issues",
                "error_kind": null,
                "evidence_id": "ev:open_issues",
                "fresh_until": "2026-10-19T21:02:44.867015+00:00",
                "kind": "OPEN_ISSUES",
                "method": "GET",
                "observed_at": "2026-10-19T20:47:44.867015+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "LIVE",
                "detail": {
                  "error": "AUTH_DENIED"
                },
                "digest": "ed76fbefd375028ae456c69ae43ea1760fe0127b3b265b01a6da7365e1f30b57",
                "endpoint": "/projects/87785099/pages",
                "error_kind": "AUTH_DENIED",
                "evidence_id": "ev:pages",
                "fresh_until": "2026-10-19T21:02:44.867015+00:00",
                "kind": "PAGES",
                "method": "GET",
                "observed_at": "2026-10-19T20:47:44.867015+00:00",
                "status": 403,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "LIVE",
                "detail": {
                  "error": "AUTH_DENIED"
                },
                "digest": "a457b85e3514de39f9ee1d8efa9a930957bd150e349e0a19bec335458186dee2",
                "endpoint": "/projects/87785099/pages",
                "error_kind": "AUTH_DENIED",
                "evidence_id": "ev:pages_deployment",
                "fresh_until": "2026-10-19T21:02:44.867015+00:00",
                "kind": "PAGES_DEPLOYMENT",
                "method": "GET",
                "observed_at": "2026-10-19T20:47:44.867015+00:00",
                "status": 403,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "LIVE",
                "detail": {
                  "latest_id": 2960507698,
                  "latest_status": "success"
                },
                "digest": "139526b14c99f11599c55963a526587621660279ee86e1f6dc295997f46548ea",
                "endpoint": "/projects/87785099/pipelines",
                "error_kind": null,
                "evidence_id": "ev:pipeline",
                "fresh_until": "2026-10-19T21:02:44.867015+00:00",
                "kind": "PIPELINE",
                "method": "GET",
                "observed_at": "2026-10-19T20:47:44.867015+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "LIVE",
                "detail": {
                  "archived": null,
                  "default_branch": "main",
                  "namespace_full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908",
                  "path_with_namespace": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "visibility": "public",
                  "web_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
                },
                "digest": "9a3e0e8923f564e7f51d2c2e7930ce020ba5983e37b83ec751a6d2c946599f64",
                "endpoint": "/projects/87785099",
                "error_kind": null,
                "evidence_id": "ev:project_identity",
                "fresh_until": "2026-10-19T21:02:44.867015+00:00",
                "kind": "PROJECT_IDENTITY",
                "method": "GET",
                "observed_at": "2026-10-19T20:47:44.867015+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              }
            ],
            "obligations": [
              {
                "description": "all evidence is bound to the exact target identity",
                "kind": "IDENTITY_BINDING",
                "mandatory": true,
                "obligation_id": "obl:identity_binding"
              },
              {
                "description": "an exact-target authorization exists for the requested action",
                "kind": "OWNERSHIP_AUTHORIZATION",
                "mandatory": true,
                "obligation_id": "obl:ownership_authorization"
              },
              {
                "description": "the target is a genuinely published Pages site observed before retirement",
                "kind": "PAGES_PUBLISHED",
                "mandatory": true,
                "obligation_id": "obl:pages_published"
              },
              {
                "description": "a fresh provider observation of the target is available",
                "kind": "PROVIDER_OBSERVATION",
                "mandatory": true,
                "obligation_id": "obl:provider_observation"
              },
              {
                "description": "no active mechanism can redeploy or recreate the target",
                "kind": "REDEPLOYMENT_PATH",
                "mandatory": true,
                "obligation_id": "obl:redeployment_path"
              },
              {
                "description": "the acting identity can administer GitLab Pages on the target",
                "kind": "RETIREMENT_PERMISSION",
                "mandatory": true,
                "obligation_id": "obl:retirement_permission"
              },
              {
                "description": "target is in the permitted, non-protected retirement scope",
                "kind": "TARGET_SCOPE",
                "mandatory": true,
                "obligation_id": "obl:target_scope"
              },
              {
                "description": "no unresolved retirement-related work item remains",
                "kind": "UNRESOLVED_WORK",
                "mandatory": true,
                "obligation_id": "obl:unresolved_work"
              }
            ],
            "schema": "termivance.retirement_obligation_graph/v1",
            "targets": [
              {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            ]
          },
          "missing_conditions": [
            "resolve TARGET_NOT_AUTHORIZED: no bound authorization supplied",
            "resolve INSUFFICIENT_PROVIDER_ACCESS: publication could not be observed (AUTH_DENIED)",
            "resolve REDEPLOYMENT_RISK: 1 observed redeployment/recreation mechanism(s)",
            "resolve INSUFFICIENT_PERMISSION: the acting identity lacks Maintainer/Owner Pages administration on the target"
          ],
          "obligations": [
            {
              "kind": "IDENTITY_BINDING",
              "mandatory": true,
              "obligation_id": "obl:identity_binding",
              "status": "SATISFIED"
            },
            {
              "kind": "OWNERSHIP_AUTHORIZATION",
              "mandatory": true,
              "obligation_id": "obl:ownership_authorization",
              "status": "VIOLATED"
            },
            {
              "kind": "PAGES_PUBLISHED",
              "mandatory": true,
              "obligation_id": "obl:pages_published",
              "status": "UNKNOWN"
            },
            {
              "kind": "PROVIDER_OBSERVATION",
              "mandatory": true,
              "obligation_id": "obl:provider_observation",
              "status": "SATISFIED"
            },
            {
              "kind": "REDEPLOYMENT_PATH",
              "mandatory": true,
              "obligation_id": "obl:redeployment_path",
              "status": "VIOLATED"
            },
            {
              "kind": "RETIREMENT_PERMISSION",
              "mandatory": true,
              "obligation_id": "obl:retirement_permission",
              "status": "VIOLATED"
            },
            {
              "kind": "TARGET_SCOPE",
              "mandatory": true,
              "obligation_id": "obl:target_scope",
              "status": "SATISFIED"
            },
            {
              "kind": "UNRESOLVED_WORK",
              "mandatory": true,
              "obligation_id": "obl:unresolved_work",
              "status": "SATISFIED"
            }
          ],
          "read_only": true,
          "reasons": [
            {
              "code": "TARGET_NOT_AUTHORIZED",
              "detail": "no bound authorization supplied",
              "evidence_id": null,
              "obligation_id": "obl:ownership_authorization"
            },
            {
              "code": "INSUFFICIENT_PROVIDER_ACCESS",
              "detail": "publication could not be observed (AUTH_DENIED)",
              "evidence_id": "ev:pages_deployment",
              "obligation_id": "obl:pages_published"
            },
            {
              "code": "REDEPLOYMENT_RISK",
              "detail": "1 observed redeployment/recreation mechanism(s)",
              "evidence_id": "ev:ci_config",
              "obligation_id": "obl:redeployment_path"
            },
            {
              "code": "INSUFFICIENT_PERMISSION",
              "detail": "the acting identity lacks Maintainer/Owner Pages administration on the target",
              "evidence_id": "ev:effective_permission",
              "obligation_id": "obl:retirement_permission"
            }
          ],
          "schema": "termivance.retirement_decision/v1",
          "target": {
            "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
            "project_id": 87785099,
            "resource_kind": "GITLAB_PAGES_SITE"
          },
          "verdict": "BLOCKED"
        },
        "duo_reconciliation": {
          "authority": "NON_AUTHORITATIVE",
          "record": {
            "claims": [
              {
                "causal_attribution": "GENUINE_DUO_TARGET_DISCOVERY: Duo independently discovered create-pages / pages: true redeployment path on target 87785099",
                "claim_id": "duo-9710085-cand-01",
                "corroboration_detail": "Target .gitlab-ci.yml at observed commit contains create-pages job with pages: true; establishes active redeployment path.",
                "corroboration_source": "GET /projects/87785099/repository/files/.gitlab-ci.yml?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
                "corroboration_status": "CORROBORATED",
                "exact_target_relationship": "TARGET_BOUND",
                "origin": "GitLab Duo Custom Flow Session 9710085",
                "retirement_relevance": "MATERIAL",
                "source_project": 87785099,
                "text": "Redeployment path: `.gitlab-ci.yml` at 87785099 (`create-pages`, `pages: true`) can republish the site on any pipeline run against the default branch. Candidate obligation: neutralize or control this path, or show that no pipeline can run. This is the main resurrection risk."
              },
              {
                "causal_attribution": "GENUINE_DUO_RISK_HYPOTHESIS: Duo reasoned about unobservable resurrection vectors and external caches",
                "claim_id": "duo-9710085-cand-02",
                "corroboration_detail": "Unobservable via anonymous provider read or GitLab REST API: pipeline schedules, trigger tokens, and edge CDN caches cannot be verified anonymously; preserved as unverified candidate risk hypothesis.",
                "corroboration_source": null,
                "corroboration_status": "UNRESOLVED",
                "exact_target_relationship": "TARGET_BOUND",
                "origin": "GitLab Duo Custom Flow Session 9710085",
                "retirement_relevance": "CONTEXTUAL",
                "source_project": 87785099,
                "text": "Out-of-repo resurrection vectors: These are not visible from repository files:    - pipeline schedules    - trigger tokens    - manual or API pipeline runs    - Pages administration actions through the UI or API    - the Pages deployment-retention behaviour of `pages: true` jobs    - the template copy at `deploy/disposable-pages/.gitlab-ci.yml` in 87779099, which could be copied back to the target"
              },
              {
                "causal_attribution": "GENUINE_DUO_RISK_HYPOTHESIS: Duo reasoned about unobservable resurrection vectors and external caches",
                "claim_id": "duo-9710085-cand-03",
                "corroboration_detail": "Unobservable via anonymous provider read or GitLab REST API: pipeline schedules, trigger tokens, and edge CDN caches cannot be verified anonymously; preserved as unverified candidate risk hypothesis.",
                "corroboration_source": null,
                "corroboration_status": "UNRESOLVED",
                "exact_target_relationship": "TARGET_BOUND",
                "origin": "GitLab Duo Custom Flow Session 9710085",
                "retirement_relevance": "CONTEXTUAL",
                "source_project": 87785099,
                "text": "Cached content: Cached or edge-replicated copies of the served content, including the marker string, may stay reachable after any provider-side change."
              },
              {
                "causal_attribution": "GENUINE_DUO_TARGET_DISCOVERY: Duo identified in-code comment and noted it does not satisfy operator authorization contract",
                "claim_id": "duo-9710085-cand-04",
                "corroboration_detail": "In-code comment verified in target .gitlab-ci.yml; deterministic policy strictly enforces that prose comments cannot grant operator authorization.",
                "corroboration_source": "GET /projects/87785099/repository/files/.gitlab-ci.yml?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d & config/retirement_policy.b3_disposable.json",
                "corroboration_status": "CORROBORATED",
                "exact_target_relationship": "TARGET_BOUND",
                "origin": "GitLab Duo Custom Flow Session 9710085",
                "retirement_relevance": "PROCEDURAL",
                "source_project": 87785099,
                "text": "Authorization binding: The policy file allowlists 87785099 and the `unpublish_pages` action but sets `authorization_required: true`. A bound, valid, single-use authorization is still required. The comment \"safe to retire\" in the target's CI file is only a repository comment. It is not authorization."
              },
              {
                "causal_attribution": "GENUINE_DUO_TARGET_DISCOVERY: Duo observed 403 access boundary on target 87785099 Pages endpoint",
                "claim_id": "duo-9710085-cand-05",
                "corroboration_detail": "Verified access boundary: anonymous GET /projects/87785099/pages returned HTTP 403 (AUTH_DENIED); proves anonymous identity is denied access, does not authenticate operator role.",
                "corroboration_source": "GET /projects/87785099/pages (HTTP 403 AUTH_DENIED)",
                "corroboration_status": "CORROBORATED",
                "exact_target_relationship": "TARGET_BOUND",
                "origin": "GitLab Duo Custom Flow Session 9710085",
                "retirement_relevance": "MATERIAL",
                "source_project": 87785099,
                "text": "Permissions: The acting identity needs Maintainer/Owner Pages administration on the target. The recorded evidence shows only anonymous read, with a 403 on the Pages endpoint."
              },
              {
                "causal_attribution": "GENUINE_DUO_OBSERVATION: Duo noted open issues in canonical hosting repository",
                "claim_id": "duo-9710085-cand-06",
                "corroboration_detail": "Issues exist in canonical repository 87779099, but their causal relevance to target project 87785099 is unproven.",
                "corroboration_source": "GET /projects/87779099/issues",
                "corroboration_status": "CONTEXTUAL_ONLY",
                "exact_target_relationship": "NO_DIRECT_TARGET_LINK",
                "origin": "GitLab Duo Custom Flow Session 9710085",
                "retirement_relevance": "CONTEXTUAL",
                "source_project": 87779099,
                "text": "Open work in the hosting project: Issues 1, 2 and 3 in 87779099 were recorded as open dependencies. Their relevance to the target is unknown."
              },
              {
                "causal_attribution": "GENUINE_DUO_TARGET_DISCOVERY: Duo independently discovered marker string in target 87785099",
                "claim_id": "duo-9710085-cand-07",
                "corroboration_detail": "Marker string TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a independently verified in target files site/marker.txt and site/index.html.",
                "corroboration_source": "GET /projects/87785099/repository/files/site%2Fmarker.txt?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
                "corroboration_status": "CORROBORATED",
                "exact_target_relationship": "TARGET_BOUND",
                "origin": "GitLab Duo Custom Flow Session 9710085",
                "retirement_relevance": "MATERIAL",
                "source_project": 87785099,
                "text": "Marker for later checks: The marker `TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a` could be used by a later deterministic check, if that check is permitted."
              }
            ],
            "generated_at": "2026-10-19T20:47:44.867015+00:00",
            "issue_iid": 5,
            "schema": "termivance.duo_reconciliation/v1",
            "session_id": "9710085",
            "target_project_id": 87785099,
            "totals": {
              "CONTEXTUAL_ONLY": 1,
              "CORROBORATED": 4,
              "TOTAL": 7,
              "UNRESOLVED": 2
            }
          },
          "state": "RECONCILED"
        },
        "identity": {
          "generated_at": "2026-10-19T20:47:44.867015+00:00",
          "provider": "GITLAB",
          "target": {
            "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
            "project_id": 87785099,
            "resource_kind": "GITLAB_PAGES_SITE"
          }
        },
        "limitation_notice": {
          "explicit_states": [
            "BLOCKED",
            "NOT_RUN",
            "NOT_OBSERVED"
          ],
          "not_to_be_claimed": "Integrity verification is a local byte-level check; it never re-observes GitLab and never extends the bounded verdict beyond its stated evidence, scope and freshness.",
          "notes": [
            "assembled by run_supervised_investigation (inv-20261019204744-ae07c3) from anonymous live reads",
            "no mutation was attempted; no absence is claimed and no control is asserted"
          ]
        },
        "mutation": {
          "attempted": false,
          "state": "NOT_RUN"
        },
        "source_evidence": {
          "state": "NOT_OBSERVED"
        },
        "witness": {
          "record": {
            "absence_claim": "NEVER_FROM_THIS_WITNESS",
            "authority": "NON_AUTHORITATIVE",
            "boundary": "this witness lists resurrection counterexamples; it never claims absence and never awards RESURRECTION_CONTROLLED — that verdict additionally requires live monitoring/control evidence this read-only sweep cannot provide",
            "commit_sha": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
            "config": {
              "configuration_complete": true,
              "digest_sha256": "fe895004ba37081c95f893bc9025a5fb24b3fc3cb51da5655d566f69a0b20620",
              "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
              "error_kind": null,
              "ref": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
              "signals": [
                "pages_true",
                "pages_keyword"
              ],
              "status": 200
            },
            "counterexamples": [
              "the target's own default-branch CI configuration at the observed commit 54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d carries Pages redeployment signal(s) ['pages_true', 'pages_keyword']; any pipeline executing that configuration can republish the site",
              "a pages-administration action through the provider API or UI could republish the site at any time, independent of repository content",
              "the Pages administration surface of this exact target is not verifiable by this observing identity right now; a site may exist and it must not be assumed away",
              "cached or edge-replicated copies of previously served content can remain reachable after the provider state changes"
            ],
            "default_branch": "main",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "pages_administration": {
              "endpoint": "/projects/87785099/pages",
              "error_kind": "AUTH_DENIED",
              "phrase": "the observing identity cannot verify this Pages administration surface (HTTP 403); a site may be present or absent right now and neither state is claimed from this observation",
              "status": 403
            },
            "provenance": "ANONYMOUS_PUBLIC_READ",
            "resurrection_controlled": "NOT_CLAIMED",
            "resurrection_possible": "MECHANISM_PRESENT_IN_OBSERVED_CONFIG",
            "schema": "termivance.resurrection_witness/v1",
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          },
          "state": "RECORDED"
        }
      }
    },
    "decision": {
      "action": "unpublish_pages",
      "authoritative": false,
      "evaluated_at": "2026-10-19T20:47:44.867015+00:00",
      "graph": {
        "dependencies": [
          {
            "active": true,
            "dependency_id": "dep:active_redeployment",
            "description": "observed Pages deployment mechanism in CI configuration",
            "evidence_id": "ev:ci_config",
            "kind": "ACTIVE_REDEPLOYMENT"
          },
          {
            "active": false,
            "dependency_id": "dep:open_work_item",
            "description": "0 open retirement-related work item(s)",
            "evidence_id": "ev:open_issues",
            "kind": "OPEN_WORK_ITEM"
          }
        ],
        "edges": [
          {
            "from": "target:87785099:GITLAB_PAGES_SITE",
            "relation": "HAS_OBLIGATION",
            "to": "obl:target_scope"
          },
          {
            "from": "target:87785099:GITLAB_PAGES_SITE",
            "relation": "HAS_OBLIGATION",
            "to": "obl:ownership_authorization"
          },
          {
            "from": "target:87785099:GITLAB_PAGES_SITE",
            "relation": "HAS_OBLIGATION",
            "to": "obl:retirement_permission"
          },
          {
            "from": "target:87785099:GITLAB_PAGES_SITE",
            "relation": "HAS_OBLIGATION",
            "to": "obl:pages_published"
          },
          {
            "from": "target:87785099:GITLAB_PAGES_SITE",
            "relation": "HAS_OBLIGATION",
            "to": "obl:identity_binding"
          },
          {
            "from": "target:87785099:GITLAB_PAGES_SITE",
            "relation": "HAS_OBLIGATION",
            "to": "obl:provider_observation"
          },
          {
            "from": "target:87785099:GITLAB_PAGES_SITE",
            "relation": "HAS_OBLIGATION",
            "to": "obl:unresolved_work"
          },
          {
            "from": "target:87785099:GITLAB_PAGES_SITE",
            "relation": "HAS_OBLIGATION",
            "to": "obl:redeployment_path"
          },
          {
            "from": "obl:provider_observation",
            "relation": "REQUIRES_EVIDENCE",
            "to": "ev:project_identity"
          },
          {
            "from": "obl:identity_binding",
            "relation": "REQUIRES_EVIDENCE",
            "to": "ev:project_identity"
          },
          {
            "from": "obl:identity_binding",
            "relation": "REQUIRES_EVIDENCE",
            "to": "ev:branch"
          },
          {
            "from": "obl:redeployment_path",
            "relation": "REQUIRES_EVIDENCE",
            "to": "ev:ci_config"
          },
          {
            "from": "obl:unresolved_work",
            "relation": "REQUIRES_EVIDENCE",
            "to": "ev:open_issues"
          },
          {
            "from": "obl:retirement_permission",
            "relation": "REQUIRES_EVIDENCE",
            "to": "ev:effective_permission"
          },
          {
            "from": "obl:identity_binding",
            "relation": "REQUIRES_EVIDENCE",
            "to": "ev:effective_permission"
          },
          {
            "from": "obl:pages_published",
            "relation": "REQUIRES_EVIDENCE",
            "to": "ev:pages_deployment"
          },
          {
            "from": "obl:identity_binding",
            "relation": "REQUIRES_EVIDENCE",
            "to": "ev:pages_deployment"
          },
          {
            "from": "obl:unresolved_work",
            "relation": "BLOCKED_BY",
            "to": "dep:open_work_item"
          },
          {
            "from": "obl:redeployment_path",
            "relation": "BLOCKED_BY",
            "to": "dep:active_redeployment"
          }
        ],
        "evidence": [
          {
            "classification": "LIVE",
            "detail": {
              "branch": "main",
              "commit_id": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
            },
            "digest": "11688fd09e0d06312ba2934b2b5aad899e1dc1b71e254639310c8b1cb9714aba",
            "endpoint": "/projects/87785099/repository/branches/main",
            "error_kind": null,
            "evidence_id": "ev:branch",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "kind": "BRANCH",
            "method": "GET",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "status": 200,
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          },
          {
            "classification": "LIVE",
            "detail": {
              "bytes": 320,
              "file": ".gitlab-ci.yml",
              "includes_present": false,
              "pages_mechanism": true,
              "pages_signals": [
                "pages_true",
                "pages_keyword"
              ],
              "present": true,
              "ref": "main",
              "refs_examined": [
                "main"
              ]
            },
            "digest": "ff9ca84d2117058681353e234a6cda441b6831cd9e8b3540a22cf02595a32b37",
            "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
            "error_kind": null,
            "evidence_id": "ev:ci_config",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "kind": "CI_CONFIG",
            "method": "GET",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "status": 200,
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          },
          {
            "classification": "LIVE",
            "detail": {
              "can_manage_pages": false,
              "effective_access_level": null,
              "pages_api_error": "AUTH_DENIED",
              "pages_api_status": 403
            },
            "digest": "034fcec2a8deeee99eadeac6496228730fa29905e4d807d8a8487d96b8dd7ec5",
            "endpoint": "/projects/87785099",
            "error_kind": null,
            "evidence_id": "ev:effective_permission",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "kind": "EFFECTIVE_PERMISSION",
            "method": "GET",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "status": 200,
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          },
          {
            "classification": "LIVE",
            "detail": {
              "error": "AUTH_DENIED"
            },
            "digest": "be458994bf4fae39544bf92130b1d29908c0c918ca5515468d47e326bb9406df",
            "endpoint": "/projects/87785099/environments",
            "error_kind": "AUTH_DENIED",
            "evidence_id": "ev:environment",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "kind": "ENVIRONMENT",
            "method": "GET",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "status": 401,
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          },
          {
            "classification": "LIVE",
            "detail": {
              "open_count": 0,
              "retirement_related": []
            },
            "digest": "e53888a5d945e88f379bf5b2d42b12de6b07f7eb50a01a60d7182ba9d8dbd941",
            "endpoint": "/projects/87785099/issues",
            "error_kind": null,
            "evidence_id": "ev:open_issues",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "kind": "OPEN_ISSUES",
            "method": "GET",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "status": 200,
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          },
          {
            "classification": "LIVE",
            "detail": {
              "error": "AUTH_DENIED"
            },
            "digest": "ed76fbefd375028ae456c69ae43ea1760fe0127b3b265b01a6da7365e1f30b57",
            "endpoint": "/projects/87785099/pages",
            "error_kind": "AUTH_DENIED",
            "evidence_id": "ev:pages",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "kind": "PAGES",
            "method": "GET",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "status": 403,
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          },
          {
            "classification": "LIVE",
            "detail": {
              "error": "AUTH_DENIED"
            },
            "digest": "a457b85e3514de39f9ee1d8efa9a930957bd150e349e0a19bec335458186dee2",
            "endpoint": "/projects/87785099/pages",
            "error_kind": "AUTH_DENIED",
            "evidence_id": "ev:pages_deployment",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "kind": "PAGES_DEPLOYMENT",
            "method": "GET",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "status": 403,
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          },
          {
            "classification": "LIVE",
            "detail": {
              "latest_id": 2960507698,
              "latest_status": "success"
            },
            "digest": "139526b14c99f11599c55963a526587621660279ee86e1f6dc295997f46548ea",
            "endpoint": "/projects/87785099/pipelines",
            "error_kind": null,
            "evidence_id": "ev:pipeline",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "kind": "PIPELINE",
            "method": "GET",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "status": 200,
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          },
          {
            "classification": "LIVE",
            "detail": {
              "archived": null,
              "default_branch": "main",
              "namespace_full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908",
              "path_with_namespace": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "visibility": "public",
              "web_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
            },
            "digest": "9a3e0e8923f564e7f51d2c2e7930ce020ba5983e37b83ec751a6d2c946599f64",
            "endpoint": "/projects/87785099",
            "error_kind": null,
            "evidence_id": "ev:project_identity",
            "fresh_until": "2026-10-19T21:02:44.867015+00:00",
            "kind": "PROJECT_IDENTITY",
            "method": "GET",
            "observed_at": "2026-10-19T20:47:44.867015+00:00",
            "status": 200,
            "target": {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          }
        ],
        "obligations": [
          {
            "description": "all evidence is bound to the exact target identity",
            "kind": "IDENTITY_BINDING",
            "mandatory": true,
            "obligation_id": "obl:identity_binding"
          },
          {
            "description": "an exact-target authorization exists for the requested action",
            "kind": "OWNERSHIP_AUTHORIZATION",
            "mandatory": true,
            "obligation_id": "obl:ownership_authorization"
          },
          {
            "description": "the target is a genuinely published Pages site observed before retirement",
            "kind": "PAGES_PUBLISHED",
            "mandatory": true,
            "obligation_id": "obl:pages_published"
          },
          {
            "description": "a fresh provider observation of the target is available",
            "kind": "PROVIDER_OBSERVATION",
            "mandatory": true,
            "obligation_id": "obl:provider_observation"
          },
          {
            "description": "no active mechanism can redeploy or recreate the target",
            "kind": "REDEPLOYMENT_PATH",
            "mandatory": true,
            "obligation_id": "obl:redeployment_path"
          },
          {
            "description": "the acting identity can administer GitLab Pages on the target",
            "kind": "RETIREMENT_PERMISSION",
            "mandatory": true,
            "obligation_id": "obl:retirement_permission"
          },
          {
            "description": "target is in the permitted, non-protected retirement scope",
            "kind": "TARGET_SCOPE",
            "mandatory": true,
            "obligation_id": "obl:target_scope"
          },
          {
            "description": "no unresolved retirement-related work item remains",
            "kind": "UNRESOLVED_WORK",
            "mandatory": true,
            "obligation_id": "obl:unresolved_work"
          }
        ],
        "schema": "termivance.retirement_obligation_graph/v1",
        "targets": [
          {
            "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
            "project_id": 87785099,
            "resource_kind": "GITLAB_PAGES_SITE"
          }
        ]
      },
      "missing_conditions": [
        "resolve TARGET_NOT_AUTHORIZED: no bound authorization supplied",
        "resolve INSUFFICIENT_PROVIDER_ACCESS: publication could not be observed (AUTH_DENIED)",
        "resolve REDEPLOYMENT_RISK: 1 observed redeployment/recreation mechanism(s)",
        "resolve INSUFFICIENT_PERMISSION: the acting identity lacks Maintainer/Owner Pages administration on the target"
      ],
      "obligations": [
        {
          "kind": "IDENTITY_BINDING",
          "mandatory": true,
          "obligation_id": "obl:identity_binding",
          "status": "SATISFIED"
        },
        {
          "kind": "OWNERSHIP_AUTHORIZATION",
          "mandatory": true,
          "obligation_id": "obl:ownership_authorization",
          "status": "VIOLATED"
        },
        {
          "kind": "PAGES_PUBLISHED",
          "mandatory": true,
          "obligation_id": "obl:pages_published",
          "status": "UNKNOWN"
        },
        {
          "kind": "PROVIDER_OBSERVATION",
          "mandatory": true,
          "obligation_id": "obl:provider_observation",
          "status": "SATISFIED"
        },
        {
          "kind": "REDEPLOYMENT_PATH",
          "mandatory": true,
          "obligation_id": "obl:redeployment_path",
          "status": "VIOLATED"
        },
        {
          "kind": "RETIREMENT_PERMISSION",
          "mandatory": true,
          "obligation_id": "obl:retirement_permission",
          "status": "VIOLATED"
        },
        {
          "kind": "TARGET_SCOPE",
          "mandatory": true,
          "obligation_id": "obl:target_scope",
          "status": "SATISFIED"
        },
        {
          "kind": "UNRESOLVED_WORK",
          "mandatory": true,
          "obligation_id": "obl:unresolved_work",
          "status": "SATISFIED"
        }
      ],
      "read_only": true,
      "reasons": [
        {
          "code": "TARGET_NOT_AUTHORIZED",
          "detail": "no bound authorization supplied",
          "evidence_id": null,
          "obligation_id": "obl:ownership_authorization"
        },
        {
          "code": "INSUFFICIENT_PROVIDER_ACCESS",
          "detail": "publication could not be observed (AUTH_DENIED)",
          "evidence_id": "ev:pages_deployment",
          "obligation_id": "obl:pages_published"
        },
        {
          "code": "REDEPLOYMENT_RISK",
          "detail": "1 observed redeployment/recreation mechanism(s)",
          "evidence_id": "ev:ci_config",
          "obligation_id": "obl:redeployment_path"
        },
        {
          "code": "INSUFFICIENT_PERMISSION",
          "detail": "the acting identity lacks Maintainer/Owner Pages administration on the target",
          "evidence_id": "ev:effective_permission",
          "obligation_id": "obl:retirement_permission"
        }
      ],
      "schema": "termivance.retirement_decision/v1",
      "target": {
        "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
        "project_id": 87785099,
        "resource_kind": "GITLAB_PAGES_SITE"
      },
      "verdict": "BLOCKED"
    },
    "duo_reconciliation": {
      "authority": "NON_AUTHORITATIVE",
      "boundary": "Duo output is candidate claims only; every status here is derived from anonymous read-only observations; no verdict may originate from this record and no claim is ever promoted beyond what a GET actually showed",
      "claims": [
        {
          "check_kind": "PROJECT_READ",
          "claim_id": "duo-9671626-01",
          "detail": "the project is publicly readable to this anonymous identity (HTTP 200)",
          "observed": {
            "observed_at": "2026-10-19T16:26:02.530404+00:00",
            "project_read_status": 200
          },
          "origin": "ANONYMOUS_API_OBSERVATION",
          "source_ladder": "independently_observed_anonymous_api[0]",
          "status": "SUPPORTED",
          "text": "project 87779099 is publicly readable (HTTP 200)"
        },
        {
          "check_kind": "ISSUE_METADATA",
          "claim_id": "duo-9671626-02",
          "detail": "the anonymous issue read confirms every stated field exactly",
          "observed": {
            "issue_metadata": {
              "author": {
                "id": 39306908,
                "name": "Mehmet Aydoğan",
                "username": "zyganali"
              },
              "created_at": "2026-10-18T18:56:41.601Z",
              "labels": [
                "retirement-decision",
                "termivance::b3"
              ],
              "state": "opened",
              "title": "[B3] Retirement status: BLOCKED (deterministic) - graph-bound authority, proven-transition absence, durable single-use authorization",
              "updated_at": "2026-10-19T08:57:41.500Z",
              "user_notes_count": 3
            },
            "issue_read_status": 200,
            "observed_at": "2026-10-19T16:26:02.530404+00:00"
          },
          "origin": "ANONYMOUS_API_OBSERVATION",
          "source_ladder": "independently_observed_anonymous_api[1]",
          "status": "SUPPORTED",
          "text": "issue #3 exists, state opened, title/labels/author match the recorded B3 retirement status thread"
        },
        {
          "check_kind": "CONSISTENCY_INFERENCE",
          "claim_id": "duo-9671626-03",
          "detail": "the observable core matches, but 'consistent with' is not proof: the inference is never promoted to SUPPORTED",
          "observed": {
            "issue_metadata": {
              "author": {
                "id": 39306908,
                "name": "Mehmet Aydoğan",
                "username": "zyganali"
              },
              "created_at": "2026-10-18T18:56:41.601Z",
              "labels": [
                "retirement-decision",
                "termivance::b3"
              ],
              "state": "opened",
              "title": "[B3] Retirement status: BLOCKED (deterministic) - graph-bound authority, proven-transition absence, durable single-use authorization",
              "updated_at": "2026-10-19T08:57:41.500Z",
              "user_notes_count": 3
            },
            "issue_read_status": 200,
            "observed_at": "2026-10-19T16:26:02.530404+00:00"
          },
          "origin": "ANONYMOUS_API_OBSERVATION",
          "source_ladder": "independently_observed_anonymous_api[2]",
          "status": "UNRESOLVED",
          "text": "issue user_notes_count=3 and updated_at=2026-10-19T08:57:41.500Z are consistent with, but not proof of, the operator-reported new comment window"
        },
        {
          "check_kind": "SESSION_UI_PROBE",
          "claim_id": "duo-9671626-04",
          "detail": "the agent-sessions UI is an authenticated surface; the anonymous probe returned 404 — an access observation that can neither confirm nor deny the session's recorded state, and is never promoted",
          "observed": {
            "observed_at": "2026-10-19T16:26:02.530404+00:00",
            "session_ui_status": 404,
            "session_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9671626"
          },
          "origin": "OPERATOR_CONFIRMED_UI",
          "source_ladder": "operator_confirmed_only[0]",
          "status": "UNRESOLVED",
          "text": "session id 9671626 exists and Finished in the authenticated automate/agent-sessions UI"
        },
        {
          "check_kind": "ISSUE_NOTE_READ",
          "claim_id": "duo-9671626-05",
          "detail": "note/discussion reads returned 401 to this anonymous identity; an access observation is not absence and is certainly not attribution — the claim cannot be attributed",
          "observed": {
            "note_id_claimed": 4040776241,
            "notes_read_status": 401,
            "observed_at": "2026-10-19T16:26:02.530404+00:00"
          },
          "origin": "OPERATOR_CONFIRMED_NOTE_CONTENT",
          "source_ladder": "operator_confirmed_only[1]",
          "status": "NOT_AUTHENTICALLY_ATTRIBUTABLE",
          "text": "the agent-authored comment note id 4040776241 was published on issue #3 by the GitLab Duo service account"
        },
        {
          "check_kind": "ISSUE_NOTE_READ",
          "claim_id": "duo-9671626-06",
          "detail": "note/discussion reads returned 401 to this anonymous identity; an access observation is not absence and is certainly not attribution — the claim cannot be attributed",
          "observed": {
            "note_id_claimed": 4040776241,
            "notes_read_status": 401,
            "observed_at": "2026-10-19T16:26:02.530404+00:00"
          },
          "origin": "OPERATOR_CONFIRMED_NOTE_CONTENT",
          "source_ladder": "operator_confirmed_only[2]",
          "status": "NOT_AUTHENTICALLY_ATTRIBUTABLE",
          "text": "the six-section analysis content itself and its read-only, non-authoritative character"
        },
        {
          "check_kind": "FLOW_INTERNALS",
          "claim_id": "duo-9671626-07",
          "detail": "flow-execution internals have no independently observable surface; the claim can never be promoted by this tool",
          "observed": {
            "observed_at": "2026-10-19T16:26:02.530404+00:00"
          },
          "origin": "OPERATOR_CONFIRMED_UI",
          "source_ladder": "operator_confirmed_only[3]",
          "status": "UNSUPPORTED",
          "text": "the agent used genuine GitLab tools and stated it did NOT directly query disposable project 87785099"
        },
        {
          "check_kind": "OBSERVABILITY_PROBE",
          "claim_id": "duo-9671626-08",
          "detail": "the anonymous probe reproduces the recorded access observation (HTTP 401)",
          "observed": {
            "actual_status": 401,
            "expected_status": 401,
            "observed_at": "2026-10-19T16:26:02.530404+00:00",
            "surface": "notes"
          },
          "origin": "ANONYMOUS_API_OBSERVATION",
          "source_ladder": "not_independently_observable_and_never_promoted[0]",
          "status": "SUPPORTED",
          "text": "note/discussion contents (HTTP 401 to anonymous readers; 401 is an access observation, never absence, never authenticity)"
        },
        {
          "check_kind": "OBSERVABILITY_PROBE",
          "claim_id": "duo-9671626-09",
          "detail": "the anonymous probe reproduces the recorded access observation (HTTP 404)",
          "observed": {
            "actual_status": 404,
            "expected_status": 404,
            "observed_at": "2026-10-19T16:26:02.530404+00:00",
            "surface": "session_ui"
          },
          "origin": "ANONYMOUS_API_OBSERVATION",
          "source_ladder": "not_independently_observable_and_never_promoted[1]",
          "status": "SUPPORTED",
          "text": "flow-execution internals behind the agent-sessions UI (HTTP 404 to anonymous clients)"
        }
      ],
      "claims_source": "C:\\Users\\MEHMET\\.gemini\\antigravity\\scratch\\Termivance\\evidence\\b4\\duo_session_9671626_readback.json",
      "duo_session_id": "9671626",
      "flow_catalog_item_id": 1018562,
      "fresh_until": "2026-10-19T16:41:02.530404+00:00",
      "observed_at": "2026-10-19T16:26:02.530404+00:00",
      "schema": "termivance.duo_reconciliation/v1",
      "surface": {
        "discussions_read_status": 401,
        "issue_iid": 3,
        "issue_metadata": {
          "author": {
            "id": 39306908,
            "name": "Mehmet Aydoğan",
            "username": "zyganali"
          },
          "created_at": "2026-10-18T18:56:41.601Z",
          "labels": [
            "retirement-decision",
            "termivance::b3"
          ],
          "state": "opened",
          "title": "[B3] Retirement status: BLOCKED (deterministic) - graph-bound authority, proven-transition absence, durable single-use authorization",
          "updated_at": "2026-10-19T08:57:41.500Z",
          "user_notes_count": 3
        },
        "issue_read_status": 200,
        "notes_read_status": 401,
        "observed_at": "2026-10-19T16:26:02.530404+00:00",
        "project_id": 87779099,
        "project_read_status": 200,
        "provenance": "ANONYMOUS_PUBLIC_READ",
        "session_ui_status": 404,
        "session_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance/-/automate/agent-sessions/9671626"
      },
      "totals": {
        "NOT_AUTHENTICALLY_ATTRIBUTABLE": 2,
        "SUPPORTED": 4,
        "UNRESOLVED": 2,
        "UNSUPPORTED": 1
      }
    },
    "portfolio": {
      "assets": [
        {
          "archived": null,
          "description": "Transcend Hackathon Showcase workspace for @zyganali (DevPost: zyganali). Visit the [onboarding issue](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/showcase/-/work_items/1) to get started.",
          "error_kind": "AUTH_DENIED",
          "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/showcase",
          "name": "Showcase",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "ok": true,
          "pages_state": "PAGES_UNVERIFIABLE_403",
          "project_id": 87777871,
          "provenance": "ANONYMOUS_PUBLIC_READ",
          "resources": [
            {
              "detail": {
                "project_id": 87777871
              },
              "endpoint": "/projects/87777871/pages",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "pages_site:87777871:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
            },
            {
              "detail": {
                "project_id": 87777871
              },
              "endpoint": "/projects/87777871/repository/files/.gitlab-ci.yml/raw",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "CI_REDEPLOYMENT_MECHANISM",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "ci_redeployment_mechanism:87777871:not_observed",
              "state": "NOT_OBSERVED (NOT_FOUND)",
              "support": "NOT_OBSERVED"
            },
            {
              "detail": {
                "project_id": 87777871
              },
              "endpoint": "/projects/87777871/environments",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "ENVIRONMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "environment:87777871:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
            },
            {
              "detail": {
                "project_id": 87777871
              },
              "endpoint": "/projects/87777871/deployments",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "DEPLOYMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "deployment:87777871:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
            },
            {
              "detail": {
                "iid": 1,
                "labels": [],
                "project_id": 87777871,
                "retirement_related": false,
                "title": "Welcome to the Transcend Hackathon 🎉"
              },
              "endpoint": "/projects/87777871/issues?state=opened",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "issue:87777871:1",
              "state": "opened",
              "support": "OBSERVED"
            }
          ],
          "role": "PROTECTED (organizer Showcase project is shared and must never be retired)",
          "visibility": "public",
          "web_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/showcase"
        },
        {
          "archived": null,
          "description": "Proof-Bounded Software Retirement Protocol (GitLab Transcend 2026, Path A / Start Fresh).",
          "error_kind": "AUTH_DENIED",
          "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance",
          "name": "Termivance",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "ok": true,
          "pages_state": "PAGES_UNVERIFIABLE_403",
          "project_id": 87779099,
          "provenance": "ANONYMOUS_PUBLIC_READ",
          "resources": [
            {
              "detail": {
                "project_id": 87779099
              },
              "endpoint": "/projects/87779099/pages",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "pages_site:87779099:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
            },
            {
              "detail": {
                "configuration_complete": true,
                "project_id": 87779099,
                "signals": []
              },
              "endpoint": "/projects/87779099/repository/files/.gitlab-ci.yml/raw",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "CI_REDEPLOYMENT_MECHANISM",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "ci_redeployment:87779099",
              "state": "NO_PAGES_SIGNAL_IN_DEFAULT_BRANCH_CONFIG",
              "support": "OBSERVED"
            },
            {
              "detail": {
                "project_id": 87779099
              },
              "endpoint": "/projects/87779099/environments",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "ENVIRONMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "environment:87779099:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
            },
            {
              "detail": {
                "project_id": 87779099
              },
              "endpoint": "/projects/87779099/deployments",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "DEPLOYMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "deployment:87779099:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
            },
            {
              "detail": {
                "iid": 5,
                "labels": [
                  "demo-neutral",
                  "retirement-decision",
                  "termivance::b4"
                ],
                "project_id": 87779099,
                "retirement_related": true,
                "title": "[B4-DEMO] Neutral supervised retirement analysis request: target project 87785099"
              },
              "endpoint": "/projects/87779099/issues?state=opened",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "issue:87779099:5",
              "state": "opened",
              "support": "OBSERVED"
            },
            {
              "detail": {
                "iid": 4,
                "labels": [
                  "retirement-decision",
                  "termivance::b4"
                ],
                "project_id": 87779099,
                "retirement_related": true,
                "title": "[B4-DEMO] Supervised retirement analysis request: target project 87785099"
              },
              "endpoint": "/projects/87779099/issues?state=opened",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "issue:87779099:4",
              "state": "opened",
              "support": "OBSERVED"
            },
            {
              "detail": {
                "iid": 3,
                "labels": [
                  "retirement-decision",
                  "termivance::b3"
                ],
                "project_id": 87779099,
                "retirement_related": true,
                "title": "[B3] Retirement status: BLOCKED (deterministic) - graph-bound authority, proven-transition absence, durable single-use authorization"
              },
              "endpoint": "/projects/87779099/issues?state=opened",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "issue:87779099:3",
              "state": "opened",
              "support": "OBSERVED"
            },
            {
              "detail": {
                "iid": 2,
                "labels": [
                  "retirement-decision",
                  "termivance::b2"
                ],
                "project_id": 87779099,
                "retirement_related": true,
                "title": "B2 retirement decision: BLOCKED (deterministic, read-only)"
              },
              "endpoint": "/projects/87779099/issues?state=opened",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "issue:87779099:2",
              "state": "opened",
              "support": "OBSERVED"
            },
            {
              "detail": {
                "iid": 1,
                "labels": [
                  "retirement-analysis",
                  "termivance::b1"
                ],
                "project_id": 87779099,
                "retirement_related": true,
                "title": "B1 retirement-analysis request (harmless, non-authoritative)"
              },
              "endpoint": "/projects/87779099/issues?state=opened",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "issue:87779099:1",
              "state": "opened",
              "support": "OBSERVED"
            }
          ],
          "role": "PROTECTED (canonical Termivance repository is expressly excluded from retirement)",
          "visibility": "public",
          "web_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance"
        },
        {
          "archived": null,
          "description": "DISPOSABLE B3 demonstration target. Temporary. Safe to retire. Do not treat as canonical.",
          "error_kind": "AUTH_DENIED",
          "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
          "name": "termivance-b3-disposable-pages-demo",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "ok": true,
          "pages_state": "PAGES_UNVERIFIABLE_403",
          "project_id": 87785099,
          "provenance": "ANONYMOUS_PUBLIC_READ",
          "resources": [
            {
              "detail": {
                "project_id": 87785099
              },
              "endpoint": "/projects/87785099/pages",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "pages_site:87785099:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
            },
            {
              "detail": {
                "configuration_complete": true,
                "project_id": 87785099,
                "signals": [
                  "pages_true",
                  "pages_keyword"
                ]
              },
              "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "CI_REDEPLOYMENT_MECHANISM",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "ci_redeployment:87785099",
              "state": "PAGES_REDEPLOYMENT_SIGNAL_PRESENT",
              "support": "OBSERVED"
            },
            {
              "detail": {
                "project_id": 87785099
              },
              "endpoint": "/projects/87785099/environments",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "ENVIRONMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "environment:87785099:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
            },
            {
              "detail": {
                "project_id": 87785099
              },
              "endpoint": "/projects/87785099/deployments",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "DEPLOYMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "deployment:87785099:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
            }
          ],
          "role": "APPROVED_RETIREMENT_TARGET",
          "visibility": "public",
          "web_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
        },
        {
          "archived": null,
          "description": "",
          "error_kind": "NOT_FOUND",
          "full_path": "projects/87786164",
          "name": "(unreadable)",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "ok": false,
          "pages_state": "UNKNOWN",
          "project_id": 87786164,
          "provenance": "ANONYMOUS_PUBLIC_READ",
          "resources": [
            {
              "detail": {
                "project_id": 87786164
              },
              "endpoint": "/projects/87786164/pages",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "pages_site:87786164:not_observed",
              "state": "NOT_OBSERVED (NOT_FOUND)",
              "support": "NOT_OBSERVED"
            }
          ],
          "role": "NON_TARGET",
          "visibility": "unknown",
          "web_url": ""
        }
      ],
      "observed_at": "2026-10-19T20:47:44.867015+00:00",
      "provenance": "ANONYMOUS_PUBLIC_READ",
      "relations": [
        {
          "dst": "pages_site:87779099:not_observed",
          "kind": "obligates",
          "src": "issue:87779099:5",
          "support": "INFERRED"
        },
        {
          "dst": "pages_site:87779099:not_observed",
          "kind": "obligates",
          "src": "issue:87779099:4",
          "support": "INFERRED"
        },
        {
          "dst": "pages_site:87779099:not_observed",
          "kind": "obligates",
          "src": "issue:87779099:3",
          "support": "INFERRED"
        },
        {
          "dst": "pages_site:87779099:not_observed",
          "kind": "obligates",
          "src": "issue:87779099:2",
          "support": "INFERRED"
        },
        {
          "dst": "pages_site:87779099:not_observed",
          "kind": "obligates",
          "src": "issue:87779099:1",
          "support": "INFERRED"
        },
        {
          "dst": "pages_site:87785099:not_observed",
          "kind": "recreates",
          "src": "ci_redeployment:87785099",
          "support": "INFERRED"
        }
      ],
      "schema": "termivance.portfolio/v2",
      "totals": {
        "approved_targets": 1,
        "assets": 4,
        "inferred_relations": 6,
        "observed_relations": 0,
        "pages_not_observed": 0,
        "pages_sites": 0,
        "pages_unverifiable": 3,
        "protected": 2,
        "resource_kinds_observed": {
          "CI_REDEPLOYMENT_MECHANISM": 2,
          "OPEN_ISSUE": 6
        },
        "resources_not_observed": 11,
        "resources_observed": 8
      }
    },
    "receipt": {
      "absence_evidence": "NOT_RUN",
      "claimed_verdict": null,
      "display_verdict": "NOT_RUN",
      "evidence_level": "NOT_APPLICABLE",
      "evidence_level_detail": "no receipt to classify",
      "ledger_validation": "NOT_APPLICABLE",
      "mutation_accepted": null,
      "mutation_attempted": null,
      "mutation_evidence": "NOT_RUN",
      "note": "no receipt artifact was supplied; the runtime records no mutation attempt and this page will not pretend otherwise",
      "receipt_integrity": "NOT_RUN",
      "receipt_state": "NOT_RUN",
      "record": null,
      "recorded_verdict": null
    },
    "risk_map": {
      "edges": [
        {
          "dst": "obl:ownership_authorization",
          "relation": "impacts",
          "src": "risk:target_not_authorized"
        },
        {
          "dst": "obl:pages_published",
          "relation": "impacts",
          "src": "risk:insufficient_provider_access"
        },
        {
          "dst": "obl:redeployment_path",
          "relation": "impacts",
          "src": "risk:redeployment_risk"
        },
        {
          "dst": "obl:retirement_permission",
          "relation": "impacts",
          "src": "risk:insufficient_permission"
        },
        {
          "dst": "obl:ownership_authorization",
          "relation": "impacts",
          "src": "obligation-violation:obl:ownership_authorization"
        },
        {
          "dst": "obl:pages_published",
          "relation": "impacts",
          "src": "obligation-unknown:obl:pages_published"
        },
        {
          "dst": "obl:redeployment_path",
          "relation": "impacts",
          "src": "obligation-violation:obl:redeployment_path"
        },
        {
          "dst": "obl:retirement_permission",
          "relation": "impacts",
          "src": "obligation-violation:obl:retirement_permission"
        },
        {
          "dst": "not-observed:pages_site:87779099:not_observed",
          "relation": "obligates",
          "src": "resource:issue:87779099:5"
        },
        {
          "dst": "not-observed:pages_site:87779099:not_observed",
          "relation": "obligates",
          "src": "resource:issue:87779099:4"
        },
        {
          "dst": "not-observed:pages_site:87779099:not_observed",
          "relation": "obligates",
          "src": "resource:issue:87779099:3"
        },
        {
          "dst": "not-observed:pages_site:87779099:not_observed",
          "relation": "obligates",
          "src": "resource:issue:87779099:2"
        },
        {
          "dst": "not-observed:pages_site:87779099:not_observed",
          "relation": "obligates",
          "src": "resource:issue:87779099:1"
        },
        {
          "dst": "not-observed:pages_site:87785099:not_observed",
          "relation": "recreates",
          "src": "resource:ci_redeployment:87785099"
        }
      ],
      "nodes": [
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:ci_redeployment_mechanism:87777871:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (NOT_FOUND) via GET /projects/87777871/repository/files/.gitlab-ci.yml/raw [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "CI_REDEPLOYMENT_MECHANISM was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:deployment:87777871:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (AUTH_DENIED) via GET /projects/87777871/deployments [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "DEPLOYMENT was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:deployment:87779099:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (AUTH_DENIED) via GET /projects/87779099/deployments [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "DEPLOYMENT was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:deployment:87785099:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (AUTH_DENIED) via GET /projects/87785099/deployments [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "DEPLOYMENT was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:environment:87777871:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (AUTH_DENIED) via GET /projects/87777871/environments [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "ENVIRONMENT was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:environment:87779099:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (AUTH_DENIED) via GET /projects/87779099/environments [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "ENVIRONMENT was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:environment:87785099:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (AUTH_DENIED) via GET /projects/87785099/environments [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "ENVIRONMENT was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:pages_site:87777871:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (AUTH_DENIED) via GET /projects/87777871/pages [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "PAGES_SITE was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:pages_site:87779099:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (AUTH_DENIED) via GET /projects/87779099/pages [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "PAGES_SITE was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:pages_site:87785099:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (AUTH_DENIED) via GET /projects/87785099/pages [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "PAGES_SITE was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [],
          "kind": "RISK",
          "mitigations": [
            "re-check via an authorized read when credentials permit"
          ],
          "node_id": "not-observed:pages_site:87786164:not_observed",
          "severity": "MEDIUM",
          "state": "NOT_OBSERVED (NOT_FOUND) via GET /projects/87786164/pages [ANONYMOUS_PUBLIC_READ]; a 401/403/404 is never absence",
          "title": "PAGES_SITE was NOT_OBSERVED at the provider"
        },
        {
          "impacts": [
            "obl:pages_published"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "obligation-unknown:obl:pages_published",
          "severity": "MEDIUM",
          "state": "status=UNKNOWN",
          "title": "obligation PAGES_PUBLISHED is unverifiable"
        },
        {
          "impacts": [
            "obl:ownership_authorization"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "obligation-violation:obl:ownership_authorization",
          "severity": "HIGH",
          "state": "status=VIOLATED",
          "title": "obligation OWNERSHIP_AUTHORIZATION is violated"
        },
        {
          "impacts": [
            "obl:redeployment_path"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "obligation-violation:obl:redeployment_path",
          "severity": "HIGH",
          "state": "status=VIOLATED",
          "title": "obligation REDEPLOYMENT_PATH is violated"
        },
        {
          "impacts": [
            "obl:retirement_permission"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "obligation-violation:obl:retirement_permission",
          "severity": "HIGH",
          "state": "status=VIOLATED",
          "title": "obligation RETIREMENT_PERMISSION is violated"
        },
        {
          "impacts": [
            "obl:retirement_permission"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "risk:insufficient_permission",
          "severity": "MEDIUM",
          "state": "the acting identity lacks Maintainer/Owner Pages administration on the target",
          "title": "operator permission missing or insufficient"
        },
        {
          "impacts": [
            "obl:pages_published"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "risk:insufficient_provider_access",
          "severity": "MEDIUM",
          "state": "publication could not be observed (AUTH_DENIED)",
          "title": "provider access cannot verify state"
        },
        {
          "impacts": [
            "obl:redeployment_path"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "risk:redeployment_risk",
          "severity": "MEDIUM",
          "state": "1 observed redeployment/recreation mechanism(s)",
          "title": "an active redeployment path can resurrect the site"
        },
        {
          "impacts": [
            "obl:ownership_authorization"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "risk:target_not_authorized",
          "severity": "MEDIUM",
          "state": "no bound authorization supplied",
          "title": "target lies outside the authorized retirement scope"
        },
        {
          "impacts": [],
          "kind": "DEPENDENCY",
          "mitigations": [
            "observation only; mutation_capability=NOT_AUTHORIZING"
          ],
          "node_id": "resource:ci_redeployment:87779099",
          "severity": "LOW",
          "state": "NO_PAGES_SIGNAL_IN_DEFAULT_BRANCH_CONFIG via GET /projects/87779099/repository/files/.gitlab-ci.yml/raw [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T21:02:44.867015+00:00]",
          "title": "CI_REDEPLOYMENT_MECHANISM NO_PAGES_SIGNAL_IN_DEFAULT_BRANCH_CONFIG"
        },
        {
          "impacts": [],
          "kind": "DEPENDENCY",
          "mitigations": [
            "observation only; mutation_capability=NOT_AUTHORIZING"
          ],
          "node_id": "resource:ci_redeployment:87785099",
          "severity": "HIGH",
          "state": "PAGES_REDEPLOYMENT_SIGNAL_PRESENT via GET /projects/87785099/repository/files/.gitlab-ci.yml/raw [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T21:02:44.867015+00:00]",
          "title": "CI_REDEPLOYMENT_MECHANISM PAGES_REDEPLOYMENT_SIGNAL_PRESENT"
        },
        {
          "impacts": [],
          "kind": "DEPENDENCY",
          "mitigations": [
            "observation only; mutation_capability=NOT_AUTHORIZING"
          ],
          "node_id": "resource:issue:87777871:1",
          "severity": "LOW",
          "state": "opened via GET /projects/87777871/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T21:02:44.867015+00:00]",
          "title": "OPEN_ISSUE opened"
        },
        {
          "impacts": [],
          "kind": "DEPENDENCY",
          "mitigations": [
            "observation only; mutation_capability=NOT_AUTHORIZING"
          ],
          "node_id": "resource:issue:87779099:1",
          "severity": "LOW",
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T21:02:44.867015+00:00]",
          "title": "OPEN_ISSUE opened"
        },
        {
          "impacts": [],
          "kind": "DEPENDENCY",
          "mitigations": [
            "observation only; mutation_capability=NOT_AUTHORIZING"
          ],
          "node_id": "resource:issue:87779099:2",
          "severity": "LOW",
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T21:02:44.867015+00:00]",
          "title": "OPEN_ISSUE opened"
        },
        {
          "impacts": [],
          "kind": "DEPENDENCY",
          "mitigations": [
            "observation only; mutation_capability=NOT_AUTHORIZING"
          ],
          "node_id": "resource:issue:87779099:3",
          "severity": "LOW",
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T21:02:44.867015+00:00]",
          "title": "OPEN_ISSUE opened"
        },
        {
          "impacts": [],
          "kind": "DEPENDENCY",
          "mitigations": [
            "observation only; mutation_capability=NOT_AUTHORIZING"
          ],
          "node_id": "resource:issue:87779099:4",
          "severity": "LOW",
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T21:02:44.867015+00:00]",
          "title": "OPEN_ISSUE opened"
        },
        {
          "impacts": [],
          "kind": "DEPENDENCY",
          "mitigations": [
            "observation only; mutation_capability=NOT_AUTHORIZING"
          ],
          "node_id": "resource:issue:87779099:5",
          "severity": "LOW",
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T21:02:44.867015+00:00]",
          "title": "OPEN_ISSUE opened"
        },
        {
          "impacts": [],
          "kind": "CONTROL",
          "mitigations": [],
          "node_id": "obl:identity_binding",
          "severity": "NONE",
          "state": "status=SATISFIED via controlled evidence",
          "title": "obligation IDENTITY_BINDING is satisfied"
        },
        {
          "impacts": [],
          "kind": "CONTROL",
          "mitigations": [],
          "node_id": "obl:ownership_authorization",
          "severity": "NONE",
          "state": "status=VIOLATED",
          "title": "obligation OWNERSHIP_AUTHORIZATION must hold"
        },
        {
          "impacts": [],
          "kind": "CONTROL",
          "mitigations": [],
          "node_id": "obl:pages_published",
          "severity": "NONE",
          "state": "status=UNKNOWN",
          "title": "obligation PAGES_PUBLISHED must hold"
        },
        {
          "impacts": [],
          "kind": "CONTROL",
          "mitigations": [],
          "node_id": "obl:provider_observation",
          "severity": "NONE",
          "state": "status=SATISFIED via controlled evidence",
          "title": "obligation PROVIDER_OBSERVATION is satisfied"
        },
        {
          "impacts": [],
          "kind": "CONTROL",
          "mitigations": [],
          "node_id": "obl:redeployment_path",
          "severity": "NONE",
          "state": "status=VIOLATED",
          "title": "obligation REDEPLOYMENT_PATH must hold"
        },
        {
          "impacts": [],
          "kind": "CONTROL",
          "mitigations": [],
          "node_id": "obl:retirement_permission",
          "severity": "NONE",
          "state": "status=VIOLATED",
          "title": "obligation RETIREMENT_PERMISSION must hold"
        },
        {
          "impacts": [],
          "kind": "CONTROL",
          "mitigations": [],
          "node_id": "obl:target_scope",
          "severity": "NONE",
          "state": "status=SATISFIED via controlled evidence",
          "title": "obligation TARGET_SCOPE is satisfied"
        },
        {
          "impacts": [],
          "kind": "CONTROL",
          "mitigations": [],
          "node_id": "obl:unresolved_work",
          "severity": "NONE",
          "state": "status=SATISFIED via controlled evidence",
          "title": "obligation UNRESOLVED_WORK is satisfied"
        }
      ],
      "schema": "termivance.risk_map/v1",
      "target": {
        "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
        "project_id": 87785099,
        "resource_kind": "GITLAB_PAGES_SITE"
      },
      "verdict": "BLOCKED"
    },
    "simulation": {
      "banner": "HYPOTHETICAL SIMULATION — no request was sent, nothing was mutated, no verdict was earned",
      "cross_resource_factors": [
        {
          "fresh_until": "2026-10-19T21:02:44.867015+00:00",
          "kind": "CI_REDEPLOYMENT_MECHANISM",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "observed_state": "NO_PAGES_SIGNAL_IN_DEFAULT_BRANCH_CONFIG",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; CI_REDEPLOYMENT_MECHANISM observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "ci_redeployment:87779099",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T21:02:44.867015+00:00",
          "kind": "CI_REDEPLOYMENT_MECHANISM",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "observed_state": "PAGES_REDEPLOYMENT_SIGNAL_PRESENT",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; CI_REDEPLOYMENT_MECHANISM observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "ci_redeployment:87785099",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T21:02:44.867015+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87777871:1",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T21:02:44.867015+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:1",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T21:02:44.867015+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:2",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T21:02:44.867015+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:3",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T21:02:44.867015+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:4",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T21:02:44.867015+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T20:47:44.867015+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:5",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "kind": "CI_REDEPLOYMENT_MECHANISM",
          "observed_state": "PAGES_REDEPLOYMENT_SIGNAL_PRESENT",
          "projection": "the recorded CI mechanism could redeploy the site after retirement (INFERRED from configuration text); resurrection is a live risk, never a verdict",
          "resource": "cross-resource:redeployment",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "INFERRED_CAPABILITY"
        }
      ],
      "decision": {
        "action": "unpublish_pages",
        "authoritative": false,
        "evaluated_at": "2026-10-19T20:47:44.867015+00:00",
        "graph": {
          "dependencies": [
            {
              "active": true,
              "dependency_id": "dep:active_redeployment",
              "description": "observed Pages deployment mechanism in CI configuration",
              "evidence_id": "ev:ci_config",
              "kind": "ACTIVE_REDEPLOYMENT"
            },
            {
              "active": false,
              "dependency_id": "dep:open_work_item",
              "description": "0 open retirement-related work item(s)",
              "evidence_id": "ev:open_issues",
              "kind": "OPEN_WORK_ITEM"
            }
          ],
          "edges": [
            {
              "from": "target:87785099:GITLAB_PAGES_SITE",
              "relation": "HAS_OBLIGATION",
              "to": "obl:target_scope"
            },
            {
              "from": "target:87785099:GITLAB_PAGES_SITE",
              "relation": "HAS_OBLIGATION",
              "to": "obl:ownership_authorization"
            },
            {
              "from": "target:87785099:GITLAB_PAGES_SITE",
              "relation": "HAS_OBLIGATION",
              "to": "obl:retirement_permission"
            },
            {
              "from": "target:87785099:GITLAB_PAGES_SITE",
              "relation": "HAS_OBLIGATION",
              "to": "obl:pages_published"
            },
            {
              "from": "target:87785099:GITLAB_PAGES_SITE",
              "relation": "HAS_OBLIGATION",
              "to": "obl:identity_binding"
            },
            {
              "from": "target:87785099:GITLAB_PAGES_SITE",
              "relation": "HAS_OBLIGATION",
              "to": "obl:provider_observation"
            },
            {
              "from": "target:87785099:GITLAB_PAGES_SITE",
              "relation": "HAS_OBLIGATION",
              "to": "obl:unresolved_work"
            },
            {
              "from": "target:87785099:GITLAB_PAGES_SITE",
              "relation": "HAS_OBLIGATION",
              "to": "obl:redeployment_path"
            },
            {
              "from": "obl:provider_observation",
              "relation": "REQUIRES_EVIDENCE",
              "to": "ev:project_identity"
            },
            {
              "from": "obl:identity_binding",
              "relation": "REQUIRES_EVIDENCE",
              "to": "ev:project_identity"
            },
            {
              "from": "obl:identity_binding",
              "relation": "REQUIRES_EVIDENCE",
              "to": "ev:branch"
            },
            {
              "from": "obl:redeployment_path",
              "relation": "REQUIRES_EVIDENCE",
              "to": "ev:ci_config"
            },
            {
              "from": "obl:unresolved_work",
              "relation": "REQUIRES_EVIDENCE",
              "to": "ev:open_issues"
            },
            {
              "from": "obl:retirement_permission",
              "relation": "REQUIRES_EVIDENCE",
              "to": "ev:effective_permission"
            },
            {
              "from": "obl:identity_binding",
              "relation": "REQUIRES_EVIDENCE",
              "to": "ev:effective_permission"
            },
            {
              "from": "obl:pages_published",
              "relation": "REQUIRES_EVIDENCE",
              "to": "ev:pages_deployment"
            },
            {
              "from": "obl:identity_binding",
              "relation": "REQUIRES_EVIDENCE",
              "to": "ev:pages_deployment"
            },
            {
              "from": "obl:unresolved_work",
              "relation": "BLOCKED_BY",
              "to": "dep:open_work_item"
            },
            {
              "from": "obl:redeployment_path",
              "relation": "BLOCKED_BY",
              "to": "dep:active_redeployment"
            }
          ],
          "evidence": [
            {
              "classification": "LIVE",
              "detail": {
                "branch": "main",
                "commit_id": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
              },
              "digest": "11688fd09e0d06312ba2934b2b5aad899e1dc1b71e254639310c8b1cb9714aba",
              "endpoint": "/projects/87785099/repository/branches/main",
              "error_kind": null,
              "evidence_id": "ev:branch",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "BRANCH",
              "method": "GET",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "status": 200,
              "target": {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            },
            {
              "classification": "LIVE",
              "detail": {
                "bytes": 320,
                "file": ".gitlab-ci.yml",
                "includes_present": false,
                "pages_mechanism": true,
                "pages_signals": [
                  "pages_true",
                  "pages_keyword"
                ],
                "present": true,
                "ref": "main",
                "refs_examined": [
                  "main"
                ]
              },
              "digest": "ff9ca84d2117058681353e234a6cda441b6831cd9e8b3540a22cf02595a32b37",
              "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
              "error_kind": null,
              "evidence_id": "ev:ci_config",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "CI_CONFIG",
              "method": "GET",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "status": 200,
              "target": {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            },
            {
              "classification": "LIVE",
              "detail": {
                "can_manage_pages": false,
                "effective_access_level": null,
                "pages_api_error": "AUTH_DENIED",
                "pages_api_status": 403
              },
              "digest": "034fcec2a8deeee99eadeac6496228730fa29905e4d807d8a8487d96b8dd7ec5",
              "endpoint": "/projects/87785099",
              "error_kind": null,
              "evidence_id": "ev:effective_permission",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "EFFECTIVE_PERMISSION",
              "method": "GET",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "status": 200,
              "target": {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            },
            {
              "classification": "LIVE",
              "detail": {
                "error": "AUTH_DENIED"
              },
              "digest": "be458994bf4fae39544bf92130b1d29908c0c918ca5515468d47e326bb9406df",
              "endpoint": "/projects/87785099/environments",
              "error_kind": "AUTH_DENIED",
              "evidence_id": "ev:environment",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "ENVIRONMENT",
              "method": "GET",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "status": 401,
              "target": {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            },
            {
              "classification": "LIVE",
              "detail": {
                "open_count": 0,
                "retirement_related": []
              },
              "digest": "e53888a5d945e88f379bf5b2d42b12de6b07f7eb50a01a60d7182ba9d8dbd941",
              "endpoint": "/projects/87785099/issues",
              "error_kind": null,
              "evidence_id": "ev:open_issues",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "OPEN_ISSUES",
              "method": "GET",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "status": 200,
              "target": {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            },
            {
              "classification": "LIVE",
              "detail": {
                "error": "AUTH_DENIED"
              },
              "digest": "ed76fbefd375028ae456c69ae43ea1760fe0127b3b265b01a6da7365e1f30b57",
              "endpoint": "/projects/87785099/pages",
              "error_kind": "AUTH_DENIED",
              "evidence_id": "ev:pages",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "PAGES",
              "method": "GET",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "status": 403,
              "target": {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            },
            {
              "classification": "LIVE",
              "detail": {
                "error": "AUTH_DENIED"
              },
              "digest": "a457b85e3514de39f9ee1d8efa9a930957bd150e349e0a19bec335458186dee2",
              "endpoint": "/projects/87785099/pages",
              "error_kind": "AUTH_DENIED",
              "evidence_id": "ev:pages_deployment",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "PAGES_DEPLOYMENT",
              "method": "GET",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "status": 403,
              "target": {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            },
            {
              "classification": "LIVE",
              "detail": {
                "latest_id": 2960507698,
                "latest_status": "success"
              },
              "digest": "139526b14c99f11599c55963a526587621660279ee86e1f6dc295997f46548ea",
              "endpoint": "/projects/87785099/pipelines",
              "error_kind": null,
              "evidence_id": "ev:pipeline",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "PIPELINE",
              "method": "GET",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "status": 200,
              "target": {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            },
            {
              "classification": "LIVE",
              "detail": {
                "archived": null,
                "default_branch": "main",
                "namespace_full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908",
                "path_with_namespace": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "visibility": "public",
                "web_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
              },
              "digest": "9a3e0e8923f564e7f51d2c2e7930ce020ba5983e37b83ec751a6d2c946599f64",
              "endpoint": "/projects/87785099",
              "error_kind": null,
              "evidence_id": "ev:project_identity",
              "fresh_until": "2026-10-19T21:02:44.867015+00:00",
              "kind": "PROJECT_IDENTITY",
              "method": "GET",
              "observed_at": "2026-10-19T20:47:44.867015+00:00",
              "status": 200,
              "target": {
                "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                "project_id": 87785099,
                "resource_kind": "GITLAB_PAGES_SITE"
              }
            }
          ],
          "obligations": [
            {
              "description": "all evidence is bound to the exact target identity",
              "kind": "IDENTITY_BINDING",
              "mandatory": true,
              "obligation_id": "obl:identity_binding"
            },
            {
              "description": "an exact-target authorization exists for the requested action",
              "kind": "OWNERSHIP_AUTHORIZATION",
              "mandatory": true,
              "obligation_id": "obl:ownership_authorization"
            },
            {
              "description": "the target is a genuinely published Pages site observed before retirement",
              "kind": "PAGES_PUBLISHED",
              "mandatory": true,
              "obligation_id": "obl:pages_published"
            },
            {
              "description": "a fresh provider observation of the target is available",
              "kind": "PROVIDER_OBSERVATION",
              "mandatory": true,
              "obligation_id": "obl:provider_observation"
            },
            {
              "description": "no active mechanism can redeploy or recreate the target",
              "kind": "REDEPLOYMENT_PATH",
              "mandatory": true,
              "obligation_id": "obl:redeployment_path"
            },
            {
              "description": "the acting identity can administer GitLab Pages on the target",
              "kind": "RETIREMENT_PERMISSION",
              "mandatory": true,
              "obligation_id": "obl:retirement_permission"
            },
            {
              "description": "target is in the permitted, non-protected retirement scope",
              "kind": "TARGET_SCOPE",
              "mandatory": true,
              "obligation_id": "obl:target_scope"
            },
            {
              "description": "no unresolved retirement-related work item remains",
              "kind": "UNRESOLVED_WORK",
              "mandatory": true,
              "obligation_id": "obl:unresolved_work"
            }
          ],
          "schema": "termivance.retirement_obligation_graph/v1",
          "targets": [
            {
              "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
              "project_id": 87785099,
              "resource_kind": "GITLAB_PAGES_SITE"
            }
          ]
        },
        "missing_conditions": [
          "resolve TARGET_NOT_AUTHORIZED: no bound authorization supplied",
          "resolve INSUFFICIENT_PROVIDER_ACCESS: publication could not be observed (AUTH_DENIED)",
          "resolve REDEPLOYMENT_RISK: 1 observed redeployment/recreation mechanism(s)",
          "resolve INSUFFICIENT_PERMISSION: the acting identity lacks Maintainer/Owner Pages administration on the target"
        ],
        "obligations": [
          {
            "kind": "IDENTITY_BINDING",
            "mandatory": true,
            "obligation_id": "obl:identity_binding",
            "status": "SATISFIED"
          },
          {
            "kind": "OWNERSHIP_AUTHORIZATION",
            "mandatory": true,
            "obligation_id": "obl:ownership_authorization",
            "status": "VIOLATED"
          },
          {
            "kind": "PAGES_PUBLISHED",
            "mandatory": true,
            "obligation_id": "obl:pages_published",
            "status": "UNKNOWN"
          },
          {
            "kind": "PROVIDER_OBSERVATION",
            "mandatory": true,
            "obligation_id": "obl:provider_observation",
            "status": "SATISFIED"
          },
          {
            "kind": "REDEPLOYMENT_PATH",
            "mandatory": true,
            "obligation_id": "obl:redeployment_path",
            "status": "VIOLATED"
          },
          {
            "kind": "RETIREMENT_PERMISSION",
            "mandatory": true,
            "obligation_id": "obl:retirement_permission",
            "status": "VIOLATED"
          },
          {
            "kind": "TARGET_SCOPE",
            "mandatory": true,
            "obligation_id": "obl:target_scope",
            "status": "SATISFIED"
          },
          {
            "kind": "UNRESOLVED_WORK",
            "mandatory": true,
            "obligation_id": "obl:unresolved_work",
            "status": "SATISFIED"
          }
        ],
        "read_only": true,
        "reasons": [
          {
            "code": "TARGET_NOT_AUTHORIZED",
            "detail": "no bound authorization supplied",
            "evidence_id": null,
            "obligation_id": "obl:ownership_authorization"
          },
          {
            "code": "INSUFFICIENT_PROVIDER_ACCESS",
            "detail": "publication could not be observed (AUTH_DENIED)",
            "evidence_id": "ev:pages_deployment",
            "obligation_id": "obl:pages_published"
          },
          {
            "code": "REDEPLOYMENT_RISK",
            "detail": "1 observed redeployment/recreation mechanism(s)",
            "evidence_id": "ev:ci_config",
            "obligation_id": "obl:redeployment_path"
          },
          {
            "code": "INSUFFICIENT_PERMISSION",
            "detail": "the acting identity lacks Maintainer/Owner Pages administration on the target",
            "evidence_id": "ev:effective_permission",
            "obligation_id": "obl:retirement_permission"
          }
        ],
        "schema": "termivance.retirement_decision/v1",
        "target": {
          "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
          "project_id": 87785099,
          "resource_kind": "GITLAB_PAGES_SITE"
        },
        "verdict": "BLOCKED"
      },
      "evaluable": true,
      "hypothetical": true,
      "obligation_projections": [
        {
          "consequence": "unchanged by this hypothetical action",
          "current_status": "SATISFIED",
          "flips_eligible": false,
          "obligation_id": "obl:identity_binding",
          "obligation_kind": "IDENTITY_BINDING",
          "projected_status": "SATISFIED"
        },
        {
          "consequence": "unchanged by this hypothetical action",
          "current_status": "VIOLATED",
          "flips_eligible": false,
          "obligation_id": "obl:ownership_authorization",
          "obligation_kind": "OWNERSHIP_AUTHORIZATION",
          "projected_status": "VIOLATED"
        },
        {
          "consequence": "still not proven published; a simulation cannot create evidence",
          "current_status": "UNKNOWN",
          "flips_eligible": false,
          "obligation_id": "obl:pages_published",
          "obligation_kind": "PAGES_PUBLISHED",
          "projected_status": "UNKNOWN"
        },
        {
          "consequence": "provider observations stay historical; they expire and are never extended by the action itself",
          "current_status": "SATISFIED",
          "flips_eligible": false,
          "obligation_id": "obl:provider_observation",
          "obligation_kind": "PROVIDER_OBSERVATION",
          "projected_status": "SATISFIED"
        },
        {
          "consequence": "an active redeployment mechanism would still be able to resurrect the site; it is consumed by retirement, not removed by it",
          "current_status": "VIOLATED",
          "flips_eligible": false,
          "obligation_id": "obl:redeployment_path",
          "obligation_kind": "REDEPLOYMENT_PATH",
          "projected_status": "VIOLATED"
        },
        {
          "consequence": "unchanged by this hypothetical action",
          "current_status": "VIOLATED",
          "flips_eligible": false,
          "obligation_id": "obl:retirement_permission",
          "obligation_kind": "RETIREMENT_PERMISSION",
          "projected_status": "VIOLATED"
        },
        {
          "consequence": "unchanged by this hypothetical action",
          "current_status": "SATISFIED",
          "flips_eligible": false,
          "obligation_id": "obl:target_scope",
          "obligation_kind": "TARGET_SCOPE",
          "projected_status": "SATISFIED"
        },
        {
          "consequence": "no recorded open work item",
          "current_status": "SATISFIED",
          "flips_eligible": false,
          "obligation_id": "obl:unresolved_work",
          "obligation_kind": "UNRESOLVED_WORK",
          "projected_status": "SATISFIED"
        }
      ],
      "projected_provider_effects": [
        {
          "effect": "authorized DELETE /projects/87785099/pages on project 87785099 would be expected to return 2xx",
          "state": "PROJECTED_NOT_OBSERVED"
        },
        {
          "effect": "GET /projects/87785099/pages would be expected to no longer report a deployment — this must be re-observed independently, never assumed",
          "state": "PROJECTED_NOT_OBSERVED"
        },
        {
          "effect": "the previously served URL may return 404 — or keep serving stale content: CDN convergence has unknown delay and errors are never promoted to verified absence",
          "state": "PROJECTED_NOT_OBSERVED"
        }
      ],
      "redeployment_risk": "HIGH: the recorded CI/Pages mechanism can redeploy the site after retirement; resurrection is a live risk unless that path is demonstrably inert — and that is a risk, never a verdict.",
      "schema": "termivance.retirement_simulation/v1",
      "target_project_id": 87785099
    },
    "supervised_review": {
      "authority": "NON_AUTHORITATIVE",
      "autonomy_summary": "Operator/CI-initiated supervised execution pipeline (not an event-driven continuous daemon): 1 genuine Duo autonomous step (session 9710085), 1 structured handoff, 5 deterministic automated step(s) EXECUTED NOW; deterministic engine enforces verdict BLOCKED and requires human operator review before any action.",
      "boundary": "this review connects the genuine Duo analysis to deterministic verification; the AI contribution adds investigation context and risk explanations but cannot award verdicts, modify provider facts, or authorize mutations",
      "candidate_claims": [
        {
          "causal_attribution": "GENUINE_DUO_TARGET_DISCOVERY: Duo independently discovered create-pages / pages: true redeployment path on target 87785099",
          "claim_id": "duo-9710085-cand-01",
          "corroboration_detail": "Target .gitlab-ci.yml at observed commit contains create-pages job with pages: true; establishes active redeployment path.",
          "corroboration_source": "GET /projects/87785099/repository/files/.gitlab-ci.yml?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
          "corroboration_status": "CORROBORATED",
          "exact_target_relationship": "TARGET_BOUND",
          "origin": "GitLab Duo Custom Flow Session 9710085",
          "retirement_relevance": "MATERIAL",
          "source_project": 87785099,
          "text": "Redeployment path: `.gitlab-ci.yml` at 87785099 (`create-pages`, `pages: true`) can republish the site on any pipeline run against the default branch. Candidate obligation: neutralize or control this path, or show that no pipeline can run. This is the main resurrection risk."
        },
        {
          "causal_attribution": "GENUINE_DUO_RISK_HYPOTHESIS: Duo reasoned about unobservable resurrection vectors and external caches",
          "claim_id": "duo-9710085-cand-02",
          "corroboration_detail": "Unobservable via anonymous provider read or GitLab REST API: pipeline schedules, trigger tokens, and edge CDN caches cannot be verified anonymously; preserved as unverified candidate risk hypothesis.",
          "corroboration_source": null,
          "corroboration_status": "UNRESOLVED",
          "exact_target_relationship": "TARGET_BOUND",
          "origin": "GitLab Duo Custom Flow Session 9710085",
          "retirement_relevance": "CONTEXTUAL",
          "source_project": 87785099,
          "text": "Out-of-repo resurrection vectors: These are not visible from repository files:    - pipeline schedules    - trigger tokens    - manual or API pipeline runs    - Pages administration actions through the UI or API    - the Pages deployment-retention behaviour of `pages: true` jobs    - the template copy at `deploy/disposable-pages/.gitlab-ci.yml` in 87779099, which could be copied back to the target"
        },
        {
          "causal_attribution": "GENUINE_DUO_RISK_HYPOTHESIS: Duo reasoned about unobservable resurrection vectors and external caches",
          "claim_id": "duo-9710085-cand-03",
          "corroboration_detail": "Unobservable via anonymous provider read or GitLab REST API: pipeline schedules, trigger tokens, and edge CDN caches cannot be verified anonymously; preserved as unverified candidate risk hypothesis.",
          "corroboration_source": null,
          "corroboration_status": "UNRESOLVED",
          "exact_target_relationship": "TARGET_BOUND",
          "origin": "GitLab Duo Custom Flow Session 9710085",
          "retirement_relevance": "CONTEXTUAL",
          "source_project": 87785099,
          "text": "Cached content: Cached or edge-replicated copies of the served content, including the marker string, may stay reachable after any provider-side change."
        },
        {
          "causal_attribution": "GENUINE_DUO_TARGET_DISCOVERY: Duo identified in-code comment and noted it does not satisfy operator authorization contract",
          "claim_id": "duo-9710085-cand-04",
          "corroboration_detail": "In-code comment verified in target .gitlab-ci.yml; deterministic policy strictly enforces that prose comments cannot grant operator authorization.",
          "corroboration_source": "GET /projects/87785099/repository/files/.gitlab-ci.yml?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d & config/retirement_policy.b3_disposable.json",
          "corroboration_status": "CORROBORATED",
          "exact_target_relationship": "TARGET_BOUND",
          "origin": "GitLab Duo Custom Flow Session 9710085",
          "retirement_relevance": "PROCEDURAL",
          "source_project": 87785099,
          "text": "Authorization binding: The policy file allowlists 87785099 and the `unpublish_pages` action but sets `authorization_required: true`. A bound, valid, single-use authorization is still required. The comment \"safe to retire\" in the target's CI file is only a repository comment. It is not authorization."
        },
        {
          "causal_attribution": "GENUINE_DUO_TARGET_DISCOVERY: Duo observed 403 access boundary on target 87785099 Pages endpoint",
          "claim_id": "duo-9710085-cand-05",
          "corroboration_detail": "Verified access boundary: anonymous GET /projects/87785099/pages returned HTTP 403 (AUTH_DENIED); proves anonymous identity is denied access, does not authenticate operator role.",
          "corroboration_source": "GET /projects/87785099/pages (HTTP 403 AUTH_DENIED)",
          "corroboration_status": "CORROBORATED",
          "exact_target_relationship": "TARGET_BOUND",
          "origin": "GitLab Duo Custom Flow Session 9710085",
          "retirement_relevance": "MATERIAL",
          "source_project": 87785099,
          "text": "Permissions: The acting identity needs Maintainer/Owner Pages administration on the target. The recorded evidence shows only anonymous read, with a 403 on the Pages endpoint."
        },
        {
          "causal_attribution": "GENUINE_DUO_OBSERVATION: Duo noted open issues in canonical hosting repository",
          "claim_id": "duo-9710085-cand-06",
          "corroboration_detail": "Issues exist in canonical repository 87779099, but their causal relevance to target project 87785099 is unproven.",
          "corroboration_source": "GET /projects/87779099/issues",
          "corroboration_status": "CONTEXTUAL_ONLY",
          "exact_target_relationship": "NO_DIRECT_TARGET_LINK",
          "origin": "GitLab Duo Custom Flow Session 9710085",
          "retirement_relevance": "CONTEXTUAL",
          "source_project": 87779099,
          "text": "Open work in the hosting project: Issues 1, 2 and 3 in 87779099 were recorded as open dependencies. Their relevance to the target is unknown."
        },
        {
          "causal_attribution": "GENUINE_DUO_TARGET_DISCOVERY: Duo independently discovered marker string in target 87785099",
          "claim_id": "duo-9710085-cand-07",
          "corroboration_detail": "Marker string TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a independently verified in target files site/marker.txt and site/index.html.",
          "corroboration_source": "GET /projects/87785099/repository/files/site%2Fmarker.txt?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
          "corroboration_status": "CORROBORATED",
          "exact_target_relationship": "TARGET_BOUND",
          "origin": "GitLab Duo Custom Flow Session 9710085",
          "retirement_relevance": "MATERIAL",
          "source_project": 87785099,
          "text": "Marker for later checks: The marker `TERMIVANCE-B3-DISPOSABLE-PAGES-MARKER-7f3c9a` could be used by a later deterministic check, if that check is permitted."
        }
      ],
      "counterfactual": {
        "corroboration_work_changed": true,
        "deterministic_verdict_changed": false,
        "investigation_queue_changed": true,
        "obligation_trace_changed": false,
        "risk_explanation_changed": false,
        "summary": "AI candidates queued: 7 claims; corroboration performed: 4 corroborated, 2 unresolved. Obligation trace changed: False (deterministic engine evaluates REDEPLOYMENT_PATH directly from target provider facts, not from AI text). Risk explanation changed: False (risk map nodes derived from deterministic decision). Deterministic verdict is BLOCKED in both cases because AI text cannot authorize mutation or award verdicts, and unpublish prerequisites remain unsatisfied.",
        "verdict_with_candidate": "BLOCKED",
        "verdict_without_candidate": "BLOCKED"
      },
      "duo_session": {
        "catalog_item_id": 1018562,
        "session_id": "9710085"
      },
      "execution_id": "inv-20261019204744-ae07c3",
      "investigation_mode": "EXECUTED_NOW",
      "observed_at": "2026-10-19T20:47:44.867015+00:00",
      "schema": "termivance.supervised_review/v1",
      "steps": [
        {
          "autonomy": "DUO_AUTONOMOUS",
          "detail": "session 9710085, catalog item 1018562; author ai-termivance-retirement-analyst-gitlab-ai-hackathon; Duo analyzed target 87785099 from issue #5 note 4045401991",
          "executed_at": "2026-10-19T19:46:42.793Z",
          "execution_id": "inv-20261019204744-ae07c3",
          "execution_mode": "RECORDED_HISTORICAL",
          "input_refs": [
            "issue:87779099:5"
          ],
          "output_ref": "agent_session:9710085",
          "provenance": "OPERATOR_CONFIRMED_NOTE_INPUT",
          "status": "COMPLETED",
          "step_id": "duo_candidate_analysis",
          "title": "GitLab Duo Custom Flow candidate analysis (Issue #5)"
        },
        {
          "autonomy": "OPERATOR_CONFIRMED_HANDOFF",
          "detail": "ingested 7 non-authoritative candidate claims from Duo session 9710085 (provenance: OPERATOR_CONFIRMED_NOTE_INPUT); passed to deterministic verification",
          "executed_at": "2026-10-19T20:47:44.867015+00:00",
          "execution_id": "inv-20261019204744-ae07c3",
          "execution_mode": "EXECUTED_NOW",
          "input_refs": [
            "gitlab_issue_note:4045401991"
          ],
          "output_ref": null,
          "provenance": "OPERATOR_CONFIRMED_NOTE_INPUT",
          "status": "COMPLETED",
          "step_id": "operator_handoff",
          "title": "Supervised pipeline ingests Duo candidate claims"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "EXECUTED NOW: reconciled 7 candidate claims against provider facts; 4 corroborated, 2 unresolved (unobservable schedules/caches), 1 contextual",
          "executed_at": "2026-10-19T20:47:44.867015+00:00",
          "execution_id": "inv-20261019204744-ae07c3",
          "execution_mode": "EXECUTED_NOW",
          "input_refs": [
            "issue:87779099:5"
          ],
          "output_ref": "evidence\\b4\\duo_reconciliation_issue_5.json",
          "provenance": "ANONYMOUS_PUBLIC_READ",
          "status": "COMPLETED",
          "step_id": "independent_reconciliation",
          "title": "Anonymous read-only reconciliation of Duo candidate claims"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "EXECUTED NOW: observed commit 54fcc9ff2b…; resurrection_possible=MECHANISM_PRESENT_IN_OBSERVED_CONFIG",
          "executed_at": "2026-10-19T20:47:44.867015+00:00",
          "execution_id": "inv-20261019204744-ae07c3",
          "execution_mode": "EXECUTED_NOW",
          "input_refs": [
            "project:87785099"
          ],
          "output_ref": "evidence\\b4\\witness_87785099.json",
          "provenance": "ANONYMOUS_PUBLIC_READ",
          "status": "COMPLETED",
          "step_id": "source_corroboration",
          "title": "Resurrection witness: target's own CI config at observed commit"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "EXECUTED NOW: verdict=BLOCKED; obligation graph evaluated with zero non-authoritative modification",
          "executed_at": "2026-10-19T20:47:44.867015+00:00",
          "execution_id": "inv-20261019204744-ae07c3",
          "execution_mode": "EXECUTED_NOW",
          "input_refs": [
            "project:87785099"
          ],
          "output_ref": "evidence\\b4\\decision.json",
          "provenance": "DETERMINISTIC",
          "status": "COMPLETED",
          "step_id": "deterministic_decision",
          "title": "Deterministic retirement obligation graph evaluation"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "EXECUTED NOW: built risk map with 35 nodes and 14 edges",
          "executed_at": "2026-10-19T20:47:44.867015+00:00",
          "execution_id": "inv-20261019204744-ae07c3",
          "execution_mode": "EXECUTED_NOW",
          "input_refs": [
            "evidence\\b4\\decision.json"
          ],
          "output_ref": "evidence\\b4\\risk_map.json",
          "provenance": "DETERMINISTIC",
          "status": "COMPLETED",
          "step_id": "risk_map",
          "title": "Deterministic risk map from decision obligations"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "EXECUTED NOW: capsule assembled; manifest sha256 15ea45e1cde3defa…",
          "executed_at": "2026-10-19T20:47:44.867015+00:00",
          "execution_id": "inv-20261019204744-ae07c3",
          "execution_mode": "EXECUTED_NOW",
          "input_refs": [
            "evidence\\b4\\decision.json",
            "evidence\\b4\\witness_87785099.json",
            "evidence\\b4\\duo_reconciliation_issue_5.json"
          ],
          "output_ref": "evidence\\b4\\proof_capsule.json",
          "provenance": "DETERMINISTIC",
          "status": "COMPLETED",
          "step_id": "proof_capsule",
          "title": "Tamper-evident proof capsule assembly"
        }
      ],
      "target": {
        "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
        "project_id": 87785099
      },
      "target_validation": {
        "checks_passed": true,
        "mismatches": [],
        "target_project_id": 87785099
      }
    },
    "tripwire": {
      "state": "UNAVAILABLE"
    },
    "witness": {
      "absence_claim": "NEVER_FROM_THIS_WITNESS",
      "authority": "NON_AUTHORITATIVE",
      "boundary": "this witness lists resurrection counterexamples; it never claims absence and never awards RESURRECTION_CONTROLLED — that verdict additionally requires live monitoring/control evidence this read-only sweep cannot provide",
      "commit_sha": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
      "config": {
        "configuration_complete": true,
        "digest_sha256": "fe895004ba37081c95f893bc9025a5fb24b3fc3cb51da5655d566f69a0b20620",
        "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw?ref=54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
        "error_kind": null,
        "ref": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d",
        "signals": [
          "pages_true",
          "pages_keyword"
        ],
        "status": 200
      },
      "counterexamples": [
        "the target's own default-branch CI configuration at the observed commit 54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d carries Pages redeployment signal(s) ['pages_true', 'pages_keyword']; any pipeline executing that configuration can republish the site",
        "a pages-administration action through the provider API or UI could republish the site at any time, independent of repository content",
        "the Pages administration surface of this exact target is not verifiable by this observing identity right now; a site may exist and it must not be assumed away",
        "cached or edge-replicated copies of previously served content can remain reachable after the provider state changes"
      ],
      "default_branch": "main",
      "fresh_until": "2026-10-19T21:02:44.867015+00:00",
      "observed_at": "2026-10-19T20:47:44.867015+00:00",
      "pages_administration": {
        "endpoint": "/projects/87785099/pages",
        "error_kind": "AUTH_DENIED",
        "phrase": "the observing identity cannot verify this Pages administration surface (HTTP 403); a site may be present or absent right now and neither state is claimed from this observation",
        "status": 403
      },
      "provenance": "ANONYMOUS_PUBLIC_READ",
      "resurrection_controlled": "NOT_CLAIMED",
      "resurrection_possible": "MECHANISM_PRESENT_IN_OBSERVED_CONFIG",
      "schema": "termivance.resurrection_witness/v1",
      "target": {
        "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
        "project_id": 87785099,
        "resource_kind": "GITLAB_PAGES_SITE"
      }
    },
    "workflow": {
      "state": "UNAVAILABLE"
    }
  },
  "verify": {
    "command": "python -m termivance.cli capsule-verify evidence/b4/proof_capsule.json",
    "note": "local integrity check only — it never re-observes GitLab"
  }
};
