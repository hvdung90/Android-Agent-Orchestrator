# Sub-agent Catalog and Dependency Rules

## Design principle

Sub-agents are workers, not authorities.

They may read, extract, compare, score, or recommend. They do not own final requirements, final design, final provisioning decisions, or product-code edits.

---

## Source readers

### Jira Reader

```yaml
source_type: jira
feature_id: <ticket key>
summary: <short>
acceptance_criteria: []
linked_docs: []
linked_designs: []
linked_issues: []
status_signals: []
open_questions_found: []
```

### Confluence Reader

```yaml
source_type: confluence
page_title: <title>
business_rules: []
flows: []
constraints: []
decisions_logged: []
unknowns_found: []
```

### Figma Reader

```yaml
source_type: figma
file_name: <name>
screens: []
components: []
visible_states: [loading, error, empty, success]
cta_labels: []
notes: []
missing_states: []
```

### Doc Reader

```yaml
source_type: doc
files_read: []
intent_summary: <short>
scope_signals: []
out_of_scope_signals: []
architecture_constraints: []
open_questions_found: []
assumed_facts: []
```

### Graph Impact Reader

```yaml
source_type: graphify
graph_available: true | false
graph_path: <A -> B -> C | none>
affected_components: []
god_nodes_touched: []
surprising_connections: []
repo_constraints: []
undocumented_dependencies: []
graph_freshness_note: <fresh | stale | unknown | graph missing>
```

---

## Analysis workers

### Ambiguity Detector

```yaml
source_type: ambiguity-analysis
ambiguous_items:
  - field: <source field or section>
    issue: <description>
    severity: blocker | major | minor
    example: <quote or reference>
overall_clarity_score: 0-10
recommendation: ready | clarify | block
```

### Conflict Detector

```yaml
source_type: conflict-analysis
conflicts:
  - id: conflict-1
    source_a: <source type + field>
    source_b: <source type + field>
    description: <what differs>
    impact: scope | behavior | api | architecture
    severity: blocker | major | minor
    resolution_options: []
conflict_count: <n>
recommendation: proceed-with-assumption | block-for-decision
```

### Missing-info Detector

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

### State Extractor

```yaml
source_type: state-extraction
states:
  - name: loading | success | empty | error | offline | permission-denied | retry
    source: figma | jira | confluence | doc | inferred
    ui_behavior: <what happens>
    business_rule: <what triggers this state>
    exit_condition: <how user/system leaves this state>
missing_states: []
edge_cases: []
```

### Dependency Impact Analyzer

```yaml
source_type: dependency-impact
direct_changes:
  - component: <name>
    layer: ui | domain | data | infra
    change_type: add | modify | delete
    risk: low | medium | high
indirect_impacts:
  - component: <name>
    reason: <why affected>
    action_needed: monitor | update | test | notify
migration_order: []
estimated_surface: small | medium | large
```

---

## Advisory workers

### Research Advisor

```yaml
source_type: research-advisory
question: <research question>
options:
  - name: <option>
    pros: []
    cons: []
    fits_current_stack: true | false
    complexity: low | medium | high
recommendation: <option + rationale>
sources_checked: []
```

### Android Advisor

```yaml
source_type: android-advisory
recommended_api_or_pattern: <name + reason>
do: []
dont: []
migration_sequence: []
compatibility_risks: []
min_sdk_impact: <api level if relevant>
```

### QA Scenario Advisor

```yaml
source_type: qa-advisory
happy_path_scenarios: []
edge_case_scenarios: []
regression_zones:
  - component: <name>
    risk: <why>
    suggested_test: <test type>
automation_candidates: []
```

### Rollout/Risk Advisor

```yaml
source_type: rollout-advisory
risk_level: low | medium | high
feature_flag_recommended: true | false
rollout_strategy: full | staged | experiment
metrics_to_monitor: []
rollback_trigger: <condition>
release_notes_draft: <short>
```

---

## Tooling Preflight Auditor

```yaml
source_type: tooling-preflight
mode: audit | bootstrap | update | refresh-graph | force-reinstall
ai_devkit:
  cli_present: true | false | unknown
  project_config_present: true | false
  action_recommended: none | install | init | install-project | update
android_cli:
  cli_present: true | false | unknown
  info_available: true | false
  action_recommended: none | install | update | init
android_skills:
  list_available: true | false
  relevant_skills_found: []
  action_recommended: none | find | add | add-all
graphify:
  cli_present: true | false | unknown
  package_present: true | false | unknown
  graph_report_present: true | false
  graph_json_present: true | false
  action_recommended: none | install | build | update
karpathy:
  guidance_present: true | false | unknown
  action_recommended: none | install-plugin | append-guidance
blockers: []
warnings: []
proceed_to_stage_0: true | false
```

---

## Parent-only responsibilities

Only the parent orchestrator may:
- choose provisioning mode,
- approve installs/updates based on user intent,
- publish preflight report,
- merge worker outputs,
- publish canonical requirements,
- select the single code owner,
- close the task.

---

## Allowed parallelism

Allowed in parallel:
- tooling read-only checks,
- source readers,
- analysis workers,
- advisory workers.

Not allowed in parallel:
- installs/updates that mutate the same tool/config,
- two workers publishing canonical requirements,
- two workers creating code patches on the same task area.
