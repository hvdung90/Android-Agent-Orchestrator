---
name: android-agent-orchestrator
description: Meta-skill for Android projects coordinating AI DevKit (process), Android skills (domain), Android CLI (runtime), Graphify (architecture graph), and Karpathy guardrails (quality) into one disciplined workflow. Use when an Android repo needs multiple agent systems to cooperate without stepping on each other — parallel at analysis/review/verify level, single-owner at code-change level.
license: MIT
metadata:
  version: 3.0.0
  category: orchestration
  lanes:
    - ai-devkit        # process owner
    - android-skills   # domain owner
    - android-cli      # runtime owner
    - graphify         # architecture knowledge (optional)
    - karpathy         # quality gate
---

# Android Agent Orchestrator

## TL;DR

**AI DevKit is the conductor. Android skills are the Android specialist. Android CLI is the runtime executor. Graphify is the architecture map. Karpathy guidelines are the rules of play.**

Lanes run in parallel for **analysis, review, and verification**. But **only one lane edits product code at any given moment**. Every other lane produces documents, recommendations, graph queries, or evidence — never a second patch on the same area.

---

## Core operating principle

> **Do not parallelize by file. Parallelize by lane.**

| Moment | Parallel | Serial |
|---|---|---|
| Intake / Discovery | AI DevKit opens phase + Graphify reads architecture + Android skills tags domain | No code touched |
| Design split | AI DevKit writes plan; Android skills writes Android memo | Neither edits code |
| Implementation | Only one owner edits code | All others in advisory/prep mode |
| Runtime verify | Android CLI runs build/device/capture | Code frozen |
| QA gate | AI DevKit + Karpathy review diff | No new changes |

**One artifact has exactly one owner.** See [Directory & ownership contract](#3-directory--ownership-contract).

---

## When to use

Use this skill when:

- The repo has **more than one agent system** working together.
- You need to **bootstrap or verify** agent systems in a project.
- You need to run a feature, bugfix, migration, or modernization **without role overlap**.
- You need a **disciplined handoff** between process owner, Android specialist, and runtime executor.
- You have an **existing codebase** and want AI to understand architecture before touching code.

## When NOT to use

- Trivial single-file edits or typo fixes.
- Pure coding tasks that don't cross agent systems.
- Repos that use only one agent system.
- Exploratory prototypes with no process discipline.

---

## Prerequisites

| Tool | Required | Purpose | How to get it |
|---|---|---|---|
| AI DevKit | Yes | Process / phase / docs / memory | `npm i -g ai-devkit` or `npx ai-devkit@latest` |
| Android CLI | Yes | Android runtime & skill management | Official Android CLI installer |
| Git ≥ 2.0 | Yes | Vendor mirrors, project management | System package manager |
| Node.js ≥ 18 | Yes | AI DevKit runtime | nodejs.org |
| Python ≥ 3.10 | If Graphify | Knowledge graph generation | python.org |
| Android SDK | If device work | Device / emulator operations | Android Studio or `sdkmanager` |

> **Fallbacks:** If `ai-devkit` global install is not allowed, use `npx ai-devkit@latest`. If `android` CLI is missing, **stop** and ask the user to install from the official source — do **not** invent an install path.

---

## Hard rules (non-negotiable)

1. **One code owner at a time.** Parallelism is allowed for analysis, docs, setup, verification, and advisory review. Never for simultaneous edits to the same area.
2. **One artifact, one owner.** AI DevKit owns `docs/ai/**` and `.ai-devkit.json`. Android skills own `.skills/`. Graphify owns `graphify-out/**`. This orchestrator owns `.project-orchestration/**`. No lane crosses into another's territory.
3. **Do not invent update commands.** Refresh Android CLI with `android update`. Verify skills with `android skills list --long`. Install with `android skills add …`. No other paths.
4. **Reconcile, don't hand-edit.** If AI DevKit manages a file, reconcile via `ai-devkit install`. Manual edits will be lost on the next reconcile.
5. **No success claim without evidence.** Every install, update, and execution produces observable output in `.project-orchestration/evidence/`. No evidence = not done.
6. **Read Graphify before touching code.** If `graphify-out/` exists, read `GRAPH_REPORT.md` before generating requirements or planning. Never guess at architecture when the graph is available.
7. **Karpathy applies to every code-touching step.** Think before coding, simplicity first, surgical changes, goal-driven execution.
8. **Always read existing docs before generating anything.** If input docs exist in `docs/ai/inputs/`, read them first. Never generate requirements from scratch when source material exists.
9. **Stop and wait for human review after generating requirements.** Do not proceed to routing or implementation without explicit confirmation.

---

## 1) The five lanes

### Lane A — AI DevKit: Process owner

**Owns:**
- Task phase flow: requirements → design → planning → implementation → testing.
- All `docs/ai/**` content.
- `dev-lifecycle`, `capture-knowledge`, `debug`, `memory`, `agent-orchestration`.
- Reconciliation via `ai-devkit install`.

**Does NOT own:**
- Android-specific best practices (Android skills lane).
- SDK / device operations (Android CLI lane).
- Architecture graph queries (Graphify lane).

**Commands:**
```bash
ai-devkit init
ai-devkit skill add codeaholicguy/ai-devkit <skill>
ai-devkit skill list
ai-devkit skill update codeaholicguy/ai-devkit
ai-devkit install --overwrite
```

---

### Lane B — Android skills: Android domain owner

**Owns:**
- Android-specialized best practice workflows: XML → Compose, AGP 9 upgrade, Navigation 3, edge-to-edge, R8 audit.
- "Android design memo" review for any plan that touches Android-specific APIs.

**Does NOT own:**
- Project phase docs or task breakdown (AI DevKit lane).
- Product scope or acceptance criteria.
- Overriding existing coding conventions.

**Interaction pattern:**
- Discovery: `android skills find "<keyword>"` to tag a task as Android-specialized.
- Review: produce a short Android memo (recommended API, pitfalls, migration sequence, compatibility risk).
- Never edits code directly — it **instructs** the single code owner.

---

### Lane C — Android CLI: Runtime / tooling executor

**Owns:**
- Installing / listing / removing Android skills.
- Device and emulator workflows.
- Screen capture for UI verification.
- Being the bridge so agents can reach Android resources.

**Does NOT own:**
- Requirement / design / planning docs.
- Task workflow ownership.
- Deciding to patch code — only runs what the code owner requests.

**Commands:**
```bash
android init
android update
android skills list --long
android skills find "<keyword>"
android skills add --skill=<n>
android skills add --agent='claude,cursor,gemini' --skill=<n>
android layout --output=<path>
android screen capture --output=<path>
```

---

### Lane D — Graphify: Architecture knowledge (optional)

Graphify turns the Android codebase into a **queryable knowledge graph**. It is not a code editor — it is a **read-only map** that every other lane queries before making decisions.

**Install:**
```bash
pip install graphifyy && graphify install
```

**Owns:**
- `graphify-out/GRAPH_REPORT.md` — high-level summary: god nodes, communities, surprising connections.
- `graphify-out/graph.json` — full persistent graph, queryable without re-reading raw source.
- `graphify-out/graph.html` — interactive visual graph.
- Architecture understanding: what connects to what, design rationale, call graphs, dependency maps.

**Does NOT own:**
- Any source code files.
- Requirement or design docs.
- Any other lane's output directory.

**Core commands:**
```bash
/graphify .                                              # build graph (first time)
/graphify . --update                                     # incremental update after changes
cat graphify-out/GRAPH_REPORT.md                         # read overview — always start here
graphify query "<keyword>" --graph graphify-out/graph.json
graphify path "ComponentA" "ComponentB" --graph graphify-out/graph.json
graphify explain "ComponentName" --graph graphify-out/graph.json
graphify claude install                                  # always-on hook for Claude Code
```

**Always-on integration (recommended):**
```bash
# Writes CLAUDE.md section + PreToolUse hook so Claude reads the graph automatically
graphify claude install
```

---

### Lane E — Karpathy guidelines: Quality gate

Derived from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills). This lane is a **guardrail**, not an engine. It owns **behavior on every code-touching step**.

