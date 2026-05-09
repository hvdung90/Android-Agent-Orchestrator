# Android Agent Orchestrator — Quick Start

Get from zero to running an Android task in 3 steps.

---

## Step 1 — Bootstrap tools (first time only)

```
Run templates/tooling-preflight.sh to audit what's installed.
Then tell the agent: "set up agents for this repo"
```

The agent runs Stage -1 in `bootstrap` mode:
- Creates `.agent-auth.yaml` (tokens requested on demand)
- Installs missing tools (AI DevKit, Android CLI, Graphify if approved)
- Writes `.project-orchestration/reports/preflight.md`

---

## Step 2 — Start a task

Tell the agent what you want to do:

```
"Implement feature X. Jira: https://<domain>.atlassian.net/browse/ANDROID-42"
"Fix bug: <repro steps>"
"Migrate LoginFragment from XML to Compose"
"Analyze the repo architecture"
```

Prompt templates are available in:

```text
templates/start-task-prompts.md
```

Optionally include links — the agent fetches them automatically:
- **Jira ticket** → reads acceptance criteria + auto-follows linked Confluence/Figma
- **Figma link** → reads screens, states, CTA labels
- **Confluence page** → reads business rules and flows

---

## Step 3 — Review and approve

The agent stops at **Stage 2** and shows you the requirements doc. After approval, Stage 2.5 decides whether an ADR-lite needs a second approval before design.

```
docs/ai/tasks/{task_id}/requirements/<task>.md   ← review this
docs/ai/tasks/{task_id}/decisions/ADR-*.md       ← review if Stage 2.5 requires ADR-lite
```

Reply `approve` to continue to the decision gate, then design + implementation when no ADR is required or the ADR is approved/deferred.
Reply with corrections to adjust requirements before coding starts.

---

## Ref loading (token-aware)

The agent loads refs only when needed:

| Your task | Refs loaded |
|---|---|
| Single-file fix, no sources | SKILL.md only |
| Docs-only task | + refs/clarification-workflow.md |
| Jira/Figma links provided | + refs/sub-agents.md |
| Migration / AGP / unfamiliar codebase | + refs/playbooks.md + all refs |

---

## Key files

```
.agent-auth.yaml                    ← tokens (gitignored, auto-created)
.project-orchestration/reports/     ← preflight, execution reports
.project-orchestration/memory/      ← session cache, tooling cache
docs/ai/                            ← all agent-generated artifacts
graphify-out/                       ← architecture graph
```

---

## Common commands

| Goal | Tell the agent |
|---|---|
| Rebuild architecture graph | "refresh the graph" |
| Update all tools | "update agents" |
| Resume interrupted task | "resume task" |
| Full clean reset | "force reinstall agents" |
| Check tool readiness | "audit tools" |
