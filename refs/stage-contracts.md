# Stage Output Contracts

_Skill version: 4.16.0 — update this when SKILL.md bumps a minor or major version._

Each stage defines a typed contract: what it requires as input, what it must produce as output, and what state it writes to `session.json` on completion or interrupt.

**Resume rule:** At Stage -1, read `session.json`. If `stage_status = in_progress`, the previous run was interrupted at `stage_reached`. Offer to resume from `resume_entry_point`. If user declines, overwrite session and start fresh.

**Interrupt safety:** On any unrecoverable error or user interruption, write the current stage's interrupt state to `session.json` before stopping. Never leave `session.json` in an inconsistent state.

---

## Stage -1 — Tooling Preflight

```yaml
stage: "-1_tooling_preflight"

input_requires:
  - git working directory accessible
  - .agent-auth.yaml (auto-created if missing)

guard_conditions:
  - Cache check: if tooling-cache.json valid_until > now AND graph_commit matches HEAD
      → skip bash script, load cached values, state_on_complete immediately

output_produces:
  - .project-orchestration/reports/preflight.md                    ← GLOBAL
  - .project-orchestration/memory/tooling-cache.json               ← GLOBAL
  - .project-orchestration/status.json (initialized if missing)    ← GLOBAL
  - .project-orchestration/tasks/{task_id}/session.json (stage_reached: -1)
  - .project-orchestration/tasks/{task_id}/skip-log.json (initialized empty)
  - context fields: tooling_readiness, auth_status, provisioning_mode, blockers, architecture_map_staleness

state_on_complete:
  stage_reached: -1
  stage_status: complete
  blocker: null

state_on_interrupt:
  stage_reached: -1
  stage_status: in_progress
  blocker: "<which preflight check failed or timed out>"

resume_entry_point: "re-run bash templates/tooling-preflight.sh from scratch (idempotent)"
```

---

## Stage 0 — Intake

```yaml
stage: "0_intake"

input_requires:
  - .project-orchestration/reports/preflight.md (stage -1 complete)
  - user task description (Jira URL / Figma URL / plain text)

guard_conditions:
  - preflight.md must have proceed_to_stage_0: true
  - if preflight has blocking gaps → show gaps, ask user to resolve before continuing
  - Task History Relevance Gate runs before source mode is finalized:
      default full-history behavior: skipped
      metadata scan only when continuation signals or possible overlap exist
      full history read only when explicit_continuation=true OR overlap_score>=medium

output_produces:
  - .project-orchestration/tasks/{task_id}/session.json (task_id, source_mode, started_at)
  - link list recorded (Jira, Figma, Confluence URLs if provided)
  - task_continuity: "new | continuation | unknown"
  - history_scan:
      performed: true | false
      mode: "skipped | metadata-only | full"
      matched_tasks: []
      overlap_score: "none | low | medium | high"
      explicit_continuation: true | false
      decision: "skip | read_full | ask_human"
  - ref tier determined (LIGHT / MEDIUM / HEAVY / FULL)
  - preliminary_mode (fast / standard / governed) derived from task description and link presence

state_on_complete:
  stage_reached: 0
  stage_status: complete
  source_mode: "A | B | C"
  task_continuity: "new | continuation | unknown"
  preliminary_mode: "fast | standard | governed"
  blocker: null
  # status.json updated: entry added or refreshed for this task_id

state_on_interrupt:
  stage_reached: 0
  stage_status: in_progress
  blocker: "awaiting user to provide task description, source links, or task-history clarification"

resume_entry_point: "re-ask user for missing source links or task-history clarification; source_mode/history_scan already derived if available"
```

---

## Stage 1 — Discovery

