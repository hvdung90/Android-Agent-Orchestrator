# Auth Bootstrap & Token Management

_Skill version: 6.1.3 — update this when SKILL.md bumps a minor or major version._

## Principles

`.agent-auth.yaml` is the **single source of truth** for all tokens/secrets.
When the skill starts → read this file.
When a tool is needed → check that tool's token at that moment.
If it is missing → show instructions for the user to add it **directly to `.agent-auth.yaml`** (never accept a token pasted into the chat), re-read the file once they confirm, and continue.

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
If it is missing → show instructions for the user to fill it **directly in `.agent-auth.yaml`** (never ask them to paste a secret into chat) → wait for confirmation → re-read the file → retry. Do not skip, and do not fabricate.

**Why not "paste here":** a token typed or pasted into the chat appears in the conversation transcript, is sent to the model provider, and may be captured in session summaries or logs. Writing it directly to `.agent-auth.yaml` keeps it out of the transcript entirely.

### Jira Reader

Required: `atlassian.domain`, `atlassian.email`, `atlassian.api_token`

```
Check each field:
  atlassian.domain → empty? → ask:
    "Your Atlassian domain (e.g. mycompany.atlassian.net).
     Open .agent-auth.yaml and fill in `atlassian.domain`, then reply 'done'."

  atlassian.email → empty? → ask:
    "Your Atlassian login email.
     Open .agent-auth.yaml and fill in `atlassian.email`, then reply 'done'."

  atlassian.api_token → empty? → show (do NOT ask them to paste the value here):
    "An Atlassian API token is required to read Jira.
     1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
     2. Click 'Create API token', copy the value.
     3. Open .agent-auth.yaml and paste it into `atlassian.api_token`.
     4. Save the file, then reply 'done' (do not paste the token here)."

User replies 'done' → re-read .agent-auth.yaml → verify field is now non-empty → run Jira Reader
```

### Confluence Reader

Same token as Jira (`atlassian.*`). If Jira has already authenticated → Confluence reuses it and does not ask again.

### Figma Reader — MCP-first, PAT fallback

If Figma MCP tools are available in the agent's own tool list (checked at Stage 1 activation time, per `refs/clarification-workflow.md` § Figma) → **no token needed here**. Auth is handled by the MCP server via the developer's logged-in Figma desktop app. Skip this section.

Only if Figma MCP tools are **not** available → fall back to REST API + PAT:

```
figma.personal_access_token → empty? → show (do NOT ask them to paste the value here):
  "A Figma Personal Access Token is required (no Figma MCP detected).
   1. Go to Figma → Account Settings → Security → Personal access tokens.
   2. Generate a new token with File content (read-only) permission, copy it.
   3. Open .agent-auth.yaml and paste it into `figma.personal_access_token`.
   4. Save the file, then reply 'done' (do not paste the token here)."

User replies 'done' → re-read .agent-auth.yaml → verify field non-empty → run Figma Reader (access_mode: rest_api)
```

### GitHub (optional)

Required: `github.personal_access_token`

```
github.personal_access_token → empty? → show (do NOT ask them to paste the value here):
  "A GitHub token is required to read private repos.
   1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained.
   2. Create a token with Contents (read-only) + Metadata (read-only), copy it.
   3. Open .agent-auth.yaml and paste it into `github.personal_access_token`.
   4. Save the file, then reply 'done' (do not paste the token here)."

User replies 'done' → re-read .agent-auth.yaml → verify field non-empty → run reader
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

## Step 4 — Confirm tokens saved to the file

The agent **never** writes a token value that the user typed or pasted into chat. Instead:

- When the user replies 'done': re-read `.agent-auth.yaml` and verify the relevant field is now non-empty.
- Do not echo or log the token value to the screen, reports, or `session.json`.
- Confirm to the user: "Token found in .agent-auth.yaml. Ready to continue."
- If the field is still empty after 'done': repeat the instructions from Step 2 and ask the user to try again.
- If the user pastes a token value directly into the chat: **warn them** that it has appeared in the transcript and they should consider rotating it, then proceed to instruct them to write it to the file instead.

---

## MCP mapping

MCP tools used in Claude Code and their corresponding token source in `.agent-auth.yaml`:

| MCP Tool                        | Auth source in .agent-auth.yaml        |
|---------------------------------|----------------------------------------|
| `mcp__claude_ai_Atlassian__*`   | `atlassian.domain` + `atlassian.email` + `atlassian.api_token` |
| Figma Dev Mode MCP tools (`get_metadata`, `get_design_context`, `get_variable_defs`, `get_screenshot`, `get_code_connect_suggestions`, `search_design_system`, `download_assets`, `whoami`) | none — MCP server handles auth via Figma desktop app login |
| Figma REST API (fallback only, when MCP tools absent) | `figma.personal_access_token` |
| `mcp__plugin_*_github__*`       | `github.personal_access_token`         |

When an MCP tool requires authentication, use the corresponding token from `.agent-auth.yaml`.
Do not use interactive OAuth if the token already exists in the file.

---

## Safety rules

- **Never accept a token pasted or typed into the chat.** Always instruct the user to write it directly to `.agent-auth.yaml`. If they paste one anyway, warn them and suggest rotating it.
- Never print, echo, or log token values to the screen, reports, `session.json`, or any other output.
- Do not commit `.agent-auth.yaml` (it is already in `.gitignore`).
- Do not store tokens in any file other than `.agent-auth.yaml`.
- Do not create tokens yourself. Only guide the user to generate and store them.
- If the user refuses to provide a token → skip that tool, record it in the preflight report, and continue with available data.
