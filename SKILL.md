---
name: android-agent-orchestrator
description: Meta-skill for Android projects coordinating auth bootstrap, provisioning preflight, AI DevKit, Android skills, Android CLI, Graphify, Karpathy, and Serena code analysis into one disciplined workflow. Single .agent-auth.yaml manages all tokens; just-in-time token check per tool.
license: MIT
metadata:
  version: 4.7.0
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
---

# Android Agent Orchestrator v4.7.0

## Activation

Load this skill when the user asks to **start, plan, analyze, or implement an Android task**.

Trigger phrases: `start task` · `new feature` · `fix bug` · `analyze repo` · `migrate` · `upgrade` · `set up agents` · `implement` · `review architecture`

Do not load this skill for non-Android projects or purely conversational questions.

---

## TL;DR

**Five-lane skeleton. Stage -1 Tooling Preflight + Auth Bootstrap. Single `.agent-auth.yaml` manages all tokens.**

- Stage -1 initializes the auth file, audits tool readiness, then proceeds to Intake.
- `.agent-auth.yaml` is the single source of truth for all tokens (Atlassian, Figma, GitHub). Tokens are requested just-in-time when a tool needs them.
- AI DevKit remains the conductor and the only owner of requirements, synthesis, routing, and final go/no-go.
- Android skills remain Android advisory specialists.
- Android CLI remains runtime verification and official Android skill management.
- Graphify remains the architecture map.
- Karpathy remains the code-touching quality gate.
- **Serena is the Code Analysis Worker** — symbol-level code retrieval, activated after Graphify identifies affected areas. Read-only in Discovery, advisory in Implementation. Never owns decisions or edits.
- **Gradle Module Impact Analyzer** derives `module_impact_chain` when `graph_impact ≥ medium` — maps architecture components to Gradle modules, produces `build_order` and `test_scope_modules` for Android CLI in Stage 5.
- Sub-agents are internal workers used during Discovery and Clarification. They do not become independent lanes and they never own final decisions or product-code edits.
- Jira Reader automatically tracks `linked_docs` and `linked_designs` (1 level deep).
- `change_type` is derived at Stage 1 and finalized at Stage 1.5 — Android CLI uses it to select required evidence from the Evidence Gate Matrix at Stage 5.
- Stage 2.5 Decision Gate decides whether an ADR-lite is required before design or implementation.
- Stage 7 finalizes decision records and task changelog after verification.

> **Auth first. Audit tools. Read the map. Analyze code surface. Clarify before planning. Approve before coding.**

---

## What changed in v4.7.0

**v4.7.0** — Decision governance layer for Android tasks.

Adds Stage 2.5 Decision Gate / ADR-lite before design, Stage 7 Docs/decision finalization after QA, `docs/ai/decisions/0000-template.md`, artifact version headers, affected-area checklist, decision ownership matrix, task changelog, drift checks, and AI-authored artifact rules.

## What changed in v4.5.0–v4.6.0

**v4.6.0** — Compliance Policy + Task-scoped Storage.

**Compliance Policy (`refs/compliance-policy.md`):** Three-tier stage compliance matrix (MANDATORY / AUTO-SKIP / CONFIRM-SKIP). Explicit confirmation protocol before any skip. Permanent list of never-bypassable rules. Audit trail via `skip-log.json` at every auto-skip and confirm-skip. Stage order violation detection with immediate stop.

**Task-scoped Storage:** All per-task artifacts moved under `.project-orchestration/tasks/{task_id}/` and `docs/ai/tasks/{task_id}/`. Global artifacts (tooling-cache, preflight) remain at root level. Prevents cross-task artifact collision; enables parallel task tracking.

---

**Pattern 1 — Module Impact Chain:** New `Gradle Module Impact Analyzer` worker in `refs/sub-agents.md`. Activated at Stage 1 when `graph_impact ≥ medium`. Maps architecture components → Gradle module boundaries, derives `build_order`, `test_scope_modules`, `api_surface_broken`. Output feeds `context-pack.json → module_impact_chain`. Android CLI uses `build_order` to scope build commands in Stage 5.

