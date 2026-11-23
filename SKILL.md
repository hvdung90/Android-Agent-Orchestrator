---
name: android-agent-orchestrator
description: Use when starting, planning, analyzing, or implementing any Android task — new feature, bug fix, refactor, migration, AGP upgrade, architecture review, team task tracking, or repo setup. Use when user says start task, new feature, fix bug, analyze repo, migrate, upgrade, implement, review architecture, team task, or set up agents for an Android project.
license: MIT
metadata:
  version: 6.2.0
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

# Android Agent Orchestrator v6.2.0

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
| **fast** | Isolated change with clear AC: UI/resource tweak, single-file bug fix, isolated logic fix, ≤ 2 files, no architecture impact, no escalation trigger | -1 → 0 → 1(inline) → 2(approval only) → 2.5(trigger check) → 3(owner + branch) → 4 → 5 → 6(diff review) → 7(summary) | Follow `workflows/fast.md`. Requirements, context and discovery inline in `session.json`; no requirements/design/plan files; the whole change is one TDD task |
| **standard** | Normal Android feature, multi-file, single module, clear requirements | -1 → 0 → 1 → [1.5] → 2 → [2.5] → 3 → 4 → 5 → 6 → 7 | Requirements ≤ 120 lines, design ≤ 180 lines |
| **governed** | Large feature, migration, multi-module, Jira + Figma, any ADR trigger | Full -1 → 7 | No restrictions |

_`micro` was folded into `fast` (ADR-0001). A legacy session with `workflow_mode: micro` is read as `fast` on resume._

_Stage suffix legend: `(inline)` = content written to `session.json` instead of a separate file. Full definitions: `refs/contracts-and-artifacts.md § Artifact budget`._

**What is never skipped — two layers (ADR-0001):**

- **Safety invariants** — every mode, no exception: no secret in context or output (`refs/auth-bootstrap.md`); one code owner; no PASS without evidence (Evidence Gate Matrix items for the `change_type`); ADR trigger check; Gate E.5 RED/GREEN, replaceable only by a row of `refs/compliance-policy.md § TDD exemption table`; Karpathy diff review; `session.json` state transitions; team-docs lock check when active.
- **Process gates** — required in `standard` / `governed`; `fast` drops them: separate requirements file, Stage 1.5 clarification, design doc, `implementation-plan.md`, full Stage 6 QA report, Stage 7 artifacts beyond `task-summary.md`, and `handoff.md` unless the code owner changes. Stage 2 approval is never dropped, but in `fast` it may come from Jira (§ FAST approval).

### FAST approval

A `fast` task needs no separate human requirements approval when **all** hold: the Jira issue's acceptance criteria are recorded with source and revision (`approval_source: jira:<KEY>@<updated-timestamp>`), every AC is testable, and no escalation trigger fires. Briefs without Jira (Mode B / C) get a one-line scope confirmation instead (`approval_source: scope_confirmation`). Any scope change after approval re-opens it. `standard` / `governed` always use `approval_source: human`.

### Escalation triggers

A `fast` task escalates to at least `standard` as soon as the task or its diff touches any of these (an ADR trigger still means `governed`):

- Billing / in-app purchase
- Auth / OAuth / account
- Security / privacy / user data
- Database schema or migration
- Public API / shared module contract
- Release config (signing, build variants, ProGuard/R8, versioning)
- Manifest permissions, exported components, intent filters
- More than one module
- Unclear or untestable acceptance criteria
- Ads SDK / mediation
- Paywall / subscription UI

Record the trigger in `session.json.mode_reasons` and in `skip-log.json` as a mode upgrade. Remote Config keys and analytics events alone do not escalate.

**Override rules (priority order):**
1. Any ADR trigger fires → minimum `governed`
2. Jira ticket + Figma link both present → minimum `standard`
3. Any § Escalation trigger fires → minimum `standard`
4. Human explicitly requests a mode → use that mode; log `mode_override` in `session.json` (a human may not request `fast` while an escalation trigger fires)
5. Task brief is incomplete or ambiguous → minimum `standard`
6. Otherwise → use computed mode from scores

Scoring, skip rules, and artifact budgets live in `refs/contracts-and-artifacts.md` and `refs/compliance-policy.md`.

---

## When to load refs

Load refs on demand; do not load all refs upfront. Rows are checked top to bottom; the **first** match wins, and the last row catches every remaining combination.

| Tier | Condition (first match wins) | Load |
|---|---|---|
| **FULL** | `workflow_mode = governed` · migration · AGP · unfamiliar codebase · god nodes in path | + `refs/playbooks.md` + all refs |
| **LIGHT** | `workflow_mode = fast` AND `graph_impact = low` | `workflows/fast.md` only; load a ref only where that file points to it |
| **HEAVY** | `source_mode = A` (Jira/Figma/Confluence links present) | + `refs/sub-agents.md` |
| **MEDIUM** | everything else — e.g. `standard` with B or C, `fast` with `graph_impact ≥ medium` | + `refs/clarification-workflow.md` |