**The four principles, enforced on every diff:**

#### 1. Think Before Coding
State assumptions explicitly. If uncertain, ask. Present multiple interpretations — don't pick silently. If a simpler approach exists, say so. **Read the Graphify graph before assuming architecture.**

#### 2. Simplicity First
Minimum code that solves the problem. Nothing speculative. No features beyond what was asked. No abstractions for single-use code. If 200 lines could be 50, rewrite it.

#### 3. Surgical Changes
Touch only what you must. Don't "improve" adjacent code. Don't refactor things that aren't broken. Match existing style. Every changed line must trace directly to the current task.

#### 4. Goal-Driven Execution
Define success criteria up front. Loop until verified.
- "Setup environment" → "`ai-devkit skill list` shows the 5 core skills"
- "Fix build" → "`./gradlew build` exits 0"
- "Migrate to Compose" → "Screenshot diff = 0"

> **Tradeoff:** Karpathy biases toward caution. For trivial one-liners, use judgment.

---

## 2) Lane responsibility matrix

| Activity | AI DevKit | Android skills | Android CLI | Graphify | Karpathy |
|---|---|---|---|---|---|
| Read architecture graph | Consumer | Consumer | — | **Owner** | — |
| Open phase / requirements | **Owner** | — | — | Input | Advisory |
| Map entry point & dependencies | **Owner** | Read-only | — | **Primary input** | Advisory |
| Android design memo | — | **Owner** | — | Input | Advisory |
| Task breakdown & risk log | **Owner** | Advisory | — | Input | Advisory |
| Edit product code | **Owner** (single lane) | Advisory only | — | — | **Enforces** |
| Install/update/list skills | Skills it manages | — | Skills it manages | — | — |
| Build graph / query graph | — | — | — | **Owner** | — |
| Run build / device / capture | — | — | **Owner** | — | — |
| QA gate on diff | **Owner** | Advisory | Evidence | Verify impact | **Enforces** |
| Close task | **Owner** | — | — | Graph updated? | Final check |

