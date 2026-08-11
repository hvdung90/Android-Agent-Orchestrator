---
name: android-agent-orchestrator
description: Use when starting, planning, analyzing, or implementing any Android task — new feature, bug fix, refactor, migration, AGP upgrade, architecture review, team task tracking, or repo setup. Use when user says start task, new feature, fix bug, analyze repo, migrate, upgrade, implement, review architecture, team task, or set up agents for an Android project.
license: MIT
metadata:
  version: 6.1.2
  category: orchestration
  lanes:
    - orchestrator
    - android-skills
    - android-cli
    - graphify
    - karpathy
  workers:
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
    - refs/android-cli-compatibility.md
---

# Android Agent Orchestrator v6.1.1

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
- `TEAM_DOCS_PATH` is set in CLAUDE.md but the path cannot be resolved.

---

## TL;DR

**Audit first. Read the map. Clarify before planning. Approve before coding. One code owner. Evidence closes the task.**

- Stage -1: auth + tooling + optional team `locks.json` conflict check.
- Stages 0–3: intake, discovery, requirements, ADR trigger, executable plan.
- Stage 4: TDD implementation by one owner.
- Stages 5–7: evidence, QA, finalization.
- Stage 8: optional retro; never blocks close.

---

## Workflow Modes

Mode is derived at Stage 0 and finalized at the end of Stage 1. Human override is allowed and must be logged in `session.json`.

| Mode | Use when | Stage sequence | Artifact depth |
|---|---|---|---|
| **micro** | Single file, additive-only, no shared state, trivially testable | -1 → 0 → 1(inline) → 2(inline) → 2.5-lite → 3-micro → 4 → 5(micro) → 6(lite) → 7(lite) | Inline requirements/context; no discovery/requirements/design files; `implementation-plan.md` still mandatory with exactly 1 task |
| **fast** | Single-file bug fix, isolated logic fix, ≤ 2 files, no architecture impact | -1 → 0 → 1 → 2(mini) → 2.5-lite → 3-lite → 4 → 5(lite) → 6(lite) → 7(lite) | Requirements ≤ 40 lines, 3-lite: plan + code_owner + branch only, lite verify |
| **standard** | Normal Android feature, multi-file, single module, clear requirements | -1 → 0 → 1 → [1.5] → 2 → [2.5] → 3 → 4 → 5 → 6 → 7 | Requirements ≤ 120 lines, design ≤ 180 lines |
| **governed** | Large feature, migration, multi-module, Jira + Figma, any ADR trigger | Full -1 → 7 | No restrictions |

_Stage suffix legend: `(inline)` = artifact inlined into `session.json` instead of a separate file; `(micro)`/`(lite)`/`(mini)` = reduced artifact depth. Full definitions: `refs/contracts-and-artifacts.md § Artifact budget`._

Never skipped in any mode: auth init, team docs lock check when active, human requirements approval, ADR trigger check, Gate E.5 RED evidence, Evidence Gate Matrix, Karpathy diff review, `session.json`, `status.json`, and applicable finalization checks. Micro/fast reduce artifact depth only.

**Override rules (priority order):**
1. Any ADR trigger fires → minimum `governed`
2. Jira ticket + Figma link both present → minimum `standard`
3. Human explicitly requests a mode → use that mode; log `mode_override` in `session.json`
4. Task brief is incomplete or ambiguous → minimum `standard`
5. Scope is ambiguous between `micro` and `fast` → minimum `fast` (never auto-select `micro` on an ambiguous read)
6. Otherwise → use computed mode from scores

Scoring, skip rules, and artifact budgets live in `refs/contracts-and-artifacts.md` and `refs/compliance-policy.md`.

---

## When to load refs

Load refs on demand; do not load all refs upfront. Highest matching tier wins.

| Tier | Condition | Load |
|---|---|---|
| **LIGHT** | `workflow_mode` ∈ {micro, fast} AND `source_mode = C` (no external sources) AND `graph_impact = low` | mandatory stage refs only; no optional/deep refs |
| **MEDIUM** | `workflow_mode = standard` AND `source_mode = B` (docs-only) | + `refs/clarification-workflow.md` |
| **HEAVY** | `source_mode = A` (Jira/Figma links present) | + `refs/sub-agents.md` |
| **FULL** | `workflow_mode = governed` · migration · AGP · unfamiliar codebase · god nodes in path | + `refs/playbooks.md` + all refs |