**When it is decided.** Stage 0 records `preliminary_ref_tier` from `preliminary_mode` + `source_mode`, treating `graph_impact` as `low` (it is not known yet). Stage 1 records the final `ref_tier` from `workflow_mode` + `source_mode` + `graph_impact`. If the final tier is higher, load the added refs before the next stage; if it is lower, simply stop loading the optional refs.

Always load the referenced file before acting on any stage pointer below. Load `refs/compliance-policy.md` before any skip. Load `refs/contracts-and-artifacts.md` before writing any artifact.

---

## Hard rules

1. **Auth first.** `.agent-auth.yaml` is the single source of truth for all tokens. The agent never sees a token: users write tokens into the file themselves (never into chat); the agent never opens the file and never types a token into a command — it uses `templates/agent_auth.py` (`init` / `status` / `exec`). Never log token values. Never commit the file. Default provisioning mode is `audit`.
2. **One code owner at a time** — including sub-agents: only the designated code owner may write files or execute mutations; sub-agents are read-only observers.
3. **One canonical synthesizer.** Orchestrator owns requirements, synthesis, routing, and final go/no-go. No other lane produces canonical artifacts.
4. **No success without evidence.** Never invent commands. Android commands require discovery/cache or documented support; see `refs/android-cli-compatibility.md`.
5. **Stage order is law.** Stages run -1 → 0 → 1 → [1.5] → 2 → 2.5 → 3 → 4 → 5 → 6 → 7 → [8]. Any re-ordering or parallel shortcut not defined in this skill is a violation — stop and report. Stage 8 is bracketed because it is optional and non-blocking (see § Stage 8 — Retro); the task is already "done" at Stage 7.
6. **Read architecture map before touching code.** When `graphify-out/` exists, read it in Discovery. Understand-Anything → Graphify fallback for new repos.
7. **Karpathy applies to every code-touching step.** Apply principles even without the plugin installed; record how the gate was applied.
8. **Every skip is logged.** Write to `skip-log.json` on every auto-skip and confirm-skip. Load `refs/compliance-policy.md` before any skip decision. MANDATORY steps cannot be skipped.
9. **ADR ledger is global and immutable.** Never edit Accepted ADR text. When a decision changes, create a new superseding ADR.
10. **`handoff.md` when code owner changes or Stage 4 interrupts.** `branch` and `assignee` must be set before Stage 4 begins.
11. **Team docs first, lazy.** If `TEAM_DOCS_PATH` is set, read `active-tasks/<repo>/locks.json` at Stage -1 `[coordination mode only]` (knowledge mode reads only `active-tasks/shared/README.md` and ADRs). Open markdown boards/tasks only on conflict, write, or explicit team status work. Reads never change the docs checkout (`templates/team_docs_sync.py read`: fetch + read from the upstream ref; no upstream or failed fetch → lock data `unknown`). Writes go `begin` → write → `commit-push` with exactly the paths the step wrote (`refs/team-docs.md § Writes`). Load `refs/team-docs.md`. Check `TEAM_DOCS_MODE` (default: `coordination`) — it controls which write operations run.
12. **Task file follows the task `[coordination mode only]`.** When `TEAM_DOCS_PATH` is set and `TEAM_DOCS_MODE: coordination`, create/update the team task file at Stage 0. Write pending `locks.json` entries immediately with `status: planning` — do not defer the initial write to Stage 3 (Stage 3 upgrades `planning → locked`, it does not create them). Update on stage transitions. Archive at Stage 7. In `knowledge` mode, skip all of the above (no task files, no locks, no boards).
13. **Decisions leave a trace `[both modes]`.** Any decision affecting other repos → create ADR in `<TEAM_DOCS_PATH>/ADRs/` + append row to `active-tasks/shared/README.md § Cross-repo Impacts`. In `coordination` mode, also write in team task file `## Decisions`.
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

If `TEAM_DOCS_PATH` is set, load `refs/team-docs.md` and read only `active-tasks/<repo>/locks.json` (coordination mode) for conflict detection unless a conflict/write requires more.

### Stage 0 — Intake

Derive task id, source mode, task continuity, preliminary mode, and project/team policy. Load `refs/clarification-workflow.md § Source integrations` and `refs/stage-contracts.md § Stage 0`.

Source mode: A = Jira/Figma/Confluence links present; B = local docs in `docs/ai/inputs/`; C = no links and no local docs — **the user's message is the task brief**. In any mode, block before Stage 1 only when the brief cannot yield a goal and at least one testable acceptance criterion; then ask the human for exactly the missing parts.

