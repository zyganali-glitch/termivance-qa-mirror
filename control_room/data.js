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
  "built_at": "2026-10-19T13:00:23.194637+00:00",
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
          "decision": "6379a5dd5992a341347f197e57ebcaa57ebfbfacd4896d6938d544ec5d87b26e",
          "duo_reconciliation": "481118324a1a80b0c2c74cd9dcf798fcf6d92e69a12ddeb09fb01b8c9c084b77",
          "identity": "7b04231f420af1f176664f2674da54d6ce77187d2ad823d5fdc8b534732866bd",
          "limitation_notice": "aec3c0abde7da82f52808b624d8edcc562004a2cfcc1981b40cabf89463018cc",
          "mutation": "8233bc272138a9c113143e1842426f82c3412faede769c095d7ee9bb74ad004e",
          "source_evidence": "58227fbfa8e806878a27d5fca70d4a1e96b2ca8b98c1d80739dffa7bb35dcbc0",
          "witness": "a754e56d6c1012552b095a3b8a4838714a3d1d75747045ece79d4700708c8b56"
        }
      },
      "manifest_digest": "eeb7a5c9b2b0f9030af42a3cf342a1cbf51081d1818f97581f467f30d95b5e93",
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
          "evaluated_at": "2026-10-19T11:31:49.660547+00:00",
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
                "digest": "2d1a4da8f838bf34063af2ba9873d03d7e822a598a2f9718536792b668413a4d",
                "endpoint": "/projects/87785099/repository/branches/main",
                "error_kind": null,
                "evidence_id": "ev:branch",
                "fresh_until": "2026-10-19T11:46:49.660547+00:00",
                "kind": "BRANCH",
                "method": "GET",
                "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                "digest": "ec4b9bfc4f53c8a9c03bec0f29d2009007d247a5b087520870ecd1e35979d1a1",
                "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
                "error_kind": null,
                "evidence_id": "ev:ci_config",
                "fresh_until": "2026-10-19T11:46:49.660547+00:00",
                "kind": "CI_CONFIG",
                "method": "GET",
                "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                "digest": "fde2561e2a6a3b5d81f40f98bd60ea62f0ded97c525ac3d22a8551a99341a5ca",
                "endpoint": "/projects/87785099",
                "error_kind": null,
                "evidence_id": "ev:effective_permission",
                "fresh_until": "2026-10-19T11:46:49.660547+00:00",
                "kind": "EFFECTIVE_PERMISSION",
                "method": "GET",
                "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                "digest": "fa6671e54026523149f34dee20cd8ecf649f73f4778ad226a0e388fe1413e3f6",
                "endpoint": "/projects/87785099/environments",
                "error_kind": "AUTH_DENIED",
                "evidence_id": "ev:environment",
                "fresh_until": "2026-10-19T11:46:49.660547+00:00",
                "kind": "ENVIRONMENT",
                "method": "GET",
                "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                "digest": "dc00d4c79a990f6978bb16cea104d9c4cfc4ac532dbd81c16f34371243b08ccd",
                "endpoint": "/projects/87785099/issues",
                "error_kind": null,
                "evidence_id": "ev:open_issues",
                "fresh_until": "2026-10-19T11:46:49.660547+00:00",
                "kind": "OPEN_ISSUES",
                "method": "GET",
                "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                "digest": "cee8711db1d2ed6aa8ea9c2b34c447798250dfe548a7aced30ec2192fa4f2d0b",
                "endpoint": "/projects/87785099/pages",
                "error_kind": "AUTH_DENIED",
                "evidence_id": "ev:pages",
                "fresh_until": "2026-10-19T11:46:49.660547+00:00",
                "kind": "PAGES",
                "method": "GET",
                "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                "digest": "79b82c3251e98db8962ebdf7cd387975b0cf44b577692ae239605c56fcd2b408",
                "endpoint": "/projects/87785099/pages",
                "error_kind": "AUTH_DENIED",
                "evidence_id": "ev:pages_deployment",
                "fresh_until": "2026-10-19T11:46:49.660547+00:00",
                "kind": "PAGES_DEPLOYMENT",
                "method": "GET",
                "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                "digest": "0a88559cf5cfc76ef095be86f68c37c4961bfd0607e18619f63570e74d61c3b4",
                "endpoint": "/projects/87785099/pipelines",
                "error_kind": null,
                "evidence_id": "ev:pipeline",
                "fresh_until": "2026-10-19T11:46:49.660547+00:00",
                "kind": "PIPELINE",
                "method": "GET",
                "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                "digest": "76ac708a6c9508c964c0e6540a936555271adc6babeeea8f23b4dad230bb8155",
                "endpoint": "/projects/87785099",
                "error_kind": null,
                "evidence_id": "ev:project_identity",
                "fresh_until": "2026-10-19T11:46:49.660547+00:00",
                "kind": "PROJECT_IDENTITY",
                "method": "GET",
                "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "authority": "NON_AUTHORITATIVE",
            "boundary": "Duo output is candidate claims only; every status here is derived from anonymous read-only observations; no verdict may originate from this record and no claim is ever promoted beyond what a GET actually showed",
            "claims": [
              {
                "check_kind": "PROJECT_READ",
                "claim_id": "duo-9671626-01",
                "detail": "the project is publicly readable to this anonymous identity (HTTP 200)",
                "observed": {
                  "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                  "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
                  "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
                  "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                  "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
                  "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
                  "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
                  "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
                  "observed_at": "2026-10-19T11:31:49.660547+00:00",
                  "surface": "session_ui"
                },
                "origin": "ANONYMOUS_API_OBSERVATION",
                "source_ladder": "not_independently_observable_and_never_promoted[1]",
                "status": "SUPPORTED",
                "text": "flow-execution internals behind the agent-sessions UI (HTTP 404 to anonymous clients)"
              }
            ],
            "claims_source": "evidence/b4/duo_session_9671626_readback.json",
            "duo_session_id": "9671626",
            "flow_catalog_item_id": 1018562,
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
          "state": "RECONCILED"
        },
        "identity": {
          "generated_at": "2026-10-19T11:31:49.660547+00:00",
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
            "assembled by scripts/refresh_b4_evidence.py from anonymous live reads",
            "no mutation was attempted; no absence is claimed and no control is asserted anywhere in this capsule"
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
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
      "evaluated_at": "2026-10-19T11:31:49.660547+00:00",
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
            "digest": "2d1a4da8f838bf34063af2ba9873d03d7e822a598a2f9718536792b668413a4d",
            "endpoint": "/projects/87785099/repository/branches/main",
            "error_kind": null,
            "evidence_id": "ev:branch",
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "kind": "BRANCH",
            "method": "GET",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "digest": "ec4b9bfc4f53c8a9c03bec0f29d2009007d247a5b087520870ecd1e35979d1a1",
            "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
            "error_kind": null,
            "evidence_id": "ev:ci_config",
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "kind": "CI_CONFIG",
            "method": "GET",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "digest": "fde2561e2a6a3b5d81f40f98bd60ea62f0ded97c525ac3d22a8551a99341a5ca",
            "endpoint": "/projects/87785099",
            "error_kind": null,
            "evidence_id": "ev:effective_permission",
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "kind": "EFFECTIVE_PERMISSION",
            "method": "GET",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "digest": "fa6671e54026523149f34dee20cd8ecf649f73f4778ad226a0e388fe1413e3f6",
            "endpoint": "/projects/87785099/environments",
            "error_kind": "AUTH_DENIED",
            "evidence_id": "ev:environment",
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "kind": "ENVIRONMENT",
            "method": "GET",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "digest": "dc00d4c79a990f6978bb16cea104d9c4cfc4ac532dbd81c16f34371243b08ccd",
            "endpoint": "/projects/87785099/issues",
            "error_kind": null,
            "evidence_id": "ev:open_issues",
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "kind": "OPEN_ISSUES",
            "method": "GET",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "digest": "cee8711db1d2ed6aa8ea9c2b34c447798250dfe548a7aced30ec2192fa4f2d0b",
            "endpoint": "/projects/87785099/pages",
            "error_kind": "AUTH_DENIED",
            "evidence_id": "ev:pages",
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "kind": "PAGES",
            "method": "GET",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "digest": "79b82c3251e98db8962ebdf7cd387975b0cf44b577692ae239605c56fcd2b408",
            "endpoint": "/projects/87785099/pages",
            "error_kind": "AUTH_DENIED",
            "evidence_id": "ev:pages_deployment",
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "kind": "PAGES_DEPLOYMENT",
            "method": "GET",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "digest": "0a88559cf5cfc76ef095be86f68c37c4961bfd0607e18619f63570e74d61c3b4",
            "endpoint": "/projects/87785099/pipelines",
            "error_kind": null,
            "evidence_id": "ev:pipeline",
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "kind": "PIPELINE",
            "method": "GET",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "digest": "76ac708a6c9508c964c0e6540a936555271adc6babeeea8f23b4dad230bb8155",
            "endpoint": "/projects/87785099",
            "error_kind": null,
            "evidence_id": "ev:project_identity",
            "fresh_until": "2026-10-19T11:46:49.660547+00:00",
            "kind": "PROJECT_IDENTITY",
            "method": "GET",
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
            "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
            "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
            "observed_at": "2026-10-19T11:31:49.660547+00:00"
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
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
            "observed_at": "2026-10-19T11:31:49.660547+00:00",
            "surface": "session_ui"
          },
          "origin": "ANONYMOUS_API_OBSERVATION",
          "source_ladder": "not_independently_observable_and_never_promoted[1]",
          "status": "SUPPORTED",
          "text": "flow-execution internals behind the agent-sessions UI (HTTP 404 to anonymous clients)"
        }
      ],
      "claims_source": "evidence/b4/duo_session_9671626_readback.json",
      "duo_session_id": "9671626",
      "flow_catalog_item_id": 1018562,
      "fresh_until": "2026-10-19T11:46:49.660547+00:00",
      "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
        "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "CI_REDEPLOYMENT_MECHANISM",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "ENVIRONMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "DEPLOYMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "CI_REDEPLOYMENT_MECHANISM",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "ENVIRONMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "DEPLOYMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
              "operation_supported": "READ_ONLY_OBSERVATION",
              "provenance": "ANONYMOUS_PUBLIC_READ",
              "ref": "deployment:87779099:not_observed",
              "state": "NOT_OBSERVED (AUTH_DENIED)",
              "support": "NOT_OBSERVED"
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "CI_REDEPLOYMENT_MECHANISM",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "ENVIRONMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "DEPLOYMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
      "observed_at": "2026-10-19T11:31:49.660547+00:00",
      "provenance": "ANONYMOUS_PUBLIC_READ",
      "relations": [
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
        "inferred_relations": 4,
        "observed_relations": 0,
        "pages_not_observed": 0,
        "pages_sites": 0,
        "pages_unverifiable": 3,
        "protected": 2,
        "resource_kinds_observed": {
          "CI_REDEPLOYMENT_MECHANISM": 2,
          "OPEN_ISSUE": 4
        },
        "resources_not_observed": 11,
        "resources_observed": 6
      }
    },
    "receipt": {
      "evidence_level": "NOT_APPLICABLE",
      "evidence_level_detail": "no receipt to classify",
      "mutation_accepted": null,
      "mutation_attempted": null,
      "note": "no receipt artifact was supplied; the runtime records no mutation attempt and this page will not pretend otherwise",
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
          "state": "NO_PAGES_SIGNAL_IN_DEFAULT_BRANCH_CONFIG via GET /projects/87779099/repository/files/.gitlab-ci.yml/raw [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T11:46:49.660547+00:00]",
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
          "state": "PAGES_REDEPLOYMENT_SIGNAL_PRESENT via GET /projects/87785099/repository/files/.gitlab-ci.yml/raw [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T11:46:49.660547+00:00]",
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
          "state": "opened via GET /projects/87777871/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T11:46:49.660547+00:00]",
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
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T11:46:49.660547+00:00]",
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
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T11:46:49.660547+00:00]",
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
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T11:46:49.660547+00:00]",
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
          "fresh_until": "2026-10-19T11:46:49.660547+00:00",
          "kind": "CI_REDEPLOYMENT_MECHANISM",
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
          "observed_state": "NO_PAGES_SIGNAL_IN_DEFAULT_BRANCH_CONFIG",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; CI_REDEPLOYMENT_MECHANISM observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "ci_redeployment:87779099",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T11:46:49.660547+00:00",
          "kind": "CI_REDEPLOYMENT_MECHANISM",
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
          "observed_state": "PAGES_REDEPLOYMENT_SIGNAL_PRESENT",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; CI_REDEPLOYMENT_MECHANISM observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "ci_redeployment:87785099",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T11:46:49.660547+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87777871:1",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T11:46:49.660547+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:1",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T11:46:49.660547+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:2",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T11:46:49.660547+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T11:31:49.660547+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:3",
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
        "evaluated_at": "2026-10-19T11:31:49.660547+00:00",
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
              "digest": "2d1a4da8f838bf34063af2ba9873d03d7e822a598a2f9718536792b668413a4d",
              "endpoint": "/projects/87785099/repository/branches/main",
              "error_kind": null,
              "evidence_id": "ev:branch",
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "BRANCH",
              "method": "GET",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "digest": "ec4b9bfc4f53c8a9c03bec0f29d2009007d247a5b087520870ecd1e35979d1a1",
              "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
              "error_kind": null,
              "evidence_id": "ev:ci_config",
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "CI_CONFIG",
              "method": "GET",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "digest": "fde2561e2a6a3b5d81f40f98bd60ea62f0ded97c525ac3d22a8551a99341a5ca",
              "endpoint": "/projects/87785099",
              "error_kind": null,
              "evidence_id": "ev:effective_permission",
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "EFFECTIVE_PERMISSION",
              "method": "GET",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "digest": "fa6671e54026523149f34dee20cd8ecf649f73f4778ad226a0e388fe1413e3f6",
              "endpoint": "/projects/87785099/environments",
              "error_kind": "AUTH_DENIED",
              "evidence_id": "ev:environment",
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "ENVIRONMENT",
              "method": "GET",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "digest": "dc00d4c79a990f6978bb16cea104d9c4cfc4ac532dbd81c16f34371243b08ccd",
              "endpoint": "/projects/87785099/issues",
              "error_kind": null,
              "evidence_id": "ev:open_issues",
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "OPEN_ISSUES",
              "method": "GET",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "digest": "cee8711db1d2ed6aa8ea9c2b34c447798250dfe548a7aced30ec2192fa4f2d0b",
              "endpoint": "/projects/87785099/pages",
              "error_kind": "AUTH_DENIED",
              "evidence_id": "ev:pages",
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "PAGES",
              "method": "GET",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "digest": "79b82c3251e98db8962ebdf7cd387975b0cf44b577692ae239605c56fcd2b408",
              "endpoint": "/projects/87785099/pages",
              "error_kind": "AUTH_DENIED",
              "evidence_id": "ev:pages_deployment",
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "PAGES_DEPLOYMENT",
              "method": "GET",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "digest": "0a88559cf5cfc76ef095be86f68c37c4961bfd0607e18619f63570e74d61c3b4",
              "endpoint": "/projects/87785099/pipelines",
              "error_kind": null,
              "evidence_id": "ev:pipeline",
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "PIPELINE",
              "method": "GET",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
              "digest": "76ac708a6c9508c964c0e6540a936555271adc6babeeea8f23b4dad230bb8155",
              "endpoint": "/projects/87785099",
              "error_kind": null,
              "evidence_id": "ev:project_identity",
              "fresh_until": "2026-10-19T11:46:49.660547+00:00",
              "kind": "PROJECT_IDENTITY",
              "method": "GET",
              "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
      "autonomy_summary": "1 genuine Duo autonomous step(s), 1 operator-confirmed handoff(s), 5 deterministic automated step(s); the chain is NOT fully autonomous because the Duo output requires operator confirmation before entering the deterministic pipeline",
      "boundary": "this review connects the genuine Duo analysis to deterministic verification; the AI contribution adds investigation context and risk explanations but cannot award verdicts, modify provider facts, or authorize mutations",
      "candidate_claims": [
        {
          "claim_id": "duo-9671626-01",
          "corroboration_detail": "the project is publicly readable to this anonymous identity (HTTP 200)",
          "corroboration_source": "PROJECT_READ",
          "corroboration_status": "CORROBORATED",
          "origin": "ANONYMOUS_API_OBSERVATION",
          "retirement_relevance": "MATERIAL",
          "source_project": 87779099,
          "text": "project 87779099 is publicly readable (HTTP 200)"
        },
        {
          "claim_id": "duo-9671626-02",
          "corroboration_detail": "the anonymous issue read confirms every stated field exactly",
          "corroboration_source": "ISSUE_METADATA",
          "corroboration_status": "CORROBORATED",
          "origin": "ANONYMOUS_API_OBSERVATION",
          "retirement_relevance": "MATERIAL",
          "source_project": null,
          "text": "issue #3 exists, state opened, title/labels/author match the recorded B3 retirement status thread"
        },
        {
          "claim_id": "duo-9671626-03",
          "corroboration_detail": "the observable core matches, but 'consistent with' is not proof: the inference is never promoted to SUPPORTED",
          "corroboration_source": "CONSISTENCY_INFERENCE",
          "corroboration_status": "UNRESOLVED",
          "origin": "ANONYMOUS_API_OBSERVATION",
          "retirement_relevance": "MATERIAL",
          "source_project": null,
          "text": "issue user_notes_count=3 and updated_at=2026-10-19T08:57:41.500Z are consistent with, but not proof of, the operator-reported new comment window"
        },
        {
          "claim_id": "duo-9671626-04",
          "corroboration_detail": "the agent-sessions UI is an authenticated surface; the anonymous probe returned 404 — an access observation that can neither confirm nor deny the session's recorded state, and is never promoted",
          "corroboration_source": "SESSION_UI_PROBE",
          "corroboration_status": "UNRESOLVED",
          "origin": "OPERATOR_CONFIRMED_UI",
          "retirement_relevance": "PROCEDURAL",
          "source_project": null,
          "text": "session id 9671626 exists and Finished in the authenticated automate/agent-sessions UI"
        },
        {
          "claim_id": "duo-9671626-05",
          "corroboration_detail": "note/discussion reads returned 401 to this anonymous identity; an access observation is not absence and is certainly not attribution — the claim cannot be attributed",
          "corroboration_source": "ISSUE_NOTE_READ",
          "corroboration_status": "NOT_CHECKED",
          "origin": "OPERATOR_CONFIRMED_NOTE_CONTENT",
          "retirement_relevance": "CONTEXTUAL",
          "source_project": 87779099,
          "text": "the agent-authored comment note id 4040776241 was published on issue #3 by the GitLab Duo service account"
        },
        {
          "claim_id": "duo-9671626-06",
          "corroboration_detail": "note/discussion reads returned 401 to this anonymous identity; an access observation is not absence and is certainly not attribution — the claim cannot be attributed",
          "corroboration_source": "ISSUE_NOTE_READ",
          "corroboration_status": "NOT_CHECKED",
          "origin": "OPERATOR_CONFIRMED_NOTE_CONTENT",
          "retirement_relevance": "CONTEXTUAL",
          "source_project": 87779099,
          "text": "the six-section analysis content itself and its read-only, non-authoritative character"
        },
        {
          "claim_id": "duo-9671626-07",
          "corroboration_detail": "flow-execution internals have no independently observable surface; the claim can never be promoted by this tool",
          "corroboration_source": "FLOW_INTERNALS",
          "corroboration_status": "NOT_CHECKED",
          "origin": "OPERATOR_CONFIRMED_UI",
          "retirement_relevance": "CONTEXTUAL",
          "source_project": null,
          "text": "the agent used genuine GitLab tools and stated it did NOT directly query disposable project 87785099"
        },
        {
          "claim_id": "duo-9671626-08",
          "corroboration_detail": "the anonymous probe reproduces the recorded access observation (HTTP 401)",
          "corroboration_source": "OBSERVABILITY_PROBE",
          "corroboration_status": "CORROBORATED",
          "origin": "ANONYMOUS_API_OBSERVATION",
          "retirement_relevance": "PROCEDURAL",
          "source_project": null,
          "text": "note/discussion contents (HTTP 401 to anonymous readers; 401 is an access observation, never absence, never authenticity)"
        },
        {
          "claim_id": "duo-9671626-09",
          "corroboration_detail": "the anonymous probe reproduces the recorded access observation (HTTP 404)",
          "corroboration_source": "OBSERVABILITY_PROBE",
          "corroboration_status": "CORROBORATED",
          "origin": "ANONYMOUS_API_OBSERVATION",
          "retirement_relevance": "PROCEDURAL",
          "source_project": null,
          "text": "flow-execution internals behind the agent-sessions UI (HTTP 404 to anonymous clients)"
        }
      ],
      "counterfactual": {
        "corroboration_work_changed": true,
        "deterministic_verdict_changed": false,
        "investigation_queue_changed": true,
        "obligation_trace_changed": true,
        "risk_explanation_changed": true,
        "summary": "the Duo candidate adds 3 material claim(s) (2 independently corroborated) that enrich the investigation queue, risk explanation and corroboration work; the deterministic verdict remains BLOCKED in both cases because AI input cannot modify authoritative provider facts or obligation graph evaluation",
        "verdict_with_candidate": "BLOCKED",
        "verdict_without_candidate": "BLOCKED"
      },
      "duo_session": {
        "catalog_item_id": 1018562,
        "session_id": "9671626"
      },
      "observed_at": "2026-10-19T12:55:01.532547+00:00",
      "schema": "termivance.supervised_review/v1",
      "steps": [
        {
          "autonomy": "DUO_AUTONOMOUS",
          "detail": "session 9671626, catalog item 1018562; the flow read project/issue metadata using genuine GitLab tools and produced a non-authoritative six-section analysis",
          "input_refs": [
            "issue:87779099:3"
          ],
          "output_ref": "evidence/b4/duo_claims.json",
          "provenance": "OPERATOR_CONFIRMED",
          "status": "COMPLETED",
          "step_id": "duo_candidate_analysis",
          "title": "GitLab Duo Custom Flow candidate analysis"
        },
        {
          "autonomy": "OPERATOR_CONFIRMED_HANDOFF",
          "detail": "the operator visually confirmed the Duo session output in the authenticated browser UI and transcribed the claims into the structured duo_claims/v1 record; this is a manual handoff, not an autonomous agent-to-agent transfer",
          "input_refs": [
            "duo_session:9671626"
          ],
          "output_ref": "evidence/b4/duo_claims.json",
          "provenance": "OPERATOR_CONFIRMED",
          "status": "COMPLETED",
          "step_id": "operator_handoff",
          "title": "Operator confirms Duo output and hands to deterministic pipeline"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "reconciled 9 claims against anonymous read-only GitLab observations; 4 SUPPORTED, findings: NOT_AUTHENTICALLY_ATTRIBUTABLE=2, SUPPORTED=4, UNRESOLVED=2, UNSUPPORTED=1",
          "input_refs": [
            "evidence/b4/duo_claims.json"
          ],
          "output_ref": "evidence/b4/duo_reconciliation.json",
          "provenance": "ANONYMOUS_PUBLIC_READ",
          "status": "COMPLETED",
          "step_id": "independent_reconciliation",
          "title": "Anonymous read-only reconciliation of Duo claims"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "read .gitlab-ci.yml at the exact observed commit; resurrection_possible=MECHANISM_PRESENT_IN_OBSERVED_CONFIG",
          "input_refs": [
            "project:87785099"
          ],
          "output_ref": "evidence/b4/witness_87785099.json",
          "provenance": "ANONYMOUS_PUBLIC_READ",
          "status": "COMPLETED",
          "step_id": "source_corroboration",
          "title": "Resurrection witness: target's own CI config at observed commit"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "verdict=BLOCKED; the engine evaluates the full obligation graph against the recorded snapshot — no AI input can modify this verdict",
          "input_refs": [
            "evidence/b4/decision.json"
          ],
          "output_ref": "evidence/b4/decision.json",
          "provenance": "DETERMINISTIC",
          "status": "COMPLETED",
          "step_id": "deterministic_decision",
          "title": "Deterministic retirement obligation graph evaluation"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "risk map generated from obligation graph; visualization-ready",
          "input_refs": [
            "evidence/b4/decision.json"
          ],
          "output_ref": "evidence/b4/risk_map.json",
          "provenance": "DETERMINISTIC",
          "status": "COMPLETED",
          "step_id": "risk_map",
          "title": "Deterministic risk map from decision obligations"
        },
        {
          "autonomy": "DETERMINISTIC_AUTOMATED",
          "detail": "capsule assembled; manifest sha256 eeb7a5c9b2b0f903…",
          "input_refs": [
            "evidence/b4/decision.json",
            "evidence/b4/witness_87785099.json",
            "evidence/b4/duo_reconciliation.json"
          ],
          "output_ref": "evidence/b4/proof_capsule.json",
          "provenance": "DETERMINISTIC",
          "status": "COMPLETED",
          "step_id": "proof_capsule",
          "title": "Tamper-evident proof capsule assembly"
        }
      ],
      "target": {
        "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
        "project_id": 87785099
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
      "fresh_until": "2026-10-19T11:46:49.660547+00:00",
      "observed_at": "2026-10-19T11:31:49.660547+00:00",
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
      "mode": "ARTIFACT_ASSESSMENT",
      "observed_at": "2026-10-19T13:00:17.794369+00:00",
      "schema": "termivance.workflow/v1",
      "stages": [
        {
          "detail": "snapshot classification=LIVE",
          "stage": "snapshot",
          "state": "COMPLETE"
        },
        {
          "detail": "decision verdict=BLOCKED",
          "stage": "decision",
          "state": "COMPLETE"
        },
        {
          "detail": "no artifact supplied for stage 'authorization'",
          "stage": "authorization",
          "state": "NOT_RUN"
        },
        {
          "detail": "no artifact supplied for stage 'approval_issue'",
          "stage": "approval_issue",
          "state": "NOT_RUN"
        },
        {
          "detail": "no artifact supplied for stage 'execute'",
          "stage": "execute",
          "state": "NOT_RUN"
        },
        {
          "detail": "no artifact supplied for stage 'absence'",
          "stage": "absence",
          "state": "NOT_RUN"
        },
        {
          "detail": "manifest digest sha256 eeb7a5c9b2b0f903…",
          "stage": "capsule",
          "state": "COMPLETE"
        }
      ],
      "summary": {
        "absence": "NOT_RUN",
        "approval_issue": "NOT_RUN",
        "authorization": "NOT_RUN",
        "capsule": "COMPLETE",
        "decision": "COMPLETE",
        "execute": "NOT_RUN",
        "snapshot": "COMPLETE"
      },
      "target": {
        "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
        "project_id": 87785099
      }
    }
  },
  "verify": {
    "command": "python -m termivance.cli capsule-verify evidence/b4/proof_capsule.json",
    "note": "local integrity check only — it never re-observes GitLab"
  }
};
