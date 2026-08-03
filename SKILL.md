---
name: android-agent-orchestrator
description: Use when starting, planning, analyzing, or implementing any Android task — new feature, bug fix, refactor, migration, AGP upgrade, architecture review, team task tracking, or repo setup. Use when user says start task, new feature, fix bug, analyze repo, migrate, upgrade, implement, review architecture, team task, or set up agents for an Android project.
license: MIT
metadata:
  version: 5.0.0
  category: orchestration
  lanes:
    - ai-devkit
    - android-skills
    - android-cli
    - graphify
    - karpathy
  workers:
    - serena-code-analysis
    - gradle-module-impact-analyzer
  refs:
    - refs/auth-bootstrap.md
    - refs/provisioning-preflight.md
    - refs/clarification-workflow.md
    - refs/sub-agents.md
    - refs/contracts-and-artifacts.md
    - refs/stage-contracts.md
    - refs/compliance-policy.md
    - refs/playbooks.md
    - refs/team-docs.md
---

# Android Agent Orchestrator v5.0.0

## Activation

Load this skill when the user asks to **start, plan, analyze, or implement an Android task**.

Trigger phrases: `start task` · `new feature` · `fix bug` · `analyze repo` · `migrate` · `upgrade` · `set up agents` · `implement` · `review architecture` · `team task`

**Do not use this skill when:**
- Answering general Android questions without any repo changes planned.
- Explanation-only or documentation read requests with no code output.
- Non-code documentation rewrites unless they accompany a code change.
- Throwaway prototypes where the user explicitly opts out of governance.
- Purely conversational questions about Android APIs or concepts.
- The project is not Android (Kotlin backend, KMP web-only, pure iOS, etc.).
- `TEAM_DOCS_PATH` is set in CLAUDE.md but the path cannot be resolved (clone the docs repo or unset the variable first).

---

## TL;DR

**Five-lane skeleton. Stage -1: Tooling Preflight + Auth Bootstrap + optional Team Docs Check. Single `.agent-auth.yaml` manages all tokens.**

- Stage -1: auth init → tooling readiness → team docs conflict check (if `TEAM_DOCS_PATH` is set).
- AI DevKit is the sole conductor: requirements, synthesis, routing, final go/no-go.
- One code owner at a time — sub-agents and all other lanes are read-only observers.
- `TEAM_DOCS_PATH` (optional in CLAUDE.md): enables cross-team file-lock coordination via a shared docs repo.

> **Auth first. Read the map. Clarify before planning. Approve before coding.**

---

## Workflow Modes

Three modes shape the stage sequence and artifact depth. Mode is derived at Stage 0 (preliminary) and finalized at the end of Stage 1. Override at any time: "use fast mode", "use standard mode", "use governed mode".

| Mode | Use when | Stage sequence | Artifact depth |
|---|---|---|---|
| **fast** | Single-file bug fix, isolated logic fix, ≤ 2 files, no architecture impact | -1 → 0 → 1 → 2(mini) → 2.5-lite → 3-lite → 4 → 5(lite) → 6(lite) → 7(lite) | Requirements ≤ 40 lines, 3-lite: plan + code_owner + branch only, lite verify |
| **standard** | Normal Android feature, multi-file, single module, clear requirements | -1 → 0 → 1 → [1.5] → 2 → [2.5] → 3 → 4 → 5 → 6 → 7 | Requirements ≤ 120 lines, design ≤ 180 lines |
| **governed** | Large feature, migration, multi-module, Jira + Figma, any ADR trigger | Full -1 → 7 | No restrictions |

**Never changes regardless of mode:** auth init, team docs check, human requirements approval, TDD evidence (Gate E.5), `session.json` + `skip-log.json` writes, `status.json` updates, Stage 2.5 ADR trigger check, Karpathy diff review.