```yaml
stage: "1_discovery"

input_requires:
  - session.json stage_reached >= 0
  - .project-orchestration/reports/preflight.md
  - source links or docs/ai/inputs/ (per source_mode)
  - matched task history docs only when session.json history_scan.decision = read_full

guard_conditions:
  - active architecture-map output read if graph exists (.understand-anything/knowledge-graph.json or graphify-out/GRAPH_REPORT.md)
  - source readers run per source_mode (A: Jira+Confluence+Figma; B: Doc Reader; C: user message only)
  - if history_scan.decision = read_full: read matched task task-summary.md first when present, then requirements, ADRs, design, and execution report only as needed before synthesis
  - if history_scan.decision = ask_human: block before Discovery until user confirms continuation vs independent task

output_produces:
  - docs/ai/tasks/{task_id}/discovery/<task>.md  (raw discovery notes)
  - docs/ai/tasks/{task_id}/clarification/context-pack.json (partial — sources, graph_path, graph_impact, change_type, history_context if read)
  - impact_assessment, regression_test_matrix, quality_gate_plan, follow_up_watchlist drafted in context-pack for code-touching tasks
  - module_impact_chain populated if graph_impact >= medium (Gradle Module Impact Analyzer)
  - .project-orchestration/tasks/{task_id}/skip-log.json appended if Gradle Module Impact Analyzer auto-skipped
  - workflow_mode (fast / standard / governed) finalized; complexity_score and risk_score computed after all sources read
  - mode_reasons list written to context-pack.json
  - session.json updated: workflow_mode, complexity_score, risk_score, mode_reasons set

state_on_complete:
  stage_reached: 1
  stage_status: complete
  workflow_mode: "fast | standard | governed"
  complexity_score: <1-10>
  risk_score: <1-10>
  blocker: null

state_on_interrupt:
  stage_reached: 1
  stage_status: in_progress
  blocker: "<which source reader failed or which auth token was missing>"
  partial_outputs:
    - "docs/ai/tasks/{task_id}/discovery/<task>.md (partial — safe to re-read)"

resume_entry_point: "re-run failed source reader; previously successful readers are already in discovery notes"
```

---

## Stage 1.5 — Clarification & Synthesis

```yaml
stage: "1.5_clarification"

input_requires:
  - docs/ai/tasks/{task_id}/discovery/<task>.md (stage 1 complete)
  - context-pack.json (partial — graph_impact, sources populated)

guard_conditions:
  - skip if ALL: docs detailed, acceptance criteria testable, no conflicts, isolated change surface
  - run if ANY trigger from SKILL.md § Stage 1.5 checklist fires

output_produces:
  - docs/ai/tasks/{task_id}/clarification/context-pack.json (complete)
  - docs/ai/tasks/{task_id}/clarification/clarification-brief.md
  - clarity_score written to context-pack.json
  - impact_assessment / regression_test_matrix / quality_gate_plan / follow_up_watchlist finalized or explicitly omitted as not_applicable
  - Serena outputs attached if triggered
  - module_impact_chain finalized (Gradle Module Impact Analyzer may refine graph_impact here)
  - change_type finalized
  - .project-orchestration/tasks/{task_id}/skip-log.json appended if Stage 1.5 was auto-skipped or confirm-skipped
  - NOTE: workflow_mode is NOT set here — it was finalized at end of Stage 1; Stage 1.5 reads it, never writes it

state_on_complete:
  stage_reached: 1
  stage_status: complete        # note: stage_reached stays 1; 1.5 is a sub-stage
  clarity_score: <0-10>
  blocker: null                 # null = clarity sufficient to proceed

state_on_interrupt:
  stage_reached: 1
  stage_status: in_progress
  blocker: "clarification blocked: <missing info item or unresolved conflict description>"
  partial_outputs:
    - "docs/ai/tasks/{task_id}/clarification/context-pack.json (partial)"

resume_entry_point: "re-run blocked analysis worker; other workers' outputs already in context-pack"
```

---

## Stage 2 — Requirements

```yaml
stage: "2_requirements"

input_requires:
  - docs/ai/tasks/{task_id}/clarification/context-pack.json (clarity_score sufficient, outcome: ready)
  - clarification-brief.md

guard_conditions:
  - outcome must be "ready" (not "blocked" or "research-loop")
  - if outcome = blocked → escalate to user before proceeding

output_produces:
  - docs/ai/tasks/{task_id}/requirements/<task>.md (canonical requirements doc)
  - requirements artifact header, Affected Areas checklist, Decision Triggers section, Impact / Regression section
  - .project-orchestration/tasks/{task_id}/session.json: requirements_approved → false (pending)

approval_gate:
  - STOP after producing requirements doc
  - Do not proceed to Stage 3 until human sets approval
  - session.json: requirements_approved: true written only after explicit human approval

state_on_complete:
  stage_reached: 2
  stage_status: complete
  requirements_approved: true
  blocker: null

state_on_interrupt:
  stage_reached: 2
  stage_status: in_progress
  blocker: "waiting for human approval of requirements/<task>.md"

resume_entry_point: "requirements doc already exists; re-present to user and await approval"
```

---

## Stage 2.5 — Decision Gate / ADR-lite

