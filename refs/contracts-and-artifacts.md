# Contracts, Artifacts, and Gates

_Skill version: 4.7.0 — update this when SKILL.md bumps a minor or major version._

---

## Canonical artifacts

Every AI-authored artifact starts with a contract header:

```yaml
artifact: <artifact-id>
version: 1.0
owner: ai-devkit | android-skills | android-cli | graphify
status: draft | proposed | approved | stable | deferred | superseded
task: <task_id or global>
```

Contract headers are required for:
- `preflight.md`
- `context-pack.json`
- `requirements/<task>.md`
- `android-memo/<task>.md`
- `design/<task>.md`
- `decisions/ADR-*.md`
- `execution.md`

### 0) `.project-orchestration/reports/preflight.md`

Purpose: records Stage -1 Tooling Preflight.

Required sections:

```markdown
# Tooling Preflight

## Mode
audit | bootstrap | update | refresh-graph | force-reinstall

## Summary
- Ready for Stage 0:
- Blocking gaps:
- Non-blocking gaps:

## Auth
- .agent-auth.yaml: present | created-empty | missing
- atlassian.api_token: set | empty
- figma.personal_access_token: set | empty
- github.personal_access_token: set | empty
- Project overrides defined: <count>

## AI DevKit
## Android CLI
## Android skills
## Graphify
## Karpathy
## Serena
## Decisions
- Tokens to request from user (just-in-time, when needed):
```

Full template: `templates/preflight-report.md`  
Full example: `examples/preflight-report.example.md`

---

### 1) `docs/ai/tasks/{task_id}/clarification/context-pack.json`

**Sparse format rule:** Only include keys that have actual values. Omit keys with empty arrays `[]`, `null`, `false` (defaults), or `0`. This reduces token cost when context-pack is re-read in later stages.

Exception: always include `feature_id`, `clarity_score`, `outcome`, `blocked`, `graph_impact`, `auth_status.file`.

```json
{
  "feature_id": "ANDROID-123 | task-brief | <slug>",
  "title": "",
  "sources": [
    {
      "type": "jira | confluence | figma | doc | ticket | note | graph | preflight",
      "ref": "<url or filename>",
      "summary": "<one-line summary>"
    }
  ],
  "history_context": {
    "task_continuity": "new | continuation | unknown",
    "scan_mode": "skipped | metadata-only | full",
    "matched_tasks": [],
    "overlap_score": "none | low | medium | high",
    "decision": "skip | read_full | ask_human",
    "summaries": [
      {
        "task_id": "<matched task id>",
        "artifacts_read": [],
        "relevant_decisions": [],
        "carry_forward_constraints": [],
        "resolved_changes": []
      }
    ]
  },
  "business_goal": "",
  "user_problem": "",
  "acceptance_criteria": [],
  "screens": [],
  "states": [],
  "dependencies": [],
  "facts": [],
  "assumptions": [],
  "unknowns": [],
  "conflicts": [],
  "decisions_needed": [],
  "recommended_v1_scope": [],
  "tooling_readiness": {
    "mode": "audit | bootstrap | update | refresh-graph | force-reinstall",
    "ai_devkit": "ready | missing | unknown",
    "android_cli": "ready | missing | unknown",
    "android_skills": "ready | partial | missing | unknown",
    "graphify": "ready | graph-missing | cli-missing | stale | unknown",
    "karpathy": "installed | manual | missing | unknown",
    "serena": "ready | missing | not-configured"
  },
  "auth_status": {
    "file": "present | created-empty | missing",
    "atlassian": "set | empty",
    "figma": "set | empty",
    "github": "set | empty",
    "active_project_override": "<name> | none"
  },
  "graph_path": "<ComponentA -> ComponentB -> ComponentC | none>",
  "god_nodes_touched": [],
  "graph_impact": "low | medium | high",
  "change_type": "ui_change | database_change | network_change | dependency_change | architecture_change | logic_change | test_change | config_change | multi",
  "module_impact_chain": {
    "affected_modules": [],
    "build_order": [],
    "test_scope_modules": [],
    "api_surface_broken": false,
    "estimated_build_scope": "single | local-chain | full-project"
  },
  "blocked": false,
  "clarity_score": 0,
  "outcome": "ready | blocked | research-loop"
}

// graph_impact guidance:
// low    — change is isolated (1 component, no shared dependencies, no god nodes)
//          → skip /graphify . --update in Stage 5
// medium — change touches 2-4 components or one shared utility
//          → run /graphify . --update in Stage 5; activate Gradle Module Impact Analyzer
// high   — change touches god nodes, crosses layer boundaries, or affects >4 components
//          → run /graphify . --update in Stage 5; optional before/after compare in Stage 6
//          → Gradle Module Impact Analyzer required; api_surface_broken check required

// change_type guidance (used by Evidence Gate Matrix in Stage 5):
// ui_change         — Compose/XML/Screen/ViewModel display logic
// database_change   — Room @Entity, @Dao, Migration, @Database schema
// network_change    — Retrofit API, data source, OkHttp, interceptor
// dependency_change — build.gradle(.kts) dependency add/remove/upgrade
// architecture_change — module restructure, DI bindings, layer boundary
// logic_change      — UseCase, Repository logic, domain model
// test_change       — test-only files; no product code touched
// config_change     — AndroidManifest, build config, ProGuard/R8, flavors
// multi             — more than one of the above; list all in facts[]

// module_impact_chain guidance:
// Populated by Gradle Module Impact Analyzer when graph_impact ≥ medium.
// Omit (sparse rule) when graph_impact = low or single-module change.

// history_context guidance:
// Omit when task_continuity = new and no metadata scan was needed.
// Include scan metadata when Stage 0 detected continuation signals or possible overlap.
// Include summaries only when full history was read.
```