**Fast mode stage skips** (all recorded in `skip-log.json`): Stage 1.5 AUTO-SKIP; Stage 2.5 ADR creation AUTO-SKIP only if no trigger fires (trigger fires → upgrade to governed); Stage 3 design doc AUTO-SKIP (3-lite still runs); Stage 6 full QA CONFIRM-SKIP (Karpathy + Gate G MANDATORY).

**Override rules (priority order):**
1. Any ADR trigger fires → minimum `governed`
2. Jira ticket + Figma link both present → minimum `standard`
3. Human explicitly requests a mode → use that mode; log `mode_override` in `session.json`
4. Task brief is incomplete or ambiguous → minimum `standard`
5. Otherwise → use computed mode from scores

### Scoring

Computed at Stage 0 from task description (preliminary). Finalized after Stage 1 when sources and Graphify data are available.

**complexity_score (1–10):**

| Signal | Score |
|---|---|
| 1–2 files, same module, same layer, additive-only change | 1–2 |
| Multi-file, single module, same architectural layer | 3–4 |
| Multi-file, multi-layer (e.g. ViewModel + Repository + tests) | 5–6 |
| Multi-module change | 7–8 |
| Migration, architecture restructure, or AGP / Kotlin version change | 9–10 |

**risk_score (1–10):**

| Signal | Score |
|---|---|
| Isolated logic, no shared state, no ADR triggers | 1–2 |
| Touches ViewModel state or shared Repository | 3–4 |
| Touches auth, billing, permissions, or notifications | 5–6 |
| Database migration or persistence schema change | 5–6 |
| API surface change across module boundary | 7–8 |
| God nodes in change path | 7–8 |
| Multiple high-risk signals simultaneously | 9–10 |

**Mode mapping:**

```
complexity_score ≤ 3 AND risk_score ≤ 3   →  fast
complexity_score ≤ 7 AND risk_score ≤ 6   →  standard
otherwise                                   →  governed
```

Write `preliminary_mode` to `session.json` at Stage 0. **Finalize at the end of Stage 1** — write `workflow_mode`, `complexity_score`, `risk_score`, `mode_reasons` to `context-pack.json` and `session.json`.

---

## Core operating principle

> **Readiness before routing. Read the map before touching code. Clarify before planning. Approve before coding.**

| Moment | Parallel | Serial |
|---|---|---|
| Tooling Preflight | Safe read-only checks | Install/update only when mode allows |
| Intake | AI DevKit opens phase; Graphify existence check | No code touched |
| Discovery | Graphify read + source readers + Android domain tagging | No code touched |
| Clarification | Multiple sub-agents analyze in parallel | Parent synthesis waits for required outputs |
| Requirements | AI DevKit writes one canonical requirements doc | Single owner |
| Decision Gate | AI DevKit decides ADR requirement; human approves Proposed ADR when required | Stop before Design if required |
| Design split | AI DevKit writes plan; Android skills writes memo | Neither edits product code |
| Implementation | One code owner only | All other lanes advisory only |
| Verify | Android CLI runs build/device/capture; Graphify updates | Code frozen |
| QA gate | AI DevKit + Karpathy review diff | No new code changes |
| Docs finalization | AI DevKit updates ADR status and task changelog | No product changes |

---

## When to load refs

Load refs on demand — **do not load all refs upfront**. Match tier to task complexity.

| Tier | Condition | Load |
|---|---|---|
| **LIGHT** | Mode C · single-file fix · no external sources | SKILL.md only |
| **MEDIUM** | Mode B · docs-only · no Jira/Figma | + `refs/clarification-workflow.md` |
| **HEAVY** | Mode A (Jira/Figma links) | + `refs/sub-agents.md` |
| **FULL** | Migration · AGP · unfamiliar codebase · god nodes in path | + `refs/playbooks.md` + all refs |

