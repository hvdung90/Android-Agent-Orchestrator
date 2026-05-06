# Auth Bootstrap & Token Management

_Skill version: 4.4.0 — update this when SKILL.md bumps a minor or major version._

## Principles

`.agent-auth.yaml` is the **single source of truth** for all tokens/secrets.
When the skill starts → read this file.
When a tool is needed → check that tool's token at that moment.
If it is missing → ask the user immediately, save it to the file, and continue.

---

## Step 1 — Initialize the auth file (runs at Stage -1)

```
check: .agent-auth.yaml exists?
        │
   ┌────┴────┐
  Yes       No
   │          │
   ▼          ▼
  Load      Create an empty file from the template:
  file        cp templates/agent-auth.example.yaml .agent-auth.yaml
              (all tokens left empty as "")
              → Notify the user:
                "Created .agent-auth.yaml.
                 Tokens will be requested when the corresponding tool needs them."
   │          │
   └────┬─────┘
        │
        ▼
  Write to preflight.md:
  - file_present: true
  - tokens_loaded: [list keys that already have values]
  - tokens_missing: [list keys that are still empty]
```

---

## Step 2 — Check tokens when using a tool (Just-in-time)

Before running any source reader, check the corresponding token.
If it is missing → ask the user → save it → retry. Do not skip, and do not fabricate.

### Jira Reader

Required: `atlassian.domain`, `atlassian.email`, `atlassian.api_token`

```
Check each field:
  atlassian.domain   → empty? → ask: "Your Atlassian domain? (e.g. mycompany.atlassian.net)"
  atlassian.email    → empty? → ask: "Atlassian login email?"
  atlassian.api_token→ empty? → ask:
    "An Atlassian API token is required to read Jira.
     Get one at: https://id.atlassian.com/manage-profile/security/api-tokens
     → Create API token → Copy → Paste it here:"

Receive token → save to .agent-auth.yaml → run Jira Reader
```

### Confluence Reader

Same token as Jira (`atlassian.*`). If Jira has already authenticated → Confluence reuses it and does not ask again.

### Figma Reader

Required: `figma.personal_access_token`

```
figma.personal_access_token → empty? → ask:
  "A Figma Personal Access Token is required to read designs.
   Get one at: Figma → Account Settings → Security → Personal access tokens → Generate new token
   Required permission: File content (read-only)
   Paste the token here:"

Receive token → save to .agent-auth.yaml → run Figma Reader
```

### GitHub (optional)

Required: `github.personal_access_token`

```
github.personal_access_token → empty? → ask:
  "A GitHub token is required to read private repos.
   Get one at: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained
   Required permissions: Contents (read-only), Metadata (read-only)
   Paste the token here:"

Receive token → save to .agent-auth.yaml → run reader
```

---

## Step 3 — Resolve credentials (when there are multiple projects)

```
Developer provides a link (e.g. "CA-42" or URL)
        │
        ▼
Extract project key prefix → "CA"
        │
        ▼
Find in .agent-auth.yaml → projects[].jira_project_key
        │
   ┌────┴────┐
  Match    No match
   │          │
   ▼          ▼
  Use       Use Level 2
  Level 3   (top-level atlassian / figma)
  override
        │
        ▼
Check the token for the override/top-level config (Step 2)
If missing → ask the user → save it to the correct block (Level 3 or Level 2)
```

---

## Step 4 — Save tokens to the file

When the user provides a token, the agent updates `.agent-auth.yaml`:

- Find the correct field in the file
- Write the value
- Do not delete other fields
- Do not log token values to the screen or to reports
- Confirm to the user: "Saved. The token will be used for this session and future sessions."

---

## MCP mapping

MCP tools used in Claude Code and their corresponding token source in `.agent-auth.yaml`:

| MCP Tool                        | Auth source in .agent-auth.yaml        |
|---------------------------------|----------------------------------------|
| `mcp__claude_ai_Atlassian__*`   | `atlassian.domain` + `atlassian.email` + `atlassian.api_token` |
| Figma REST API                  | `figma.personal_access_token`          |
| `mcp__plugin_*_github__*`       | `github.personal_access_token`         |

When an MCP tool requires authentication, use the corresponding token from `.agent-auth.yaml`.
Do not use interactive OAuth if the token already exists in the file.

---

## Safety rules

- Never print tokens to the screen or reports at any time.
- Do not commit `.agent-auth.yaml` (it is already in `.gitignore`).
- Do not store tokens in any file other than `.agent-auth.yaml`.
- Do not create tokens yourself. Only ask the user to provide them.
- If the user refuses to provide a token → skip that tool, record it in the report, and continue with available data.