**Pattern 2 — Evidence Gate Matrix:** New matrix in `refs/contracts-and-artifacts.md`. `context-pack.json` gains `change_type` field (`ui_change | database_change | network_change | dependency_change | architecture_change | logic_change | test_change | config_change | multi`). Android CLI derives required and optional evidence from matrix at Stage 5. Gate F now enforces matrix compliance.

**Pattern 3 — Stage Output Contracts:** New `refs/stage-contracts.md`. Every stage now has typed `input_requires`, `output_produces`, `state_on_complete`, `state_on_interrupt`, and `resume_entry_point`. `session.json` schema extended with `change_type`, `module_impact_chain_scope`, `evidence_collected`, and `partial_outputs`.

---

## What changed in v4.2.x

**v4.2.0** — Stage -1 Tooling Preflight, provisioning modes (`audit`/`bootstrap`/`update`/`refresh-graph`/`force-reinstall`), Graphify freshness policy.

**v4.2.1** — README slim (human-facing only); SKILL.md explicit `→ Load refs/` per stage; Stage 1.5 binary trigger checklist; Mode C escape hatch; refs version headers.

**v4.2.2** — Source integrations: Jira/Figma/Confluence link-driven (no upfront setup required); source mode derivation table (A/B/C).

**v4.2.3** — `docs/FLOW.md`: complete ASCII flow diagram, all 10 use cases, worker matrix, Graphify map.

**v4.2.4** — Jira Reader auto-follow: automatically reads `linked_docs` and `linked_designs` (Confluence, Figma, Doc, Jira child — 1 level).

**v4.2.5** — `.gitignore`; `templates/agent-auth.example.yaml` (Level 1/2/3); auth check at Stage -1; credential resolution per project key prefix.

**v4.2.6** — `docs/FLOW.md` rewrite fully reflects v4.2.5.

**v4.2.7** — `refs/auth-bootstrap.md`: centralized auth management — Step 1 (auto-create file), Step 2 (just-in-time token check per tool), Step 3 (Level 1/2/3 resolve), Step 4 (save securely). MCP mapping table. Required auth per source reader.

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
Always load when writing artifacts: `refs/contracts-and-artifacts.md`.  
Always load when resuming an interrupted task: `refs/stage-contracts.md`.  
Always load when any stage skip or bypass is considered: `refs/compliance-policy.md`.  
Load when `graph_impact ≥ medium` or multi-module change detected: `refs/sub-agents.md` (Gradle Module Impact Analyzer).

---

## Hard rules

1. Run Stage -1 before Stage 0 for every non-trivial task.
2. Default to `audit`.
3. Do not install, update, reinstall, rebuild graph, or mutate global tooling unless the user's request allows it.
4. One code owner at a time.
5. One canonical synthesizer.
6. Sub-agents are read-only or advisory.
7. Do not skip Clarification when source material is weak.
8. No success without evidence.
9. Read Graphify before touching code when `graphify-out/` exists.
10. Stop after requirements, then stop again for ADR-lite approval when Stage 2.5 requires one.
11. No invented commands.
12. Karpathy applies to every code-touching step.
13. If sources disagree, record the conflict.
14. `.agent-auth.yaml` is the single source of truth for all tokens. Never log token values. Never commit the file.
15. Serena is read-only and advisory. Never call Serena code-mutation tools (`rename_symbol`, `replace_symbol_body`, `insert_*`, `safe_delete_symbol`). Code owner owns all edits.
16. **Compliance first.** Before skipping any stage or step, load `refs/compliance-policy.md` and apply the compliance matrix. MANDATORY steps cannot be skipped. AUTO-SKIP requires the stated condition to be true and must be written to `skip-log.json`. CONFIRM-SKIP requires explicit human confirmation — implicit agreement is not enough.
17. **Every skip is logged.** Write to `.project-orchestration/tasks/{task_id}/skip-log.json` on every auto-skip and confirm-skip. This log is never deleted.
18. **Task isolation.** Write all task artifacts under `.project-orchestration/tasks/{task_id}/` and `docs/ai/tasks/{task_id}/`. Never read or overwrite another task's directory.
19. **Decision changes need ADR-lite.** If a task touches a required decision trigger, create a Proposed ADR in Stage 2.5 and stop for human approval before Stage 3.
20. **Stage order is law.** Stages run -1 → 0 → 1 → [1.5] → 2 → 2.5 → 3 → 4 → 5 → 6 → 7. Any re-ordering or parallel shortcut not defined in this skill is a violation — stop and report to human.

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