---

### 2) `docs/ai/tasks/{task_id}/requirements/<task>.md`

Purpose: canonical human-reviewed requirements for the task. This artifact is generated by AI DevKit and must not be treated as accepted until human approval is recorded.

Required sections:

```markdown
---
artifact: android-requirements
version: 1.0
owner: ai-devkit
status: draft
task: <task_id>
---

# Requirements — <task title>

## Sources
- <source ref> — <fact learned>

## Facts
- <verified fact>

## Assumptions
- <assumption requiring review>

## Affected Areas
- [ ] UI / Compose
- [ ] XML Views
- [ ] Navigation
- [ ] ViewModel / state
- [ ] Repository / data
- [ ] Database / migration
- [ ] Network / API
- [ ] DI
- [ ] Gradle / build logic
- [ ] Permissions
- [ ] Background work
- [ ] Tests
- [ ] Analytics / logging
- [ ] Accessibility
- [ ] Edge-to-edge / insets

## Acceptance Criteria
- <testable behavior>

## Decision Triggers
- <module boundary | navigation | public API | ... | none>

## Verification Plan
- <required evidence from Evidence Gate Matrix>

## Out of Scope
- <explicit non-goal>
```

### 3) `docs/ai/tasks/{task_id}/design/<task>.md`

Purpose: implementation design after Requirements and Decision Gate are approved.

Required sections:

```markdown
---
artifact: android-design
version: 1.0
owner: ai-devkit
status: draft
task: <task_id>
---

# Design — <task title>

## Inputs
- requirements:
- context-pack:
- decision records:

## Affected Areas
<repeat the checklist from requirements; mark only areas touched by the design>

## Approach

## Module / API Boundaries

## State Ownership

## Test Strategy

## Rollback / Migration

## Implementation Lock
- code_owner:
- files/modules:
```

### 4) `docs/ai/tasks/{task_id}/decisions/ADR-NNNN-<slug>.md`

Purpose: short decision record for Android tasks with architectural or broad behavioral impact.

Create only when Stage 2.5 finds one or more decision triggers. Use `docs/ai/decisions/0000-template.md` as the global template.

Required front matter:

```yaml
artifact: android-adr-lite
version: 1.0
owner: ai-devkit
status: proposed | accepted | deferred | superseded
task: <task_id>
```

Required sections:
- Context
- Decision
- Alternatives
- Consequences
- Validation
- Related

### 5) `.project-orchestration/tasks/{task_id}/reports/execution.md`

Purpose: final evidence manifest, gate log, task changelog, drift check, and close status.

Required Task Changelog section:

```markdown
## Task Changelog

| Item | Before | After | Evidence |
|---|---|---|---|
| <behavior/area> | <previous state> | <new state> | <test/screenshot/log/ADR> |
```

Required Drift Check section:

```markdown
## Drift Check

- [ ] README current version matches SKILL.md metadata.version
- [ ] CHANGELOG latest version matches SKILL.md metadata.version
- [ ] refs/* Skill version headers match SKILL.md metadata.version
- [ ] all refs listed in SKILL.md metadata exist
- [ ] all templates/examples referenced by refs exist
- [ ] artifact schema examples match this contract
- [ ] no stale stage names
- [ ] no invented command names
- [ ] public repo version sync checked against installed/local skill when applicable
```

---

