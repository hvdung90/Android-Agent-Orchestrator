---
name: android-agent-orchestrator
description: Four-lane orchestrator for Android projects that coordinates AI DevKit (process), Android skills (domain), Android CLI (runtime), and Karpathy guardrails (quality) into one disciplined workflow. Use when an Android repo needs multiple agent systems to cooperate without stepping on each other — parallel at the analysis/review/verify level, single-owner at the code-change level.
license: MIT
metadata:
  version: 2.0.0
  category: orchestration
  complexity: advanced
  lanes:
    - ai-devkit        # process owner
    - android-skills   # domain owner
    - android-cli      # runtime owner
    - karpathy         # quality gate
---

# Android Agent Orchestrator

## TL;DR

**AI DevKit is the conductor. Android skills are the Android specialist. Android CLI is the runtime executor. Karpathy guidelines are the rules of play.**

Lanes run in parallel for **analysis, review, and verification**. But **only one lane edits product code at any given moment**. Every other lane, at that same moment, is producing documents, recommendations, prepared commands, or evidence — never a second patch on the same area.

This skill enforces that discipline end-to-end: intake, discovery, design split, implementation lock, runtime verify, and QA gate.

---

## Core operating principle

> **Do not parallelize by file. Parallelize by lane.**

| Moment | What is parallel | What is serial |
|---|---|---|
| Intake / Discovery | AI DevKit opens phase + Android skills tags the domain | Not applicable — no code touched yet |
| Design split | AI DevKit writes plan/design; Android skills writes Android memo | Neither lane edits code |
| Implementation | Only one owner edits code | All other lanes are in advisory / prep mode |
| Runtime verify | Android CLI runs build/device/screen capture | Code is frozen during verify |
| QA gate | AI DevKit + Karpathy review diff | No new changes unless a new cycle opens |