Always load at Stage -1: `refs/auth-bootstrap.md`, `refs/provisioning-preflight.md`.
If `TEAM_DOCS_PATH` is set in CLAUDE.md: also load `refs/team-docs.md` at Stage -1.
Always load when writing artifacts: `refs/contracts-and-artifacts.md`.
Always load when resuming an interrupted task: `refs/stage-contracts.md`.
Always load before any stage skip: `refs/compliance-policy.md`.
Load when `graph_impact ≥ medium` or multi-module: `refs/sub-agents.md` (Gradle Module Impact Analyzer).

---

## Hard rules

1. **Auth first.** `.agent-auth.yaml` is the single source of truth for all tokens. Never log token values. Never commit the file. Default provisioning mode is `audit`.
2. **One code owner at a time** — including sub-agents: only the designated code owner may write files or execute mutations; sub-agents are read-only observers.
3. **One canonical synthesizer.** AI DevKit owns requirements, synthesis, routing, and final go/no-go. No other lane produces canonical artifacts.
4. **No success without evidence.** Never invent commands — only use commands found in project docs, Makefile, README, or confirmed by shell `which`/`--help`. Every claim of success requires runnable proof.
5. **Stage order is law.** Stages run -1 → 0 → 1 → [1.5] → 2 → 2.5 → 3 → 4 → 5 → 6 → 7. Any re-ordering or parallel shortcut not defined in this skill is a violation — stop and report.
6. **Read architecture map before touching code.** When `graphify-out/` exists, read it in Discovery. Understand-Anything → Graphify fallback for new repos.
7. **Karpathy applies to every code-touching step.** Apply principles even without the plugin installed; record how the gate was applied.
8. **Every skip is logged.** Write to `skip-log.json` on every auto-skip and confirm-skip. Load `refs/compliance-policy.md` before any skip decision. MANDATORY steps cannot be skipped.
9. **ADR ledger is global and immutable.** Never edit Accepted ADR text. When a decision changes, create a new superseding ADR.
10. **`handoff.md` when code owner changes or Stage 4 interrupts.** `branch` and `assignee` must be set before Stage 4 begins.
11. **Team docs first.** If `TEAM_DOCS_PATH` is set in project CLAUDE.md, read `active-tasks/README.md` + `active-tasks/<repo>/README.md` at Stage -1. If any planned file overlaps `locked_files` → HARD STOP. Load `refs/team-docs.md` for the full protocol.
12. **Task file follows the task.** When `TEAM_DOCS_PATH` is set, create/update the team task file at Stage 0. Write pending lock entries immediately — do not defer to Stage 3. Update on stage transitions. Archive at Stage 7.
13. **Decisions leave a trace.** Any decision affecting other repos → write in team task file `## Decisions` + update `active-tasks/README.md § Cross-repo Impacts`.

---

## Lanes

### Lane A — AI DevKit
Owns phase control, `docs/ai/**`, routing, synthesis, final requirements, planning, and review gates.

### Lane B — Android skills
Owns Android advisory memos, platform guidance, migration notes, API pitfalls, and compatibility advice.

### Lane C — Android CLI
Owns runtime evidence, screenshots, layout capture, device actions, official Android skill management, and verification commands.

### Lane D — Graphify
Owns graph build/query/update and architecture evidence.

### Lane E — Karpathy guidelines
Owns code-touching behavior and diff review.

---

## Sub-agents

→ **Load `refs/sub-agents.md`** for the full worker catalog with YAML output contracts and Serena activation matrix.

Sub-agents are internal workers activated by the parent orchestrator during Discovery and Clarification. They are **read-only or advisory** — they never own final decisions or product-code edits.

| Category | Workers |
|---|---|
| Source readers | Jira Reader, Confluence Reader, Figma Reader, Doc Reader, Graph Impact Reader |
| **Module analysis** | **Gradle Module Impact Analyzer** — Gradle module boundary mapping; read-only; activated when `graph_impact ≥ medium` |
| Analysis workers | Ambiguity Detector, Conflict Detector, Missing-info Detector, State Extractor, Dependency Impact Analyzer |
| Advisory workers | Research Advisor, Android Advisor, QA Scenario Advisor, Rollout/Risk Advisor |
| **Code Analysis** | **Code Analysis Worker (Serena)** — symbol-level queries; read-only; agent-decided activation |
| Preflight | Tooling Preflight Auditor |