v4.2 does **not** add a sixth lane. Stage -1 is a stage.

---

## Sub-agents

→ **Load `refs/sub-agents.md`** for the full worker catalog with YAML output contracts.

Sub-agents are internal workers activated by the parent orchestrator during Discovery and Clarification. They are **read-only or advisory** — they never own final decisions or product-code edits.

| Category | Workers |
|---|---|
| Source readers | Jira Reader, Confluence Reader, Figma Reader, Doc Reader, Graph Impact Reader |
| **Module analysis** | **Gradle Module Impact Analyzer** — Gradle module boundary mapping; read-only; activated when `graph_impact ≥ medium` |
| Analysis workers | Ambiguity Detector, Conflict Detector, Missing-info Detector, State Extractor, Dependency Impact Analyzer |
| Advisory workers | Research Advisor, Android Advisor, QA Scenario Advisor, Rollout/Risk Advisor |
| **Code Analysis** | **Code Analysis Worker (Serena)** — symbol-level queries; read-only; agent-decided activation |
| Preflight | Tooling Preflight Auditor |

**Serena activation matrix (summary):**

| Stage | Condition | Serena tool | Decided by |
|---|---|---|---|
| 1 Discovery | graph_impact ≥ medium OR symbol named | `get_symbols_overview`, `find_symbol` | Agent |
| 1.5 Clarification | Interface in change path / surprising connection | `find_implementations`, `find_referencing_symbols` | Agent |
| 4 Implementation | Code owner needs usage context | `find_declaration` | Code owner request |
| 5 Verify | graph_impact ≥ medium AND kotlin-ls stable | `get_diagnostics_for_file` | Agent |
| 6 QA | Scope discipline check | `find_referencing_symbols` | Agent (optional) |
| JetBrains backend | Android Studio running | all above tools | Dev opt-in |

---

## Stage model

### Stage -1 — Tooling Preflight

Run before Intake.

→ **Load `refs/auth-bootstrap.md`** — run Step 1 (initialize auth file) at the start of Stage -1.
→ **Load `refs/provisioning-preflight.md`** for full decision tables, cache check, and safety rules.

**Cache check first:** Read `.project-orchestration/memory/tooling-cache.json`. If `valid_until` is in the future AND `graph_commit` matches `git rev-parse HEAD` → skip tool checks, use cached result, go directly to Stage 0.

**Otherwise run:** `bash templates/tooling-preflight.sh` — all checks run in parallel; output is the preflight report draft.

Determine:
- active provisioning mode,
- whether AI DevKit exists,
- whether `.ai-devkit.json` exists,
- whether Android CLI exists,
- whether Android skills can be listed/found/added,
- whether Graphify exists,
- whether `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` exist,
- whether graph must be built, updated, or only read,
- whether Karpathy guidelines exist as plugin, skill, or project instruction,
- what actions are allowed,
- what blockers prevent Stage 0.

Default mode is `audit`.

Deliverable:
- `.project-orchestration/reports/preflight.md`

### Stage 0 — Intake

Open the task, confirm source availability, determine whether external task/design sources exist, and consume Stage -1 findings.

→ **Load `refs/clarification-workflow.md` § Source integrations** for source mode derivation.