If team docs is active and `TEAM_DOCS_MODE: coordination` and this is a new task, write the team task file and planning locks via `refs/team-docs.md`. In `knowledge` mode, skip task file and lock writes.

### Stage 1 — Discovery

Read task sources, architecture map, relevant history metadata, and derive `change_type`, impact, and final `workflow_mode`. Load `refs/stage-contracts.md § Stage 1`; load `refs/sub-agents.md` when `graph_impact ≥ medium` or multi-module.

### Stage 1.5 — Clarification & Synthesis

Run only when clarification triggers fire; otherwise skip per policy. Load `refs/clarification-workflow.md` for triggers, worker sequence, Android docs lookup rules, and exit criteria.

### Stage 2 — Requirements

Write canonical requirements and stop for human approval (`fast`: inline requirements in `session.json` and the approval source from § FAST approval; never skip the approval itself). Load `refs/contracts-and-artifacts.md` for schema and Gate D.

### Stage 2.5 — Decision Gate / ADR-lite

ADR trigger check is mandatory in every mode. Load `refs/contracts-and-artifacts.md` for ADR schema, trigger handling, and Decision Ownership. Stop for human approval when ADR-lite is required.

### Stage 3 — Design split + Executable Plan

No product-code changes. Produce `design/design-doc.md` only when its trigger is met, plus required planning artifacts, command/version snapshot, Kotlin/Android rule checklist when applicable, `implementation-plan.md`, `handoff.md`, code owner, branch, and `commit_policy`. In `fast`, Stage 3 only sets code owner, branch and `commit_policy` (no plan, design or handoff file; the whole change is one TDD task whose id is the `task_id`). Load `refs/stage-contracts.md § Stage 3`, `refs/contracts-and-artifacts.md § design-doc / implementation-plan`, `refs/android-cli-compatibility.md`, and `refs/playbooks.md`.

If team docs is active and `TEAM_DOCS_MODE: coordination`, reconcile `locks.json` to the final file list. In `knowledge` mode, skip this step.

### Stage 4 — Implementation Lock with Android TDD

Single code owner. Gate E.5 RED evidence is mandatory per task before product code unless a row of `refs/compliance-policy.md § TDD exemption table` applies (that table is the only definition of exemptions and their AUTO-SKIP/CONFIRM-SKIP tier). Load `refs/stage-contracts.md § Stage 4`, `refs/contracts-and-artifacts.md § Gate E.5`, `refs/compliance-policy.md`, and `refs/android-cli-compatibility.md` before Android Studio commands.

### Stage 5 — Verify

Run Evidence Gate Matrix items for `change_type`; update Graphify when `graph_impact ≥ medium`. Load `refs/stage-contracts.md § Stage 5`, `refs/contracts-and-artifacts.md § Evidence Gate Matrix`, and `refs/android-cli-compatibility.md` for command support/fallbacks.

### Stage 6 — QA gate

Review diff, evidence, acceptance coverage, regression/security/performance closure, Kotlin/Android closure, and Karpathy/code-quality gate. Load `refs/stage-contracts.md § Stage 6`; use `refs/android-cli-compatibility.md` before static-analysis IDE commands.

### Stage 7 — Docs / Decision Finalization

No product-code changes. Finalize ADR status, Task Changelog, Impact Closure, Kotlin/Android Rule Closure, `task-summary.md`, Artifact Integrity Check, and applicable Skill Drift Check. Load `refs/stage-contracts.md § Stage 7`, `refs/contracts-and-artifacts.md § execution.md`, and `refs/compliance-policy.md`.

If team docs is active, remove task locks from `locks.json` and archive the task file via `refs/team-docs.md`.

### Telemetry

Every task keeps running counters in `session.json.telemetry` — paths and counts only, never content: each skill-pack file or section opened (`policy_reads`, re-reads included), each stop for a human (`human_interrupts`), mode upgrades, the first product-code edit, stages per model tier. At Stage 7 close, append one line to `.project-orchestration/memory/retro-log.jsonl` (`refs/contracts-and-artifacts.md § retro-log.jsonl`); a failed write is noted and never blocks the close. `scripts/pilot_report.py` turns these lines into the ADR-0001 pilot comparison (`docs/pilot/README.md`).

### Stage 8 — Retro (optional, non-blocking)

Optional, non-blocking, never reopens a complete Stage 7 task. Reflection only: the telemetry record is written at Stage 7 (§ Telemetry).

---

## Model routing

Claude Code only (ADR-0001). Two capability tiers — never a pinned model ID or a versioned model name, because those go stale and the developer chooses which models are available:

- **`default`** — the session's model, as selected by the developer. Every stage in every mode runs here unless the table says otherwise, including all code writing.
- **`deep-reasoning`** — the most capable model the developer has enabled. Only for the `governed` reasoning stages below, and only at a stage boundary: switching models mid-stage loses context and cache. If it is unavailable or the developer declines, stay on `default` and note it in `session.json.mode_reasons`.

