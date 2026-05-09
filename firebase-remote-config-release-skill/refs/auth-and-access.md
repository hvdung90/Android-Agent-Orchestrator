# Auth and Access

Run this access preflight at intake. Do not request secrets unless the current task needs them.

## Access Matrix

| Capability | Needed for | Evidence |
|---|---|---|
| Jira read | Ticket requirements, acceptance criteria | Ticket readable or user-provided export |
| Confluence/docs read | Product/design docs | Page/doc readable or local copy |
| App repo read | Find RC parameter keys and code behavior | Repo path/PR readable |
| Graphify read | Architecture/feature impact context | `graphify-out/` or report readable |
| Manifest repo read | Review manifest, stable branch, PR | Repo/branch/manifest readable |
| Manifest repo write | Create branch, push manifest, open/update PR | GitHub token or Git remote push works |
| Jenkins read | Inspect job params/logs | Jenkins URL/log provided or token available |
| Jenkins build | Trigger EXPORT/PUBLISH/ROLLBACK/SYNC_STG | Jenkins token/job permission + explicit approval |
| Firebase RC read | Export STG/PROD, list versions | GCP service account/ADC read scopes |
| Firebase RC write | Publish, rollback, sync | GCP service account write scopes + approval |

## Recommended Local Auth File

If the project has no standard auth file, ask the user to create `.rc-agent-auth.yaml` locally and never commit it:

```yaml
workspace:
  name: mobile-rc

jira:
  base_url: "https://example.atlassian.net"
  email: ""
  api_token: ""

confluence:
  base_url: "https://example.atlassian.net/wiki"
  email: ""
  api_token: ""

github:
  manifest_repo: "vulcanlabsvn/Vulcan-Firebase-RC"
  token_env: "GITHUB_TOKEN"

jenkins:
  base_url: "https://jenkins.example.com"
  token_env: "JENKINS_TOKEN"
  job_name: ""

firebase:
  credentials_env: "GOOGLE_APPLICATION_CREDENTIALS"
  projects:
    Android_ChatSmith:
      environment_model: stg_prod
      staging_project_id: "chatsmith-staging-android"
      production_project_id: "chat-gpt-android"
      stable_branch: "feature/android-chatsmith"
```

## Missing Access Behavior

- Missing docs/ticket access: ask user to paste/export requirements; continue only with assumptions clearly marked.
- Missing app repo/Graphify: continue with RC artifacts only; mark parameter discovery confidence.
- Missing manifest repo read: cannot review PR/branch; ask for manifest YAML or PR diff.
- Missing manifest repo write: can prepare manifest and PR text; cannot push/open PR.
- Missing Jenkins read: ask for log text or screenshot.
- Missing Jenkins build: can provide command plan only.
- Missing Firebase read: cannot produce current-state diff; require provided backup JSON/export.
- Missing Firebase write: can review/validate plan only; cannot apply/rollback/sync.

## Secret Handling

- Never print token values.
- Prefer env var names over raw secrets.
- Do not commit `.rc-agent-auth.yaml`, service account JSON, backup secrets, or Firebase credentials.
- For production mutation, re-confirm target project id even if credentials are present.