---

## 3) Directory & ownership contract

| Path | Owner | Notes |
|---|---|---|
| `.ai-devkit.json` | **AI DevKit** | Source of truth for its install |
| `docs/ai/**` | **AI DevKit** | Phase docs, memory, decisions |
| `docs/ai/inputs/` | **You** | Your raw input docs — never overwritten |
| `docs/ai/requirements/` | **AI DevKit** | Agent-generated from your inputs |
| `docs/ai/discovery/` | **AI DevKit** | capture-knowledge + graphify query outputs |
| `AGENTS.md`, `CLAUDE.md` (generated) | **AI DevKit** | Reconciled by `ai-devkit install` |
| `.skills/` | **Android skills** | Project-local Android skills only |
| `graphify-out/**` | **Graphify** | Graph outputs — never hand-edit |
| `.project-orchestration/**` | **This orchestrator** | Mirrors, reports, evidence |

---

## 4) Input-driven requirement workflow

Use when you have existing docs (task briefs, architecture notes, feature lists, design notes).

### Flow

```
docs/ai/inputs/ has content?
        │
        ▼ Yes
  [Graphify] Read GRAPH_REPORT.md      ← understand real architecture first
        │
        ▼
  [AI DevKit] Read all input docs      ← understand your intent
        │
        ▼
  Cross-check: input docs vs graph     ← detect conflicts early
        │
        ▼
  Gaps that need research?
        ├── Yes (optional) ──→  graphify query OR capture-knowledge
        │                                  │
        ▼ No                               ▼
        └──────────────────────→  Generate requirements doc
                                          │
                                          ▼
                                 STOP — wait for human review
                                          │
                                          ▼ Approved
                                  Route → Execute → Verify
```

### Input doc organization

Place your raw docs here before starting:
```
docs/ai/inputs/
  task-brief.md         ← short task descriptions, tickets
  architecture.md       ← your architecture notes
  features.md           ← feature list with basic design notes
  design-notes.md       ← UI/UX notes
```

### Requirement doc output format

```markdown
# Requirements: [Feature Name]

## Source documents
- docs/ai/inputs/<file>
- graphify-out/GRAPH_REPORT.md (architecture reference)

## Context
- Architecture components (from Graphify): <list>
- Graph path affected: ComponentA → ComponentB → ComponentC
- Affected layers: UI / Domain / Data

## User stories
- As a [user], I want [action] so that [benefit]

## Acceptance criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

## Affected components
- UI: <Compose screens, ViewModels>
- Domain: <UseCases>
- Data: <Repositories, APIs>
- Graph god nodes touched: <from GRAPH_REPORT>

## Edge cases
- <edge case 1>

## Open questions
- ? <anything unclear — for human to resolve>

## Research findings (if research was performed)
- <findings from graphify query or capture-knowledge>
```

### Confirmation prompt (show after generating)

```
Requirements doc generated at docs/ai/requirements/<feature-name>.md

Please review and confirm:
  [A] Approve — proceed to routing and implementation
  [E] Edit — I will update the doc, then re-read and replan
  [R] Re-research — research these specific gaps: <list>
```

---

## 5) Graphify integration: when and how

Graphify is **optional but strongly recommended** for existing codebases. Once built, querying costs 71x fewer tokens than reading raw files.

### Trigger rules: when to read Graphify output

| Scenario | When to read | What to query |
|---|---|---|
| **New feature on existing codebase** | Before reading input docs, at Stage 1 | `GRAPH_REPORT.md` + `graphify query "<feature area>"` |
| **Edit existing feature** | Before requirements | `graphify query "<feature name>"` + `graphify path` |
| **Bug investigation** | During Stage 1 Discovery | `graphify path "<symptom>" "<cause>"` |
| **Migration (XML→Compose, AGP)** | During requirements | `graphify query "xml layout view"` to list all affected |
| **Unfamiliar codebase** | First action, before anything else | Full `GRAPH_REPORT.md` → god nodes → entry point query |

### When NOT to query Graphify

- Graph doesn't exist AND task is simple (single new file, no existing dependencies).
- Task is purely additive with no connection to existing components.
- Codebase is very small (< 10 files) — reading files directly is fine.

### Stage-by-stage Graphify usage

#### Stage 0 — Intake
- Check: does `graphify-out/GRAPH_REPORT.md` exist?
- If yes → read it as context. Note god nodes and affected communities.
- If no → consider building the graph if codebase is large.

#### Stage 1 — Discovery ← **Primary Graphify stage**
When graph exists, run these in parallel with `capture-knowledge`:
```bash
# Architecture overview
cat graphify-out/GRAPH_REPORT.md

# Query the specific area
graphify query "<task keyword>" --graph graphify-out/graph.json

# Trace affected dependency path
graphify path "<entry component>" "<target component>" --graph graphify-out/graph.json
```
Append graph query output to `docs/ai/discovery/<task-id>.md`.