| Stage | Task | Tier | Step-up |
|---|---|---|---|
| -1 Preflight | bash checks, cache reads | `default` | — |
| 0 Intake | classify, derive source mode | `default` | — |
| 1 Discovery | read sources, derive impact + `workflow_mode` | `default` | — |
| 1.5 Clarification | identify ambiguity, synthesize context-pack | `default` | — |
| 2 Requirements | write canonical requirements + acceptance criteria | `default` | `deep-reasoning` when `governed` |
| 2.5 ADR Decision | architectural trade-off, cross-repo impact | `default` | `deep-reasoning` when `governed` |
| 3 Design + Plan | design-doc, implementation-plan.md | `default` | `deep-reasoning` when `governed` |
| 4 Implementation | code, Android TDD | `default` | — |
| 5 Verify | run tests, check evidence gates | `default` | — |
| 6 QA gate | Karpathy diff, acceptance coverage | `default` | — |
| 7 Finalize | ADR status, task summary, archive | `default` | — |
| 8 Retro | reflection, telemetry append | `default` | — |

`fast` never steps up. Read-only sub-agents run on `default` too. Correctness is decided by the evidence gates, never by which model wrote the code.

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
3. Before Design: wait for approval of requirements (`fast`: per § FAST approval — Jira-inherited or one-line scope confirmation).
4. Before Design: wait for approved or explicitly deferred ADR-lite when Stage 2.5 requires one.
5. Before Implementation: wait for approved requirements, decision gate result, design doc and executable `implementation-plan.md` when the mode requires them (`fast` requires neither), Android memo if Android-specific, and chosen single code owner with branch set.
6. **Gate E.5 — Test-first ready (before each task in Stage 4):** wait for failing test written + RED evidence recorded, or a recorded exemption from `refs/compliance-policy.md § TDD exemption table`. Per-task, not per-stage.
7. Before Close: wait for runtime evidence, graph update if needed, spec-compliance ✅, Karpathy diff review ✅, acceptance coverage check, and Stage 7 finalization.

---

## Directory layout

```text
.project-orchestration/                       ← gitignored
├── status.json                               ← GLOBAL: project-level task index (all tasks)
├── memory/
│   ├── tooling-cache.json                    ← GLOBAL: Stage -1 cache
│   ├── graph-stamp.json                      ← GLOBAL: graph staleness (repo-level, one per repo — not per task)
│   └── retro-log.jsonl                       ← GLOBAL: append-only telemetry, one line per finished task (Stage 7, best-effort)
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
│   ├── shared/
│   │   └── README.md                          ← Cross-repo Impacts (all repos read; lib writes)
│   ├── TASK_TEMPLATE.md                       ← template for new task files
│   └── <repo>/                                ← coordination zone (one per coordination-mode repo)
│       ├── README.md                          ← per-repo board (Overview + File Locks)
│       ├── locks.json                         ← conflict index (read at Stage -1, [C] only)
│       └── <task-id>-<slug>.md                ← task file (owned by Stage 0, [C] only)
├── ADRs/                                      ← cross-repo ADRs (all repos write/read)
├── contracts/                                 ← shared interfaces
└── archive/YYYY-MM/                           ← done tasks moved here at Stage 7 ([C] only)
```

**Team docs does NOT replace `docs/ai/decisions/` and `.project-orchestration/` in the code repo** — those remain for per-repo artifacts. Team docs is the shared coordination layer: file locks, cross-repo decisions, and task visibility across the team.

**Task isolation:** Write all task artifacts under `.project-orchestration/tasks/{task_id}/` and `docs/ai/tasks/{task_id}/`. Never read or overwrite another task's directory.

---

## Minimal operating algorithm

1. **Auth init** — check `.agent-auth.yaml`; auto-create if missing (`refs/auth-bootstrap.md` Step 1). Cannot be skipped.
2. **Team lock check** — if `TEAM_DOCS_PATH` is set and `TEAM_DOCS_MODE: coordination`, read `active-tasks/<repo>/locks.json`; hard-stop or reclaim stale locks per `refs/team-docs.md`.
3. **Cache + resume check** — read `tooling-cache.json`; if valid, use cached tool/command state. Scan in-progress sessions and run `refs/stage-contracts.md § Integrity reconciliation` before trusting `stage_reached`.
4. **Tooling Preflight** — on cache miss, run `templates/tooling-preflight.sh` JSON + markdown, then write cache including Android command discovery.
5. **Intake + discovery** — derive source mode, task continuity, change type, impact, and finalized workflow mode.
6. **Clarify + approve** — clarify when triggers fire; write requirements; stop for approval (`fast`: § FAST approval).
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