Always load the referenced file before acting on any stage pointer below. Load `refs/compliance-policy.md` before any skip. Load `refs/contracts-and-artifacts.md` before writing any artifact.

---

## Hard rules

1. **Auth first.** `.agent-auth.yaml` is the single source of truth for all tokens. Never log token values. Never commit the file. Default provisioning mode is `audit`.
2. **One code owner at a time** — including sub-agents: only the designated code owner may write files or execute mutations; sub-agents are read-only observers.
3. **One canonical synthesizer.** Orchestrator owns requirements, synthesis, routing, and final go/no-go. No other lane produces canonical artifacts.
4. **No success without evidence.** Never invent commands. Android commands require discovery/cache or documented support; see `refs/android-cli-compatibility.md`.
5. **Stage order is law.** Stages run -1 → 0 → 1 → [1.5] → 2 → 2.5 → 3 → 4 → 5 → 6 → 7 → [8]. Any re-ordering or parallel shortcut not defined in this skill is a violation — stop and report. Stage 8 is bracketed because it is optional and non-blocking (see § Stage 8 — Retro); the task is already "done" at Stage 7.
6. **Read architecture map before touching code.** When `graphify-out/` exists, read it in Discovery. Understand-Anything → Graphify fallback for new repos.
7. **Karpathy applies to every code-touching step.** Apply principles even without the plugin installed; record how the gate was applied.
8. **Every skip is logged.** Write to `skip-log.json` on every auto-skip and confirm-skip. Load `refs/compliance-policy.md` before any skip decision. MANDATORY steps cannot be skipped.
9. **ADR ledger is global and immutable.** Never edit Accepted ADR text. When a decision changes, create a new superseding ADR.
10. **`handoff.md` when code owner changes or Stage 4 interrupts.** `branch` and `assignee` must be set before Stage 4 begins.
11. **Team docs first, lazy.** If `TEAM_DOCS_PATH` is set, read `active-tasks/locks.json` at Stage -1 `[both modes]`. Open markdown boards/tasks only on conflict, write, or explicit team status work. Load `refs/team-docs.md`. Check `TEAM_DOCS_MODE` (default: `coordination`) — it controls which write operations run.
12. **Task file follows the task `[coordination mode only]`.** When `TEAM_DOCS_PATH` is set and `TEAM_DOCS_MODE: coordination`, create/update the team task file at Stage 0. Write pending `locks.json` entries immediately with `status: planning` — do not defer the initial write to Stage 3 (Stage 3 upgrades `planning → locked`, it does not create them). Update on stage transitions. Archive at Stage 7. In `knowledge` mode, skip all of the above (no task files, no locks, no boards).
13. **Decisions leave a trace `[both modes]`.** Any decision affecting other repos → create ADR in `<TEAM_DOCS_PATH>/ADRs/` + append row to `active-tasks/README.md § Cross-repo Impacts`. In `coordination` mode, also write in team task file `## Decisions`.
14. **Warn on session end if docs have unpushed changes.** When `TEAM_DOCS_PATH` is set and the session ends or interrupts before Stage 7, run `git -C <TEAM_DOCS_PATH> status --porcelain`; warn if non-empty. Do not auto-push unless the stage contract requires it.

---

## Lanes

| Lane | Owns |
|---|---|
| Orchestrator | phase control, `docs/ai/**`, routing, synthesis, requirements, planning, final go/no-go |
| Android skills | platform guidance, migration notes, API pitfalls, compatibility advice |
| Android CLI | command discovery, runtime evidence, Android docs lookup, IDE/device commands |
| Graphify | graph build/query/update and architecture evidence |
| Karpathy | code-touching behavior and diff review |

---

## Sub-agents

Use sub-agents only as read-only/advisory workers. Load `refs/sub-agents.md` for worker catalog, activation rules, and YAML output contracts.

---

## Stage model

### Stage -1 — Tooling Preflight

Auth and readiness before any task work. Load `refs/auth-bootstrap.md`, `refs/provisioning-preflight.md`, `refs/android-cli-compatibility.md`, and `refs/stage-contracts.md § Stage -1`.

If `TEAM_DOCS_PATH` is set, load `refs/team-docs.md` and read only `active-tasks/locks.json` for conflict detection unless a conflict/write requires more.

### Stage 0 — Intake

Derive task id, source mode, task continuity, preliminary mode, and project/team policy. Load `refs/clarification-workflow.md § Source integrations` and `refs/stage-contracts.md § Stage 0`.