**Why Graphify before `capture-knowledge`:** Graphify gives the structural map cheaply. `capture-knowledge` fills in detailed flow for the specific entry point. Together = complete picture.

#### Stage 2 — Design split
```bash
# Understand design rationale of affected components
graphify explain "<ComponentName>" --graph graphify-out/graph.json

# Find all Android-specific nodes in scope
graphify query "viewmodel compose navigation" --graph graphify-out/graph.json
```

#### Stage 3 — Implementation lock
- **No Graphify queries during active coding.** The map was read in Stage 1.
- Karpathy "Surgical Changes": only touch nodes in the graph path identified in Stage 1.

#### Stage 4 — Runtime verify
```bash
# After implementation: update graph to reflect changes
/graphify . --update
```

#### Stage 5 — QA gate
```bash
# Optional: compare GRAPH_REPORT.md before/after
# Karpathy surgical check: every changed line in the graph path?
graphify query "<changed area>" --graph graphify-out/graph.json
```

---

## 6) Graphify by task type

### New feature on existing codebase
```bash
# 1. Read architecture map
cat graphify-out/GRAPH_REPORT.md

# 2. Find components the feature will touch
graphify query "<feature keyword>" --graph graphify-out/graph.json

# 3. Understand the "why" of existing related code
graphify explain "<RelatedComponent>" --graph graphify-out/graph.json

# 4. Read your input docs
# 5. Cross-check: does your plan conflict with graph structure?
# 6. Generate requirements — include graph path in affected components
# 7. Implement → Update graph after
/graphify . --update
```

### Edit existing feature
```bash
# 1. Find all nodes for the feature
graphify query "<feature name>" --graph graphify-out/graph.json

# 2. Trace full dependency — know what could break
graphify path "<EntryPoint>" "<TargetComponent>" --graph graphify-out/graph.json

# 3. Read input docs
# 4. Generate requirements with impact analysis from graph
# 5. Implement surgically — only nodes in the identified path
# 6. Update graph
/graphify . --update
```

### Bug investigation
```bash
# 1. Trace path between symptom and suspected cause
graphify path "<SymptomComponent>" "<SuspectedComponent>" --graph graphify-out/graph.json

# 2. Capture runtime evidence
android layout --output=.project-orchestration/evidence/logs/layout-bug.json
android screen capture --output=.project-orchestration/evidence/screenshots/bug.png

# 3. Cross-reference: graph path + runtime evidence → root cause
# 4. Apply minimal fix
/graphify . --update
```

### Migration: XML → Compose
```bash
# 1. List ALL xml/view components that need migrating
graphify query "xml layout view fragment" --graph graphify-out/graph.json

# 2. Find their dependents — what will break if you migrate them
graphify query "fragment activity adapter" --graph graphify-out/graph.json

# 3. Order migration by graph: leaf nodes first, god nodes last
# 4. Capture before state
android screen capture --output=.project-orchestration/evidence/screenshots/before-compose.png

# 5. Migrate one component at a time (single owner)
# 6. Update graph after each batch
/graphify . --update
graphify query "xml layout" --graph graphify-out/graph.json  # verify fewer xml nodes remain

# 7. Final verification
android screen capture --output=.project-orchestration/evidence/screenshots/after-compose.png
```

### Unfamiliar codebase (first contact)
```bash
# 1. Build graph first
/graphify .

# 2. Read the report — this is your orientation
cat graphify-out/GRAPH_REPORT.md
# God nodes = what everything connects through
# Surprising connections = non-obvious links
# Suggested questions = what to investigate next

# 3. Open graph.html in browser for visual exploration

# 4. Query entry point
graphify query "<main activity or feature area>" --graph graphify-out/graph.json

# 5. THEN run capture-knowledge for detailed flow on specific area

# 6. Only after the map exists, route to the correct owner
```

---

## 7) The six-stage workflow

Every task goes through these stages in order. **Do not skip stages.**

### Stage 0 — Intake

**Owner:** AI DevKit | **Code frozen:** Yes.

Open the task. Produce: goal, scope, acceptance criteria, suspected entry points.
Check: does `graphify-out/` exist? → Flag for Stage 1.

---

### Stage 1 — Discovery

**Owner:** AI DevKit (`capture-knowledge`)
**Parallel:** Android skills classifies domain. Graphify queries run simultaneously.
**Code frozen:** Yes.

**If `graphify-out/` exists:**
```bash
# [Graphify lane — in parallel]
cat graphify-out/GRAPH_REPORT.md
graphify query "<task keyword>" --graph graphify-out/graph.json
graphify path "<entry>" "<target>" --graph graphify-out/graph.json

# [AI DevKit lane — in parallel]
# ai-devkit capture-knowledge --entry-point=<file>

# [Android skills lane — in parallel]
android skills find "<keyword>"
```

**If `graphify-out/` does not exist:**
```bash
# Consider building if codebase is significant
# pip install graphifyy && /graphify .
# Otherwise: capture-knowledge only
```