## Stage gates

### Gate -1 — Tooling Preflight complete

Required:
- `.agent-auth.yaml` initialized (present or auto-created),
- token status recorded (set / empty) for atlassian, figma, github,
- provisioning mode recorded,
- AI DevKit checked,
- Android CLI checked,
- Android skills checked if Android CLI exists,
- Graphify checked,
- graph state recorded,
- Karpathy state recorded,
- Serena checked (uv present, MCP configured or not; always non-blocking),
- action permissions recorded,
- blockers recorded,
- decision: proceed to Stage 0 yes/no.

### Gate A — Intake complete

Required:
- source list exists,
- graph availability checked,
- preflight report consumed,
- initial task scope noted.

### Gate B — Discovery complete

Required:
- graph overview read if present,
- raw sources read,
- discovery notes stored in `docs/ai/tasks/{task_id}/discovery/`.

### Gate C — Clarification complete

Required:
- `context-pack.json`,
- `clarification-brief.md`,
- clarity report or embedded clarity section,
- Serena Code Analysis Worker outputs attached or summarized (if Serena ready and triggers fired),
- parent outcome chosen.

### Gate D — Requirements complete

Required:
- canonical requirements doc exists,
- artifact version header present,
- Affected Areas checklist completed,
- facts and assumptions separated,
- decision triggers recorded,
- human approval recorded.

### Gate D.5 — Decision Gate complete

Required:
- ADR trigger checklist evaluated,
- if ADR required: Proposed ADR exists and human approval or deferral is recorded,
- if ADR not required: `adr_required: false` and reason recorded in `session.json`,
- decision owner and required validation evidence recorded.

### Gate E — Design ready

Required:
- design doc exists,
- Android memo exists if Android-specific,
- approved or deferred ADR-lite linked if one was required,
- single code owner selected.

### Gate F — Verification ready

Required:
- All **required** evidence items for the task's `change_type` collected (see Evidence Gate Matrix below),
- Graphify update run if `graph_impact ≥ medium`,
- acceptance coverage checked,
- `module_impact_chain.build_order` modules all built successfully (if module_impact_chain present).

### Gate G — Close ready

Required:
- Karpathy diff review passed,
- final execution report written,
- Task Changelog completed,
- ADR-lite status finalized (`Accepted`, `Deferred`, or `Superseded`) if present,
- drift checks completed,
- no unresolved blockers remain.

---

## Evidence Gate Matrix

Android CLI uses `context-pack.json → change_type` to determine which evidence commands to run in Stage 5. Gate F is satisfied only when all **required** items are present.

When `change_type` is `multi`, apply the union of required items for each applicable type.

| change_type | Required evidence | Optional evidence |
|---|---|---|
| `ui_change` | screenshot_before + screenshot_after, layout_inspector_capture | accessibility_report, animated_state_recording |
| `database_change` | migration_test_pass, room_schema_diff | db_inspector_screenshot, populated_query_log |
| `network_change` | logcat_network_capture, api_contract_test_pass | charles_proxy_har, mock_server_recording |
| `dependency_change` | build_success_all_modules, license_check_pass | binary_size_diff, dependency_tree_diff |
| `architecture_change` | graphify_updated, module_dependency_diff | architecture_decision_record, before_after_graph_compare |
| `logic_change` | unit_test_pass, coverage_report (≥ 80% on changed files) | integration_test_pass, scenario_trace_log |
| `test_change` | test_pass (no product code changed) | coverage_delta_report |
| `config_change` | build_success_release_variant, manifest_diff | lint_report, proguard_mapping_diff |

### Evidence command reference (Android CLI)

```yaml
evidence_commands:
  screenshot_before:        "adb exec-out screencap -p > evidence/screen_before.png  (run BEFORE Stage 4)"
  screenshot_after:         "adb exec-out screencap -p > evidence/screen_after.png   (run at Stage 5)"
  layout_inspector_capture: "android capture layout --output evidence/layout.xml"
  migration_test_pass:      "./gradlew :<db_module>:test --tests '*MigrationTest*'"
  room_schema_diff:         "git diff HEAD~1 -- '**/schemas/**/*.json'"
  logcat_network_capture:   "adb logcat -s OkHttp:D > evidence/network.log  (during smoke test)"
  api_contract_test_pass:   "./gradlew :<network_module>:test --tests '*ContractTest*'"
  build_success_all_modules: "./gradlew $(echo $BUILD_ORDER | tr ' ' '\n' | sed 's/^//' | xargs -I{} echo {}:assembleDebug) --continue"
  license_check_pass:       "./gradlew dependencyCheckAnalyze  (or licensee)"
  binary_size_diff:         "bundletool get-size total --apks=release.apks"
  graphify_updated:         "/graphify . --update"
  module_dependency_diff:   "git diff HEAD~1 -- '**/build.gradle*' '**/settings.gradle*'"
  unit_test_pass:           "./gradlew :affected_module:test"
  coverage_report:          "./gradlew :affected_module:jacocoTestReport"
  build_success_release_variant: "./gradlew assembleRelease"
  manifest_diff:            "git diff HEAD~1 -- '**/AndroidManifest.xml'"
```

