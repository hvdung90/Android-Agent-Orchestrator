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

## Step 4 — Handoff a task (multi-dev)

When **Dev A** needs to stop and hand off to **Dev B**:

```
Tell the agent: "dừng lại, bàn giao cho dev-b"
```

The agent will:
1. Update `docs/ai/tasks/{task_id}/handoff.md` with current state
2. Update `.project-orchestration/status.json` → `assignee: dev-b`
3. Write interrupt state to `session.json`

**Dev B** picks up with one command:

```
Tell the agent: "resume task ANDROID-42"
```

The agent reads `handoff.md` and resumes from the exact interrupted stage.

### Check all active tasks (team view)

```
Read: .project-orchestration/status.json
```

Shows every task: stage, assignee, branch, PR, blocker — in one file.

### Key handoff files

```
docs/ai/tasks/{task_id}/handoff.md        ← full task snapshot for incoming dev
.project-orchestration/status.json        ← all tasks dashboard
```

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
.agent-auth.yaml                              ← tokens (gitignored, auto-created)
.project-orchestration/status.json            ← all tasks dashboard (gitignored)
.project-orchestration/reports/               ← preflight, execution reports
.project-orchestration/memory/                ← session cache, tooling cache
.project-orchestration/tasks/{task_id}/       ← per-task state + evidence
docs/ai/tasks/{task_id}/handoff.md            ← handoff snapshot for incoming dev
docs/ai/                                      ← all agent-generated artifacts
graphify-out/                                 ← architecture graph
```

---

## Common commands

| Goal | Tell the agent |
|---|---|
| Rebuild architecture graph | "refresh the graph" |
| Update all tools | "update agents" |
| Resume interrupted task | "resume task ANDROID-XX" |
| Full clean reset | "force reinstall agents" |
| Check tool readiness | "audit tools" |
| Hand off to another dev | "dừng lại, bàn giao cho \<dev-name\>" |
| View all active tasks | Read `.project-orchestration/status.json` |
| View task handoff state | Read `docs/ai/tasks/{task_id}/handoff.md` |