**Deliverable:** `docs/ai/discovery/<task-id>.md` — graph query output + capture-knowledge findings merged.

---

### Stage 2 — Design split

**Owner:** Two branches, both advisory. **Code frozen:** Yes.

**Branch A — AI DevKit:**
Writes design, planning, risk, rollback, test plan into `docs/ai/design/` and `docs/ai/planning/`.
Uses `graphify explain` to understand design rationale of affected components.

**Branch B — Android skills:**
Produces "Android design memo": recommended API, pitfalls, migration sequence, compatibility risks, Do/Don't.

**Deliverable:** `docs/ai/design/<task-id>.md` + `docs/ai/android-memo/<task-id>.md`.

---

### Stage 3 — Implementation lock

**Owner:** Exactly one lane edits code. **Karpathy:** Fully active.

- AI DevKit lane follows the plan and Android memo.
- Android skills consumed as instruction packs — not a second edit lane.
- Android CLI stays in prep mode.
- **No Graphify queries during coding** — the map was read in Stage 1.

**Forbidden:** Two lanes editing the same file simultaneously. "While we're here" refactors. Merging changes from two lanes on the same area.

---

### Stage 4 — Runtime verify

**Owner:** Android CLI. **Code frozen:** Yes.

```bash
./gradlew clean build > .project-orchestration/evidence/logs/build.txt 2>&1

android screen capture --output=.project-orchestration/evidence/screenshots/after.png
android layout --output=.project-orchestration/evidence/logs/layout.json

# Update graph to reflect implementation
/graphify . --update
```

---

### Stage 5 — QA gate

**Owner:** AI DevKit + Karpathy guardrails.

**Karpathy diff review (mandatory):**
- Every changed line traces to the task? (Surgical Changes)
- No dead code left by this change? (Surgical Changes)
- No speculative abstraction introduced? (Simplicity First)
- Assumptions documented? (Think Before Coding)
- Success criteria verified with evidence? (Goal-Driven Execution)

**Close condition — all must hold:**
1. Acceptance criteria in `docs/ai/`.
2. Diff matches the plan.
3. Verification evidence in `.project-orchestration/evidence/`.
4. Minimum tests passed.
5. Graph updated (`/graphify . --update` ran successfully).

---

## 8) Handoff contracts

### AI DevKit → Android skills
```yaml
task_id: <id>
scope: feature | bug | migration
entry_point: <file/function>
graph_path: ComponentA → ComponentB → ComponentC   # from Graphify Stage 1
design_question: <specific Android question>
codebase_constraints: <conventions, min SDK, Compose version>
```

### Android skills → AI DevKit
```yaml
task_id: <id>
recommended_framework_or_pattern: <name + reason>
do: <list>
dont: <list>
migration_sequence: <ordered steps>
android_specific_risks: <list>
```

### AI DevKit → Android CLI
```yaml
task_id: <id>
branch: <branch-name>
commands_to_run:
  - <cmd 1>
  - <cmd 2>
expected_result: <success condition>
files_or_modules_involved: <list>
```

### Android CLI → AI DevKit
```yaml
task_id: <id>
build_status: <success | failure + exit code>
logs: <path under evidence/logs/>
screenshots: <path under evidence/screenshots/>
graph_updated: <yes | no>
environment:
  device: <name / emulator id>
  android_version: <version>
  abi: <x86_64 / arm64>
```

---

## 9) Recommended project layout

```text
.project-orchestration/
├── vendor/
│   ├── ai-devkit/
│   ├── android-skills/
│   └── optional/
│       ├── andrej-karpathy-skills/
│       ├── rcosteira79-android-skills/
│       └── android-skills-mcp/
├── reports/
│   ├── provisioning.md
│   ├── inventory.md
│   ├── routing.md
│   └── execution.md
└── evidence/
    ├── logs/
    └── screenshots/

docs/ai/
├── inputs/           ← your raw docs (never overwritten by agent)
├── requirements/     ← agent-generated from inputs
├── design/
├── planning/
├── implementation/
├── testing/
├── discovery/        ← graphify queries + capture-knowledge merged
└── android-memo/     ← Android skills review memos

graphify-out/         ← Graphify territory (never hand-edit)
├── GRAPH_REPORT.md
├── graph.json
└── graph.html

.skills/              ← Android skills territory
.ai-devkit.json       ← AI DevKit source of truth
.graphifyignore       ← exclude build/, vendor/, generated files
```

---

## 10) Provisioning algorithm

### Step 0 — Create control directories
```bash
mkdir -p docs/ai/{inputs,requirements,discovery} \
         .project-orchestration/vendor/optional \
         .project-orchestration/{reports,evidence/logs,evidence/screenshots}
```