Source mode: A = Jira/Figma/Confluence links present; B = local docs only; C = no sources → **BLOCK here, ask human for task brief** before proceeding to Stage 1.

If team docs is active and `TEAM_DOCS_MODE: coordination` and this is a new task, write the team task file and planning locks via `refs/team-docs.md`. In `knowledge` mode, skip task file and lock writes.

### Stage 1 — Discovery

Read task sources, architecture map, relevant history metadata, and derive `change_type`, impact, and final `workflow_mode`. Load `refs/stage-contracts.md § Stage 1`; load `refs/sub-agents.md` when `graph_impact ≥ medium` or multi-module.

### Stage 1.5 — Clarification & Synthesis

Run only when clarification triggers fire; otherwise skip per policy. Load `refs/clarification-workflow.md` for triggers, worker sequence, Android docs lookup rules, and exit criteria.

### Stage 2 — Requirements

Write canonical requirements and stop for human approval. Load `refs/contracts-and-artifacts.md` for schema and Gate D.

### Stage 2.5 — Decision Gate / ADR-lite

ADR trigger check is mandatory in every mode. Load `refs/contracts-and-artifacts.md` for ADR schema, trigger handling, and Decision Ownership. Stop for human approval when ADR-lite is required.

### Stage 3 — Design split + Executable Plan

No product-code changes. Produce `design/design-doc.md` only when its trigger is met, plus required planning artifacts, command/version snapshot, Kotlin/Android rule checklist when applicable, `implementation-plan.md`, `handoff.md`, code owner, branch, and `commit_policy`. Load `refs/stage-contracts.md § Stage 3`, `refs/contracts-and-artifacts.md § design-doc / implementation-plan`, `refs/android-cli-compatibility.md`, and `refs/playbooks.md`.

If team docs is active and `TEAM_DOCS_MODE: coordination`, reconcile `locks.json` to the final file list. In `knowledge` mode, skip this step.

### Stage 4 — Implementation Lock with Android TDD

Single code owner. Gate E.5 RED evidence is mandatory per task before product code. Load `refs/stage-contracts.md § Stage 4`, `refs/contracts-and-artifacts.md § Gate E.5`, `refs/compliance-policy.md` for TDD exemptions, and `refs/android-cli-compatibility.md` before Android Studio commands.

### Stage 5 — Verify

Run Evidence Gate Matrix items for `change_type`; update Graphify when `graph_impact ≥ medium`. Load `refs/stage-contracts.md § Stage 5`, `refs/contracts-and-artifacts.md § Evidence Gate Matrix`, and `refs/android-cli-compatibility.md` for command support/fallbacks.

### Stage 6 — QA gate

Review diff, evidence, acceptance coverage, regression/security/performance closure, Kotlin/Android closure, and Karpathy/code-quality gate. Load `refs/stage-contracts.md § Stage 6`; use `refs/android-cli-compatibility.md` before static-analysis IDE commands.

### Stage 7 — Docs / Decision Finalization

No product-code changes. Finalize ADR status, Task Changelog, Impact Closure, Kotlin/Android Rule Closure, `task-summary.md`, Artifact Integrity Check, and applicable Skill Drift Check. Load `refs/stage-contracts.md § Stage 7`, `refs/contracts-and-artifacts.md § execution.md`, and `refs/compliance-policy.md`.

If team docs is active, remove task locks from `locks.json` and archive the task file via `refs/team-docs.md`.

### Stage 8 — Retro (optional, non-blocking)

Optional, non-blocking, never reopens a complete Stage 7 task. Append best-effort telemetry to `.project-orchestration/memory/retro-log.jsonl` using `refs/contracts-and-artifacts.md`.

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