Run the **Task History Relevance Gate**:
- Default to **no full history read** for a new unrelated task.
- Set `task_continuity` to `continuation` when the user references previous work, an existing `task_id`, ADR, requirements/design/execution path, current branch/PR, or an in-progress session.
- Set `task_continuity` to `new` when the task is clearly independent and has no old-task reference.
- Set `task_continuity` to `unknown` when files/modules/screens overlap previous task metadata but the relationship is unclear.
- For `continuation` or `unknown`, scan metadata only first: `session.json`, requirements front matter, ADR front matter, and task titles. Do not read full old requirements/design/execution unless overlap is `medium` or `high`, or the user explicitly asks to continue/review old context.
- If overlap is ambiguous and may affect strategy or requirements, ask one concise clarification before reading full history.

Intake must record:
- Jira / Figma / Confluence links provided by developer, if any
- Source mode (A / B / C) derived from what was provided
- `task_continuity` (`new | continuation | unknown`)
- `history_scan` decision (`skipped | metadata-only | full | ask_human`)

### Stage 1 — Discovery

Read `.project-orchestration/reports/preflight.md`, `graphify-out/GRAPH_REPORT.md` if present, docs in `docs/ai/inputs/` if present, and source material.

If Task History Relevance Gate decided `full`, also read the matched task history before synthesis:
- `docs/ai/tasks/{matched_task_id}/requirements/*.md`
- `docs/ai/tasks/{matched_task_id}/decisions/ADR-*.md`
- `docs/ai/tasks/{matched_task_id}/design/*.md`
- `.project-orchestration/tasks/{matched_task_id}/reports/execution.md`

Derive `change_type` (initial estimate) from source material and Graphify output — record in `context-pack.json`.

If `graph_impact ≥ medium`: activate **Gradle Module Impact Analyzer** in parallel with other source readers. Output populates `context-pack.json → module_impact_chain`. Write `module_impact_chain_scope` to `session.json`.

→ **Load `refs/stage-contracts.md` § Stage 1** for typed input/output contract and interrupt state.

### Stage 1.5 — Clarification & Synthesis

→ **Load `refs/clarification-workflow.md`** for sequence, exit criteria, and clarity scoring.

Run Stage 1.5 if **ANY** of the following are true:
- [ ] Task brief is < 50 words and has no linked ticket or design source
- [ ] No acceptance criteria are explicitly stated
- [ ] Two or more sources contradict each other on behavior or scope
- [ ] Graph exists and shows affected components not mentioned in sources
- [ ] Graph shows god nodes in the change path
- [ ] API, state handling, or error behavior is unspecified

Skip or minimize when: docs are detailed, acceptance criteria are testable, no conflicts exist, and graph shows a clean isolated change surface.

Source modes:
- **Mode A** — Jira/Figma/Confluence present: run full clarification with source readers and analysis workers.
- **Mode B** — docs-only (`docs/ai/inputs/`): run Doc Reader + Graph Impact Reader + Ambiguity Detector + Missing-info Detector.
- **Mode C** — no sources:
  - If task is clearly bounded (single-file refactor, rename, or documented bug with reproduction steps): treat as Mode B using the user's message as the sole doc.
  - Otherwise: block and ask the human for a task brief before proceeding.

### Stage 2 — Requirements

AI DevKit writes canonical requirements from synthesized context. Stop for human review.

→ **Load `refs/contracts-and-artifacts.md`** for `requirements/<task>.md` schema and Gate D criteria.

Requirements must include:
- artifact version header,
- Affected Areas checklist,
- facts and assumptions separated,
- decision triggers observed,
- acceptance criteria and required evidence.

### Stage 2.5 — Decision Gate / ADR-lite

AI DevKit decides whether an ADR-lite is required before design.

Create an ADR-lite when the task touches any of:
- module boundary,
- navigation graph,
- public API or internal contract,
- persistence schema,
- DI graph,
- Gradle / AGP / Kotlin version,
- Compose / View migration,
- state ownership,
- background work, permissions, billing, auth, or notifications,
- test strategy with broad impact.

If ADR-lite is required:
- create `docs/ai/tasks/{task_id}/decisions/ADR-NNNN-<slug>.md` from `docs/ai/decisions/0000-template.md`,
- set status to `Proposed`,
- record owner, task, alternatives, consequences, validation evidence plan, and related files/modules,
- stop for human approval before Stage 3.