### Step 1 — Clone or refresh vendor mirrors
```bash
clone_or_refresh() {
  local url="$1" dir="$2"
  if [ ! -d "$dir/.git" ]; then
    git clone --depth=1 "$url" "$dir"
  else
    git -C "$dir" fetch --all --prune && git -C "$dir" pull --ff-only
  fi
}

clone_or_refresh https://github.com/codeaholicguy/ai-devkit.git \
  .project-orchestration/vendor/ai-devkit

clone_or_refresh https://github.com/android/skills.git \
  .project-orchestration/vendor/android-skills

clone_or_refresh https://github.com/forrestchang/andrej-karpathy-skills.git \
  .project-orchestration/vendor/optional/andrej-karpathy-skills

# Optional: only if approved and needed
# clone_or_refresh https://github.com/rcosteira79/android-skills.git \
#   .project-orchestration/vendor/optional/rcosteira79-android-skills
# clone_or_refresh https://github.com/skydoves/android-skills-mcp.git \
#   .project-orchestration/vendor/optional/android-skills-mcp
```

### Step 2 — Ensure AI DevKit is available
```bash
if ! command -v ai-devkit >/dev/null 2>&1; then
  npm install -g ai-devkit || true
fi
AI_DEVKIT_BIN="ai-devkit"
if ! command -v "$AI_DEVKIT_BIN" >/dev/null 2>&1; then
  AI_DEVKIT_BIN="npx ai-devkit@latest"
fi
```

### Step 3 — Ensure Android CLI is available
```bash
if ! command -v android >/dev/null 2>&1; then
  echo "Android CLI missing. Install from official source, then rerun."
  exit 1
fi
android update && android init
```

### Step 4 — Ensure `.ai-devkit.json` exists
```bash
[ ! -f .ai-devkit.json ] && $AI_DEVKIT_BIN init
```

Example template:
```yaml
environments: [cursor, claude, codex]
phases: [requirements, design, planning, implementation, testing]
paths:
  docs: docs/ai
skills:
  - { registry: codeaholicguy/ai-devkit, skill: dev-lifecycle }
  - { registry: codeaholicguy/ai-devkit, skill: debug }
  - { registry: codeaholicguy/ai-devkit, skill: capture-knowledge }
  - { registry: codeaholicguy/ai-devkit, skill: memory }
  - { registry: codeaholicguy/ai-devkit, skill: agent-orchestration }
mcpServers:
  memory:
    transport: stdio
    command: npx
    args: ["-y", "@ai-devkit/memory"]
```

### Step 5 — Install core AI DevKit skills
```bash
for skill in dev-lifecycle debug capture-knowledge memory agent-orchestration; do
  $AI_DEVKIT_BIN skill add codeaholicguy/ai-devkit $skill
done
$AI_DEVKIT_BIN skill update codeaholicguy/ai-devkit
$AI_DEVKIT_BIN install --overwrite
$AI_DEVKIT_BIN skill list
```

### Step 6 — Install official Android skills (on demand)
```bash
android skills list --long
android skills find "compose"

# Install only what the current task needs
android skills add --skill=edge-to-edge
android skills add --skill=agp-9-upgrade
```

### Step 7 — Install Graphify (optional, recommended for existing codebase)
```bash
pip install graphifyy && graphify install

# Configure ignore patterns
cat > .graphifyignore <<EOF
build/
.gradle/
.project-orchestration/vendor/
node_modules/
*.generated.*
graphify-out/
EOF

# Build the initial graph
/graphify .

# Make Claude Code always read the graph before tasks
graphify claude install
```

### Step 8 — Install Karpathy guardrail (one canonical copy)
```bash
# Option A — Global plugin (Claude Code):
# /plugin marketplace add forrestchang/andrej-karpathy-skills
# /plugin install andrej-karpathy-skills@karpathy-skills

# Option B — Per-project:
curl https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

### Step 9 — Generate provisioning report
```bash
cat > .project-orchestration/reports/provisioning.md <<EOF
# Provisioning report — $(date -Iseconds)

## AI DevKit
version: $($AI_DEVKIT_BIN --version 2>/dev/null || echo n/a)
skills:
$($AI_DEVKIT_BIN skill list 2>/dev/null)

## Android CLI
version: $(android --version 2>/dev/null || echo n/a)
skills:
$(android skills list 2>/dev/null)

## Graphify
installed: $(command -v graphify >/dev/null && echo yes || echo no)
graph_exists: $([ -f graphify-out/GRAPH_REPORT.md ] && echo yes || echo no)
always_on: $([ -f .graphifyignore ] && echo configured || echo not configured)

