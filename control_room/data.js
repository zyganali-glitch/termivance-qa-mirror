window.TERMIVANCE_DATA = {
  "boundaries": [
    "A successful mutation is not proof of retirement; absence is only claimed by the receipt-bound bounded-absence rules.",
    "NOT_RUN / BLOCKED / NOT_OBSERVED are first-class states and are never promoted to success.",
    "Unpublishing targets exactly one disposable Pages project; the canonical repository and every other project are out of scope."
  ],
  "built_at": "2026-10-19T07:28:25.726937+00:00",
  "generated_by": "scripts/build_control_room.py (deterministic, from recorded files)",
  "mutation_status": "NOT_RUN",
  "provenance_label": "RECORDED_LIVE",
  "read_provenance": "ANONYMOUS_PUBLIC_READ",
  "schema": "termivance.control_room/v1",
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
    "portfolio": {
      "assets": [
        {
          "archived": null,
          "description": "Proof-Bounded Software Retirement Protocol (GitLab Transcend 2026, Path A / Start Fresh).",
          "error_kind": "AUTH_DENIED",
          "full_path": "gitlab-ai-hackathon/transcend-october-2026/39306908/termivance",
          "name": "Termivance",
          "observed_at": "2026-10-19T07:15:08.771520+00:00",
          "ok": true,
          "pages_state": "PAGES_UNVERIFIABLE_403",
          "project_id": 87779099,
          "provenance": "ANONYMOUS_PUBLIC_READ",
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
          "observed_at": "2026-10-19T07:15:08.771520+00:00",
          "ok": true,
          "pages_state": "PAGES_UNVERIFIABLE_403",
          "project_id": 87785099,
          "provenance": "ANONYMOUS_PUBLIC_READ",
          "role": "APPROVED_RETIREMENT_TARGET",
          "visibility": "public",
          "web_url": "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/39306908/termivance-b3-disposable-pages-demo"
        }
      ],
      "observed_at": "2026-10-19T07:15:08.771520+00:00",
      "provenance": "ANONYMOUS_PUBLIC_READ",
      "schema": "termivance.portfolio/v1",
      "totals": {
        "approved_targets": 1,
        "assets": 2,
        "pages_sites": 0,
        "pages_unverifiable": 2,
        "protected": 1
      }
    },
    "receipt": {
      "state": "NOT_OBSERVED"
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
          "src": "risk:missing_evidence"
        },
        {
          "dst": "obl:provider_observation",
          "relation": "impacts",
          "src": "risk:missing_evidence"
        },
        {
          "dst": "obl:redeployment_path",
          "relation": "impacts",
          "src": "risk:redeployment_risk"
        },
        {
          "dst": "obl:retirement_permission",
          "relation": "impacts",
          "src": "risk:missing_evidence"
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
          "dst": "obl:provider_observation",
          "relation": "impacts",
          "src": "obligation-unknown:obl:provider_observation"
        },
        {
          "dst": "obl:redeployment_path",
          "relation": "impacts",
          "src": "obligation-violation:obl:redeployment_path"
        },
        {
          "dst": "obl:retirement_permission",
          "relation": "impacts",
          "src": "obligation-unknown:obl:retirement_permission"
        }
      ],
      "nodes": [
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
            "obl:provider_observation"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "obligation-unknown:obl:provider_observation",
          "severity": "MEDIUM",
          "state": "status=UNKNOWN",
          "title": "obligation PROVIDER_OBSERVATION is unverifiable"
        },
        {
          "impacts": [
            "obl:retirement_permission"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "obligation-unknown:obl:retirement_permission",
          "severity": "MEDIUM",
          "state": "status=UNKNOWN",
          "title": "obligation RETIREMENT_PERMISSION is unverifiable"
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
            "obl:pages_published"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "risk:missing_evidence",
          "severity": "MEDIUM",
          "state": "publication evidence is RECORDED_LIVE, not live",
          "title": "required evidence is missing"
        },
        {
          "impacts": [
            "obl:provider_observation"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "risk:missing_evidence",
          "severity": "MEDIUM",
          "state": "provider evidence is RECORDED_LIVE, not a live observation; fixtures and records cannot satisfy a live requirement",
          "title": "required evidence is missing"
        },
        {
          "impacts": [
            "obl:retirement_permission"
          ],
          "kind": "RISK",
          "mitigations": [],
          "node_id": "risk:missing_evidence",
          "severity": "MEDIUM",
          "state": "permission evidence is RECORDED_LIVE, not a live observation",
          "title": "required evidence is missing"
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
      "banner": "HYPOTHETICAL SIMULATION \u2014 no request was sent, nothing was mutated, no verdict was earned",
      "decision": {
        "action": "unpublish_pages",
        "authoritative": false,
        "evaluated_at": "2026-10-19T07:19:18.483295+00:00",
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
          "current_status": "UNKNOWN",
          "flips_eligible": false,
          "obligation_id": "obl:provider_observation",
          "obligation_kind": "PROVIDER_OBSERVATION",
          "projected_status": "UNKNOWN"
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
          "current_status": "UNKNOWN",
          "flips_eligible": false,
          "obligation_id": "obl:retirement_permission",
          "obligation_kind": "RETIREMENT_PERMISSION",
          "projected_status": "UNKNOWN"
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
          "effect": "GET /projects/87785099/pages would be expected to no longer report a deployment \u2014 this must be re-observed independently, never assumed",
          "state": "PROJECTED_NOT_OBSERVED"
        },
        {
          "effect": "the previously served URL may return 404 \u2014 or keep serving stale content: CDN convergence has unknown delay and errors are never promoted to verified absence",
          "state": "PROJECTED_NOT_OBSERVED"
        }
      ],
      "redeployment_risk": "HIGH: the recorded CI/Pages mechanism can redeploy the site after retirement; resurrection is a live risk unless that path is demonstrably inert \u2014 and that is a risk, never a verdict.",
      "schema": "termivance.retirement_simulation/v1",
      "target_project_id": 87785099
    },
    "tripwire": {
      "state": "NOT_OBSERVED"
    },
    "workflow": {
      "mode": "ARTIFACT_ASSESSMENT",
      "observed_at": "2026-10-19T07:20:23.469524+00:00",
      "schema": "termivance.workflow/v1",
      "stages": [
        {
          "detail": "snapshot classification=RECORDED_LIVE",
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
    "note": "local integrity check only \u2014 it never re-observes GitLab"
  }
};