If ADR-lite is not required, record `adr_required: false` and the reason in `session.json` and `execution.md`.

→ **Load `refs/contracts-and-artifacts.md`** for the ADR-lite schema and Decision Ownership matrix.

### Stage 3 — Design split

AI DevKit writes design/planning docs. Android skills write Android memo. No product-code changes.

→ **Load `refs/playbooks.md`** to select the correct workflow for the task type.

### Stage 4 — Implementation lock

Exactly one code owner edits code.

### Stage 5 — Verify

Android CLI gathers runtime evidence. Graphify runs update after implementation if graph exists.

**Evidence Gate Matrix:** Read `context-pack.json → change_type`. Look up required and optional evidence from the matrix in `refs/contracts-and-artifacts.md § Evidence Gate Matrix`. Run all required items. Gate F is not satisfied until all required items are present.

**Module-scoped builds:** If `module_impact_chain` is present, scope build commands to `module_impact_chain.build_order` rather than full project build.

**Graphify skip condition:** If `context-pack.json → graph_impact` is `low`, skip `/graphify . --update`. Record skip reason in execution report. Run update only when `graph_impact` is `medium` or `high`.

→ **Load `refs/stage-contracts.md` § Stage 5** for typed input/output contract and interrupt state.

### Stage 6 — QA gate

AI DevKit + Karpathy review diff, evidence, graph update, acceptance coverage, and scope discipline.

### Stage 7 — Docs / Decision Finalization

AI DevKit finalizes governance artifacts after QA:
- update ADR-lite from `Proposed` to `Accepted`, `Deferred`, or `Superseded`,
- update `.project-orchestration/tasks/{task_id}/reports/execution.md` with Task Changelog,
- run drift checks for skill refs/templates/version consistency,
- record any missing evidence as a blocker instead of marking success.

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

### AI DevKit
- If CLI missing in `audit`, report missing.
- If `.ai-devkit.json` missing and setup requested, run `ai-devkit init`.
- If `.ai-devkit.json` exists and setup/update requested, prefer `ai-devkit install`.
- Use `npx ai-devkit@latest ...` only as fallback or when global install is not desired.

### Android CLI
- If CLI missing in `audit`, report missing.
- If update requested, run `android update`.
- If agent setup requested, run `android init`.
- If verification requires Android CLI and it is missing, block runtime verification.

### Android skills
- Run `android skills list --long` before deciding which Android skills are available.
- Use `android skills find "<keyword>"` for task-specific discovery.
- Use `android skills add --skill=<skill-name>` only when the skill name is confirmed.
- Use `android skills add --all` only when explicitly requested.

### Graphify
- If `graphify-out/` exists, read it in Discovery.
- If graph is missing, build only in `bootstrap` or `refresh-graph`.
- If implementation changed code and graph exists, update in Verify.
- Never hand-edit `graphify-out/**`.

### Karpathy
- Check whether guidelines are installed or present.
- If missing in `audit`, record the gap.
- If code is touched, apply the principles even if the plugin is not installed, and record how the gate was applied.
- Do not overwrite existing `CLAUDE.md` unless explicitly requested.

### Serena
- Check `uv` presence and `uvx serena` availability in Stage -1 (non-blocking).
- If missing: record `serena: not-configured`; never block Stage 0.
- If ready: activate Code Analysis Worker automatically per stage conditions.
- JetBrains backend is dev opt-in only — agent does not detect or start Android Studio.
- Kotlin LS diagnostics are disabled until dev confirms `kotlin_ls_stable: true`.
- Never call mutation tools: `rename_symbol`, `replace_symbol_body`, `insert_before_symbol`, `insert_after_symbol`, `safe_delete_symbol`, or any `jet_brains_*` refactoring tool.
- Serena outputs feed `context-pack.json → dependencies`, `facts`, and may upgrade `graph_impact`.
- Install command (bootstrap/update mode, if approved): `uv tool install oraios-serena`

---

## Waiting rules

