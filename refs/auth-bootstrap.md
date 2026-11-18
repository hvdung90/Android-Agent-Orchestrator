# Auth Bootstrap & Token Management

_Skill version: 6.1.3 — update this when SKILL.md bumps a minor or major version._

## Principles

`.agent-auth.yaml` is the **single source of truth** for all tokens/secrets. It lives on the developer's machine, is gitignored, and is created with owner-only permissions (0600).

**The agent never sees a token value.** Anything that enters the agent's context — chat messages, file reads, command lines, command output — ends up in the transcript, is sent to the model provider, and may be kept in session summaries or logs. So:

- the user writes tokens **into the file themselves** — never into the chat;
- the agent **never opens `.agent-auth.yaml`** with Read, `cat`, `grep`, `sed`, an editor, or any other tool. The only thing that opens it is `templates/agent_auth.py`;
- the agent **never types a token into a command**. Calls that need one go through `agent_auth.py exec`, which passes credentials as environment variables and redacts them from the output.

| Need | Command | Shows |
|---|---|---|
| Create the file | `python3 templates/agent_auth.py init` | created / exists (never overwrites) |
| Is a token there? | `python3 templates/agent_auth.py status [--project KEY] [--json]` | `set` / `empty` / `missing_key` per field, file permissions — never values |
| Fix permissions | `python3 templates/agent_auth.py status --fix-permissions` | chmod 600 on the file only |
| Call an API with a token | `python3 templates/agent_auth.py exec <atlassian\|figma\|github> [--project KEY] -- <command…>` | command output with every credential value replaced by `[REDACTED:<service>.<field>]` |

`exec` sets: `AAO_ATLASSIAN_DOMAIN`, `AAO_ATLASSIAN_EMAIL`, `AAO_ATLASSIAN_API_TOKEN`, `AAO_FIGMA_TOKEN`, `AAO_GITHUB_TOKEN`. If a required field is empty it refuses to run the command (exit 3) and says which field the user must fill.

---

## Step 1 — Initialize the auth file (runs at Stage -1)

```
python3 templates/agent_auth.py init
        │
   ┌────┴─────────────┐
 exists             created
   │                  │
   │                  ▼
   │       Notify the user:
   │         "Created .agent-auth.yaml (owner-only). Tokens are requested
   │          only when a tool needs them."
   └────┬─────────────┘
        ▼
python3 templates/agent_auth.py status --json
        │
        ▼
Write to preflight.md § Auth (states only, never values):
  - .agent-auth.yaml: present | created-empty | missing | unreadable
  - permissions: ok | too_open   (too_open → tell the user; offer `status --fix-permissions`)
  - per-token state: set | empty | missing_key
```

`tooling-preflight.sh` reports the same states (it uses the same parser).

---

## Step 2 — Check tokens when using a tool (Just-in-time)

Before running any source reader, run `python3 templates/agent_auth.py status --json` (add `--project KEY` when Step 3 applies) and look at the fields that reader needs.
If one is not `set` → show the instructions below → wait for the user to reply 'done' → run `status` again → retry. Do not skip, and do not fabricate.

**Why not "paste here":** a token typed or pasted into the chat appears in the conversation transcript, is sent to the model provider, and may be captured in session summaries or logs. Writing it directly to `.agent-auth.yaml` keeps it out of the transcript entirely — as long as the agent then never reads the file (see Principles).

### Jira / Confluence

**Prefer the Atlassian connector** if its tools are available (e.g. `mcp__claude_ai_Atlassian__*`): it authenticates with its own OAuth session, needs nothing from `.agent-auth.yaml`, and the agent must not try to pass file values to it. Use the file only for the REST fallback below.

Required for REST: `atlassian.domain`, `atlassian.email`, `atlassian.api_token`

```
status shows a field not `set` → show:
  "Jira access needs <field> in .agent-auth.yaml.
   (api_token: create one at https://id.atlassian.com/manage-profile/security/api-tokens)
   Open .agent-auth.yaml yourself, fill in `atlassian.<field>`, save,
   then reply 'done'. Do not paste the value here."

User replies 'done' → status again → all `set` → call via exec:

  python3 templates/agent_auth.py exec atlassian -- sh -c \
    'curl -sf -u "$AAO_ATLASSIAN_EMAIL:$AAO_ATLASSIAN_API_TOKEN" \
       "https://$AAO_ATLASSIAN_DOMAIN/rest/api/3/issue/CA-42"'
```

Confluence uses the same `atlassian.*` fields. Once Jira works, Confluence does not ask again.

### Figma Reader — MCP-first, PAT fallback