### Evidence derivation rule

Android CLI derives required evidence at the start of Stage 5:

1. Read `context-pack.json → change_type`.
2. Look up required evidence items from the matrix.
3. If `module_impact_chain` present: replace single-module commands with `build_order`-scoped equivalents.
4. Run required items; collect optional items when tooling is ready.
5. Write collected evidence paths to `.project-orchestration/tasks/{task_id}/evidence/` and list them in `execution.md`.

---

---

## Local memory schemas

**Global** (shared across tasks, stored in `.project-orchestration/memory/`):
- `tooling-cache.json` — Stage -1 cache
- `preflight.md` written to `.project-orchestration/reports/`

**Per-task** (stored in `.project-orchestration/tasks/{task_id}/`):
- `session.json`, `skip-log.json`, `memory/graph-stamp.json`, `reports/execution.md`, `evidence/**`

All paths in `.project-orchestration/` are gitignored.

### `tooling-cache.json`

Cache Stage -1 results to skip preflight if tooling has not changed.

```json
{
  "checked_at": "2026-05-05T09:00:00Z",
  "valid_until": "2026-05-06T09:00:00Z",
  "graph_commit": "abc1234",
  "ai_devkit": "2.1.0 | missing",
  "android_cli": "present | missing",
  "android_cli_version": "34",
  "graphify": "0.9.1 | missing",
  "karpathy": "installed | manual | missing",
  "auth_file": "present | missing"
}
```

**Skip rule:** If `valid_until` > now AND `graph_commit` == `git rev-parse HEAD` → skip Stage -1 tool checks entirely. Load cached values into preflight context and proceed to Stage 0.  
**Invalidate when:** any tool is installed/updated, or TTL expires (default 24h).

### `session.json`

In-progress task state — allows resume after an interruption.

```json
{
  "task_id": "ANDROID-42 | task-slug",
  "started_at": "2026-05-07T09:00:00Z",
  "updated_at": "2026-05-07T11:30:00Z",
  "stage_reached": -1,
  "stage_status": "complete | in_progress | blocked",
  "source_mode": "A | B | C",
  "task_continuity": "new | continuation | unknown",
  "history_scan": {
    "performed": true,
    "mode": "skipped | metadata-only | full",
    "matched_tasks": [],
    "overlap_score": "none | low | medium | high",
    "decision": "skip | read_full | ask_human"
  },
  "code_owner": "agent-name | null",
  "requirements_approved": false,
  "adr_required": false,
  "adr_status": "proposed | accepted | deferred | superseded | not_required | null",
  "decision_record": "docs/ai/tasks/{task_id}/decisions/ADR-NNNN-slug.md | null",
  "change_type": "ui_change | database_change | network_change | dependency_change | architecture_change | logic_change | test_change | config_change | multi | null",
  "module_impact_chain_scope": "single | local-chain | full-project | null",
  "evidence_collected": [],
  "blocker": "null | <human-readable reason>",
  "partial_outputs": []
}
```

**Path:** `.project-orchestration/tasks/{task_id}/session.json`

**Resume rule:** At Stage -1, scan `.project-orchestration/tasks/` for any `session.json` with `stage_status: in_progress`. Ask user: "Resume task `<task_id>` from Stage `<stage_reached>`?" If yes, skip stages already completed per compliance matrix. If no, overwrite session.

**Interrupt safety:** On any error or interruption, write interrupt state before stopping. `partial_outputs` lists artifact paths written before the interrupt — agent must not re-run those steps on resume unless explicitly asked. See `refs/stage-contracts.md` for per-stage interrupt state and `resume_entry_point`.

### `skip-log.json`

**Path:** `.project-orchestration/tasks/{task_id}/skip-log.json`