Load `refs/provisioning-preflight.md` for provisioning decisions. Load `refs/android-cli-compatibility.md` before using Android/Android Studio commands. Android skills are discovered with `android skills list --long` and `android skills find "<keyword>"` before adding. Graphify is read in Discovery, built only in approved provisioning modes, and updated in Verify when impact requires it. Karpathy principles apply even when no plugin is installed.

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
│   ├── tooling-cache.json                    ← GLOBAL: Stage -1 cache
│   ├── graph-stamp.json                      ← GLOBAL: graph staleness (repo-level, one per repo — not per task)
│   └── retro-log.jsonl                       ← GLOBAL: append-only, one line per completed task (Stage 8, best-effort)
├── reports/
│   └── preflight.md                          ← GLOBAL: Stage -1 result
└── tasks/
    └── {task_id}/                            ← e.g. ANDROID-42 | add-login-flow
        ├── session.json                      ← task state + stage compliance log
        ├── skip-log.json                     ← append-only audit of every skip/bypass
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
.agent-auth.yaml                              ← gitignored; auto-created; contains all tokens
```

```text
# When TEAM_DOCS_PATH is defined in project CLAUDE.md:
<TEAM_DOCS_PATH>/                              ← e.g. ~/dev/vulcan-android-docs
├── active-tasks/
│   ├── locks.json                             ← conflict index (read at Stage -1)
│   ├── README.md                              ← global board (read/write only when needed)
│   ├── TASK_TEMPLATE.md                       ← template for new task files
│   └── <repo>/
│       ├── README.md                          ← per-repo board
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
2. **Team lock check** — if `TEAM_DOCS_PATH` is set, read `active-tasks/locks.json`; hard-stop or reclaim stale locks per `refs/team-docs.md`.
3. **Cache + resume check** — read `tooling-cache.json`; if valid, use cached tool/command state. Scan in-progress sessions and run `refs/stage-contracts.md § Integrity reconciliation` before trusting `stage_reached`.
4. **Tooling Preflight** — on cache miss, run `templates/tooling-preflight.sh` JSON + markdown, then write cache including Android command discovery.
5. **Intake + discovery** — derive source mode, task continuity, change type, impact, and finalized workflow mode.
6. **Clarify + approve** — clarify when triggers fire; write requirements; stop for human approval.
7. **Decision gate** — run ADR trigger check; create/approve/defer ADR when required.
8. **Plan + lock** — write executable plan, Android memo when applicable, handoff, code owner/branch, and team locks.
9. **Implement + verify** — per-task TDD loop, Evidence Gate Matrix, Android fallback rules, graph update, Karpathy/code-quality review.
10. **Finalize** — changelog/closures/summary, Artifact Integrity, applicable Skill Drift, status complete, team archive.

---

## Ref-load schedule (consolidated)

Every `→ Load refs/...` pointer scattered through the stages above, in one place. This table is the source of truth for *when*; the inline arrows at each stage are convenience pointers back here — if the two ever disagree, this table wins.

| When | Ref | Why |
|---|---|---|
| Stage -1, always | `refs/auth-bootstrap.md` | Step 1: initialize `.agent-auth.yaml` |
| Stage -1, always | `refs/provisioning-preflight.md` | decision tables, cache check, safety rules |
| Stage -1, Android command discovery | `refs/android-cli-compatibility.md` | command support cache and fallbacks |
| Stage -1, if `TEAM_DOCS_PATH` set | `refs/team-docs.md` | lazy `locks.json` conflict protocol |
| Stage 0 | `refs/clarification-workflow.md` § Source integrations | source mode (A/B/C) derivation |
| Stage 1 | `refs/stage-contracts.md` § Stage 1 | typed input/output contract |
| Stage 1, if `graph_impact ≥ medium` or multi-module | `refs/sub-agents.md` | Gradle Module Impact Analyzer |
| Stage 1.5, if not AUTO-SKIP | `refs/clarification-workflow.md` | full sequence, exit criteria, clarity scoring |
| Stage 2 | `refs/contracts-and-artifacts.md` | requirements schema, Gate D criteria |
| Stage 2.5 | `refs/contracts-and-artifacts.md` | ADR-lite schema, Decision Ownership matrix |
| Stage 3 | `refs/playbooks.md` | select correct workflow for task type |
| Stage 3/4/5/6 Android commands | `refs/android-cli-compatibility.md` | check cached support and choose fallback |
| Stage 5 | `refs/stage-contracts.md` § Stage 5 | typed input/output contract |
| Any resume of an interrupted task | `refs/stage-contracts.md` | resume rule + integrity reconciliation |
| Any stage-skip decision (auto or confirm) | `refs/compliance-policy.md` | tier definitions, confirmation protocol |
| Any artifact write | `refs/contracts-and-artifacts.md` | canonical schema for whatever is being written |
| Tool provisioning decisions (any stage) | `refs/provisioning-preflight.md` | per-tool decision tables |

---

## Final operating principle

> **Audit first. Read the map. Read the task. Clarify before planning. Approve before coding. Parallelize analysis, not authority.**
