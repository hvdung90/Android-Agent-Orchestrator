# Sub-agent Catalog and Dependency Rules

## Design principle

Sub-agents are workers, not authorities.
They may read, extract, compare, score, or recommend.
They do not own final requirements, final design, or product-code edits.

---

## Worker groups

## A. Source readers

### 1) Jira Reader
**Purpose:** extract delivery intent from ticket data.

**Input:** Jira URL or normalized ticket payload.

**Output contract:**
```yaml
source_type: jira
feature_id: <ticket key>
summary: <short>
acceptance_criteria: [..]
linked_docs: [..]
linked_designs: [..]
linked_issues: [..]
status_signals: [..]
open_questions_found: [..]
```

---

### 2) Confluence Reader
**Purpose:** extract business rules and process context.

**Input:** Confluence URL or page content.

**Output contract:**
```yaml
source_type: confluence
page_title: <title>
business_rules: [..]
flows: [..]
constraints: [..]
decisions_logged: [..]
unknowns_found: [..]
```

---

### 3) Figma Reader
**Purpose:** extract UI structure and visible states.

**Input:** Figma URL or exported summary.

**Output contract:**
```yaml
source_type: figma
file_name: <n>
screens: [..]
components: [..]
visible_states: [loading, error, empty, success]
cta_labels: [..]
notes: [..]
missing_states: [..]       # states visible in code/graph but not in Figma
```

---

### 4) Doc Reader
**Purpose:** extract task/architecture intent from local markdown docs.

**Use when:** only `docs/ai/inputs/` files exist — no Jira, no Figma, no Confluence.

**Input:** files under `docs/ai/inputs/` (task-brief.md, architecture.md, features.md, design-notes.md, etc.)

**Output contract:**
```yaml
source_type: doc
files_read: [..]
intent_summary: <short>
scope_signals: [..]           # what is explicitly in scope
out_of_scope_signals: [..]    # what is explicitly excluded
architecture_constraints: [..]
open_questions_found: [..]
assumed_facts: [..]
```

---

### 5) Graph Impact Reader
**Purpose:** map repo reality and impact area.

**Input:** `graphify-out/graph.json` + task keyword or entry point.

**Output contract:**
```yaml
source_type: graphify
graph_path: <A -> B -> C>
affected_components: [..]
god_nodes_touched: [..]
surprising_connections: [..]
repo_constraints: [..]        # patterns or rules implied by graph structure
undocumented_dependencies: [..] # things graph shows but task docs don't mention
```

---

## B. Analysis workers

### 6) Ambiguity Detector
**Purpose:** identify vague behavior, underspecified business rules, unclear scope.

**Input:** any source reader outputs, raw docs.

**Output contract:**
```yaml
source_type: ambiguity-analysis
ambiguous_items:
  - field: <source field or section>
    issue: <description of the vagueness>
    severity: blocker | major | minor
    example: <quote or reference from source>
overall_clarity_score: 0-10   # 0 = completely unclear, 10 = crystal clear
recommendation: ready | clarify | block
```

**Severity guide:**
- `blocker` — cannot write acceptance criteria without resolving this.
- `major` — will cause rework if assumed wrong.
- `minor` — safe to assume with a documented assumption.

---

### 7) Conflict Detector
**Purpose:** find contradictions between sources (Jira vs Figma, docs vs graph, etc.)

**Input:** two or more source reader outputs.

**Output contract:**
```yaml
source_type: conflict-analysis
conflicts:
  - id: conflict-1
    source_a: <source type + field>
    source_b: <source type + field>
    description: <what they say differently>
    impact: scope | behavior | api | architecture
    severity: blocker | major | minor
    resolution_options:
      - <option 1>
      - <option 2>
conflict_count: <n>
recommendation: proceed-with-assumption | block-for-decision
```

---

### 8) Missing-info Detector
**Purpose:** find absent acceptance criteria, APIs, states, dependencies, metrics, rollout notes, ownership.

**Input:** source reader outputs + clarification-brief if exists.

**Output contract:**
```yaml
source_type: missing-info-analysis
missing_items:
  - category: acceptance_criteria | api | state | dependency | metric | rollout | ownership | error_handling
    description: <what is missing>
    severity: blocker | major | minor
    suggested_default: <safe assumption if unblocked>
completeness_score: 0-10
recommendation: ready | clarify | block
```

---

### 9) State Extractor
**Purpose:** build a state map — happy path, loading, empty, error, offline, permission, retry.

**Input:** Figma Reader output + Jira/Confluence behavior notes + Doc Reader output if no Figma.

