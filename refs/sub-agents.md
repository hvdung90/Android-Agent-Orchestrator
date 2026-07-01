# Sub-agent Catalog and Dependency Rules

_Skill version: 4.12.0 — update this when SKILL.md bumps a minor or major version._

## Design principle

Sub-agents are workers, not authorities.

They may read, extract, compare, score, or recommend. They do not own final requirements, final design, final provisioning decisions, or product-code edits.

---

## Source readers

### Jira Reader

Required auth (check before running — see `refs/auth-bootstrap.md` Step 2):
- `atlassian.domain`
- `atlassian.email`
- `atlassian.api_token`

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

**Auto-follow rule:** After extracting the ticket, immediately fetch and run the appropriate reader for each item in `linked_docs` and `linked_designs`:

| Attachment type | Reader to run |
|---|---|
| Confluence page URL | Confluence Reader |
| Figma link | Figma Reader |
| Google Doc / PDF / markdown | Doc Reader |
| Another Jira ticket | Jira Reader (one level deep only) |
| Image / screenshot | record URL in `linked_designs`, do not fetch |

Do not follow links recursively beyond one level. If a linked Confluence page itself links further pages, stop at the first page.

### Confluence Reader

Required auth: `atlassian.domain` + `atlassian.email` + `atlassian.api_token`
(Same token as Jira. If Jira Reader has already authenticated in this session → reuse it and do not ask again.)

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

Required auth: `figma.personal_access_token`

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

Reads whichever architecture-map tool is active (Understand-Anything checked first; Graphify is the fallback).

```yaml
source_type: architecture-map
tool: understand-anything | graphify | none
graph_available: true | false
graph_path: <A -> B -> C | none>
affected_components: []
god_nodes_touched: []
surprising_connections: []
repo_constraints: []
undocumented_dependencies: []
graph_freshness_note: <fresh | stale | unknown | graph missing>
```

### Gradle Module Impact Analyzer

Activated at Stage 1 Discovery when `graph_impact ≥ medium` OR when affected components span more than one Gradle module. Read-only. Never edits build files.

**Inputs:** active architecture-map output (`.understand-anything/knowledge-graph.json` or `graphify-out/GRAPH_REPORT.md`) affected components list + `settings.gradle[.kts]` module declarations.

**Purpose:** Map architecture-level components to their Gradle module boundaries, derive the full build/test scope, and detect API surface changes that ripple across module boundaries.

```yaml
source_type: gradle-module-impact
trigger: graph_impact >= medium OR cross_module_change detected
modules_scanned:
  - path: <:feature:auth>
    type: feature | core | data | app | lib
    api_surface: true | false      # exposes api() dependencies
modules_affected:
  - module: <:feature:auth>
    reason: <direct change | transitive dependency | api surface consumer>
    change_type: add | modify | delete
    build_required: true | false
    test_scope: unit | integration | instrumented | none
build_order:
  - <:core:network>              # ordered leaf → root
  - <:feature:auth>
  - <:app>
api_surface_broken: true | false  # true = breaking change in api() module
test_scope_modules: []            # modules that must run tests
estimated_build_scope: single | local-chain | full-project
recommendation: <one-line note for code owner and Android CLI>
```

**Output feeds into:** `context-pack.json → module_impact_chain`; Stage 5 Android CLI build command scope.

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

## Code Analysis workers

### Code Analysis Worker (Serena)

Read-only and advisory. Never calls code-touching tools. Activated by parent orchestrator.

**Prerequisite:** Serena MCP configured (`serena: ready` in preflight report). Non-blocking if missing — silently skip and note in report.

**Activation is agent-decided**, based on conditions below. No manual trigger required.

#### When agent activates (auto-decided)

| Condition | Stage | Tool called |
|---|---|---|
| Architecture map identified affected components | 1 Discovery | `get_symbols_overview` |
| Specific symbol named in architecture-map output or task | 1 Discovery | `find_symbol` |
| Abstract class / interface in change path | 1.5 Clarification | `find_implementations` |
| Surprising connection found by Graph Impact Reader | 1.5 Clarification | `find_referencing_symbols` |
| Missing-info flags unknown implementation pattern | 1.5 Clarification | `find_referencing_symbols` |
| Code owner needs usage pattern before editing | 4 Implementation (advisory) | `find_declaration` |
| graph_impact ≥ medium AND Kotlin LS confirmed stable | 5 Verify | `get_diagnostics_for_file` |
| Scope discipline check at QA gate | 6 QA (optional) | `find_referencing_symbols` |

#### Backend selection (dev-decided, not agent-decided)

| Backend | Condition | Accuracy |
|---|---|---|
| LSP default | `uv` + serena installed; no IDE required | Good |
| JetBrains plugin | Android Studio running; dev opts in | Full IDE accuracy |

Default is LSP. Agent does not start Android Studio. Dev configures JetBrains backend separately.

#### Kotlin LS stability gate

Kotlin Language Server is pre-alpha. Before calling `get_diagnostics_for_file` or `get_diagnostics_for_symbol`:
- If dev confirms Kotlin LS stable → proceed.
- If stability unknown → skip diagnostics; note in report: `"serena diagnostics skipped: kotlin-ls pre-alpha"`.

#### Tools NEVER called by agent (code owner only)

`rename_symbol` · `replace_symbol_body` · `insert_before_symbol` · `insert_after_symbol` · `safe_delete_symbol` · `jet_brains_move` · `jet_brains_inline_symbol` · all other mutation tools.

#### YAML output contract

```yaml
source_type: serena-analysis
stage: discovery | clarification | implementation-advisory | verify | qa
query_type: symbol-overview | find-symbol | find-implementations | find-referencing | find-declaration | diagnostics
symbol_queried: <name or "area overview">
component_layer: ui | domain | data | infra | unknown
android_pattern: ViewModel | Repository | UseCase | Navigator | DI-module | none
results:
  - symbol: <qualified name>
    kind: class | interface | function | property | object
    file: <relative path>
    line: <n>
    summary: <one-line>
callers_count: <n>
implementors_count: <n>
diagnostics: []            # only when get_diagnostics_* called
kotlin_ls_stable: true | false | unknown
recommendation: <one-line impact note for parent orchestrator>
```

---

## Tooling Preflight Auditor

```yaml
source_type: tooling-preflight
mode: audit | bootstrap | update | refresh-graph | force-reinstall
spec_kit:
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
architecture_map:
  active_tool: understand-anything | graphify | none
  understand_anything:
    plugin_present: true | false | unknown
    graph_present: true | false
  graphify:
    cli_present: true | false | unknown
    package_present: true | false | unknown
    graph_report_present: true | false
    graph_json_present: true | false
  action_recommended: none | install | build | update
karpathy:
  guidance_present: true | false | unknown
  action_recommended: none | install-plugin | append-guidance
serena:
  uv_present: true | false
  mcp_configured: true | false
  backend: lsp | jetbrains | unknown
  kotlin_ls_stable: true | false | unknown
  action_recommended: none | install | configure
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
- source readers (including Gradle Module Impact Analyzer),
- analysis workers,
- advisory workers.

Not allowed in parallel:
- installs/updates that mutate the same tool/config,
- two workers publishing canonical requirements,
- two workers creating code patches on the same task area.
