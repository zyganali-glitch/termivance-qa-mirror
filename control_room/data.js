window.TERMIVANCE_DATA = {
  "authorization_gates": [
    {
      "detail": "anonymous public reads are permitted; authenticated reads require operator-supplied credentials (none stored on the executor machine)",
      "gate": "READ-ONLY GITLAB API (GET)",
      "state": "AVAILABLE"
    },
    {
      "detail": "bound to immutable numeric project id, exact endpoint, one-time operator-signed approval + trust policy, durable single-use ledger, fresh SAFE_TO_RETIRE decision and operator-provided credential; GitHub-namespace approvals and API-key possession never equal consent",
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
  "built_at": "2026-10-19T10:22:15.767576+00:00",
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
          "decision": "9c4dd6e3734ffb4535a1cc72615f679ae2d0818a875207dbffe565f379314287",
          "identity": "929fd180c11518cb31f7b659860484ea212840f7daaacc404b2dea3b2be0aacc",
          "limitation_notice": "6e074fa32063f535a22ad5b51f849ed8240366988d4e2f191d3f450eb1141127",
          "mutation": "8233bc272138a9c113143e1842426f82c3412faede769c095d7ee9bb74ad004e",
          "source_evidence": "58227fbfa8e806878a27d5fca70d4a1e96b2ca8b98c1d80739dffa7bb35dcbc0"
        }
      },
      "manifest_digest": "744f5aa8bf9bbd453a1991ec67fe97b7c5c452770a16f9468e7c682e540701fd",
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
          "evaluated_at": "2026-10-19T07:19:09.149461+00:00",
          "evidence_classification": "RECORDED_LIVE",
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
                "classification": "RECORDED_LIVE",
                "detail": {
                  "branch": "main",
                  "commit_id": "54fcc9ff2bfde1038a8192216178a5a8b6a6ee1d"
                },
                "digest": "153f22a1a6d1d8a032b7a08198b4edd12385b7f12715c071f24887c968b6b4c8",
                "endpoint": "/projects/87785099/repository/branches/main",
                "error_kind": null,
                "evidence_id": "ev:branch",
                "fresh_until": "2026-10-19T07:33:29.746582+00:00",
                "kind": "BRANCH",
                "method": "GET",
                "observed_at": "2026-10-19T07:18:29.746582+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "RECORDED_LIVE",
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
                "digest": "a49c1c07a23cbe49e0bd749ea8181c8164ed590d9aab320db8cec641e1b2b832",
                "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
                "error_kind": null,
                "evidence_id": "ev:ci_config",
                "fresh_until": "2026-10-19T07:33:29.746582+00:00",
                "kind": "CI_CONFIG",
                "method": "GET",
                "observed_at": "2026-10-19T07:18:29.746582+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "RECORDED_LIVE",
                "detail": {
                  "can_manage_pages": false,
                  "effective_access_level": null,
                  "pages_api_error": "AUTH_DENIED",
                  "pages_api_status": 403
                },
                "digest": "5f1faa356664016fb9806d7e8bc769d31002faa69252850a646170daab1c686f",
                "endpoint": "/projects/87785099",
                "error_kind": null,
                "evidence_id": "ev:effective_permission",
                "fresh_until": "2026-10-19T07:33:29.746582+00:00",
                "kind": "EFFECTIVE_PERMISSION",
                "method": "GET",
                "observed_at": "2026-10-19T07:18:29.746582+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "RECORDED_LIVE",
                "detail": {
                  "error": "AUTH_DENIED"
                },
                "digest": "5e0c3127b4a66181fea370971794bafbae16e3fdcc3e34cdde2afde9761d5051",
                "endpoint": "/projects/87785099/environments",
                "error_kind": "AUTH_DENIED",
                "evidence_id": "ev:environment",
                "fresh_until": "2026-10-19T07:33:29.746582+00:00",
                "kind": "ENVIRONMENT",
                "method": "GET",
                "observed_at": "2026-10-19T07:18:29.746582+00:00",
                "status": 401,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "RECORDED_LIVE",
                "detail": {
                  "open_count": 0,
                  "retirement_related": []
                },
                "digest": "93231a31ad8136757802c65fe4e0d5f3f1f4db68faac0e5c65159941c3bf3ddc",
                "endpoint": "/projects/87785099/issues",
                "error_kind": null,
                "evidence_id": "ev:open_issues",
                "fresh_until": "2026-10-19T07:33:29.746582+00:00",
                "kind": "OPEN_ISSUES",
                "method": "GET",
                "observed_at": "2026-10-19T07:18:29.746582+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "RECORDED_LIVE",
                "detail": {
                  "error": "AUTH_DENIED"
                },
                "digest": "106d8f43929d388bfe3258b85058a603bf042dd3b4c857de314da372ebf7b9a3",
                "endpoint": "/projects/87785099/pages",
                "error_kind": "AUTH_DENIED",
                "evidence_id": "ev:pages",
                "fresh_until": "2026-10-19T07:33:29.746582+00:00",
                "kind": "PAGES",
                "method": "GET",
                "observed_at": "2026-10-19T07:18:29.746582+00:00",
                "status": 403,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "RECORDED_LIVE",
                "detail": {
                  "error": "AUTH_DENIED"
                },
                "digest": "0565fb60a295618c228551650bf7893b4ffe58c14e0229f4f88b2fe0183b64f5",
                "endpoint": "/projects/87785099/pages",
                "error_kind": "AUTH_DENIED",
                "evidence_id": "ev:pages_deployment",
                "fresh_until": "2026-10-19T07:33:29.746582+00:00",
                "kind": "PAGES_DEPLOYMENT",
                "method": "GET",
                "observed_at": "2026-10-19T07:18:29.746582+00:00",
                "status": 403,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "RECORDED_LIVE",
                "detail": {
                  "latest_id": 2960507698,
                  "latest_status": "success"
                },
                "digest": "bd71c3e6b6e710385140d8a35d839119d0cf3519a1c94896dacc09d2aac30648",
                "endpoint": "/projects/87785099/pipelines",
                "error_kind": null,
                "evidence_id": "ev:pipeline",
                "fresh_until": "2026-10-19T07:33:29.746582+00:00",
                "kind": "PIPELINE",
                "method": "GET",
                "observed_at": "2026-10-19T07:18:29.746582+00:00",
                "status": 200,
                "target": {
                  "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "resource_kind": "GITLAB_PAGES_SITE"
                }
              },
              {
                "classification": "RECORDED_LIVE",
                "detail": {
                  "archived": null,
                  "default_branch": "main",
                  "namespace_full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908",
                  "path_with_namespace": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo",
                  "project_id": 87785099,
                  "visibility": "public",
                  "web_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
                },
                "digest": "904acd6227d5e94d13d63c8cd542b9b74f5be46bfd59be00579b1fad6bd58069",
                "endpoint": "/projects/87785099",
                "error_kind": null,
                "evidence_id": "ev:project_identity",
                "fresh_until": "2026-10-19T07:33:29.746582+00:00",
                "kind": "PROJECT_IDENTITY",
                "method": "GET",
                "observed_at": "2026-10-19T07:18:29.746582+00:00",
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
            "resolve MISSING_EVIDENCE: publication evidence is RECORDED_LIVE, not live",
            "resolve MISSING_EVIDENCE: provider evidence is RECORDED_LIVE, not a live observation; fixtures and records cannot satisfy a live requirement",
            "resolve REDEPLOYMENT_RISK: 1 observed redeployment/recreation mechanism(s)",
            "resolve MISSING_EVIDENCE: permission evidence is RECORDED_LIVE, not a live observation"
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
              "status": "UNKNOWN"
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
              "status": "UNKNOWN"
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
              "code": "MISSING_EVIDENCE",
              "detail": "publication evidence is RECORDED_LIVE, not live",
              "evidence_id": "ev:pages_deployment",
              "obligation_id": "obl:pages_published"
            },
            {
              "code": "MISSING_EVIDENCE",
              "detail": "provider evidence is RECORDED_LIVE, not a live observation; fixtures and records cannot satisfy a live requirement",
              "evidence_id": "ev:project_identity",
              "obligation_id": "obl:provider_observation"
            },
            {
              "code": "REDEPLOYMENT_RISK",
              "detail": "1 observed redeployment/recreation mechanism(s)",
              "evidence_id": "ev:ci_config",
              "obligation_id": "obl:redeployment_path"
            },
            {
              "code": "MISSING_EVIDENCE",
              "detail": "permission evidence is RECORDED_LIVE, not a live observation",
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
        "identity": {
          "generated_at": "2026-10-19T07:26:33.002545+00:00",
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
            "no-mutation-yet capsule: assembled from a recorded deterministic decision only; no Pages unpublication is claimed",
            "mutation and absence sections are NOT_OBSERVED by design until a real authorized receipt exists"
          ]
        },
        "mutation": {
          "attempted": false,
          "state": "NOT_RUN"
        },
        "source_evidence": {
          "state": "NOT_OBSERVED"
        }
      }
    },
    "decision": {
      "action": "unpublish_pages",
      "authoritative": false,
      "evaluated_at": "2026-10-19T10:21:07.237741+00:00",
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
            "digest": "9dbdcb62cb7cc9fb029c7c9185bbbd6f98e669aa801a5791b9c46b94a2164f56",
            "endpoint": "/projects/87785099/repository/branches/main",
            "error_kind": null,
            "evidence_id": "ev:branch",
            "fresh_until": "2026-10-19T10:36:07.237741+00:00",
            "kind": "BRANCH",
            "method": "GET",
            "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
            "digest": "f585a6bf4dbbc3cacb3c947a49e3cb09d377a5aaf1749854ae5e98773e1259e6",
            "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
            "error_kind": null,
            "evidence_id": "ev:ci_config",
            "fresh_until": "2026-10-19T10:36:07.237741+00:00",
            "kind": "CI_CONFIG",
            "method": "GET",
            "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
            "digest": "8c4e103a9b145fd9bbf86ddedaed2791f75c9e5a9d29812c5584eb82dab916c8",
            "endpoint": "/projects/87785099",
            "error_kind": null,
            "evidence_id": "ev:effective_permission",
            "fresh_until": "2026-10-19T10:36:07.237741+00:00",
            "kind": "EFFECTIVE_PERMISSION",
            "method": "GET",
            "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
            "digest": "18ad0a17b79ccddbc8df38be6fcd0dc4f0a20ca90d23af93b0dbdc13e0f1d871",
            "endpoint": "/projects/87785099/environments",
            "error_kind": "AUTH_DENIED",
            "evidence_id": "ev:environment",
            "fresh_until": "2026-10-19T10:36:07.237741+00:00",
            "kind": "ENVIRONMENT",
            "method": "GET",
            "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
            "digest": "527320c7df7ffd2983b098d5a4159a1e53ceb185b82daa973a608b7a1acee68b",
            "endpoint": "/projects/87785099/issues",
            "error_kind": null,
            "evidence_id": "ev:open_issues",
            "fresh_until": "2026-10-19T10:36:07.237741+00:00",
            "kind": "OPEN_ISSUES",
            "method": "GET",
            "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
            "digest": "8e9473f89c959cb459ab9adaa4c25e104839c89935321bb4cbf25c5971b5abed",
            "endpoint": "/projects/87785099/pages",
            "error_kind": "AUTH_DENIED",
            "evidence_id": "ev:pages",
            "fresh_until": "2026-10-19T10:36:07.237741+00:00",
            "kind": "PAGES",
            "method": "GET",
            "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
            "digest": "caae5af39bae3b170c1ac430808fbe095ce178e42261306e82a8d95ca19def3c",
            "endpoint": "/projects/87785099/pages",
            "error_kind": "AUTH_DENIED",
            "evidence_id": "ev:pages_deployment",
            "fresh_until": "2026-10-19T10:36:07.237741+00:00",
            "kind": "PAGES_DEPLOYMENT",
            "method": "GET",
            "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
            "digest": "97ea1e227aab9b7bfea8380fad49fd06e6e6e89a9e25eca8e81accd7c41a27e0",
            "endpoint": "/projects/87785099/pipelines",
            "error_kind": null,
            "evidence_id": "ev:pipeline",
            "fresh_until": "2026-10-19T10:36:07.237741+00:00",
            "kind": "PIPELINE",
            "method": "GET",
            "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
            "digest": "52d0bf8651ff4a6ab2c4c4650fdca8b129ae795469c0cd46167fd7d7e771644b",
            "endpoint": "/projects/87785099",
            "error_kind": null,
            "evidence_id": "ev:project_identity",
            "fresh_until": "2026-10-19T10:36:07.237741+00:00",
            "kind": "PROJECT_IDENTITY",
            "method": "GET",
            "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
    "portfolio": {
      "assets": [
        {
          "archived": null,
          "description": "Transcend Hackathon Showcase workspace for @zyganali (DevPost: zyganali). Visit the [onboarding issue](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/showcase/-/work_items/1) to get started.",
          "error_kind": "AUTH_DENIED",
          "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/showcase",
          "name": "Showcase",
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "CI_REDEPLOYMENT_MECHANISM",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "ENVIRONMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "DEPLOYMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "CI_REDEPLOYMENT_MECHANISM",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "ENVIRONMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "DEPLOYMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "OPEN_ISSUE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "CI_REDEPLOYMENT_MECHANISM",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "ENVIRONMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "DEPLOYMENT",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "PAGES_SITE",
              "mutation_capability": "NOT_AUTHORIZING",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
      "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
      "state": "NOT_RUN"
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
          "state": "NO_PAGES_SIGNAL_IN_DEFAULT_BRANCH_CONFIG via GET /projects/87779099/repository/files/.gitlab-ci.yml/raw [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T10:36:07.237741+00:00]",
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
          "state": "PAGES_REDEPLOYMENT_SIGNAL_PRESENT via GET /projects/87785099/repository/files/.gitlab-ci.yml/raw [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T10:36:07.237741+00:00]",
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
          "state": "opened via GET /projects/87777871/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T10:36:07.237741+00:00]",
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
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T10:36:07.237741+00:00]",
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
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T10:36:07.237741+00:00]",
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
          "state": "opened via GET /projects/87779099/issues?state=opened [ANONYMOUS_PUBLIC_READ, fresh until 2026-10-19T10:36:07.237741+00:00]",
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
          "fresh_until": "2026-10-19T10:36:07.237741+00:00",
          "kind": "CI_REDEPLOYMENT_MECHANISM",
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
          "observed_state": "NO_PAGES_SIGNAL_IN_DEFAULT_BRANCH_CONFIG",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; CI_REDEPLOYMENT_MECHANISM observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "ci_redeployment:87779099",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T10:36:07.237741+00:00",
          "kind": "CI_REDEPLOYMENT_MECHANISM",
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
          "observed_state": "PAGES_REDEPLOYMENT_SIGNAL_PRESENT",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; CI_REDEPLOYMENT_MECHANISM observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "ci_redeployment:87785099",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T10:36:07.237741+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87777871:1",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T10:36:07.237741+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:1",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T10:36:07.237741+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
          "observed_state": "opened",
          "projection": "an authorized DELETE of the Pages publication acts on the Pages resource only; OPEN_ISSUE observed here is NOT acted on by that endpoint — any post-retirement change would have to be re-observed independently",
          "resource": "issue:87779099:2",
          "state": "PROJECTED_NOT_OBSERVED",
          "support": "OBSERVED"
        },
        {
          "fresh_until": "2026-10-19T10:36:07.237741+00:00",
          "kind": "OPEN_ISSUE",
          "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
        "evaluated_at": "2026-10-19T10:21:07.237741+00:00",
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
              "digest": "9dbdcb62cb7cc9fb029c7c9185bbbd6f98e669aa801a5791b9c46b94a2164f56",
              "endpoint": "/projects/87785099/repository/branches/main",
              "error_kind": null,
              "evidence_id": "ev:branch",
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "BRANCH",
              "method": "GET",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "digest": "f585a6bf4dbbc3cacb3c947a49e3cb09d377a5aaf1749854ae5e98773e1259e6",
              "endpoint": "/projects/87785099/repository/files/.gitlab-ci.yml/raw",
              "error_kind": null,
              "evidence_id": "ev:ci_config",
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "CI_CONFIG",
              "method": "GET",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "digest": "8c4e103a9b145fd9bbf86ddedaed2791f75c9e5a9d29812c5584eb82dab916c8",
              "endpoint": "/projects/87785099",
              "error_kind": null,
              "evidence_id": "ev:effective_permission",
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "EFFECTIVE_PERMISSION",
              "method": "GET",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "digest": "18ad0a17b79ccddbc8df38be6fcd0dc4f0a20ca90d23af93b0dbdc13e0f1d871",
              "endpoint": "/projects/87785099/environments",
              "error_kind": "AUTH_DENIED",
              "evidence_id": "ev:environment",
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "ENVIRONMENT",
              "method": "GET",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "digest": "527320c7df7ffd2983b098d5a4159a1e53ceb185b82daa973a608b7a1acee68b",
              "endpoint": "/projects/87785099/issues",
              "error_kind": null,
              "evidence_id": "ev:open_issues",
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "OPEN_ISSUES",
              "method": "GET",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "digest": "8e9473f89c959cb459ab9adaa4c25e104839c89935321bb4cbf25c5971b5abed",
              "endpoint": "/projects/87785099/pages",
              "error_kind": "AUTH_DENIED",
              "evidence_id": "ev:pages",
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "PAGES",
              "method": "GET",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "digest": "caae5af39bae3b170c1ac430808fbe095ce178e42261306e82a8d95ca19def3c",
              "endpoint": "/projects/87785099/pages",
              "error_kind": "AUTH_DENIED",
              "evidence_id": "ev:pages_deployment",
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "PAGES_DEPLOYMENT",
              "method": "GET",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "digest": "97ea1e227aab9b7bfea8380fad49fd06e6e6e89a9e25eca8e81accd7c41a27e0",
              "endpoint": "/projects/87785099/pipelines",
              "error_kind": null,
              "evidence_id": "ev:pipeline",
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "PIPELINE",
              "method": "GET",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
              "digest": "52d0bf8651ff4a6ab2c4c4650fdca8b129ae795469c0cd46167fd7d7e771644b",
              "endpoint": "/projects/87785099",
              "error_kind": null,
              "evidence_id": "ev:project_identity",
              "fresh_until": "2026-10-19T10:36:07.237741+00:00",
              "kind": "PROJECT_IDENTITY",
              "method": "GET",
              "observed_at": "2026-10-19T10:21:07.237741+00:00",
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
    "tripwire": {
      "state": "UNAVAILABLE"
    },
    "workflow": {
      "mode": "ARTIFACT_ASSESSMENT",
      "observed_at": "2026-10-19T10:21:19.527116+00:00",
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
          "detail": "no artifact supplied for stage 'capsule'",
          "stage": "capsule",
          "state": "NOT_RUN"
        }
      ],
      "summary": {
        "absence": "NOT_RUN",
        "approval_issue": "NOT_RUN",
        "authorization": "NOT_RUN",
        "capsule": "NOT_RUN",
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