**Output contract:**
```yaml
source_type: state-extraction
states:
  - name: loading | success | empty | error | offline | permission-denied | retry
    source: figma | jira | confluence | doc | inferred
    ui_behavior: <what happens on screen>
    business_rule: <what triggers this state>
    exit_condition: <how user or system leaves this state>
missing_states: [..]     # states likely needed but not found in any source
edge_cases: [..]
```

---

### 10) Dependency Impact Analyzer
**Purpose:** map feature/request to modules, layers, services, and likely change surface.

**Input:** Graph Impact Reader output + source reader outputs.

**Output contract:**
```yaml
source_type: dependency-impact
direct_changes:
  - component: <name>
    layer: ui | domain | data | infra
    change_type: add | modify | delete
    risk: low | medium | high
indirect_impacts:
  - component: <name>
    reason: <why it is affected>
    action_needed: monitor | update | test | notify
migration_order: [..]     # suggested order if multiple components change
estimated_surface: small | medium | large
```

---

## C. Advisory workers

### 11) Research Advisor
**Purpose:** produce comparable options and trade-offs when the task is directionally clear but not solution-complete.

**Input:** `context-pack.json` + specific research question.

**Output contract:**
```yaml
source_type: research-advisory
question: <what was researched>
options:
  - name: <option>
    pros: [..]
    cons: [..]
    fits_current_stack: true | false
    complexity: low | medium | high
recommendation: <option name + brief rationale>
sources_checked: [..]
```

---

### 12) Android Advisor
**Purpose:** produce Android memo inputs — recommended patterns, pitfalls, compatibility notes.

**Input:** `context-pack.json` + affected components from Graph Impact Reader.

**Output contract:**
```yaml
source_type: android-advisory
recommended_api_or_pattern: <name + reason>
do: [..]
dont: [..]
migration_sequence: [..]    # ordered steps if this is a migration
compatibility_risks: [..]
min_sdk_impact: <api level if relevant>
```

---

### 13) QA Scenario Advisor
**Purpose:** produce likely test scenarios and regression zones.

**Input:** requirements or clarification brief.

**Output contract:**
```yaml
source_type: qa-advisory
happy_path_scenarios: [..]
edge_case_scenarios: [..]
regression_zones:
  - component: <name>
    risk: <why it might regress>
    suggested_test: <test type>
automation_candidates: [..]
```

---

### 14) Rollout/Risk Advisor
**Purpose:** produce release-risk notes, feature-flag suggestions, metrics to monitor.

**Input:** `context-pack.json` + Dependency Impact output.

**Output contract:**
```yaml
source_type: rollout-advisory
risk_level: low | medium | high
feature_flag_recommended: true | false
rollout_strategy: full | staged | experiment
metrics_to_monitor: [..]
rollback_trigger: <condition>
release_notes_draft: <short>
```

---

## Parent-only responsibilities

Only the parent orchestrator may:
- merge worker outputs,
- score readiness officially,
- publish `context-pack.json`,
- publish `clarification-brief.md`,
- publish canonical requirements,
- decide whether to block, re-research, or proceed,
- select the single code owner,
- close the task.

---

## Waiting dependencies

### Required before `context-pack.json`
- at least one source reader (Jira / Confluence / Figma / Doc / Graph Impact)
- Graph Impact Reader when `graphify-out/` exists
- Ambiguity Detector
- Missing-info Detector

### Required before `clarification-brief.md`
- `context-pack.json`
- Conflict Detector if two or more sources exist
- State Extractor if UI or UX is involved

### Required before requirements
- `clarification-brief.md`
- explicit parent decision = `ready-for-requirements`

### Required before implementation
- approved requirements
- design doc
- Android memo if Android-specific
- chosen single code owner

---

## Allowed parallelism

**Allowed in parallel:**
- Jira Reader + Confluence Reader + Figma Reader + Doc Reader + Graph Impact Reader
- Ambiguity Detector + Conflict Detector + Missing-info Detector + State Extractor + Dependency Impact Analyzer
- Research Advisor + Android Advisor + QA Scenario Advisor + Rollout/Risk Advisor

**Not allowed in parallel:**
- two workers publishing canonical requirements
- two workers publishing final design
- two workers creating code patches on the same task area

---

## Escalation rules

Escalate to parent immediately when:
- two sources directly conflict on a business rule,
- a graph constraint invalidates the task doc assumption,
- requirements would depend on a missing product decision,
- research yields more than one plausible v1 path.