**One artifact has exactly one owner.** Never let two lanes write to the same directory or file category. See [Directory & ownership contract](#3-directory--ownership-contract).

---

## When to use

Use this skill when:

- The repo has **more than one agent system** (AI DevKit + Android skills + Android CLI + Claude/Cursor/Codex/Gemini).
- You need to **bootstrap or verify** these systems in a project.
- You need to run a feature, bugfix, migration, or modernization **without role overlap**.
- You need a **disciplined handoff** between process owner, Android specialist, and runtime executor.
- You need to install or refresh capabilities (`ai-devkit install`, `android update`, `android skills add`).

## When NOT to use

- Trivial single-file edits or typo fixes — use judgment, not the full rigor.
- Pure Android coding tasks that don't cross agent systems.
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
| Android SDK | If device work | Device / emulator operations | Android Studio or `sdkmanager` |

> **Fallbacks:** If `ai-devkit` global install is not allowed, use `npx ai-devkit@latest`. If `android` CLI is missing, **stop** and ask the user to install it from the official source — do **not** invent an install path.

---

## Hard rules (non-negotiable)

1. **One code owner at a time.** Parallelism is allowed for analysis, documentation, setup, verification, and advisory review. It is **never** allowed for simultaneous edits to the same implementation area.
2. **One artifact, one owner.** AI DevKit owns `.ai-devkit.json`, `docs/ai/**`, its generated `AGENTS.md`/`CLAUDE.md`, `.cursor/`, `.claude/`, and whatever `ai-devkit install` manages. Android skills own `.skills/`. Do not let the two collide — pick one directory per lane and keep it.
3. **Do not invent update commands.** Refresh Android CLI with `android update`. Verify skills with `android skills list --long`. Install missing skills with `android skills add …`. If you need fresher official skills, update the CLI first, then re-apply. That is the only path.
4. **Reconcile, don't hand-edit.** If AI DevKit manages a file, reconcile via `ai-devkit install` (or `ai-devkit install --overwrite`) rather than editing by hand. Manual edits will be lost on the next reconcile.
5. **No success claim without evidence.** Every install, update, and task execution produces observable evidence in `.project-orchestration/evidence/` (logs, screenshots, command output). No evidence = not done.
6. **Karpathy applies to every code-touching step.** Think before coding, simplicity first, surgical changes, goal-driven execution. See [Karpathy quality gate](#4-lane-d--karpathy-guidelines-quality-gate).

---

## 1) The four lanes

### Lane A — AI DevKit: Process owner

**Owns:**
- Task phase flow: requirements → design → planning → implementation → testing.
- All `docs/ai/**` content.
- `dev-lifecycle` for end-to-end flow, `capture-knowledge` for entry-point mapping, `debug` for RCA, `memory` for project decisions, `agent-orchestration` for cross-agent coordination.
- Reconciliation via `ai-devkit install` (reads `.ai-devkit.json`, applies/overwrites managed artifacts).

**Does NOT own:**
- Latest Android-specific best practices (that is the Android skills lane).
- SDK / emulator / device operations (that is the Android CLI lane).
- Hand-editing artifacts managed by another lane.

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
- Android-specialized best practice and repeatable workflows: XML → Compose, AGP 9 upgrade, Navigation 3, edge-to-edge, R8 audit, etc.
- "Android design memo" review for any plan that touches Android-specific APIs.
- Auto-activating on Android-tagged tasks when the skill is already installed.

**Does NOT own:**
- Project phase docs, task breakdown, or memory (AI DevKit lane).
- Product scope or acceptance criteria.
- Overriding the codebase's existing coding conventions.

**Interaction pattern:**
- Discovery mode: `android skills find "<keyword>"` to tag a task as Android-specialized.
- Review mode: produce a short Android memo (recommended API/framework, pitfalls, migration sequence, compatibility risk).
- Never edits code directly — it **instructs** the single code owner.

---

### Lane C — Android CLI: Runtime / tooling executor

**Owns:**
- Installing / listing / removing Android skills: `android skills add|list|remove`.
- Device and emulator workflows from the CLI.
- Screen capture for UI verification: `android screen capture`.
- Being the bridge so agents in any environment can reach Android resources.

**Does NOT own:**
- Requirement / design / planning docs.
- Task workflow ownership.
- Deciding to patch code on its own — it only runs what the current code owner asks for.

**Commands:**
```bash
android init
android update
android skills list --long
android skills find "<keyword>"
android skills add --skill=<name>
android skills add --agent='claude,cursor,gemini' --skill=<name>
android layout --output=<path>
android screen capture --output=<path>
```

---

### Lane D — Karpathy guidelines: Quality gate

Derived from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills). This lane is a **guardrail**, not an engine. It does not own files or commands; it owns **behavior on every code-touching step**.

**The four principles, enforced on every diff:**

#### 1. Think Before Coding
State assumptions explicitly. If uncertain, ask. If multiple interpretations exist, present them — don't pick silently. If a simpler approach exists, say so. If something is unclear, stop and name what's confusing.

#### 2. Simplicity First
Minimum code that solves the problem. Nothing speculative. No features beyond what was asked. No abstractions for single-use code. No "flexibility" that wasn't requested. No error handling for impossible scenarios. If 200 lines could be 50, rewrite it.

#### 3. Surgical Changes
Touch only what you must. Don't "improve" adjacent code, comments, or formatting. Don't refactor things that aren't broken. Match existing style. If you notice unrelated dead code, mention it — don't delete it. Remove imports/variables that **your** changes orphaned; don't remove pre-existing dead code unless asked. Every changed line must trace directly to the current task.

#### 4. Goal-Driven Execution
Define success criteria up front. Loop until verified.
- "Setup environment" → "`ai-devkit skill list` shows the 5 core skills"
- "Fix build" → "`./gradlew build` exits 0"
- "Migrate to Compose" → "Screenshot diff between before/after = 0"

**Does NOT own:**
- Any files, commands, or workflows of its own.
- Competing with AI DevKit as a second process engine.
- Multiple conflicting copies across the repo — keep **one** canonical source (global plugin, or one thin project rule file).

> **Tradeoff:** Karpathy biases toward caution over speed. For trivial one-liners, use judgment. The goal is fewer costly mistakes on non-trivial work, not slowing down simple edits.

---

## 2) Lane responsibility matrix

| Activity | AI DevKit | Android skills | Android CLI | Karpathy |
|---|---|---|---|---|
| Open phase / write requirements | **Owner** | — | — | Advisory |
| Map entry point & dependencies | **Owner** (`capture-knowledge`) | Read-only | — | Advisory |
| Android design memo | — | **Owner** | — | Advisory |
| Task breakdown & risk log | **Owner** | Advisory | — | Advisory |
| Edit product code | **Owner** (single lane) | Advisory only | — | **Enforces** |
| Install/update/list skills | Skills it manages | — | Skills it manages | — |
| Run build / device / capture | — | — | **Owner** | — |
| QA gate on diff | **Owner** | Advisory | Evidence provider | **Enforces** |
| Close task | **Owner** | — | — | Final check |

Rule of thumb: if two cells show **Owner** for the same activity, the design is wrong. There must be exactly one.

---

## 3) Directory & ownership contract

This is the most important overlap-prevention rule. Decide it once, write it down, do not drift.

### Locked ownership

| Path | Owner | Notes |
|---|---|---|
| `.ai-devkit.json` | **AI DevKit** | Source of truth for its install |
| `docs/ai/**` | **AI DevKit** | Phase docs, memory, decisions |
| `AGENTS.md`, `CLAUDE.md` (generated) | **AI DevKit** | Reconciled by `ai-devkit install` |
| `.cursor/commands/**`, `.claude/commands/**` | **AI DevKit** | Command artifacts |
| `.cursor/skills/**`, `.claude/skills/**` | **AI DevKit** | Skills it distributes |
| `.agents/skills/**`, `.agent/skills/**` | **AI DevKit** (if configured) | Check `.ai-devkit.json` |
| `.skills/` | **Android skills** | Project-local Android skills only |
| Global Android install | **Android skills** via `android skills add` | Outside repo |
| `.project-orchestration/**` | **This orchestrator** | Mirrors, reports, evidence |

### The critical choice

Both AI DevKit and Android skills can, in some environments, write to `.agent/skills/`. To avoid collisions:

- **Recommended:** put Android skills in `.skills/` and let AI DevKit own `.agent/skills/` (or disable the latter in `.ai-devkit.json` if unused).
- **Never** let both lanes write to the same directory. Pick one per directory and commit to it in the project README.

### If reconciliation conflicts happen

`ai-devkit install --overwrite` will overwrite artifacts AI DevKit manages. If you hand-edited one and it got overwritten: that's expected behavior, not a bug. Move the customization into `.ai-devkit.json` or a template, then reconcile again.

---

## 4) The six-stage workflow

Every task — feature, bug, migration, investigation — goes through these six stages in order. **Do not skip stages.** Each stage produces a named deliverable.

### Stage 0 — Intake

**Owner:** AI DevKit
**Allowed in parallel:** Android skills may tag the domain while AI DevKit opens the phase.
**Code frozen:** Yes.

Open the task with `dev-lifecycle` or a `/new-requirement` command. Produce:
- Goal
- Scope
- Acceptance criteria
- Entry points suspected to be affected

```bash
ai-devkit skill add codeaholicguy/ai-devkit dev-lifecycle   # if missing
# Then invoke dev-lifecycle per your environment
```

---

### Stage 1 — Discovery

**Owner:** AI DevKit (`capture-knowledge`)
**Parallel:** Android skills classifies whether the task is Android-specialized.
**Code frozen:** Yes.

AI DevKit runs `capture-knowledge` on the entry point (file, folder, function, endpoint). It maps dependencies and execution paths.

Android skills answers one question: *Is this Android-specialized?* If yes, tag it:
- `compose-migration`
- `edge-to-edge`
- `navigation-3`
- `r8-audit`
- `agp-upgrade`
- …etc. (run `android skills find "<keyword>"` to check availability)

**Deliverable:** discovery memo in `docs/ai/discovery/<task-id>.md`.

---

### Stage 2 — Design split

**Owner:** Two branches, both advisory.
**Code frozen:** Yes.

Two lanes run **in parallel**, both producing documents only.

**Branch A — AI DevKit:**
Writes design, planning, risk, rollback, and test plan into `docs/ai/design/` and `docs/ai/planning/`.

**Branch B — Android skills:**
Produces a short "Android design memo" covering:
- Recommended API / framework
- Pitfalls specific to the Android version / surface
- Required migration sequence
- Compatibility risks
- "Do / Don't" for the Android layer

**Hard rule:** Neither branch edits code at this stage. They exchange memos via handoff contracts (see below).

**Deliverable:** `docs/ai/design/<task-id>.md` (A) + `docs/ai/android-memo/<task-id>.md` (B).

---

### Stage 3 — Implementation lock

**Owner:** Exactly one lane edits code. Usually AI DevKit's implementation lane, referencing the Android memo.
**Code frozen:** No, but only for the owner.
**Karpathy:** Fully active — every diff must pass the four principles.

This is where overlap is most dangerous.

- AI DevKit lane follows the plan and docs.
- Android skills are consumed **as instruction packs** — the agent auto-activates the installed skill, but does not open a second edit lane.
- Android CLI stays in advisory / prep mode (it may prepare commands but does not execute patches).

**Forbidden:**
- AI DevKit lane edits a file while an Android lane also edits the same file.
- One agent patches code while another "beautifies" adjacent code in the same diff.
- Merging changes from two lanes that both wrote to the same area.

**Deliverable:** a single diff in a single branch, authored by one lane, verified locally by the owner before Stage 4.

---

### Stage 4 — Runtime verify

**Owner:** Android CLI.
**Code frozen:** Yes (no new patches during verify).

After the diff is complete, the Android CLI lane runs verification:

```bash
# Build / run evidence
./gradlew clean build \
  > .project-orchestration/evidence/logs/build.txt 2>&1

# UI evidence (if task touches UI)
android screen capture \
  --output=.project-orchestration/evidence/screenshots/after.png

# Layout evidence (if task touches layout)
android layout \
  --output=.project-orchestration/evidence/logs/layout.json
```

**Required outputs:**
- Build / run result (exit code + log)
- Screenshot / video / log for UI work
- Environment + device info

If verification fails, return to Stage 3 (single owner patches again). Do **not** open a second edit lane to "help."

---

### Stage 5 — QA gate

**Owner:** AI DevKit + Karpathy guardrails.

- If feature: run testing / code-review inside `dev-lifecycle`.
- If bug: use `debug` for RCA if cause is still uncertain, then require a regression test that reproduces the original bug.

**Karpathy diff review (mandatory):**
- Every changed line traces to the task? (Surgical Changes)
- No dead code left by this change? (Surgical Changes)
- No speculative abstraction introduced? (Simplicity First)
- Assumptions documented where ambiguous? (Think Before Coding)
- Success criteria verified with evidence? (Goal-Driven Execution)

**Close condition — all four must hold:**
1. Acceptance criteria present in `docs/ai/`.
2. Diff matches the plan.
3. Verification evidence exists in `.project-orchestration/evidence/`.
4. Minimum tests / checks passed.

If any fails: reopen, do not close.

---

## 5) Handoff contracts

Every handoff between lanes uses a fixed template. This is what makes the choreography predictable.

### AI DevKit → Android skills
```yaml
task_id: <id>
scope: feature | bug | migration
entry_point: <file/function/endpoint>
design_question: <specific Android question needing review>
codebase_constraints: <conventions, min SDK, Compose version, etc.>
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
environment:
  device: <name / emulator id>
  android_version: <version>
  abi: <x86_64 / arm64>
```

Any handoff missing required fields = the receiving lane sends it back. No ad-hoc handoffs.

---

## 6) Recommended project layout

```text
.project-orchestration/
├── vendor/                           # Read-only mirrors for audit/reference
│   ├── ai-devkit/
│   ├── android-skills/
│   └── optional/
│       ├── rcosteira79-android-skills/
│       ├── android-skills-mcp/
│       └── andrej-karpathy-skills/   # Karpathy guardrail source
├── reports/
│   ├── provisioning.md               # What got installed / updated
│   ├── inventory.md                  # Pre-run environment snapshot
│   ├── routing.md                    # Ownership decision per task
│   └── execution.md                  # Final synthesis per task
└── evidence/
    ├── logs/
    └── screenshots/

docs/ai/                              # AI DevKit territory
├── requirements/
├── design/
├── planning/
├── implementation/
├── testing/
├── discovery/                        # capture-knowledge outputs
└── android-memo/                     # Android skills review memos

.skills/                              # Android skills territory (if file-based)
.ai-devkit.json                       # AI DevKit source of truth
```

---

## 7) Provisioning algorithm

Run this when bootstrapping a repo or onboarding a new environment.

### Step 0 — Create control directories
```bash
mkdir -p .project-orchestration/vendor/optional \
         .project-orchestration/reports \
         .project-orchestration/evidence/logs \
         .project-orchestration/evidence/screenshots
```

### Step 1 — Clone or refresh vendor mirrors
```bash
clone_or_refresh() {
  local url="$1"
  local dir="$2"
  if [ ! -d "$dir/.git" ]; then
    git clone --depth=1 "$url" "$dir"
  else
    git -C "$dir" fetch --all --prune
    git -C "$dir" pull --ff-only
  fi
}

# Required mirrors
clone_or_refresh https://github.com/codeaholicguy/ai-devkit.git \
  .project-orchestration/vendor/ai-devkit
clone_or_refresh https://github.com/android/skills.git \
  .project-orchestration/vendor/android-skills

# Karpathy guardrail source (recommended)
clone_or_refresh https://github.com/forrestchang/andrej-karpathy-skills.git \
  .project-orchestration/vendor/optional/andrej-karpathy-skills

# Optional — only if approved and needed
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
  echo "Android CLI is missing. Install it from the official source, then rerun."
  exit 1
fi
android update
android init
```

### Step 4 — Ensure `.ai-devkit.json` exists
```bash
if [ ! -f .ai-devkit.json ]; then
  $AI_DEVKIT_BIN init   # interactive
  # or: $AI_DEVKIT_BIN init --template ./ai-devkit-template.yaml
fi
```

Example template for non-interactive init:
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
$AI_DEVKIT_BIN skill add codeaholicguy/ai-devkit dev-lifecycle
$AI_DEVKIT_BIN skill add codeaholicguy/ai-devkit debug
$AI_DEVKIT_BIN skill add codeaholicguy/ai-devkit capture-knowledge
$AI_DEVKIT_BIN skill add codeaholicguy/ai-devkit memory
$AI_DEVKIT_BIN skill add codeaholicguy/ai-devkit agent-orchestration
$AI_DEVKIT_BIN skill update codeaholicguy/ai-devkit
$AI_DEVKIT_BIN install --overwrite
$AI_DEVKIT_BIN skill list
```

### Step 6 — Discover and install official Android skills (on demand)
```bash
android skills list --long
android skills find "compose"
android skills find "migration"
android skills find "navigation"

# Install only what the current task needs
android skills add --skill=edge-to-edge
android skills add --skill=agp-9-upgrade
# For multi-agent install:
# android skills add --agent='gemini,claude,cursor' --skill=compose-migration
```

> Default policy: **only** `android-cli` is installed by default. Do not run `android skills add --all` unless project policy explicitly allows it.

### Step 7 — Install Karpathy guardrail (one canonical copy)
Pick **one** location, not both:

**Option A — Global plugin (Claude Code):**
```
/plugin marketplace add forrestchang/andrej-karpathy-skills
/plugin install andrej-karpathy-skills@karpathy-skills
```

**Option B — Per-project CLAUDE.md append:**
```bash
curl https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md \
  >> CLAUDE.md
```

> Do not duplicate Karpathy rules into every skill file. One canonical source keeps them from drifting out of sync.

### Step 8 — Optional Android-local skills folder
```bash
# Only if the environment requires file-based skills
mkdir -p .skills
# Copy approved Android skills into .skills/ (do NOT use .agent/skills/ — that's AI DevKit territory)
```

### Step 9 — Generate provisioning report
```bash
cat > .project-orchestration/reports/provisioning.md <<EOF
# Provisioning report
date: $(date -Iseconds)

## AI DevKit
- binary: $AI_DEVKIT_BIN
- version: $($AI_DEVKIT_BIN --version 2>/dev/null || echo n/a)
- skills:
$($AI_DEVKIT_BIN skill list 2>/dev/null || echo n/a)

## Android CLI
- version: $(android --version 2>/dev/null || echo n/a)
- skills:
$(android skills list 2>/dev/null || echo n/a)

## Mirrors
$(ls -1 .project-orchestration/vendor 2>/dev/null)
$(ls -1 .project-orchestration/vendor/optional 2>/dev/null)

## Karpathy guardrail
- source: $([ -d .project-orchestration/vendor/optional/andrej-karpathy-skills ] && echo "mirrored" || echo "missing")
- installed as: <global plugin | project CLAUDE.md | both>
EOF
```

---

## 8) Update algorithm

### AI DevKit
```bash
$AI_DEVKIT_BIN skill update codeaholicguy/ai-devkit
$AI_DEVKIT_BIN install --overwrite
$AI_DEVKIT_BIN skill list
```

### Android CLI + official skills
```bash
android update
android init
android skills list --long
# Re-apply any missing skill:
android skills add --skill=<name>
```

### Vendor mirrors
Re-run `clone_or_refresh` for every mirror. This includes the Karpathy mirror.

---

## 9) Routing rules (by task type)

### Rule A — New feature
1. **AI DevKit** (`dev-lifecycle`) — requirements, design, planning, testing docs.
2. **Android skills** — if Android-specialized, produce memo + auto-activate during implementation.
3. **AI DevKit lane** — single code owner, implements per plan + memo.
4. **Android CLI** — build / device / screenshot verification.
5. **Karpathy gate** — diff review before close.

### Rule B — Bugfix
1. **AI DevKit** (`debug`) — reproduce, RCA, minimal patch plan.
2. **Android skills** — join only if the bug is in an Android specialization.
3. **AI DevKit lane** — smallest safe patch.
4. **Android CLI** — runtime re-verify.
5. **Karpathy gate** — regression test required.

### Rule C — Migration / modernization (e.g., XML → Compose, AGP 9)
1. **AI DevKit** — migration plan, risk log, rollback plan.
2. **Android skills** — procedure for the specialized migration.
3. **AI DevKit lane** — single code owner, stepwise changes.
4. **Android CLI** — build + visual parity screenshots (before / after).
5. **Karpathy gate** — no adjacent refactors; every change traces to the migration step.

### Rule D — Unfamiliar codebase
1. **AI DevKit** (`capture-knowledge`) — map entry point first.
2. Produce dependency + flow summary.
3. Only **after** the map exists, route the task to the correct owner.
4. Karpathy enforces "Think Before Coding" — no edits until understanding is written down.

---

## 10) Playbooks

### Playbook 1 — Feature: add edge-to-edge support
```bash
# Stage 0-1: intake + discovery
# (use dev-lifecycle via your agent)

# Stage 1 (Android skills lane)
android skills find "edge-to-edge"
android skills add --skill=edge-to-edge

# Stage 2: both lanes write memos. No code edits.

# Stage 3: AI DevKit lane implements.
#   Karpathy active: surgical changes only, no "while we're here" refactors.

# Stage 4: runtime verify
android screen capture --output=.project-orchestration/evidence/screenshots/edge-to-edge.png

# Stage 5: QA gate
#   AI DevKit runs dev-lifecycle testing phase.
#   Karpathy diff review.
```

### Playbook 2 — Bugfix: layout broken on tablets
```bash
# Stage 0-1: AI DevKit debug reproduces.
android layout --output=.project-orchestration/evidence/logs/layout-tablet.json
android screen capture --output=.project-orchestration/evidence/screenshots/bug.png

# Stage 2: design memo only.

# Stage 3: smallest patch, AI DevKit lane.

# Stage 4: re-verify
android screen capture --output=.project-orchestration/evidence/screenshots/fixed.png

# Stage 5: regression test added.
```

### Playbook 3 — Migration: XML → Compose
```bash
# Stage 1: capture-knowledge on the XML entry point.

# Stage 2:
android skills find "compose"
android skills add --skill=compose-migration

# Stage 3: stepwise migration, single owner.
android screen capture --output=.project-orchestration/evidence/screenshots/before.png
# (migration)
android screen capture --output=.project-orchestration/evidence/screenshots/after.png

# Stage 5: visual parity check. Cleanup plan documented.
```

### Playbook 4 — AGP 9 upgrade
```bash
# Stage 1: AI DevKit migration plan + risk log.

# Stage 2:
android skills add --skill=agp-9-upgrade

# Stage 3: controlled migration steps, single owner.
./gradlew --version > .project-orchestration/evidence/logs/gradle-before.txt
./gradlew dependencies > .project-orchestration/evidence/logs/deps-before.txt

# Stage 4:
./gradlew clean build \
  > .project-orchestration/evidence/logs/build-after.txt 2>&1

# Stage 5: new version baselines recorded; follow-up items filed.
```

---

## 11) Optional external skills policy

Only add external skills when there is a **justified gap** that official skills and project rules do not cover.

| Option | Purpose | Use when |
|---|---|---|
| [rcosteira79/android-skills](https://github.com/rcosteira79/android-skills) | Broader Android / KMP patterns (architecture, testing, coroutines, flows, RxJava migration) | Official set doesn't cover the pattern you need |
| [skydoves/android-skills-mcp](https://github.com/skydoves/android-skills-mcp) | MCP bridge for Android skills | Your agent consumes MCP better than file-based skills |
| [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) | Karpathy behavioral guardrail | **Recommended always** — install one canonical copy |

**Install pattern — mirror then adopt:**
```bash
clone_or_refresh https://github.com/<owner>/<repo>.git \
  .project-orchestration/vendor/optional/<n>
# Then follow that repo's install instructions separately.
```

Do **not** copy third-party skill files into `docs/ai/` or `.ai-devkit.json`-managed paths. Keep them in their own sandbox or the official install location.

---

## 12) Required reporting contract

At the end of every orchestration run, produce `.project-orchestration/reports/execution.md` with these sections:

### 1. Provisioning summary
- Repos cloned / refreshed
- Tools already installed
- Tools newly installed
- Tools updated

### 2. Installed capability summary
- AI DevKit skills active
- Android skills active (per target agent)
- Optional externals enabled (including Karpathy guardrail source)

### 3. Ownership summary
- Code owner for this task
- Support owners (advisory only)
- Forbidden overlaps that were avoided

### 4. Execution evidence
- Commands run
- Notable logs
- Screenshots / layout captures
- Unresolved blockers

### 5. Karpathy diff review
- Every changed line traces to task? (yes/no + notes)
- Dead code introduced or orphaned? (yes/no)
- Speculative abstraction avoided? (yes/no)
- Assumptions documented? (yes/no)
- Success criteria verified with evidence? (yes/no)

### 6. Final synthesis
- What changed and why
- Why each owner was involved
- What remains as follow-up

---

## 13) Failure handling

### AI DevKit unavailable
Fall back to `npx ai-devkit@latest …`. Do not skip the lane.

### Android CLI unavailable
Stop. Ask the user to install from the official source. Do **not** fabricate a package-manager install path.

### Official Android skill not installable in the target agent
Try, in order:
1. `android skills add --agent=<explicit list> --skill=<name>`
2. Project-local `.skills/` import if the environment supports it.
3. MCP bridge (if policy allows).
4. Approved community pack.

### Reconcile overwrote your hand edits
Expected behavior. Move the customization into `.ai-devkit.json` or a template and reconcile again. Don't re-edit by hand.

### Two lanes both want to edit code
Stop. Re-read [Stage 3 — Implementation lock](#stage-3--implementation-lock). Pick one owner. The other lane converts its work into an advisory memo and hands it over.

### Conflict between lane recommendations
Priority order:
1. Safety and reproducibility
2. Official Android skill guidance (for Android-specific decisions)
3. AI DevKit workflow discipline (for process and docs)
4. Project-local coding conventions
5. Optional external skills

---

## 14) Quick command checklist

```bash
# Mirrors
clone_or_refresh https://github.com/codeaholicguy/ai-devkit.git \
  .project-orchestration/vendor/ai-devkit
clone_or_refresh https://github.com/android/skills.git \
  .project-orchestration/vendor/android-skills
clone_or_refresh https://github.com/forrestchang/andrej-karpathy-skills.git \
  .project-orchestration/vendor/optional/andrej-karpathy-skills

# AI DevKit
ai-devkit init
ai-devkit skill add codeaholicguy/ai-devkit dev-lifecycle
ai-devkit skill add codeaholicguy/ai-devkit debug
ai-devkit skill add codeaholicguy/ai-devkit capture-knowledge
ai-devkit skill add codeaholicguy/ai-devkit memory
ai-devkit skill add codeaholicguy/ai-devkit agent-orchestration
ai-devkit skill update codeaholicguy/ai-devkit
ai-devkit install --overwrite
ai-devkit skill list

# Android CLI + official skills
android update
android init
android skills list --long
android skills find "compose"
android skills add --skill=edge-to-edge
android skills add --skill=agp-9-upgrade
android layout --output=.project-orchestration/evidence/logs/layout.json
android screen capture --output=.project-orchestration/evidence/screenshots/ui.png

# Karpathy guardrail — pick ONE install target
# Global plugin (Claude Code):
#   /plugin marketplace add forrestchang/andrej-karpathy-skills
#   /plugin install andrej-karpathy-skills@karpathy-skills
# OR per-project:
#   curl https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

---

## Final operating principle

> **Parallel by lane, serial by file. One active code owner at any moment.**

- **AI DevKit** owns process, phase, docs, memory.
- **Android skills** own Android domain guidance.
- **Android CLI** owns runtime, device, and skill management.
- **Karpathy guidelines** own behavior on every code-touching step.
- **This orchestrator** owns setup, routing, handoff, and synthesis.

Keep the lanes moving in parallel wherever that produces value (analysis, review, verification). Lock the code-change lane to exactly one owner per task. Every handoff uses a contract. Every close needs evidence.

That is the whole discipline.