If Figma MCP tools are available in the agent's own tool list (checked at Stage 1 activation time, per `refs/clarification-workflow.md` § Figma) → **no token needed here**. Auth is handled by the MCP server via the developer's logged-in Figma desktop app. Skip this section.

Only if Figma MCP tools are **not** available → REST API + PAT:

```
figma.personal_access_token not `set` → show:
  "A Figma Personal Access Token is required (no Figma MCP detected).
   1. Figma → Account Settings → Security → Personal access tokens.
   2. Generate a token with File content (read-only) permission.
   3. Open .agent-auth.yaml yourself and put it in `figma.personal_access_token`.
   4. Save, then reply 'done'. Do not paste the token here."

'done' → status again → `set` → call via exec:

  python3 templates/agent_auth.py exec figma -- sh -c \
    'curl -sf -H "X-Figma-Token: $AAO_FIGMA_TOKEN" "https://api.figma.com/v1/files/<key>"'
```

### GitHub (optional)

Prefer the user's existing `gh` login or a GitHub MCP server they configured themselves; neither needs `.agent-auth.yaml`. Use the file for private-repo reads only when neither is available.

```
github.personal_access_token not `set` → show:
  "A GitHub token is required to read private repos.
   1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained.
   2. Contents (read-only) + Metadata (read-only).
   3. Open .agent-auth.yaml yourself and put it in `github.personal_access_token`.
   4. Save, then reply 'done'. Do not paste the token here."

'done' → status again → `set` → call via exec:

  python3 templates/agent_auth.py exec github -- sh -c 'GH_TOKEN="$AAO_GITHUB_TOKEN" gh api repos/<owner>/<repo>'
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
python3 templates/agent_auth.py status --project CA --json
  → each field's `sources` says `project:CA` (Level 3 override) or `default` (Level 2)
        │
        ▼
Use the same --project on exec:
  python3 templates/agent_auth.py exec atlassian --project CA -- <command…>
```

Fields declared in the matching `projects[]` block override Level 2 one by one; undeclared fields fall back to Level 2. If a field is missing, tell the user which block to fill (Level 3 `projects[CA].atlassian.<field>` or Level 2 `atlassian.<field>`).

---

## Step 4 — Confirm tokens saved to the file

The agent **never** writes a token value into the file and never reads one out of it. Instead:

- When the user replies 'done': run `agent_auth.py status` and check that the field is now `set`.
- Confirm to the user: "Token found in .agent-auth.yaml. Ready to continue."
- If the field is still not `set`: repeat the instructions from Step 2.
- If the user pastes a token value directly into the chat: **warn them** that it is now in the transcript and they should rotate it, then ask them to put the new value in the file instead.

---

## Connectors and tools vs `.agent-auth.yaml`

| Tool | Credential source | Agent's role |
|---|---|---|
| Atlassian connector (`mcp__claude_ai_Atlassian__*`) | the connector's own OAuth session | none — never pass file values to it |
| Jira / Confluence REST (no connector) | `atlassian.*` | `agent_auth.py exec atlassian` |
| Figma Dev Mode MCP tools (`get_metadata`, `get_design_context`, `get_variable_defs`, `get_screenshot`, `get_code_connect_suggestions`, `search_design_system`, `download_assets`, `whoami`) | Figma desktop app login | none |
| Figma REST API (fallback only, when MCP tools absent) | `figma.personal_access_token` | `agent_auth.py exec figma` |
| GitHub MCP server (`mcp__plugin_*_github__*`) | that server's own config, set up by the user | none — do not read the file to configure it |
| `gh` / GitHub REST | user's `gh` login, else `github.personal_access_token` | `agent_auth.py exec github` |

---

## Safety rules

- **Never accept a token pasted or typed into the chat.** Always instruct the user to write it directly to `.agent-auth.yaml`. If they paste one anyway, warn them and suggest rotating it.
- **Never open `.agent-auth.yaml`** with Read, `cat`, `head`, `grep`, `sed`, an editor, or a script of your own. Use `agent_auth.py status` / `exec` only.
- **Never put a token value in a command line.** Reference `$AAO_*` variables inside `agent_auth.py exec … -- sh -c '…'` (single quotes, so your shell does not expand them).
- Never print, echo, or log token values to the screen, reports, `session.json`, or any other output. Do not add `set -x`, `curl -v`, or similar to `exec` commands; redaction is a safety net, not a licence.
- Do not commit `.agent-auth.yaml` (it is already in `.gitignore`). Keep it at 0600.
- Do not store tokens in any file other than `.agent-auth.yaml`.
- Do not create tokens yourself. Only guide the user to generate and store them.
- If the user refuses to provide a token → skip that tool, record it in the preflight report, and continue with available data.
