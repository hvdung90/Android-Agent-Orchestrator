# Compliance Policy

_Skill version: 6.1.3 — update this when SKILL.md bumps a minor or major version._

The skill **must** follow every defined stage and gate in order. No stage may be skipped, condensed, or reordered without explicit confirmation. This file defines what requires confirmation, what is auto-allowed, what is permanently forbidden, and how every deviation is recorded.

---

## 1. Stage compliance matrix

Three tiers: **MANDATORY**, **AUTO-SKIP** (condition-gated, no human needed), **CONFIRM-SKIP** (human must say yes).

| Stage / Step | Compliance tier | Auto-skip condition |
|---|---|---|
| Stage -1 Tooling Preflight | **MANDATORY** unless cache valid | `tooling-cache.json valid_until > now AND graph_commit matches HEAD` |
| Stage -1 Auth init | **MANDATORY — never skippable** | — |
| Stage 0 Intake | **MANDATORY** | — |
| Stage 1 Discovery — source readers | **MANDATORY** per source_mode | — |
| Stage 1 Gradle Module Impact Analyzer | AUTO-SKIP when `graph_impact = low` | `graph_impact = low` confirmed in context-pack |
| Stage 1/1.5 Impact + Regression Plan | **MANDATORY for code-touching tasks** | — |
| Stage 1.5 Clarification | AUTO-SKIP when all exit conditions met | all 6 trigger conditions false AND docs detailed |
| Stage 2 Requirements write | **MANDATORY** | — |
| Stage 2 Human approval gate | **MANDATORY — never skippable** | — |
| Stage 2.5 Decision Gate | **MANDATORY** | — |
| Stage 2.5 duplicate-ADR check | **MANDATORY** — always runs before creating a new ADR | — |
| Stage 2.5 ADR-lite creation | AUTO-SKIP when no ADR trigger fires, or when an existing Accepted ADR already covers it | all ADR trigger conditions false, or covering ADR found |
| Stage 2.5 ADR-lite approval/deferral | **MANDATORY when ADR exists** | — |
| Stage 3 `design/design-doc.md` | **MANDATORY when trigger met** | required if `workflow_mode=governed OR graph_impact≥medium OR ADR-lite was triggered`; otherwise AUTO-SKIP with trigger reason |
| Stage 3 `implementation-plan.md` generation | **MANDATORY** — no placeholders (exact test command/method/path always required; exact code body required only in `governed` mode) | — |
| Stage 3 `handoff.md` generation | **MANDATORY when code_owner is confirmed** | — |
| Stage 3 Android memo | AUTO-SKIP when non-Android change | `change_type` ∉ {ui_change, database_change, network_change, architecture_change} AND no Android API mentioned |
| Stage 3 Android Advisor convention consult | AUTO-SKIP when `kotlin_convention_scope` is empty | no mapped Affected Area touched AND no Kotlin file in scope |
| Stage 1.5 Clarification (fast/micro mode) | AUTO-SKIP when `workflow_mode` ∈ {fast, micro} | scores finalized after Stage 1; write to skip-log |
| Stage 2.5 ADR trigger check (fast/micro mode) | **MANDATORY** | trigger evaluation always runs regardless of mode |
| Stage 2.5 ADR creation + approval (fast/micro mode) | AUTO-SKIP only if no ADR trigger fires | if any trigger fires → mode upgrades to governed; write to skip-log |
| Stage 3 design doc (no trigger) | AUTO-SKIP when `workflow_mode` ∈ {fast, micro}, or when standard mode has `graph_impact=low` and no ADR trigger | implementation-plan.md still MANDATORY (1 task entry for micro); write to skip-log |
| Stage 1 discovery note file (micro mode) | AUTO-SKIP when `workflow_mode = micro` | findings recorded inline in session.json instead; write to skip-log |
| Stage 1 context-pack.json file (micro mode) | AUTO-SKIP when `workflow_mode = micro` | content inlined into session.json["context"]; no skip-log entry needed (mode-defined form) |
| Stage 2 requirements doc file (micro mode) | AUTO-SKIP when `workflow_mode = micro` | ≤15-line inline summary substitutes; human approval gate itself still MANDATORY; write to skip-log |
| Stage 6 full QA report (fast/micro mode) | CONFIRM-SKIP when `workflow_mode` ∈ {fast, micro} | TDD evidence from Stage 4 substitutes; must ask human; Karpathy diff review + Gate G close remain MANDATORY |
| Stage 4 screenshot_before | AUTO-SKIP when not UI | `change_type` does not include `ui_change` |
| Stage 4 Gate E.5 RED evidence per task | **MANDATORY** unless a § TDD exemption table row applies (with that row's tier) | § TDD exemption table |
| Stage 4 GREEN evidence per task | **MANDATORY** unless a § TDD exemption table row applies (with that row's tier) | § TDD exemption table |
| Stage 4 spec-compliance review per task | **MANDATORY — never skippable** | — |
| Stage 4 quality review (Karpathy + Kotlin/Android convention) per task | **MANDATORY — never skippable** | — |
| Stage 4 Kotlin / Android official-rule checklist review | **MANDATORY when Kotlin product code changed** | — |
| Stage 4 regression/security/performance check status per task | **MANDATORY when declared in `quality_gate_plan`** | — |
| Stage 4 interrupt: update `handoff.md` | **MANDATORY — never skippable** | — |
| Stage 4 interrupt: update `status.json` | **MANDATORY — never skippable** | — |
| Stage 5 Evidence Gate Matrix required items | **MANDATORY** | — |
| Stage 5 Kotlin static analysis evidence | **MANDATORY when Kotlin product code changed** | — |
| Stage 5 required regression/security/performance evidence | **MANDATORY when declared in context-pack** | — |
| Stage 5 Evidence Gate Matrix optional items | AUTO-SKIP (never required) | always optional |
| Stage 5 required evidence item — tool/command absent or not configured | AUTO-SKIP | detection command confirms tool absent; record an Unavailable-tool record (see `refs/contracts-and-artifacts.md` § Unavailable-tool record) |
| Stage 5 architecture-map update | AUTO-SKIP when `graph_impact = low` | `graph_impact = low` in context-pack |
| Stage 5 Gradle Module Impact build scope | AUTO-SKIP when `module_impact_chain` absent | `module_impact_chain` not populated |
| Stage 7 architecture-doc update | AUTO-SKIP when trigger condition false | `adr_required=false AND estimated_build_scope=single AND change_type≠architecture_change` |
| Stage 6 Karpathy diff review | **MANDATORY — never skippable** | — |
| Stage 6 Gate G close | **MANDATORY** | — |
| Stage 7 Docs/decision finalization | **MANDATORY** | — |
| Stage 7 ADR final status | **MANDATORY when ADR exists** | — |
| Stage 7 Task Changelog | **MANDATORY** | — |
| Stage 7 Kotlin / Android Rule Closure | **MANDATORY when Kotlin product code changed** | — |
| Stage 7 Impact Closure | **MANDATORY for code-touching tasks** | — |
| Stage 7 `task-summary.md` | **MANDATORY for code-touching tasks** | — |
| Stage 7 Artifact Integrity Check | **MANDATORY** | — |
| Stage 7 Skill Drift Check | AUTO-SKIP when task did not touch skill's own files | task did not modify `SKILL.md`/`refs/**`/`templates/**`/`docs/FLOW.md`/`CHANGELOG.md` |
| Write session.json state transitions | **MANDATORY — never skippable** | — |
| Write skip-log.json on any skip | **MANDATORY — never skippable** | — |
| Update status.json on every stage transition | **MANDATORY — never skippable** | — |
| Update handoff.md on stage transition or interrupt (Stage 3+) | **MANDATORY — never skippable** | — |

### CONFIRM-SKIP — requires explicit human "yes" before proceeding

These steps are mandatory by default but a human may override them. Agent must **ask and wait** — never assume:

| Step | Ask before skipping |
|---|---|
| Workflow mode downgrade (governed → standard, standard → fast, fast → micro) | "Current task is scored as `<mode>`. Downgrade to `<lower mode>` removes [clarification / ADR gate / QA gate / discovery+requirements files]. Confirm? (y/n)" |
| Stage 1.5 Clarification when any trigger fires | "Clarification trigger fired: `<reason>`. Skip clarification and proceed directly to requirements? (y/n)" |
| Stage 2.5 ADR-lite when any decision trigger fires | "Decision trigger fired: `<reason>`. Skip ADR-lite and proceed to design? This removes the architecture decision record. (y/n)" |
| Stage 4 Gate E.5 TDD for a specific task (CONFIRM-SKIP rows of § TDD exemption table only) | "Task `<task-id>` is `<change_type>`; its diff fits the `<reason>` exemption (`<scope_check>`). Replace RED/GREEN with `<replacement evidence>` for this task? (y/n)" — AUTO-SKIP rows are logged without asking; anything outside the table is denied, not asked. |
| Stage 5 required evidence item — tool present but check failed or contradicted expectation | "Required evidence `<item>`'s tool is present but the check failed/contradicted expectation (`<reason>`). Skip and proceed without it? This will be recorded in skip-log.json. (y/n)" |
| Stage 5 Kotlin static analysis failure or unavailable configured tool | "`<tool>` is required for Kotlin static analysis but failed/is unavailable (`<reason>`). Fix before close, or defer with follow-up `<tracking_ref>`? Confirm defer? (y/n)" |
| Stage 5 required regression/security/performance evidence (tool unavailable or manual-only) | "Required impact evidence `<item>` cannot be collected (`<reason>`). Defer with follow-up `<tracking_ref>` or block the task? Confirm defer? (y/n)" |
| Stage 6 Karpathy CRITICAL/HIGH finding | "Karpathy flagged `<issue>`. Proceed to close without fixing? This overrides the QA gate. (y/n)" |
| Stage 7 Artifact Integrity / applicable Skill Drift failure | "Stage 7 close check failed: `<reason>`. Close anyway? This will be recorded in skip-log.json. (y/n)" |
| Any stage re-ordering or parallel shortcut not defined in SKILL.md | "This would run Stage `<X>` before Stage `<Y>` is complete. Confirm? (y/n)" |

### TDD exemption table

**This table is the only definition of when Gate E.5 RED/GREEN evidence may be replaced.** README, `SKILL.md`, `refs/contracts-and-artifacts.md § Gate E.5`, `refs/stage-contracts.md`, the stage compliance matrix above and `docs/FLOW.md` point here and must not restate or narrow it. Outside these rows the request is denied.

The tier column is binding: **AUTO-SKIP** applies without asking when the scope rule holds (still logged); **CONFIRM-SKIP** needs the human's yes for that specific task (ask row above). An exemption never means "no evidence": the replacement evidence must be collected and recorded like any other evidence — a task cannot self-declare PASS.

| `reason` | Tier | Qualifies only when (scope rule, checked against the actual diff) | Replacement evidence (recorded under `evidence/`) | Still required |
|---|---|---|---|---|
| `build-only` | AUTO-SKIP | `change_type ∈ {dependency_change, config_change}` and the diff touches **only** Gradle build files (`build.gradle*`, `settings.gradle*`, version catalogs, `gradle.properties`, wrapper). No `.kt`/`.java`, no resources, no `AndroidManifest.xml`. | `build_success_all_modules` (dependency_change) or `build_success_release_variant` (config_change) — the same items the Evidence Gate Matrix already requires | Clean build of every affected module |
| `manifest-config` | CONFIRM-SKIP | As `build-only`, but the diff also touches `AndroidManifest.xml` or build-variant config. Manifest edits can change behavior (permissions, `exported`, intent filters), so a human confirms. | `build_success_release_variant` + `manifest_diff`, plus an instrumented/Robolectric check when a permission, component or intent filter changed | Spec-compliance review, quality review |
| `resource-presentation` | AUTO-SKIP | Diff touches **only** presentation resources: values in `res/values*/{colors,dimens,styles,themes}.xml`, text-only edits in `res/values*/strings.xml`, files under `res/drawable*/`, `res/mipmap*/`, `res/font/`. No resource is renamed or removed; no string gains/loses/reorders format placeholders (`%s`, `%1$d`, …) or plural quantities; no `.kt`/`.java`, layout, navigation, `res/xml`, menu or manifest file. | `build_success` + `lint_report` for the affected module; `screenshot_after` of an affected screen when a device/emulator or snapshot test (Paparazzi/Roborazzi) is available, else the degraded-evidence note | Spec-compliance review, quality review |
| `ui-pixel-tweak` | CONFIRM-SKIP | Layout XML attribute edits or Compose modifier/value edits (padding, size, color, typography, alignment) that add or remove **no** view, id, state, callback, binding expression or logic. | `screenshot_before` + `screenshot_after`, or a Paparazzi/Roborazzi snapshot diff; existing UI/Robolectric tests for that screen pass | Spec-compliance review, quality review |
| `pure-refactor` | CONFIRM-SKIP | Behavior unchanged; a new test would only duplicate existing ones. | Existing test suite green before **and** after; diff reviewed for scope creep | No new behavior introduced |
| `legacy-untestable` | CONFIRM-SKIP | No test harness exists and adding one costs more than the change. | Characterization test committed before product code, **or** a minimal harness added as its own task with full TDD | Characterization test / harness evidence |
| `spike` | CONFIRM-SKIP | Exploratory work; no product code merges. | Notes, spike branch or draft in `docs/ai/inputs/` | Spike discarded, or converted to a new task with full TDD |

**Never an exemption** (normal RED/GREEN applies):
- Anything outside the scope rule of its row — one product-code file in the diff ends every resource/build exemption for that task.
- `res/navigation/`, `res/xml/` (preferences, network security config, file providers), menus, data-binding or view-binding expressions, `onClick`/listener attributes, new or removed views/ids: these change behavior.
- Features that are "hard to test" but testable with effort (use Android Advisor for test strategy); new screens or flows (Compose semantics or Robolectric); any task whose acceptance criteria can be written as a unit or integration test.
- Time pressure.

**Exemption record (always written to `skip-log.json`):**
```json
{
  "stage": "4",
  "step": "gate_e5_tdd",
  "tier": "AUTO-SKIP | CONFIRM-SKIP",
  "reason": "build-only | manifest-config | resource-presentation | ui-pixel-tweak | pure-refactor | legacy-untestable | spike",
  "task_id": "<task-id>",
  "confirmed_by": "policy | human",
  "scope_check": "<files in the diff, and why they satisfy the row's scope rule>",
  "alternative": "<replacement evidence paths>",
  "consequence": "RED evidence not collected for this task"
}
```

---

## Autonomy policy

Names the boundary already defined by the tiers above — no tier changes here, documentation only. The agent runs every AUTO-SKIP condition automatically, without asking. It asks the human only for:

1. Any CONFIRM-SKIP step per the tables above.
2. Genuine scope ambiguity that blocks progress.
3. An ADR-required decision needing approval or deferral.
4. An evidence-collection failure needing a defer decision (tool present but check failed — not simple tool absence, which AUTO-records per § Unavailable-tool record).
5. An implementation decision with more than one reasonable interpretation that produces materially different behavior.

It does not ask "should I continue?" between routine steps — see `SKILL.md` Stage 4 "Do not:" list.

---

## 2. Confirmation protocol

When the skill needs to skip or bypass a step requiring confirmation:

```
Step 1 — STOP. Do not proceed.
Step 2 — State clearly:
          "I want to skip [step name] because [reason].
           This means [consequence].
           Confirm skip? (y/n)"
Step 3 — Wait for explicit "y" or "yes".
          If user says "n" or anything else → do not skip, continue with the step.
Step 4 — Write skip record to skip-log.json (regardless of outcome).
Step 5 — Proceed.
```

**Implicit confirmation is not allowed.** A user saying "keep going" or "continue" does NOT confirm a skip unless the skip was explicitly stated and acknowledged.

**Timeout is not confirmation.** If the user does not respond, do not skip.

---

## 3. What can never be bypassed

These rules are absolute. No user instruction, no time pressure, no "just this once" overrides them:

1. Auth init — `.agent-auth.yaml` must be checked at every Stage -1 entry.
2. Human approval at Gate D (Requirements) — must be an explicit "approve" or equivalent.
3. Decision Gate evaluation at Stage 2.5 — ADR triggers must always be checked.
4. Karpathy review at Stage 6 — may report findings but cannot be silenced.
5. Stage 7 Task Changelog and Artifact Integrity Check — final status cannot be success without them. Skill Drift Check applies only when this task modified the orchestrator skill's own files.
6. Writing `session.json` state on every stage transition and interrupt.
7. Writing to `skip-log.json` on every skip (auto or confirmed); file is lazy-created on the first write — it need not exist before the task's first skip occurs and its absence is not a violation for tasks with zero skips.
8. One code owner at a time — no parallel code edits.
9. Updating `.project-orchestration/status.json` on every stage transition — the project index must never lag more than one stage behind.
11. Generating `docs/ai/tasks/{task_id}/handoff.md` when `code_owner` is confirmed (Stage 3) and updating it on every Stage 4 interrupt — a developer picking up an interrupted task must always find a current handoff file.
12. Generating `docs/ai/tasks/{task_id}/planning/implementation-plan.md` at Stage 3 with no placeholders — RED evidence cannot be written without knowing the exact test command.
13. Collecting RED evidence (`evidence/red-<task-id>.txt`) before writing any product code for that task — spec-compliance and quality review order is spec first, then quality; never reversed.
14. Computing and recording `preliminary_mode` at Stage 0 and `workflow_mode` (final) after Stage 1 — mode must be set before any stage-skip decision is made. A mode cannot be applied retroactively to justify a skip that already happened.
15. ADR ledger immutability — an `Accepted` ADR is never edited in place, only superseded (new ADR with `supersedes:`, old ADR gets `superseded_by:` + index update).
16. Recording `kotlin_convention_check` tier for every Stage 4 task with a non-empty `kotlin_convention_scope` — the check itself may degrade through the fallback tiers, the record may not be omitted.
17. Impact closure — for every code-touching task, Stage 7 must record impacted features, regression evidence, security/performance outcomes, and unresolved follow-ups in `execution.md` and `task-summary.md`.
18. Kotlin static analysis — every Kotlin product-code change must collect `kotlin_static_analysis_pass` evidence or an explicit human-approved deferred follow-up. Configured static-analysis failures cannot be silently ignored.
19. Official-reference Kotlin review — if official Android/Kotlin docs or companion skill docs are available, a Kotlin convention review cannot close as `general_knowledge` only.
20. Resume integrity reconciliation — before ever offering to resume an `in_progress` task, verify the declared `stage_reached`'s mandatory artifacts actually exist on disk (`refs/stage-contracts.md § Integrity reconciliation`). `session.json` is never trusted blindly for resume.

---

## 4. Audit trail

### `skip-log.json`

Stored at `.project-orchestration/tasks/{task_id}/skip-log.json`. **Lazy-create:** not pre-created at Stage -1. The file is created on the first write (first skip entry). A task that completes with zero skips never writes this file; its absence is not a violation. Once created: written on every auto-skip and every confirm-skip; never deleted within a task's lifecycle.

```json
{
  "task_id": "ANDROID-42 | task-slug",
  "skips": [
    {
      "at": "2026-05-07T10:15:00Z",
      "stage": "1",
      "step": "gradle_module_impact_analyzer",
      "tier": "AUTO-SKIP",
      "reason": "graph_impact: low",
      "condition_met": "graph_impact = low in context-pack",
      "confirmed_by": "auto",
      "consequence": "module_impact_chain not populated; build scope = single module"
    },
    {
      "at": "2026-05-07T11:00:00Z",
      "stage": "1.5",
      "step": "clarification",
      "tier": "CONFIRM-SKIP",
      "reason": "all 6 trigger conditions false; docs detailed",
      "condition_met": "auto-exit criteria satisfied",
      "confirmed_by": "human",
      "confirmed_at": "2026-05-07T11:00:30Z",
      "consequence": "proceeding to requirements without clarification workers"
    }
  ]
}
```

Fields:
- `tier`: `AUTO-SKIP` | `CONFIRM-SKIP`
- `confirmed_by`: `auto` (condition-gated) | `human` (explicit approval) | `never` (step was not skipped — log entry records the ask-and-decline)

### Stage gate log (within `execution.md`)

Every gate transition must be recorded in `execution.md`:

```markdown
## Gate log

| Gate | Status | Timestamp | Notes |
|---|---|---|---|
| Gate -1 | passed | 2026-05-07T09:05Z | cache miss; full preflight run |
| Gate A  | passed | 2026-05-07T09:06Z | source_mode: A |
| Gate B  | passed | 2026-05-07T09:20Z | graph read; 3 sources loaded |
| Gate C  | passed | 2026-05-07T09:35Z | clarity_score: 8 |
| Gate D  | passed | 2026-05-07T10:00Z | human approved requirements |
| Gate D.5 | passed | 2026-05-07T10:15Z | ADR-lite: accepted |
| Gate E  | passed | 2026-05-07T10:30Z | code_owner: orchestrator; implementation-plan.md generated |
| Gate E.5 | passed | 2026-05-07T10:45Z | RED evidence: evidence/red-task-1.txt, red-task-2.txt |
| Gate F  | passed | 2026-05-07T11:45Z | all required evidence collected |
| Gate G  | passed | 2026-05-07T12:00Z | Karpathy: no critical issues; Impact Closure complete; Stage 7 finalized |
```

---

## 5. Stage order enforcement

Stages must run in this order: **-1 → 0 → 1 → [1.5] → 2 → 2.5 → 3 → 4 → 5 → 6 → 7 → [8]**.

Brackets `[]` = may be auto-skipped under conditions above. Stage 8 is bracketed for a different reason than 1.5 — it is optional/non-blocking by design (retro telemetry, never gates anything), not conditionally skipped; the task's success/failure is fully determined by Stage 7.

**Violations that require immediate stop:**
- Code is touched before Stage 2 approval (Gate D).
- Design starts before Stage 2.5 Decision Gate is complete.
- Implementation begins before code_owner is set in session.json.
- Implementation begins before `implementation-plan.md` exists with no placeholders (Gate E).
- Product code is written for a task before RED evidence exists for that task (Gate E.5).
- Spec-compliance review is skipped or run after quality review for any task.
- Stage 5 closes without all required evidence items.
- Stage 5 closes a Kotlin product-code change without `kotlin_static_analysis_pass` evidence or explicit deferred follow-up.
- Stage 5 closes without required regression/security/performance evidence or explicit deferred follow-up.
- Stage 6 closes with unresolved CRITICAL Karpathy findings.
- Stage 7 closes with missing ADR final status, Kotlin / Android Rule Closure, Impact Closure, Task Changelog, task-summary.md, Artifact Integrity Check, or applicable Skill Drift Check.
- `workflow_mode` is not set before any fast-mode AUTO-SKIP is recorded.
- Mode is downgraded (e.g. governed → fast) without explicit human confirmation.
- `artifact_budget.fast` is exceeded without mode being upgraded to `standard`.

On violation: write violation to `skip-log.json` with `tier: VIOLATION`, stop, and report to human.

---

## 6. Task isolation rule

Each task runs in its own scoped directory under `.project-orchestration/tasks/{task_id}/`. A new task must not read or overwrite artifacts from a different task's directory.

**task_id derivation:**
1. Use Jira ticket key if present: `ANDROID-42`
2. Use slug from task title if no ticket: `add-login-flow`
3. Fall back to ISO date + short hash: `2026-05-07-a1b2`

**Shared (global) paths — readable by all tasks, writable only by Stage -1:**
- `.project-orchestration/memory/tooling-cache.json`
- `.project-orchestration/reports/preflight.md`
- `docs/ai/inputs/` (human-provided, never overwritten by agent)

**Shared (global) path — readable by all tasks, writable by Stage -1 (bootstrap/refresh-graph) or by the active task's Stage 5 when `graph_impact ≥ medium` (never on behalf of a different task_id):**
- `.project-orchestration/memory/graph-stamp.json` — repo-level graph staleness; one file, not one per task (relocated from `tasks/{task_id}/memory/` in v6.0.0)

**Shared (global) paths — readable by all tasks, writable only by Stage 2.5/Stage 7 of the currently active task (never by Stage -1, never on behalf of a different task_id):**
- `docs/ai/decisions/` — ADR ledger + `README.md` index (Stage 2.5 creates/links, Stage 7 finalizes status)
- `docs/ai/architecture/` — living knowledge base + `README.md` index (Stage 7 only, section-level patch, gated by the trigger condition in `refs/contracts-and-artifacts.md` § 4e)