```yaml
stage: "2.5_decision_gate"

input_requires:
  - docs/ai/tasks/{task_id}/requirements/<task>.md (requirements_approved: true)
  - docs/ai/tasks/{task_id}/clarification/context-pack.json
  - refs/contracts-and-artifacts.md: ADR trigger list + Decision Ownership matrix
  - docs/ai/decisions/README.md (read for duplicate-ADR check; auto-create if missing and a trigger fires)

guard_conditions:
  - evaluate ADR triggers: module boundary, navigation graph, public API/internal contract,
    persistence schema, DI graph, Gradle/AGP/Kotlin version, Compose/View migration,
    state ownership, background work, permissions, billing, auth, notifications,
    broad test strategy
  - if any trigger fires: check docs/ai/decisions/README.md for an existing covering Accepted ADR first
  - if a covering ADR exists and is still valid: link to it, adr_required: false, reason: "covered by ADR-NNNN"
  - if a covering ADR exists but decision changed: create new ADR with supersedes: ADR-NNNN
  - if no covering ADR: create Proposed ADR-lite (numbered per § 4c) and stop for human approval
  - if no trigger fires: record adr_required: false and reason

output_produces:
  - docs/ai/decisions/ADR-NNNN-<slug>.md (GLOBAL, if required)
  - docs/ai/decisions/README.md (index row added for the new ADR)
  - .project-orchestration/tasks/{task_id}/session.json:
      adr_required: true | false
      adr_status: "proposed | accepted | deferred | superseded | not_required"
      decision_record: "<path or null>"
  - .project-orchestration/tasks/{task_id}/skip-log.json appended if ADR-lite not required

approval_gate:
  - STOP when ADR status is Proposed
  - Do not proceed to Stage 3 until human approves or explicitly defers the ADR

state_on_complete:
  stage_reached: 2.5
  stage_status: complete
  adr_required: true | false
  adr_status: "accepted | deferred | not_required"
  blocker: null

state_on_interrupt:
  stage_reached: 2.5
  stage_status: in_progress
  blocker: "waiting for human approval/deferral of ADR-lite"
  partial_outputs:
    - "docs/ai/decisions/ADR-NNNN-<slug>.md (Proposed, GLOBAL)"

resume_entry_point: "ADR decision already exists; re-present Proposed ADR and await approval/deferral"
```

---

## Stage 3 — Design Split

```yaml
stage: "3_design"

input_requires:
  - docs/ai/tasks/{task_id}/requirements/<task>.md (requirements_approved: true)
  - context-pack.json (module_impact_chain, change_type available)
  - session.json: adr_status is accepted | deferred | not_required

guard_conditions:
  - requirements_approved must be true in session.json
  - decision gate must be complete
  - no product-code changes allowed in this stage

output_produces:
  - docs/ai/tasks/{task_id}/design/<task>.md (Spec Kit design doc)
  - docs/ai/tasks/{task_id}/planning/<task>.md (Spec Kit planning doc)
  - docs/ai/tasks/{task_id}/planning/implementation-plan.md (executable TDD plan; MANDATORY — no placeholders; includes regression/security/performance checks)
  - docs/ai/tasks/{task_id}/android-memo/<task>.md (Android skills memo, if Android-specific — auto-skip written to skip-log if omitted)
  - docs/ai/tasks/{task_id}/handoff.md (generated when code_owner is confirmed; MANDATORY)
  - .project-orchestration/tasks/{task_id}/session.json: code_owner, assignee, branch set
  - .project-orchestration/status.json: entry updated (stage_reached: 3, assignee, branch)

state_on_complete:
  stage_reached: 3
  stage_status: complete
  code_owner: "<agent-name>"
  assignee: "<dev-name | agent-name>"
  branch: "<branch name>"
  blocker: null

state_on_interrupt:
  stage_reached: 3
  stage_status: in_progress
  blocker: "<design doc incomplete or code_owner not yet selected>"
  partial_outputs:
    - "docs/ai/tasks/{task_id}/design/<task>.md (partial)"

resume_entry_point: "resume writing incomplete design doc; if code_owner missing, derive from design scope; regenerate handoff.md after code_owner is confirmed"
```

---

## Stage 4 — Implementation Lock

