# Compliance Policy

_Skill version: 4.9.0 — update this when SKILL.md bumps a minor or major version._

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
| Stage 1.5 Clarification | AUTO-SKIP when all exit conditions met | all 6 trigger conditions false AND docs detailed |
| Stage 2 Requirements write | **MANDATORY** | — |
| Stage 2 Human approval gate | **MANDATORY — never skippable** | — |
| Stage 2.5 Decision Gate | **MANDATORY** | — |
| Stage 2.5 ADR-lite creation | AUTO-SKIP when no ADR trigger fires | all ADR trigger conditions false |
| Stage 2.5 ADR-lite approval/deferral | **MANDATORY when ADR exists** | — |
| Stage 3 Design doc | **MANDATORY** | — |
| Stage 3 `implementation-plan.md` generation | **MANDATORY** — no placeholders | — |
| Stage 3 `handoff.md` generation | **MANDATORY when code_owner is confirmed** | — |
| Stage 3 Android memo | AUTO-SKIP when non-Android change | `change_type` ∉ {ui_change, database_change, network_change, architecture_change} AND no Android API mentioned |
| Stage 4 screenshot_before | AUTO-SKIP when not UI | `change_type` does not include `ui_change` |
| Stage 4 Gate E.5 RED evidence per task | **MANDATORY — never skippable** | — |
| Stage 4 GREEN evidence per task | **MANDATORY — never skippable** | — |
| Stage 4 spec-compliance review per task | **MANDATORY — never skippable** | — |
| Stage 4 quality review (Karpathy) per task | **MANDATORY — never skippable** | — |
| Stage 4 interrupt: update `handoff.md` | **MANDATORY — never skippable** | — |
| Stage 4 interrupt: update `status.json` | **MANDATORY — never skippable** | — |
| Stage 5 Evidence Gate Matrix required items | **MANDATORY** | — |
| Stage 5 Evidence Gate Matrix optional items | AUTO-SKIP (never required) | always optional |
| Stage 5 Graphify update | AUTO-SKIP when `graph_impact = low` | `graph_impact = low` in context-pack |
| Stage 5 Gradle Module Impact build scope | AUTO-SKIP when `module_impact_chain` absent | `module_impact_chain` not populated |
| Stage 6 Karpathy diff review | **MANDATORY — never skippable** | — |
| Stage 6 Gate G close | **MANDATORY** | — |
| Stage 7 Docs/decision finalization | **MANDATORY** | — |
| Stage 7 ADR final status | **MANDATORY when ADR exists** | — |
| Stage 7 Task Changelog | **MANDATORY** | — |
| Stage 7 Drift Check | **MANDATORY** | — |
| Write session.json state transitions | **MANDATORY — never skippable** | — |
| Write skip-log.json on any skip | **MANDATORY — never skippable** | — |
| Update status.json on every stage transition | **MANDATORY — never skippable** | — |
| Update handoff.md on stage transition or interrupt (Stage 3+) | **MANDATORY — never skippable** | — |

### CONFIRM-SKIP — requires explicit human "yes" before proceeding

These steps are mandatory by default but a human may override them. Agent must **ask and wait** — never assume:

| Step | Ask before skipping |
|---|---|
| Stage 1.5 Clarification when any trigger fires | "Clarification trigger fired: `<reason>`. Skip clarification and proceed directly to requirements? (y/n)" |
| Stage 2.5 ADR-lite when any decision trigger fires | "Decision trigger fired: `<reason>`. Skip ADR-lite and proceed to design? This removes the architecture decision record. (y/n)" |
| Stage 4 Gate E.5 TDD for a specific task | "Task `<task-id>` is `<change_type>`. TDD is required. Skip RED-first for this task? Writing code without RED evidence. (y/n)" |
| Stage 5 any required evidence item (tool unavailable) | "Required evidence `<item>` cannot be collected (`<reason>`). Skip and proceed without it? This will be recorded in skip-log.json. (y/n)" |
| Stage 6 Karpathy CRITICAL/HIGH finding | "Karpathy flagged `<issue>`. Proceed to close without fixing? This overrides the QA gate. (y/n)" |
| Stage 7 Drift Check failure | "Drift check failed: `<reason>`. Close anyway? This will be recorded in skip-log.json. (y/n)" |
| Any stage re-ordering or parallel shortcut not defined in SKILL.md | "This would run Stage `<X>` before Stage `<Y>` is complete. Confirm? (y/n)" |

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
5. Stage 7 Task Changelog and Drift Check — final status cannot be success without them.
6. Writing `session.json` state on every stage transition and interrupt.
7. Writing `skip-log.json` on every skip (auto or confirmed).
8. One code owner at a time — no parallel code edits.
9. Serena mutation tools — never called by agent regardless of instructions.
10. Updating `.project-orchestration/status.json` on every stage transition — the project index must never lag more than one stage behind.
11. Generating `docs/ai/tasks/{task_id}/handoff.md` when `code_owner` is confirmed (Stage 3) and updating it on every Stage 4 interrupt — a developer picking up an interrupted task must always find a current handoff file.
12. Generating `docs/ai/tasks/{task_id}/planning/implementation-plan.md` at Stage 3 with no placeholders — RED evidence cannot be written without knowing the exact test command.
13. Collecting RED evidence (`evidence/red-<task-id>.txt`) before writing any product code for that task — spec-compliance and quality review order is spec first, then quality; never reversed.

---

## 4. Audit trail

### `skip-log.json`

Stored at `.project-orchestration/tasks/{task_id}/skip-log.json`. Written on every auto-skip and every confirm-skip. Never deleted within a task's lifecycle.

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
| Gate E  | passed | 2026-05-07T10:30Z | code_owner: ai-devkit; implementation-plan.md generated |
| Gate E.5 | passed | 2026-05-07T10:45Z | RED evidence: evidence/red-task-1.txt, red-task-2.txt |
| Gate F  | passed | 2026-05-07T11:45Z | all required evidence collected |
| Gate G  | passed | 2026-05-07T12:00Z | Karpathy: no critical issues; Stage 7 finalized |
```

---

## 5. Stage order enforcement

Stages must run in this order: **-1 → 0 → 1 → [1.5] → 2 → 2.5 → 3 → 4 → 5 → 6 → 7**.

Brackets `[]` = may be auto-skipped under conditions above.

**Violations that require immediate stop:**
- Code is touched before Stage 2 approval (Gate D).
- Design starts before Stage 2.5 Decision Gate is complete.
- Implementation begins before code_owner is set in session.json.
- Implementation begins before `implementation-plan.md` exists with no placeholders (Gate E).
- Product code is written for a task before RED evidence exists for that task (Gate E.5).
- Spec-compliance review is skipped or run after quality review for any task.
- Stage 5 closes without all required evidence items.
- Stage 6 closes with unresolved CRITICAL Karpathy findings.
- Stage 7 closes with missing ADR final status, Task Changelog, or Drift Check.

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