---

## Stage model

### Stage -1 — Tooling Preflight

Run before Intake.

→ **Load `refs/auth-bootstrap.md`** — run Step 1 (initialize auth file) at the start of Stage -1.
→ **Load `refs/provisioning-preflight.md`** for full decision tables, cache check, and safety rules.

**Team Docs Check (run first, when `TEAM_DOCS_PATH` is set in CLAUDE.md):**
- Load `refs/team-docs.md` for the full protocol.
- Resolve `TEAM_DOCS_PATH` (absolute, `~`-prefixed, or relative to git root). If path doesn't exist → HARD STOP.
- `git pull --rebase` on docs repo.
- Read `active-tasks/README.md` → collect `locked_files[]` from "Cross-repo Conflicts" section.
- Read `active-tasks/<repo>/README.md` → collect per-repo locked paths.
- Match planned scope against `locked_files[]`. If overlap → HARD STOP, print conflict table with owner @github-handle.
- If clean → log `team_docs.conflict_check: clean` in `session.json`.
- Else: skip, note `team_docs: not-configured` in `session.json`.

**Cache check first:** Read `.project-orchestration/memory/tooling-cache.json`. If `valid_until` is in the future AND `graph_commit` matches `git rev-parse HEAD` → skip tool checks, use cached result, go directly to Stage 0.

**Otherwise run:** `bash templates/tooling-preflight.sh --json > .project-orchestration/reports/preflight.json && bash templates/tooling-preflight.sh > .project-orchestration/reports/preflight.md` — parallel checks; JSON for gate decisions, markdown for human reading. Use `preflight.json → ready_for_stage_0` as the boolean gate; do not parse markdown for proceed/block decisions.

**Graphify staleness check:** After commit-hash check, read `graph-stamp.json → built_at`. If `built_at + 7 days < now` → flag `stale (time-based)` in `preflight.md`, non-blocking.

**Project status index:** Read `.project-orchestration/status.json`. If missing, create with empty `tasks: []`. Surface any `stage_status: in_progress` tasks at Stage 0.

Default mode: `audit`.

Deliverable: `.project-orchestration/reports/preflight.md`

### Stage 0 — Intake

Open the task, confirm source availability, determine external sources, and consume Stage -1 findings.

→ **Load `refs/clarification-workflow.md` § Source integrations** for source mode derivation.

**Team Task Create (when `TEAM_DOCS_PATH` is set and user is starting a new task):**
- `git pull --rebase` on docs repo.
- If `TASK_TEMPLATE.md` exists → copy to `active-tasks/<repo>/<task-id>-<slug>.md`. If not → use embedded fallback in `refs/team-docs.md § Fallback template`.
- Ask user for GitHub handle if not derivable from git config.
- Update `active-tasks/<repo>/README.md` (+1 row) and `active-tasks/README.md` (count++).
- **Immediately write pending lock entries** (`⏳ planning`) for all files likely to be touched. This closes the race window between Stage -1 conflict-check and Stage 3 — do not defer.

**Task History Relevance Gate:**
- Default: no full history read for a new unrelated task.
- `task_continuity: continuation` when user references previous work, existing `task_id`, ADR, current branch/PR, or in-progress session.
- `task_continuity: new` when task is clearly independent.
- `task_continuity: unknown` when files overlap previous task metadata but relationship is unclear.
- For `continuation` or `unknown`: scan metadata only first; full history read only if `explicit_continuation=true` or overlap is medium/high.

Intake must record: Jira/Figma/Confluence links, source mode (A/B/C), `task_continuity`, `history_scan.mode`, `preliminary_mode`.