The parent orchestrator must wait:
1. Before Stage 0: wait for Stage -1 result.
2. Before Requirements: wait for required Clarification outputs if any trigger fires.
3. Before Design: wait for human approval of requirements.
4. Before Design: wait for approved or explicitly deferred ADR-lite when Stage 2.5 requires one.
5. Before Implementation: wait for approved requirements, decision gate result, design doc, Android memo if Android-specific, and chosen single code owner.
6. Before Close: wait for runtime evidence, graph update if graph exists, Karpathy diff review, acceptance coverage check, and Stage 7 documentation finalization.

---

## Directory layout

```text
.project-orchestration/                       ← gitignored
├── memory/
│   └── tooling-cache.json                    ← GLOBAL: Stage -1 cache
├── reports/
│   └── preflight.md                          ← GLOBAL: Stage -1 result
└── tasks/
    └── {task_id}/                            ← e.g. ANDROID-42 | add-login-flow
        ├── session.json                      ← task state + stage compliance log
        ├── skip-log.json                     ← append-only audit of every skip/bypass
        ├── memory/
        │   └── graph-stamp.json              ← graph freshness for this task
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
        └── android-memo/

graphify-out/
.skills/
.ai-devkit.json
.agent-auth.yaml                              ← gitignored; auto-created; contains all tokens
```

---

## Minimal operating algorithm

1. **Auth init** — check `.agent-auth.yaml`; auto-create if missing (refs/auth-bootstrap.md Step 1). Cannot be skipped.
2. **Cache + resume check** — read `.project-orchestration/memory/tooling-cache.json`; if valid → AUTO-SKIP Stage -1 (write skip-log). Scan `.project-orchestration/tasks/` for any `session.json` with `stage_status: in_progress` → offer resume using `refs/stage-contracts.md → resume_entry_point`. Load `refs/compliance-policy.md` before any skip decision.
3. **Tooling Preflight** — run `bash templates/tooling-preflight.sh`; write `preflight.md` (global); write `tooling-cache.json` (global); init `tasks/{task_id}/session.json` and `tasks/{task_id}/skip-log.json`.
4. **Intake** — collect links; derive source mode (A/B/C); resolve credential set; derive `task_id` (Jira key → slug → date-hash); write/update `tasks/{task_id}/session.json` with `task_id`, `source_mode`.
5. **Determine ref tier** — LIGHT / MEDIUM / HEAVY / FULL; load only needed refs. Load `refs/stage-contracts.md` if resuming.
6. **Discovery** — read Graphify if present; activate source readers in parallel; auto-follow Jira attachments (1 level). Derive `change_type` (initial). Activate Gradle Module Impact Analyzer if `graph_impact ≥ medium`. Write `module_impact_chain` and `change_type` to context-pack.
7. **Token check** — just before each source reader, verify its token; prompt user if missing.
8. **Clarification** — if any trigger fires, run workers in parallel; finalize `change_type` and `module_impact_chain`; parent synthesizes context-pack + brief (sparse format).
9. **Requirements** — AI DevKit writes canonical doc with version header + Affected Areas; **stop for human approval**; update `session.json → requirements_approved: true`.
10. **Decision Gate** — decide whether ADR-lite is required; create Proposed ADR and stop for approval if required; write `adr_required`, `adr_status`, and `decision_record` to `session.json`.
11. **Design split** — AI DevKit + Android skills in parallel; select code owner; update `session.json → code_owner`.
12. **Implementation** — one owner edits code; capture `screenshot_before` if `change_type` includes `ui_change`; all other lanes advisory only.
13. **Verify** — derive required evidence from Evidence Gate Matrix using `change_type`; Android CLI runs required commands scoped to `module_impact_chain.build_order` if present; Graphify updates graph only if `graph_impact ≥ medium`. Write `evidence_collected` to `session.json`.
14. **QA gate** — AI DevKit + Karpathy review diff; verify Gate F (all required evidence present); keep code frozen.
15. **Docs / decision finalization** — update ADR status, Task Changelog, gate log, and drift check result; mark `session.json → stage_status: complete`.

---

## Final operating principle

> **Audit first. Read the map. Read the task. Clarify before planning. Approve before coding. Parallelize analysis, not authority.**