```yaml
stage: "4_implementation"

input_requires:
  - docs/ai/tasks/{task_id}/design/<task>.md (stage 3 complete)
  - docs/ai/tasks/{task_id}/planning/<task>.md
  - docs/ai/tasks/{task_id}/planning/implementation-plan.md (exists, no placeholders)
  - session.json: code_owner set, requirements_approved: true
  - session.json: adr_status is accepted | deferred | not_required
  - context-pack.json: module_impact_chain (for build scope awareness)

guard_conditions:
  - exactly one code owner — all other lanes advisory only
  - Karpathy guidelines applied to every code change
  - Serena advisory only (no mutation tools)
  - screenshot_before captured BEFORE first code change (if change_type includes ui_change)
  - Gate E.5 enforced per task: RED evidence must exist before any product code for that task

output_produces:
  - product code changes (owned by code_owner)
  - evidence/screen_before.png (if change_type: ui_change — captured before first edit)
  - evidence/red-<task-id>.txt per task (RED test run output — MANDATORY before product code)
  - evidence/green-<task-id>.txt per task (GREEN test run output — MANDATORY after implementation)
  - spec-compliance review record per task (in execution.md or inline comment)
  - quality review (Karpathy) record per task
  - regression/security/performance check status per task when declared in quality_gate_plan
  - .project-orchestration/status.json: entry updated (stage_reached: 4)

state_on_complete:
  stage_reached: 4
  stage_status: complete
  tdd_evidence_complete: true   # all tasks have red + green evidence
  blocker: null

state_on_interrupt:
  stage_reached: 4
  stage_status: in_progress
  blocker: "<build error | test failure | blocked on advisory clarification>"
  partial_outputs:
    - "product code partial — do not consider shipped"
  # MANDATORY on interrupt: update docs/ai/tasks/{task_id}/handoff.md with current state,
  # files modified so far, last completed task, and next action before stopping.
  # MANDATORY on interrupt: update .project-orchestration/status.json entry with blocker.

resume_entry_point: "read implementation-plan.md for task list; read handoff.md for last completed task; continue from next incomplete task; Gate E.5 still applies to remaining tasks"
```

---

## Stage 5 — Verify

```yaml
stage: "5_verify"

input_requires:
  - stage 4 complete (code_owner signals done)
  - context-pack.json: change_type, module_impact_chain
  - Android CLI available

guard_conditions:
  - derive required evidence from Evidence Gate Matrix using change_type
  - derive required regression/security/performance evidence from context-pack regression_test_matrix and quality_gate_plan
  - if module_impact_chain present: scope build commands to build_order modules
  - if graph_impact >= medium: run the active architecture-map update (/understand or /graphify . --update)
  - if graph_impact = low: skip architecture-map update (record skip reason in execution.md)

output_produces:
  - .project-orchestration/tasks/{task_id}/evidence/* (all required evidence files)
  - .project-orchestration/tasks/{task_id}/reports/execution.md (evidence manifest with Gate log and Impact Closure)
  - active architecture-map output updated (.understand-anything/ or graphify-out/, if graph_impact >= medium; skip written to skip-log if graph_impact = low)
  - .project-orchestration/tasks/{task_id}/session.json: stage_reached: 5, evidence_collected: [...]
  - .project-orchestration/status.json: entry updated (stage_reached: 5)

state_on_complete:
  stage_reached: 5
  stage_status: complete
  blocker: null

state_on_interrupt:
  stage_reached: 5
  stage_status: in_progress
  blocker: "<which required evidence item failed>"
  partial_outputs:
    - ".project-orchestration/tasks/{task_id}/evidence/ (partial)"

resume_entry_point: "re-run only failed evidence commands; already-collected evidence is preserved"
```

---

## Stage 6 — QA Gate

```yaml
stage: "6_qa_gate"

input_requires:
  - stage 5 complete (all required evidence collected)
  - .project-orchestration/tasks/{task_id}/reports/execution.md
  - context-pack.json: change_type, acceptance_criteria

guard_conditions:
  - all required evidence items from Evidence Gate Matrix must be present (Gate F)
  - every required regression/security/performance row must be passed, blocked, or explicitly deferred
  - no new code changes allowed; QA gate is review only

output_produces:
  - .project-orchestration/tasks/{task_id}/reports/execution.md updated with QA review + Gate log
  - Karpathy diff review recorded
  - .project-orchestration/tasks/{task_id}/session.json: stage_reached: 6
  - .project-orchestration/status.json: entry updated (stage_reached: 6)

approval_gate:
  - if Karpathy flags CRITICAL or HIGH issues → block and report to human
  - if acceptance criteria not fully covered → block and report to human
  - if required regression/security/performance evidence is missing → block and report to human

state_on_complete:
  stage_reached: 6
  stage_status: complete
  blocker: null

state_on_interrupt:
  stage_reached: 6
  stage_status: in_progress
  blocker: "<unresolved QA issue or missing acceptance coverage>"

resume_entry_point: "QA review findings already written in execution.md; re-check blocking issues only"
```

---

## Stage 7 — Docs / Decision Finalization