### Stage 1 — Discovery

Read `.project-orchestration/reports/preflight.md`, `graphify-out/GRAPH_REPORT.md` if present, docs in `docs/ai/inputs/` if present, and source material.

If `task_continuity = full`, read matched task history: requirements, decisions, design, execution report.

Derive `change_type` (initial estimate). Record in `context-pack.json`.

If `graph_impact ≥ medium`: activate **Gradle Module Impact Analyzer** in parallel with source readers. Populate `context-pack.json → module_impact_chain`.

**Finalize workflow mode at end of Stage 1:** Compute final scores → `workflow_mode`. Apply override rules. Write `workflow_mode`, `complexity_score`, `risk_score`, `mode_reasons` to `context-pack.json` and `session.json`. Stage 1.5 reads this value; it does not re-compute.

→ **Load `refs/stage-contracts.md` § Stage 1** for typed input/output contract.

### Stage 1.5 — Clarification & Synthesis

→ **Load `refs/clarification-workflow.md`** for sequence, exit criteria, and clarity scoring.

Run Stage 1.5 if **ANY** of the following are true:
- [ ] Task brief is < 50 words and has no linked ticket or design source
- [ ] No acceptance criteria are explicitly stated
- [ ] Graph exists and shows affected components not mentioned in sources
- [ ] API, state handling, or error behavior is unspecified

If `workflow_mode = fast` → AUTO-SKIP (write to `skip-log.json`). Skip or minimize when docs are detailed, acceptance criteria are testable, no conflicts exist, and graph shows a clean isolated change surface.

Source modes:
- **Mode A** — Jira/Figma/Confluence present: full clarification with source readers and analysis workers.
- **Mode B** — docs-only: Doc Reader + Graph Impact Reader + Ambiguity Detector + Missing-info Detector.
- **Mode C** — no sources: if task is clearly bounded (single-file refactor, rename, documented bug with repro steps) treat as Mode B; otherwise block and ask for a task brief.

### Stage 2 — Requirements

AI DevKit writes canonical requirements from synthesized context. Stop for human review.

→ **Load `refs/contracts-and-artifacts.md`** for `requirements/<task>.md` schema and Gate D criteria.

Requirements must include: artifact version header, Affected Areas checklist, facts and assumptions separated, decision triggers observed, acceptance criteria and required evidence.

### Stage 2.5 — Decision Gate / ADR-lite

AI DevKit decides whether an ADR-lite is required before design. **ADR trigger check is MANDATORY in all modes.**

Create an ADR-lite when the task touches any of: module boundary, navigation graph, public API or internal contract, persistence schema, DI graph, Gradle/AGP/Kotlin version, Compose/View migration, state ownership, background work, permissions, billing, auth, notifications, or test strategy with broad impact.

If ADR-lite is required: create `docs/ai/tasks/{task_id}/decisions/ADR-NNNN-<slug>.md`, set status `Proposed`, stop for human approval before Stage 3. If `TEAM_DOCS_PATH` is set, also cross-link this ADR in the team task file `## Decisions`.

**"Affects other repos" heuristic** (triggers team task file cross-repo write): decision touches `commonLibrary/*`, any Gradle shared module, published APIs that other repos import, or root build config affecting the whole monorepo.

If ADR-lite not required: record `adr_required: false` and reason in `session.json` and `execution.md`.

→ **Load `refs/contracts-and-artifacts.md`** for ADR-lite schema and Decision Ownership matrix.

### Stage 3 — Design split + Executable Plan

AI DevKit writes design/planning docs. Android skills write Android memo. No product-code changes. **Fast mode:** skip design doc entirely; produce `implementation-plan.md` only (≤ 5 tasks). Write AUTO-SKIP for design doc to `skip-log.json`.

→ **Load `refs/playbooks.md`** to select the correct workflow for the task type.