Append-only audit log of every skipped step. Written on auto-skips and confirm-skips. Never deleted.

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
    }
  ]
}
```

See `refs/compliance-policy.md` for full tier definitions and confirmation protocol.

### `graph-stamp.json`

**Path:** `.project-orchestration/tasks/{task_id}/memory/graph-stamp.json`

Metadata about the most recent Graphify run.

```json
{
  "built_at": "2026-05-05T08:00:00Z",
  "commit_sha": "abc1234",
  "graph_report": "graphify-out/GRAPH_REPORT.md",
  "god_nodes": ["AppModule", "NetworkClient"],
  "component_count": 42
}
```

**Freshness rule:** If `commit_sha` == `git rev-parse HEAD` → graph is fresh; skip rebuild check. If commits have landed since `built_at` → flag graph as potentially stale in preflight.

---

## Graphify stage trigger rules

| Stage | Trigger | Action |
|---|---|---|
| Stage -1 | Always | Check Graphify CLI/package and graph files |
| Intake | Check existence | Note graph present/absent |
| Discovery | Graph exists | Read `GRAPH_REPORT.md`; query affected area |
| Clarification | Graph exists | Graph Impact Reader feeds dependencies into context-pack |
| Design split | Graph exists | Use graph rationale if needed |
| Implementation | — | No graph queries during coding |
| Verify | Graph exists | `/graphify . --update` after implementation |
| QA gate | Graph exists | Optional compare before/after; check god nodes |

---

## Ownership rules

| Artifact | Path | Owner | Others may |
|---|---|---|---|
| `preflight.md` | `.project-orchestration/reports/preflight.md` | Parent orchestrator | provide raw audit output |
| `tooling-cache.json` | `.project-orchestration/memory/tooling-cache.json` | Stage -1 only | read only |
| `session.json` | `.project-orchestration/tasks/{task_id}/session.json` | Parent orchestrator | read only |
| `skip-log.json` | `.project-orchestration/tasks/{task_id}/skip-log.json` | Parent orchestrator | read only |
| `context-pack.json` | `docs/ai/tasks/{task_id}/clarification/context-pack.json` | Parent orchestrator / AI DevKit | propose raw fields |
| `clarification-brief.md` | `docs/ai/tasks/{task_id}/clarification/clarification-brief.md` | Parent orchestrator / AI DevKit | recommend wording |
| `requirements/<task>.md` | `docs/ai/tasks/{task_id}/requirements/` | Parent orchestrator / AI DevKit | review only |
| `decisions/ADR-*.md` | `docs/ai/tasks/{task_id}/decisions/` | Parent orchestrator / AI DevKit | advise; human approves |
| `design/<task>.md` | `docs/ai/tasks/{task_id}/design/` | Parent orchestrator / AI DevKit | review only |
| `android-memo/<task>.md` | `docs/ai/tasks/{task_id}/android-memo/` | Android skills | supply advice only |
| runtime evidence | `.project-orchestration/tasks/{task_id}/evidence/` | Android CLI | request commands |
| `execution.md` | `.project-orchestration/tasks/{task_id}/reports/execution.md` | Parent orchestrator | append evidence paths |
| `graphify-out/**` | `graphify-out/` | Graphify | consume/query only |
| `docs/ai/inputs/**` | `docs/ai/inputs/` | Human | never overwritten by agent |

---

## Decision Ownership

| Area | Owner lane | Required evidence |
|---|---|---|
| Compose UI | Android skills | screenshot + layout behavior |
| XML Views | Android skills | before/after screenshot + view binding/layout check |
| Navigation | AI DevKit + Android skills | route/back stack test + ADR-lite if graph changes |
| ViewModel / state | AI DevKit | unit test + state ownership note |
| Repository / data | AI DevKit | unit/integration test + API contract note |
| Database / migration | Android skills + Android CLI | migration test + schema diff |
| Network / API | AI DevKit + Android CLI | contract test + network log/mock evidence |
| DI | AI DevKit | compile/build output + injection path check |
| Gradle / build logic | Android skills + Android CLI | build output + dependency/module diff |
| Permissions / background work | Android skills + Android CLI | manifest diff + runtime evidence |
| Billing / auth / notifications | Android skills + Android CLI | scenario test + runtime evidence |
| Architecture impact | Graphify | graph diff/report |
| Final go/no-go | AI DevKit | requirements coverage + Gate log |

---

## AI-authored artifact rules

- Do not treat generated requirements as accepted until human approval is recorded.
- Record assumptions separately from facts.
- If a decision changes architecture or broad behavior, create ADR-lite.
- If sources conflict, preserve both claims and block for clarification.
- If verification evidence is missing, final status cannot be success.

---

## Approval rule

Do not proceed from Requirements to Design/Implementation without explicit human approval.
