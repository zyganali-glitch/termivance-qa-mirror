import json, sys
sys.path.insert(0, "tests")
from datetime import UTC, datetime
from conftest import ScriptedTransport, live_responses
from termivance.attestation import ControlAttestation, target_key_for
from termivance.authorization import Authorization, OperatorApproval
from termivance.discovery import graph_from_snapshot
from termivance.engine import evaluate
from termivance.gitlab_client import GitLabClient, HttpReply
from termivance.policy import Policy
from termivance.retirement import establish_eligibility
from termivance.target import TargetIdentity

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
TARGET = TargetIdentity(12345678, "grp/disposable-pages", "GITLAB_PAGES_SITE")
URL = "https://disposable-pages.pages.example/"
ACTION = "unpublish_pages"
policy = Policy(1, "OPERATOR_APPROVED", True, "GITLAB_PAGES",
                (TARGET.project_id,), (TARGET.full_path,), (ACTION,), True)
a = Authorization.issue(TARGET, ACTION, nonce="n", now=NOW, ttl=__import__("datetime").timedelta(minutes=10))
a.approval = OperatorApproval("op", f"I authorize exactly one {ACTION} using {a.exact_endpoint}", NOW, "chan", a.binding())
read_client = GitLabClient("t", transport=ScriptedTransport(live_responses(TARGET, pages_url=URL),
      scripted={"/pages": [HttpReply(200, json.dumps({"url": URL, "deployments":[{"id":1}]}))]*4}))
ctl = ControlAttestation("op", "no redeployment path", NOW, target_key_for(TARGET))
el = establish_eligibility(TARGET, policy, a, read_client=read_client, served_url=URL, marker="MARKER",
                           control_attestation=ctl, now=NOW)
print("verdict", el.decision.verdict)
for o in el.decision.obligations:
    print(" ", o["kind"], o["status"], o["mandatory"])
for r in el.decision.reasons:
    print("reason:", r.code, "|", r.detail)