**Executable implementation plan (MANDATORY):** `docs/ai/tasks/{task_id}/planning/implementation-plan.md` — one task per acceptance criterion, each 2–5 minutes of work. Every task contains: exact file path(s), exact test command with expected output, RED step, GREEN step, refactor note, commit message. No placeholders.

TDD mapping per `change_type`:

| change_type | Test-first target |
|---|---|
| `logic_change` | Unit test for ViewModel / UseCase / Repository |
| `ui_change` | Compose semantics test or screenshot comparison |
| `database_change` | Room `MigrationTest` |
| `network_change` | Mock server / contract test |
| `dependency_change` | Build success + license check |
| `architecture_change` | Module boundary compile test |
| `test_change` | (tests are the artifact — verify they fail for the right reason) |
| `config_change` | Build variant success + manifest diff |

When `code_owner` confirmed: generate `handoff.md`, update `session.json → assignee`, `branch`, update `status.json`.

If `TEAM_DOCS_PATH` set: upgrade pending lock entries from `⏳ planning` → `🔒 locked` with the final file list from `implementation-plan.md`. Remove any pending entries for files that won't be touched.

### Stage 4 — Implementation Lock with Android TDD

Exactly one code owner edits code. All other lanes are advisory only.

**Iron law:** No product-code change without a failing test first, or an approved TDD exemption (CONFIRM-SKIP per compliance matrix). **If code is written before a failing test exists: delete it. No exceptions.**

**Per-task loop** (repeat for every task in `implementation-plan.md`):

1. Read the exact task. Do not batch multiple tasks.
2. Write the smallest failing test for one acceptance criterion.
3. Run the test → record RED output to `evidence/red-<task-id>.txt`. Verify failure is for the right reason.
4. Write minimum Android code to make the test pass. YAGNI strictly enforced.
5. Run the same test → record GREEN output to `evidence/green-<task-id>.txt`. All affected module tests must also pass.
6. Run `./gradlew :<module>:test` for modules in `module_impact_chain.test_scope_modules`.
7. Refactor only while tests remain green. No new behavior.
8. Commit: `git commit -m "<type>(<scope>): <what and why>"`.
9. Spec-compliance review ✅ → code-quality (Karpathy) review ✅ → next task.

**Blocked states:** Record `BLOCKED: <reason>` in `session.json → blocker`, update `handoff.md`, stop and report. Do not retry the same approach without a change.

On interrupt: update `handoff.md` and `status.json` before stopping.

### Stage 5 — Verify

Android CLI gathers runtime evidence. Graphify updates if `graph_impact ≥ medium`.

Read `context-pack.json → change_type`. Look up required evidence from the Evidence Gate Matrix (`refs/contracts-and-artifacts.md`). Run all required items. Gate F is not satisfied until all required items are present.

Scope build commands to `module_impact_chain.build_order` if present.

→ **Load `refs/stage-contracts.md` § Stage 5** for typed input/output contract.

### Stage 6 — QA gate

AI DevKit + Karpathy review diff, evidence, graph update, acceptance coverage, and scope discipline.

### Stage 7 — Docs / Decision Finalization

AI DevKit finalizes governance artifacts after QA:
- Update ADR-lite from `Proposed` to `Accepted`, `Deferred`, or `Superseded`.
- Update `execution.md` with Task Changelog.
- Run drift checks for skill refs/templates/version consistency.
- Record any missing evidence as a blocker instead of marking success.
- Update `status.json` entry to `stage_status: complete`.

**Team Task Archive (when `TEAM_DOCS_PATH` is set):**
- `git pull --rebase` on docs repo.
- Update team task file status → `✅ done`.
- Create `archive/YYYY-MM/` directory if it doesn't exist.
- Move `active-tasks/<repo>/<task-id>-<slug>.md` → `archive/YYYY-MM/<repo>-<task-id>-<slug>.md`.
- Remove row from `active-tasks/<repo>/README.md`. Decrement count in global README. Remove lock entries owned by this task from Cross-repo Conflicts.