```yaml
stage: "7_docs_decision_finalization"

input_requires:
  - stage 6 complete
  - .project-orchestration/tasks/{task_id}/reports/execution.md
  - decision_record path if ADR-lite was required

guard_conditions:
  - no product-code changes allowed
  - if ADR exists: status must become Accepted, Deferred, or Superseded
  - if architecture-doc trigger met (adr_required OR estimated_build_scope in {local-chain, full-project}
    OR change_type: architecture_change): section-level patch only, never whole-file rewrite;
    Change Log section always appended; otherwise AUTO-SKIP
  - Task Changelog must summarize behavior changes, not just file diffs
  - Drift Check must pass or list blockers

output_produces:
  - docs/ai/decisions/ADR-NNNN-<slug>.md updated with final status (GLOBAL, if present)
  - docs/ai/decisions/README.md index row updated to match (GLOBAL)
  - docs/ai/architecture/<domain>.md created-or-updated (GLOBAL, only if trigger condition met)
  - docs/ai/architecture/README.md index updated (GLOBAL, only if trigger condition met)
  - .project-orchestration/tasks/{task_id}/reports/execution.md updated with Task Changelog
  - .project-orchestration/tasks/{task_id}/reports/execution.md updated with Impact Closure
  - .project-orchestration/tasks/{task_id}/reports/execution.md updated with Drift Check
  - docs/ai/tasks/{task_id}/task-summary.md written with compact continuity summary
  - .project-orchestration/tasks/{task_id}/session.json: stage_status: complete
  - docs/ai/tasks/{task_id}/handoff.md: status set to complete; final summary written
  - .project-orchestration/status.json: entry updated (stage_reached: 7, stage_status: complete, pr_url if known)

state_on_complete:
  stage_reached: 7
  stage_status: complete
  blocker: null

state_on_interrupt:
  stage_reached: 7
  stage_status: in_progress
  blocker: "<ADR final status missing | task changelog incomplete | impact closure incomplete | drift check failed>"

resume_entry_point: "finish execution.md Task Changelog / Impact Closure / Drift Check, write task-summary.md, and finalize ADR status"
```

---

## Session state transitions (summary)

```
Stage -1 complete → stage_reached: -1, stage_status: complete
Stage 0  complete → stage_reached:  0, stage_status: complete, source_mode set
Stage 1  complete → stage_reached:  1, stage_status: complete
Stage 2  complete → stage_reached:  2, stage_status: complete, requirements_approved: true
Stage 2.5 complete → stage_reached: 2.5, stage_status: complete, adr_status set
Stage 3  complete → stage_reached:  3, stage_status: complete, code_owner set
Stage 4  complete → stage_reached:  4, stage_status: complete
Stage 5  complete → stage_reached:  5, stage_status: complete
Stage 6  complete → stage_reached:  6, stage_status: complete
Stage 7  complete → stage_reached:  7, stage_status: complete  ← task done

Any interrupt → stage_status: in_progress, blocker: "<reason>"
```

---

## Updated `session.json` schema

**Path:** `.project-orchestration/tasks/{task_id}/session.json`

```json
{
  "task_id": "ANDROID-42 | task-slug",
  "started_at": "2026-05-07T09:00:00Z",
  "updated_at": "2026-05-07T11:30:00Z",
  "stage_reached": -1,
  "stage_status": "complete | in_progress | blocked",
  "source_mode": "A | B | C",
  "code_owner": "agent-name | null",
  "assignee": "dev-name | agent-name | unassigned",
  "handoff_to": "dev-name | null",
  "branch": "feature/ANDROID-42-login | null",
  "pr_url": "https://github.com/org/repo/pull/123 | null",
  "requirements_approved": false,
  "adr_required": false,
  "adr_status": "proposed | accepted | deferred | superseded | not_required | null",
  "decision_record": "docs/ai/decisions/ADR-NNNN-slug.md | null",
  "workflow_mode": "fast | standard | governed | null",
  "preliminary_mode": "fast | standard | governed | null",
  "mode_override": "fast | standard | governed | null",
  "complexity_score": 0,
  "risk_score": 0,
  "change_type": "ui_change | database_change | network_change | dependency_change | architecture_change | logic_change | test_change | config_change | multi | null",
  "module_impact_chain_scope": "single | local-chain | full-project | null",
  "evidence_collected": [],
  "impact_closure_status": "not_started | partial | complete | blocked | null",
  "follow_up_watchlist": [],
  "blocker": "null | <human-readable reason>",
  "partial_outputs": []
}
```

`partial_outputs` lists artifact paths written before an interrupt — safe to re-read on resume. Agent must NOT re-run work that produced these outputs unless explicitly asked.
