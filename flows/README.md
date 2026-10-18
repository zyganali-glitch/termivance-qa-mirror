# Termivance Duo Custom Flow assets

**Status: `NOT_RUN` / `NOT_DEPLOYED`.**

`termivance_retirement_analyst.yaml` is the source definition for the single
GitLab Duo Agent Platform **Custom Flow** used by Termivance. It is committed so
the design is reviewable, but **a YAML file in a repository is not an active
GitLab flow**.

To make it real (requires the **Maintainer or Owner** role, and GitLab Duo
Agent Platform turned on for the project):

1. In the project, go to **AI > Flows**.
2. Select **New flow**; set **Display name** = `Termivance Retirement Analyst`.
3. Under **Configuration**, choose **Flow** and paste this YAML.
4. Select **Create flow**.
5. Select **Enable**, choose the project, and add a **Mention** trigger.
6. Trigger it by mentioning the flow service account (`ai-<flow>-<group>`) on the
   dedicated B1 retirement-analysis issue.
7. Independently read back the resulting issue comment via the API.

Until those steps run against a live GitLab instance, the flow, its enablement,
and any session remain `NOT_RUN` in `docs/EVIDENCE_MATRIX.md`.