---

## Provisioning modes

| Mode | Meaning | May install/update? |
|---|---|---|
| `audit` | Check readiness only | No |
| `bootstrap` | Install missing approved tools and initialize missing project setup | Yes, missing only |
| `update` | Update approved installed tools and reconcile project setup | Yes |
| `refresh-graph` | Build/update Graphify output | Graph only |
| `force-reinstall` | Clean reinstall/reset when explicitly requested | Yes |

If unsure, choose `audit`.

---

## Tool action rules

→ **Load `refs/provisioning-preflight.md`** for full per-tool decision tables and safety rules.

### AI DevKit
- If CLI missing in `audit`, report missing. If `.ai-devkit.json` missing and setup requested, run `ai-devkit init`. If exists and update requested, prefer `ai-devkit install`.

### Android CLI
- If CLI missing in `audit`, report missing. If update requested, run `android update`. If missing when verification requires it, block runtime verification.

### Android skills
- Run `android skills list --long` before deciding which skills are available. Use `android skills find "<keyword>"` for task-specific discovery. Use `android skills add --skill=<skill-name>` only when name is confirmed.

### Graphify
- If `graphify-out/` exists, read it in Discovery. Build only in `bootstrap` or `refresh-graph`. Update in Verify when `graph_impact` is `medium` or `high`. Never hand-edit `graphify-out/**`.

### Karpathy
- Check whether guidelines are installed. If missing in `audit`, record the gap. Apply principles even without the plugin; record how gate was applied. Do not overwrite existing `CLAUDE.md` unless explicitly requested.

### Serena
- Check `uv` + `uvx serena` at Stage -1 (non-blocking). If missing: record `serena: not-configured`; never block Stage 0.
- Never call mutation tools: `rename_symbol`, `replace_symbol_body`, `insert_*`, `safe_delete_symbol`, or any `jet_brains_*` tool.
- → See `refs/sub-agents.md § Serena` for full activation matrix and per-stage conditions.

---

## Waiting rules

The parent orchestrator must wait:
1. Before Stage 0: wait for Stage -1 result (including team docs conflict check when active).
2. Before Requirements: wait for required Clarification outputs if any trigger fires.
3. Before Design: wait for human approval of requirements.
4. Before Design: wait for approved or explicitly deferred ADR-lite when Stage 2.5 requires one.
5. Before Implementation: wait for approved requirements, decision gate result, design doc, executable `implementation-plan.md`, Android memo if Android-specific, and chosen single code owner with branch set.
6. **Gate E.5 — Test-first ready (before each task in Stage 4):** wait for failing test written + RED evidence recorded. Per-task, not per-stage.
7. Before Close: wait for runtime evidence, graph update if needed, spec-compliance ✅, Karpathy diff review ✅, acceptance coverage check, and Stage 7 finalization.

---

## Directory layout

```text
.project-orchestration/                       ← gitignored
├── status.json                               ← GLOBAL: project-level task index (all tasks)
├── memory/
│   └── tooling-cache.json                    ← GLOBAL: Stage -1 cache
├── reports/
│   └── preflight.md                          ← GLOBAL: Stage -1 result
└── tasks/
    └── {task_id}/                            ← e.g. ANDROID-42 | add-login-flow
        ├── session.json                      ← task state + stage compliance log
        ├── skip-log.json                     ← append-only audit of every skip/bypass
        ├── memory/
        │   └── graph-stamp.json
        ├── reports/
        │   └── execution.md                  ← Stage 5-6 evidence manifest + Gate log
        └── evidence/
            ├── logs/
            └── screenshots/

docs/ai/
├── inputs/                                   ← GLOBAL: human-provided, never overwritten
├── decisions/
│   └── 0000-template.md                      ← GLOBAL ADR-lite template
└── tasks/
    └── {task_id}/
        ├── discovery/
        ├── clarification/
        │   ├── context-pack.json
        │   └── clarification-brief.md
        ├── requirements/
        ├── decisions/
        ├── design/
        ├── planning/
        ├── testing/
        ├── android-memo/
        └── handoff.md                        ← generated at Stage 3; updated on interrupt

graphify-out/
.skills/
.ai-devkit.json
.agent-auth.yaml                              ← gitignored; auto-created; contains all tokens
```