## Karpathy guardrail
mirrored: $([ -d .project-orchestration/vendor/optional/andrej-karpathy-skills ] && echo yes || echo no)
EOF
```

---

## 11) Update algorithm

### AI DevKit
```bash
$AI_DEVKIT_BIN skill update codeaholicguy/ai-devkit
$AI_DEVKIT_BIN install --overwrite
$AI_DEVKIT_BIN skill list
```

### Android CLI + official skills
```bash
android update && android init
android skills list --long
android skills add --skill=<n>   # re-apply missing
```

### Graphify
```bash
/graphify . --update   # incremental — only processes changed files
```

### Vendor mirrors
```bash
# Re-run clone_or_refresh for every mirror including Karpathy
```

---

## 12) Routing rules (by task type)

### Rule A — New feature (existing codebase)
1. **Graphify** — read `GRAPH_REPORT.md` + query feature area.
2. **AI DevKit** — read input docs → cross-check with graph → generate requirements → wait for approval.
3. **Android skills** — Android memo if Android-specialized.
4. **AI DevKit lane** — single code owner, implements per plan + memo.
5. **Android CLI** — build / device / screenshot verification.
6. **Graphify** — `--update` after implementation.
7. **Karpathy gate** — diff review before close.

### Rule B — Edit existing feature
1. **Graphify** — `query + path` for full dependency map.
2. **AI DevKit** — requirements with impact analysis from graph → wait for approval.
3. **Android skills** — Android memo if needed.
4. **AI DevKit lane** — surgical edits only within graph path.
5. **Android CLI** — runtime re-verify.
6. **Graphify** — `--update` + compare before/after.
7. **Karpathy gate** — every changed line in graph path?

### Rule C — Bug investigation
1. **Graphify** — `path "<symptom>" "<cause>"` to trace dependency.
2. **Android CLI** — capture runtime evidence.
3. **AI DevKit** (`debug`) — cross-reference graph path + runtime evidence → root cause.
4. **AI DevKit lane** — smallest safe patch.
5. **Android CLI** — re-verify.
6. **Graphify** — `--update`.
7. **Karpathy gate** — regression test required.

### Rule D — Migration (XML → Compose, AGP)
1. **Graphify** — list all components in migration scope, ordered by dependency (leaf nodes first).
2. **AI DevKit** — migration plan, risk log based on graph scope.
3. **Android skills** — migration procedure.
4. **AI DevKit lane** — stepwise, one component at a time.
5. **Android CLI** — visual parity screenshots (before / after each batch).
6. **Graphify** — `--update` after each batch; verify no old nodes remain.
7. **Karpathy gate** — no adjacent refactors.

### Rule E — Unfamiliar codebase
1. **Graphify** — `/graphify .` build → read `GRAPH_REPORT.md` (god nodes, communities, surprising connections).
2. **AI DevKit** (`capture-knowledge`) — detailed entry-point map.
3. Merge: graph structure + capture-knowledge → `docs/ai/discovery/`.
4. Only after the map exists, route to the correct owner.
5. **Karpathy:** "Think Before Coding" — no edits until understanding is written down.

---

## 13) Playbooks

### Playbook 1 — Feature: add edge-to-edge support
```bash
# Stage 1: Discovery
cat graphify-out/GRAPH_REPORT.md
graphify query "window insets edge" --graph graphify-out/graph.json
android skills find "edge-to-edge" && android skills add --skill=edge-to-edge

# Stage 2: Design memos (no code)
# Stage 3: AI DevKit lane implements — Karpathy active
# Stage 4: Verify
android screen capture --output=.project-orchestration/evidence/screenshots/after.png
/graphify . --update
# Stage 5: QA gate
```

### Playbook 2 — Bug: layout broken on tablets
```bash
# Stage 1: Discovery
graphify path "LayoutComponent" "TabletTarget" --graph graphify-out/graph.json
android layout --output=.project-orchestration/evidence/logs/layout-tablet.json
android screen capture --output=.project-orchestration/evidence/screenshots/bug.png

# Stage 3: Smallest patch, AI DevKit lane
# Stage 4: Re-verify
android screen capture --output=.project-orchestration/evidence/screenshots/fixed.png
/graphify . --update
# Stage 5: Regression test added
```

### Playbook 3 — Migration: XML → Compose
```bash
# Stage 1: List all xml components + their dependents
graphify query "xml layout view fragment" --graph graphify-out/graph.json
android skills add --skill=compose-migration
android screen capture --output=.project-orchestration/evidence/screenshots/before-compose.png

# Stage 3: Migrate leaf-first (from graph), single owner
# After each batch:
/graphify . --update
graphify query "xml layout" --graph graphify-out/graph.json   # verify fewer xml nodes

# Stage 4: Final verification
android screen capture --output=.project-orchestration/evidence/screenshots/after-compose.png
# Stage 5: Visual parity check + cleanup plan
```

### Playbook 4 — AGP 9 upgrade
```bash
# Stage 1: Scope
graphify query "gradle build agp" --graph graphify-out/graph.json
android skills add --skill=agp-9-upgrade
./gradlew --version > .project-orchestration/evidence/logs/gradle-before.txt

# Stage 3: Controlled migration, single owner
# Stage 4: Verify
./gradlew clean build > .project-orchestration/evidence/logs/build-after.txt 2>&1
/graphify . --update
# Stage 5: New version baselines recorded
```

### Playbook 5 — First contact: unfamiliar codebase
```bash
# Step 1: Build the map
/graphify .

# Step 2: Read the map
cat graphify-out/GRAPH_REPORT.md
# open graphify-out/graph.html in browser

# Step 3: Query entry point
graphify query "main activity entry" --graph graphify-out/graph.json

# Step 4: Detailed flow
# ai-devkit capture-knowledge --entry-point=MainActivity.kt