```text
# When TEAM_DOCS_PATH is defined in project CLAUDE.md:
<TEAM_DOCS_PATH>/                              ← e.g. ~/dev/vulcan-android-docs
├── active-tasks/
│   ├── README.md                              ← global board (read at Stage -1)
│   ├── TASK_TEMPLATE.md                       ← template for new task files
│   └── <repo>/
│       ├── README.md                          ← per-repo board (read at Stage -1)
│       └── <task-id>-<slug>.md                ← task file (owned by Stage 0)
├── ADRs/                                      ← optional: team-level ADRs (cross-repo)
├── contracts/                                 ← optional: shared interfaces
└── archive/YYYY-MM/                           ← done tasks moved here at Stage 7
```

**Team docs does NOT replace `docs/ai/decisions/` and `.project-orchestration/` in the code repo** — those remain for per-repo artifacts. Team docs is the shared coordination layer: file locks, cross-repo decisions, and task visibility across the team.

**Task isolation:** Write all task artifacts under `.project-orchestration/tasks/{task_id}/` and `docs/ai/tasks/{task_id}/`. Never read or overwrite another task's directory.

---

## Minimal operating algorithm

1. **Auth init** — check `.agent-auth.yaml`; auto-create if missing (`refs/auth-bootstrap.md` Step 1). Cannot be skipped.
2. **Team docs check** — if `TEAM_DOCS_PATH` is set: `git pull --rebase` docs repo; read global + per-repo boards; HARD STOP on file conflict.
3. **Cache + resume check** — read `tooling-cache.json`; if valid → AUTO-SKIP Stage -1 (write skip-log). Scan `tasks/` for `stage_status: in_progress` → offer resume via `refs/stage-contracts.md`. Load `refs/compliance-policy.md` before any skip.
4. **Tooling Preflight** — run `bash templates/tooling-preflight.sh --json` → `preflight.json`; run without flag → `preflight.md`; write `tooling-cache.json`. Read `preflight.json → ready_for_stage_0` for the gate.
5. **Intake** — collect links; derive source mode (A/B/C); resolve credentials; derive `task_id`; write `session.json`. If team docs active: create task file + write pending lock entries immediately.
6. **Discovery** — read Graphify; activate source readers in parallel; auto-follow Jira attachments (1 level). Derive `change_type` (initial). Activate Gradle Module Impact Analyzer if `graph_impact ≥ medium`. Finalize `workflow_mode` at end of Stage 1.
7. **Clarification** (Stage 1.5) — if fast mode: AUTO-SKIP. Otherwise: if any trigger fires, run workers in parallel; parent synthesizes context-pack + brief.
8. **Requirements → Decision Gate** — AI DevKit writes canonical requirements; human approves; Stage 2.5 trigger check (MANDATORY); create ADR if required, stop for approval. Cross-link ADR in team task file if team docs active.
9. **Design + Implementation** — Stage 3: plan + `implementation-plan.md` (no placeholders); code owner + branch confirmed; handoff.md generated; team lock entries upgraded to `🔒`. Stage 4: per-task TDD loop per `implementation-plan.md`.
10. **Verify → Close** — Evidence Gate Matrix determines required evidence; Android CLI runs it; Graphify updates if `graph_impact ≥ medium`; QA gate; Stage 7 finalization + ADR status update + team task archive.

---

## Final operating principle

> **Audit first. Read the map. Read the task. Clarify before planning. Approve before coding. Parallelize analysis, not authority.**