# Step 5: Route to correct owner only after map is documented
```

---

## 14) Optional external skills policy

| Option | Purpose | When to use |
|---|---|---|
| [safishamsi/graphify](https://github.com/safishamsi/graphify) | Architecture knowledge graph | **Recommended** for any existing codebase |
| [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) | Behavioral quality guardrail | **Recommended always** |
| [rcosteira79/android-skills](https://github.com/rcosteira79/android-skills) | Broader Android / KMP patterns | When official set doesn't cover the pattern |
| [skydoves/android-skills-mcp](https://github.com/skydoves/android-skills-mcp) | MCP bridge for Android skills | When agent consumes MCP better than file-based |

---

## 15) Required reporting contract

Produce `.project-orchestration/reports/execution.md` after every run:

### 1. Provisioning summary
- Repos cloned / refreshed; tools installed / updated; Graphify graph status.

### 2. Installed capability summary
- AI DevKit skills active; Android skills active; Graphify: node count, god nodes; optional externals.

### 3. Ownership summary
- Code owner; support owners; graph path touched; forbidden overlaps avoided.

### 4. Execution evidence
- Commands run; notable logs; screenshots; **graph queries run and key findings**; blockers.

### 5. Karpathy diff review
- Every changed line traces to task? (yes/no)
- Dead code introduced? (yes/no)
- Speculative abstraction avoided? (yes/no)
- Assumptions documented? (yes/no)
- Success criteria verified? (yes/no)

### 6. Final synthesis
- What changed and why; why each lane was involved; graph before/after comparison; follow-up.

---

## 16) Failure handling

### AI DevKit unavailable
Fall back to `npx ai-devkit@latest`. Do not skip the lane.

### Android CLI unavailable
Stop. Ask the user to install from the official source. Do **not** fabricate an install path.

### Graphify not installed or graph not built
Proceed without it. Use `capture-knowledge` as fallback. Note in report that Graphify was skipped.

### Graphify graph is stale
Run `/graphify . --update` before querying. If update fails, use last known graph with caution and note it.

### Official Android skill not installable
Try in order: `--agent=<explicit list>` → `.skills/` import → MCP bridge → community pack.

### Two lanes both want to edit code
Stop. Pick one owner. The other converts its work into an advisory memo.

### Conflict between lane recommendations
Priority: safety → official Android skill guidance → AI DevKit workflow → project conventions → optional external skills.

---

## 17) Quick command checklist

```bash
# ── Mirrors ──────────────────────────────────────────────────────────────────
clone_or_refresh https://github.com/codeaholicguy/ai-devkit.git .project-orchestration/vendor/ai-devkit
clone_or_refresh https://github.com/android/skills.git .project-orchestration/vendor/android-skills
clone_or_refresh https://github.com/forrestchang/andrej-karpathy-skills.git .project-orchestration/vendor/optional/andrej-karpathy-skills

# ── AI DevKit ────────────────────────────────────────────────────────────────
ai-devkit init
ai-devkit skill add codeaholicguy/ai-devkit dev-lifecycle
ai-devkit skill add codeaholicguy/ai-devkit debug
ai-devkit skill add codeaholicguy/ai-devkit capture-knowledge
ai-devkit skill add codeaholicguy/ai-devkit memory
ai-devkit skill add codeaholicguy/ai-devkit agent-orchestration
ai-devkit skill update codeaholicguy/ai-devkit
ai-devkit install --overwrite && ai-devkit skill list

# ── Android CLI + official skills ────────────────────────────────────────────
android update && android init
android skills list --long
android skills find "compose"
android skills add --skill=edge-to-edge
android skills add --skill=agp-9-upgrade
android layout --output=.project-orchestration/evidence/logs/layout.json
android screen capture --output=.project-orchestration/evidence/screenshots/ui.png

# ── Graphify ─────────────────────────────────────────────────────────────────
pip install graphifyy && graphify install
/graphify .                                              # build graph
/graphify . --update                                     # incremental update
graphify claude install                                  # always-on hook
cat graphify-out/GRAPH_REPORT.md                         # read overview
graphify query "<keyword>" --graph graphify-out/graph.json
graphify path "ComponentA" "ComponentB" --graph graphify-out/graph.json
graphify explain "ComponentName" --graph graphify-out/graph.json

# ── Karpathy guardrail ───────────────────────────────────────────────────────
# Global: /plugin install andrej-karpathy-skills@karpathy-skills
# Per-project: curl https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

---

## Final operating principle

> **Parallel by lane, serial by file. Read the map before touching code.**

- **AI DevKit** owns process, phase, docs, memory, requirements.
- **Android skills** own Android domain guidance.
- **Android CLI** owns runtime, device, and skill management.
- **Graphify** owns architecture understanding — read before every task on existing code.
- **Karpathy guidelines** own behavior on every code-touching step.
- **This orchestrator** owns setup, routing, handoff, and synthesis.

Keep lanes moving in parallel wherever that produces value. Lock the code-change lane to exactly one owner. Read the graph first. Every handoff uses a contract. Every close needs evidence.
