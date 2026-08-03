# Android Agent Orchestrator — Complete Flow

_Reflects skill v4.18.0. Update when SKILL.md changes._

---

## 1. Entry point — Determine task type

```
Developer provides task
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│  What type of task is this?                               │
└───────────────────────────────────────────────────────────┘
        │
        ├── Analyze / inspect repo        ──► [A] Analyze repo
        ├── Setup / first-time tool install ─► [B] Bootstrap repo
        ├── Update tooling                ──► [C] Update tools
        ├── Rebuild architecture graph    ──► [D] Refresh graph
        ├── New feature                   ──► [E] New feature
        ├── Edit existing feature         ──► [F] Edit feature
        ├── Fix bug                       ──► [G] Bug fix
        ├── XML → Compose migration       ──► [H] Migration
        ├── AGP / build modernization     ──► [I] AGP upgrade
        └── Unfamiliar codebase + raw brief ─► [J] Unfamiliar codebase

All task types start with Stage -1.
[A][B][C][D] end after Stage -1.
[E]–[J] go through Stage 0–7. Some stages may be minimal, but each gate is considered.
```

---

## 2. Stage -1 — Tooling Preflight

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE -1: TOOLING PREFLIGHT                                    │
│  Ref: refs/provisioning-preflight.md                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Auth init (refs/auth-bootstrap.md Step 1):           │
    │  .agent-auth.yaml present? No → auto-create           │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  status.json init:                                    │
    │  .project-orchestration/status.json present?          │
    │    Yes → read; surface blocked/in-progress tasks      │
    │    No  → create with tasks: []                        │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Cache check (tooling-cache.json):                    │
    │                                                       │
    │  valid_until in future                                │
    │  AND graph_commit == git rev-parse HEAD?              │
    │         │                                             │
    │    ┌────┴────┐                                        │
    │   Yes        No                                       │
    │    │          │                                       │
    │    ▼          ▼                                       │
    │  CACHE HIT   Run full preflight.sh (parallel)        │
    │  → skip tool  → write tooling-cache.json             │
    │    checks     → write/update session.json            │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Architecture-map staleness check (active tool;       │
    │  independent of cache + commit check):                │
    │                                                       │
    │  Graphify: graph-stamp.json built_at + 7d > now?      │
    │  Understand-Anything: knowledge-graph.json mtime      │
    │                       + 7d > now? (no stamp file)     │
    │    Yes → graph is fresh (time)                        │
    │    No  → flag architecture_map: stale-time            │
    │          (non-blocking); warn in preflight.md         │
    └───────────────────────────────────────────────────────┘
                            │
    ┌───────────────────────┴───────────────────────────────┐
    │  session.json: interrupted task present?              │
    │    Yes → offer user: "Resume <task_id> from Stage N?" │
    │          surface handoff.md if present               │
    │    No  → continue                                     │
    └───────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴──────────────┐
              │  What did the developer request? │
              └─────────────┬──────────────┘
                            │
        ┌───────────────────┼──────────────────────────────┐
        │                   │                              │
   "analyze"/"inspect" "set up"/"init"             "update tools"
   (default)                │                              │
        │                   ▼                              ▼
        ▼             mode=bootstrap                mode=update
   mode=audit               │                              │
        │             "rebuild graph"          "clean reset"
        │                   │                              │
        │                   ▼                              ▼
        │           mode=refresh-graph        mode=force-reinstall
        │                   │                              │
        └───────────────────┴──────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Auth init — Step 1 (refs/auth-bootstrap.md):         │
    │                                                       │
    │  .agent-auth.yaml exists?                            │
    │    Yes → Load; note tokens set vs empty               │
    │    No  → Auto-create from template (empty tokens)     │
    │            Notify user                                │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Parallel checks (read-only, all modes):              │
    │                                                       │
    │  ① Spec Kit    — CLI present? .specify/?              │
    │  ② Android CLI  — present? android info?              │
    │  ③ Android skills — list available?                   │
    │  ④ Understand-Anything — plugin/skill present?        │
    │                   knowledge-graph.json present?       │
    │  ⑤ Graphify (fallback) — CLI/package present?         │
    │                   GRAPH_REPORT.md? graph.json?        │
    │  ⑥ Karpathy     — plugin / skill / CLAUDE.md?         │
    │  ⑦ Auth status  — tokens set / empty (from Step 1)    │
    └───────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
       mode=audit                  mode=bootstrap / update /
            │                      refresh-graph / force-reinstall
            ▼                               │
    Report gaps only                Apply tool actions
    (install nothing)               per decision tables
            │                               │
            └───────────────┬───────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Write: .project-orchestration/reports/preflight.md   │
    │                                                       │
    │  Record:                                              │
    │  - provisioning mode                                  │
    │  - tool readiness (①–⑥)                              │
    │  - auth readiness (⑦)                                 │
    │  - blockers / warnings                                │
    │  - proceed to Stage 0: yes / no                      │
    └───────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
        Blocker exist?               No blocker
              │                           │
              ▼                           ▼
    STOP — fix first         [A][B][C][D] → DONE
    (mode does not allow     [E]–[J]      → Stage 0
     required action)
```

---

## 3. Stage 0 — Intake + Source mode

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 0: INTAKE                                                │
│  Ref: refs/clarification-workflow.md § Source integrations      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Consume preflight.md:                                │
    │  - tool readiness summary                             │
    │  - auth readiness (.agent-auth.yaml status)           │
    │  - graph present / absent                             │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    Which links did the developer provide?
                            │
        ┌───────────────────┼───────────────────────┐
        │                   │                       │
  Jira / Figma /       Only files             Nothing
  Confluence link      docs/ai/inputs/
        │                   │                       │
        ▼                   ▼                       ▼
     Mode A              Mode B                  Mode C
  (External)           (Docs-only)        Clear task?
                                          (1-file refactor /
                                           rename / bug+repro)
                                                   │
                                         ┌─────────┴─────────┐
                                         │                   │
                                        Yes                  No
                                         │                   │
                                         ▼                   ▼
                                  Treat as Mode B       BLOCK —
                                  (developer message    require developer
                                   is the sole doc)     to provide a brief
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Credential resolution (refs/auth-bootstrap.md Step 3)│
    │  Occurs just-in-time when the reader is activated:    │
    │                                                       │
    │  1. Extract project key prefix (e.g. "CA" from "CA-42")│
    │  2. Match in projects[] → use Level 3 override        │
    │     No match → use Level 2 top-level                  │
    │  3. Check that tool's token (Step 2):                 │
    │       Set   → proceed                                  │
    │       Empty → ask user → save to file → proceed       │
    │       User refuses → skip reader, record in report    │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    Record: source mode (A/B/C), links, credential source
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Preliminary mode scoring                             │
    │  (complexity_score + risk_score → preliminary_mode)   │
    │                                                       │
    │  Signals from task description only:                  │
    │  - file count estimate, layer crossing, link types    │
    │  - ADR keyword? → governed                            │
    │  - Jira + Figma both present? → min standard          │
    │  - single-file bug fix, no links? → fast (tentative)  │
    │                                                       │
    │  Write preliminary_mode to session.json               │
    │  (will be finalized and may be upgraded after Stage 1)│
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Task History Relevance Gate                          │
    │                                                       │
    │  Default: do NOT read full task history.              │
    │                                                       │
    │  continuation signals?                               │
    │  - user says continue/resume/previous task            │
    │  - task_id / ADR / requirements path provided         │
    │  - current branch/PR or in-progress session matches   │
    │                                                       │
    │  possible overlap?                                    │
    │  - same module + same screen/flow                     │
    │  - same public/internal contract                      │
    │                                                       │
    │  none → history_scan=skipped                          │
    │  signals/overlap → metadata-only scan                 │
    │  overlap >= medium or explicit continuation           │
    │      → read full matched task history                 │
    │  ambiguous and strategy may change                    │
    │      → ask human one concise question                 │
    └───────────────────────────────────────────────────────┘
    → Stage 1
```

---

## 4. Stage 1 — Discovery

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: DISCOVERY                                             │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │           Parallel reads              │
        │                                       │
        ▼                                       ▼
  architecture-map graph present?      Source material
        │                                       │
   ┌────┴────┐                      ┌───────────┴───────────┐
  Yes        No                  Mode A                  Mode B
   │          │                     │                       │
   ▼          ▼                     ▼                       ▼
 Read        Skip            Jira Reader                Doc Reader
 GRAPH_                           │                   docs/ai/inputs/
 REPORT.md                        │
                        linked_docs / linked_designs?
                                  │
                    ┌─────────────┴─────────────┐
                    │  Auto-follow (1 level):    │
                    │  Confluence URL → Conf.Rdr │
                    │  Figma link    → Figma Rdr │
                    │  Doc / PDF     → Doc Rdr   │
                    │  Jira child    → Jira Rdr  │
                    │  Image/screenshot → record URL │
                    └─────────────┬─────────────┘
                                  │
                    (parallel with the original Jira Reader)
                                  │
        └───────────────────┬─────┘
                            │
                            ▼
          history_scan.decision = read_full?
                            │
                      ┌─────┴─────┐
                     Yes          No
                      │            │
                      ▼            ▼
       Read matched task history   Skip old task docs
       before synthesis:
       - requirements/*.md
       - design/*.md
       - reports/execution.md
       - docs/ai/decisions/*.md   (global ledger; match by task: field)
                            │
                            ▼
                  Store → docs/ai/tasks/{task_id}/discovery/
```

---

## 5. Stage 1.5 — Clarification & Synthesis

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1.5: CLARIFICATION & SYNTHESIS                           │
│  Ref: refs/clarification-workflow.md                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
    Should Clarification run?
    Run if ANY condition below is true:
    ┌───────────────────────────────────────────────────┐
    │  ☐ Brief < 50 words, no ticket/design             │
    │  ☐ No acceptance criteria                         │
    │  ☐ ≥2 sources contradict each other               │
    │  ☐ Graph has component not mentioned in docs      │
    │  ☐ Graph has god node in change path              │
    │  ☐ API / state / error behavior unclear           │
    └───────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
      ≥1 condition true             No conditions true
            │                               │
            ▼                               ▼
    Run Clarification                 Skip / minimize
            │                          → Stage 2 directly
            ▼
    ┌─────────────────────────────────────────────────────┐
    │  Parallel workers (by Source mode):                 │
    │                                                     │
    │  Mode A ─► Jira Reader          ┐                   │
    │            Confluence Reader    │ parallel          │
    │            Figma Reader         │ Figma: MCP-first, │
    │            Graph Impact Reader  ┘  else .agent-auth │
    │            ─────────────────────────────────────    │
    │            Ambiguity Detector   ┐                   │
    │            Conflict Detector    │ parallel          │
    │            Missing-info Det.    │                   │
    │            State Extractor      │                   │
    │            Dependency Impact    ┘                   │
    │                                                     │
    │  Mode B ─► Doc Reader           ┐ parallel          │
    │            Graph Impact Reader  │                   │
    │            Ambiguity Detector   │                   │
    │            Missing-info Det.    ┘                   │
    │                                                     │
    │  Advisory (on demand, any mode):                    │
    │            Android Advisor                          │
    │            Research Advisor                         │
    │            QA Scenario Advisor                      │
    │            Rollout/Risk Advisor                     │
    └─────────────────────────────────────────────────────┘
                            │
                            ▼
    Parent synthesizes (serial — 1 owner):
    ┌───────────────────────────────────────────────────┐
    │  docs/ai/tasks/{task_id}/clarification/           │
    │  ├── context-pack.json                            │
    │  ├── clarification-brief.md                       │
    │  └── clarity-report.md  (Mode A) /                │
    │       embedded clarity section (Mode B)           │
    └───────────────────────────────────────────────────┘
                            │
                            ▼
                  Clarity score (0–10)
                            │
        ┌───────────┬───────┴────────┬───────────┐
        │           │                │           │
      8–10        6–7              4–5          0–3
        │           │                │           │
        ▼           ▼                ▼           ▼
      ready    ready +           research-   blocked
               assumptions         loop         │
        │           │                │      Ask human
        └─────┬─────┘           More        (do not
              │                 research    fabricate)
              ▼
          Stage 2
```

---

## 6. Stage 2–7 — Requirements → Close

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: REQUIREMENTS                                          │
│  Ref: refs/contracts-and-artifacts.md                           │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Spec Kit writes docs/ai/tasks/{task_id}/requirements/<task>.md
  with artifact header + Affected Areas + Decision Triggers
        │
        ▼
  ██████████████████████████████████████████████
  █  MANDATORY STOP — Human approval           █
  █  Do not continue until approved           █
  ██████████████████████████████████████████████
        │
        │  Human approves
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2.5: DECISION GATE / ADR-LITE                            │
│  Ref: refs/contracts-and-artifacts.md                           │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Does task touch module boundary, navigation, public/internal
  contract, persistence, DI, build versions, migration, state
  ownership, permissions/background/billing/auth/notifications,
  or broad test strategy?
        │
   ┌────┴────┐
  Yes        No
   │          │
   ▼          ▼
  Check docs/ai/decisions/README.md   Record adr_required=false
  for existing Accepted ADR that       + reason in session.json
  already covers this decision
        │
   ┌────┴─────────────┐
  Covers it, valid    No match / decision changed
   │                   │
   ▼                   ▼
  Link to it;         Create Proposed ADR-lite
  adr_required=false  (docs/ai/decisions/, GLOBAL;
  reason: "covered     number = max existing + 1;
  by ADR-NNNN"         supersedes: <old ADR> if changed)
   │                   │
   │                   ▼
   │  ██████████████████████████████████████████████
   │  █  MANDATORY STOP — Human approve/defer ADR  █
   │  ██████████████████████████████████████████████
   │                   │
   └─────────┬─────────┘
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: DESIGN SPLIT                                          │
│  Ref: refs/playbooks.md                                         │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Parallel (no code changes):
  ┌────────────────────────┬──────────────────────────────┐
  │  Spec Kit              │  Android skills              │
  │  docs/ai/tasks/...     │  docs/ai/tasks/...           │
  │  design/ + planning/   │  android-memo/<task>.md      │
  └────────────────────────┴──────────────────────────────┘
        │
        ▼
  Single code owner selected + recorded in session.json
  Ask developer: branch name? assignee?
  session.json → code_owner, assignee, branch set
        │
        ▼
  Compute kotlin_convention_scope[] once (Affected Areas + change_type)
  → written into implementation-plan.md header; Stage 4 reuses it
  → Android Advisor consults matching companion skill(s) if available
        │
        ▼
  ┌───────────────────────────────────────────────────────┐
  │  HANDOFF ARTIFACT GENERATED (MANDATORY)               │
  │                                                       │
  │  docs/ai/tasks/{task_id}/handoff.md → CREATED        │
  │  .project-orchestration/status.json → UPDATED        │
  │  (stage_reached: 3, assignee, branch recorded)       │
  └───────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4: IMPLEMENTATION LOCK                                   │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Read implementation-plan.md — work task by task
  Exactly ONE code owner edits code
  All other lanes: advisory only, no edits
        │
        ▼
  ┌─────────────────────────────── PER-TASK TDD LOOP ─────────────┐
  │                                                               │
  │  ① Write smallest failing test (RED)                         │
  │     Run → record RED to evidence/red-<task-id>.txt           │
  │     Gate E.5: RED evidence MUST exist before product code     │
  │                                                               │
  │  ② Write minimum code to pass (GREEN)                        │
  │     Run → record GREEN to evidence/green-<task-id>.txt       │
  │                                                               │
  │  ③ Run full module test suite                                │
  │     ./gradlew :<module>:test                                  │
  │                                                               │
  │  ④ Refactor while green                                      │
  │                                                               │
  │  ⑤ Commit                                                    │
  │                                                               │
  │  ⑥ Spec-compliance review ✅  (FIRST — does it meet AC?)     │
  │  ⑦ Quality/Karpathy review ✅ (SECOND — is it clean code?)   │
  │  ⑧ Kotlin/Android convention ✅ (same dispatch, if in scope) │
  │                                                               │
  │  → Next task                                                  │
  └───────────────────────────────────────────────────────────────┘
        │
        │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
        │           INTERRUPT / HANDOFF PATH
        │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤
        │  Developer stops and wants to hand off:          │
        │                                                  │
        │  ① Update handoff.md (MANDATORY before stop):   │
        │    - Last completed task (with RED/GREEN)        │
        │    - Files modified so far                       │
        │    - Next task for incoming dev                  │
        │    - Notes / WIP warnings                        │
        │                                                  │
        │  ② Update status.json → blocker + handoff_to    │
        │  ③ Write session.json interrupt state            │
        │                                                  │
        │  Incoming dev runs: "resume task ANDROID-XX"     │
        │  Skill reads handoff.md → continues Stage 4     │
        │  Gate E.5 still applies to remaining tasks       │
        │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 5: VERIFY                                                │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Parallel:
  ┌──────────────────────────┬───────────────────────────────┐
  │  Android CLI             │  Architecture map (if exists) │
  │  build + device tests    │  /understand or /graphify     │
  │  screenshots + logs  →   │  --update                     │
  │  .project-orchestration/ │  .understand-anything/ or     │
  │  evidence/               │  graphify-out/ updated        │
  └──────────────────────────┴───────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 6: QA GATE                                               │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Parallel review:
  ┌──────────────────────────┬───────────────────────────────┐
  │  Spec Kit                │  Karpathy guidelines          │
  │  - diff review           │  - surgical changes           │
  │  - acceptance coverage   │  - no over-engineering        │
  │  - scope discipline      │  - explicit assumptions       │
  └──────────────────────────┴───────────────────────────────┘
        │
        ▼
  Write QA review into .project-orchestration/tasks/{task_id}/reports/execution.md
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 7: DOCS / DECISION FINALIZATION                          │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Finalize ADR status (docs/ai/decisions/, update README.md index row),
  Task Changelog, Gate log, Drift Check. No product-code changes.
        │
        ▼
  adr_required OR estimated_build_scope∈{local-chain,full-project}
  OR change_type=architecture_change ?
        │
   ┌────┴────┐
  Yes        No
   │          │
   ▼          ▼
  Patch      AUTO-SKIP
  docs/ai/architecture/<domain>.md
  (section-level only) + README.md index
   │          │
   └────┬─────┘
        ▼
  ┌───────────────────────────────────────────────────────┐
  │  Handoff + Status finalization (MANDATORY):           │
  │                                                       │
  │  handoff.md → status: complete, final summary added  │
  │  status.json → stage_reached: 7, stage_status:       │
  │                complete, pr_url if created           │
  └───────────────────────────────────────────────────────┘
        │
        ▼
  ✅ DONE — Task closed
```

---

## 7. Auth credential resolution

```
┌─────────────────────────────────────────────────────────────────┐
│  .agent-auth.yaml  (gitignored — do not commit)                 │
│  Template: templates/agent-auth.example.yaml                    │
└─────────────────────────────────────────────────────────────────┘

  Level 1 — Workspace
  ├── workspace.name
  └── workspace.default_jira_project   (e.g. "ANDROID")

  Level 2 — Tool credentials (default for the whole session)
  ├── atlassian.domain / email / api_token   ← Jira + Confluence shared
  ├── figma.personal_access_token
  └── github.personal_access_token           (optional)

  Level 3 — Per-project overrides            (optional)
  └── projects[]
      ├── name: "client-alpha"
      ├── jira_project_key: "CA"
      ├── atlassian.*                        ← override Level 2
      └── figma.*                            ← if unset → fallback to Level 2

Resolve flow when the agent receives a link:
  ─────────────────────────────────────────────────────────────
  Dev provides "CA-42"
        │
        ▼
  Extract prefix → "CA"
        │
        ▼
  Find in projects[].jira_project_key
        │
   ┌────┴────┐
  Match    No match
   │          │
   ▼          ▼
  Use       Use Level 2
  Level 3   (top-level)
  override       │
   │             │
   └──────┬──────┘
          │
          ▼
  Fetch source with the correct credentials

  .agent-auth.yaml missing + link provided:
  → WARN in preflight.md
  → Source reader skip
  → Do not fabricate content
```

---

## 8. Playbook flows — All use cases

### [A] Analyze repo
```
Stage -1 (audit) → report gaps → DONE
Do not run Stage 0–7 unless task docs are also analyzed
```

### [B] Bootstrap repo
```
Stage -1 (bootstrap)
  → Install missing tools
  → specify init --here --integration <agent> / android init
  → Build graph if codebase exists + approved
  → Write preflight.md
→ DONE
```

### [C] Update tools
```
Stage -1 (update)
  → android update / specify self upgrade
  → Refresh skills list
  → Update Understand-Anything if approved; update Graphify package instead only if unavailable
  → Write preflight.md
→ DONE
```

### [D] Refresh graph
```
Stage -1 (refresh-graph)
  → Understand-Anything checked first: /understand (build or rebuild)
  → Graphify (fallback, only if Understand-Anything unavailable):
      /graphify .          (graph missing)
      /graphify . --update (graph exists)
  → Do not touch product code
→ DONE
```

### [E] New feature
```
-1 (audit + auth check + status.json init)
→ 0 (collect links → Mode A/B/C → resolve credentials)
→ 1 (read graph + source readers + auto-follow Jira attachments)
→ 1.5 (minimal clarification, only run if a trigger fires)
→ 2 (requirements) → 2.5 decision gate → STOP if ADR approval needed human approval
→ 3 (design + Android memo)
   → handoff.md CREATED; status.json updated (stage: 3, assignee, branch)
→ 4 (one owner implements)
   → handoff.md UPDATED on any interrupt
→ 5 (CLI evidence + graph update)
→ 6 (Karpathy QA)
→ 7 (handoff.md FINALIZED; status.json stage_status: complete)
```

### [F] Edit existing feature
```
-1 (audit + auth check + status.json init)
→ 0 (collect links)
→ 1 (architecture-map path query if graph exists + source readers)
→ 1.5 (Ambiguity + Missing-info + Dependency Impact)
→ 2 (requirements: graph path + out-of-scope list) → STOP
→ 3 (design delta + Android memo if Android-specific)
   → handoff.md CREATED; status.json updated
→ 4 (surgical changes only — Karpathy)
   → handoff.md UPDATED on interrupt
→ 5 (update graph + verify)
→ 6 (QA gate)
→ 7 (handoff.md FINALIZED)
```

### [G] Bug fix
```
-1 (audit Android CLI + architecture map (Understand-Anything → Graphify fallback) + auth check + status.json init)
→ 0 (collect: repro steps, device, version, expected behavior)
→ 1 (graph path + runtime evidence if available)
→ 1.5 (clarify only when repro is unclear)
→ 2 (minimal bug requirements) → STOP
→ 3 (fix plan + verification design)
   → handoff.md CREATED; status.json updated
→ 4 (smallest safe patch)
   → handoff.md UPDATED on interrupt
→ 5 (runtime evidence + graph update if graph exists)
→ 6 (QA gate)
→ 7 (handoff.md FINALIZED)
```

### [H] XML → Compose migration
```
-1 (check Android CLI + Android skills + architecture map (Understand-Anything → Graphify fallback) + auth + status.json init)
→ 0 (collect migration target, sources, constraints)
→ 1 (architecture-map query "xml layout view fragment"
      android skills find "compose")
→ 1.5 (Android Advisor + Dependency Impact + Rollout/Risk)
→ 2 (migration plan) → STOP
→ 3 (batch plan + Android migration memo)
   → handoff.md CREATED per-batch; status.json updated
→ 4 (per-batch, single owner for each batch)
   → handoff.md UPDATED between batches and on interrupt
→ 5 (visual evidence + graph update)
→ 6 (QA gate)
→ 7 (handoff.md FINALIZED)
```

### [I] AGP / Build modernization
```
-1 (check Spec Kit + Android CLI + Android skills
     + Gradle wrapper + architecture map (Understand-Anything → Graphify fallback) + auth + status.json init)
→ 0 (collect upgrade target, constraints, source docs)
→ 1 (architecture-map query "gradle build agp"
      android skills find "agp")
→ 1.5 (Dependency Impact + Rollout/Risk + Android Advisor)
→ 2 (upgrade plan) → STOP
→ 3 (implementation plan + compatibility memo)
   → handoff.md CREATED; status.json updated
→ 4 (controlled implementation)
   → handoff.md UPDATED on interrupt
→ 5 (clean build + graph update)
→ 6 (QA gate)
→ 7 (handoff.md FINALIZED)
```

### [J] Unfamiliar codebase + raw brief
```
-1 (audit + auth check + status.json init; refresh-graph only if approved)
→ 0 (collect task brief)
→ 1 (read GRAPH_REPORT.md + Doc Reader reads docs/ai/inputs/)
→ 1.5 (Ambiguity + Missing-info + Graph Impact
         + Dependency Impact — full clarification)
→ 2 (requirements after outcome=ready) → STOP
→ 3 (design + implementation plan)
   → handoff.md CREATED; status.json updated
→ 4 (one owner implements)
   → handoff.md UPDATED on interrupt
→ 5 (runtime evidence + graph update)
→ 6 (QA gate)
→ 7 (handoff.md FINALIZED)
```

---

## 9. Source mode × Worker activation matrix

```
                      Mode A           Mode B          Mode C
                   (links provided)  (docs-only)    (msg as doc)
                   ──────────────────────────────────────────────
Jira Reader             ✓                –               –
  └─ auto-follow        ✓                –               –
Confluence Reader       ✓                –               –
Figma Reader            ✓                –               –
Doc Reader              –                ✓               ✓
Graph Impact Reader     ✓ (if graph)     ✓ (if graph)    ✓ (if graph)
Ambiguity Detector      ✓                ✓               ✓
Conflict Detector       ✓                –               –
Missing-info Det.       ✓                ✓               ✓
State Extractor         ✓ (Figma)        –               –
Dependency Impact       ✓ (if graph)     ✓ (if graph)    –
Android Advisor         on demand        on demand        –
QA Scenario Adv.        on demand        on demand        –
Rollout/Risk Adv.       on demand        on demand        –
```

---

## 10. Architecture-map trigger map

Understand-Anything is checked first; Graphify is the fallback only if Understand-Anything is unavailable.

```
Stage -1   → check active tool + graph files + freshness (2 checks):
              ① commit check (Graphify only): graph_commit == git rev-parse HEAD?
              ② time check:   built_at/mtime + stale_after_days (7) > now?
              Either fails → flag stale (non-blocking, surface in preflight.md)
Stage 0    → note graph present / absent + which tool + staleness flag from -1
Stage 1    → READ active output (knowledge-graph.json or GRAPH_REPORT.md) if present
Stage 1.5  → Graph Impact Reader feeds context-pack
Stage 3    → use graph rationale for design decisions
Stage 4    → DO NOT query graph while coding
Stage 5    → /understand or /graphify . --update (if graph_impact >= medium)
              skip if graph_impact = low (write to skip-log)
Stage 6    → optional before/after compare; check god nodes
Stage 7    → finalize ADR status + task changelog + drift check
```

---

## 11. Parallel vs Serial

```
PARALLEL allowed                     SERIAL required
─────────────────────────────────    ──────────────────────────────────
Tooling read-only checks (Stage -1)  Install/update the same tool
Auth check (Stage -1)                2 workers publish requirements
Source readers (Stage 1 / 1.5)       2 workers edit the same code file
Auto-follow readers (Stage 1)        Credential resolution (per link)
Analysis workers (Stage 1.5)         Parent synthesis
Advisory workers (Stage 1.5)         Requirements → human approval
Decision review (Stage 2.5)          ADR approval when trigger fires
Lane reads in Discovery              Code ownership (1 owner only)
Design split (Spec Kit + Android)   Stage gates (wait for gate pass)
Verify (Android CLI + architecture-map tool)
QA review (Spec Kit + Karpathy)
Docs finalization (Stage 7)
```

---

## 12. Hard stop points

```
①  Stage -1 → Stage 0  :  Blocker in preflight is unresolved
②  Stage -1 → Stage 0  :  .agent-auth.yaml missing + external links present → WARN
                           (does not block, but source readers will skip)
③  Stage 0  (Mode C)   :  Task unclear → require developer to provide a brief
④  Stage 1.5 outcome   :  blocked → ask human, do not fabricate requirements
⑤  Stage 2 → 2.5       :  MANDATORY human approval requirements
⑥  Stage 2.5 → Stage 3 :  Decision trigger fired but ADR-lite not approved/deferred
⑦  Stage 3 → Stage 4   :  Missing design doc + single code owner
                           Missing branch name or assignee (must be set before coding)
                           implementation-plan.md missing or contains placeholders (Gate E)
⑧  Stage 4 per-task    :  Product code written before RED evidence exists (Gate E.5)
                           Spec-compliance review skipped or run after quality review
⑨  Stage 4 interrupt   :  handoff.md not updated before stopping (MANDATORY)
⑩  Stage 5 → Stage 6   :  Missing runtime evidence + graph update
⑪  Stage 6 → Stage 7   :  Karpathy review has not passed
⑫  Stage 7 → Close     :  Missing ADR final status, Task Changelog, or Drift Check
                           handoff.md not finalized to status: complete
```

---

## 13. Handoff workflow

```
Dev A owns task (Stage 3–4)          Skill                 Dev B picks up
         │                              │                        │
         │  "dừng, bàn giao dev-b"     │                        │
         │─────────────────────────────►│                        │
         │                    ① Update handoff.md:              │
         │                      - stage_reached: 4              │
         │                      - files modified                │
         │                      - next action                   │
         │                      - WIP warnings                  │
         │                    ② Update status.json:             │
         │                      - assignee: dev-b              │
         │                      - handoff_to: dev-b            │
         │                      - blocker: null                 │
         │                    ③ Write session.json interrupt    │
         │◄─────────────────────────────│                        │
         │  "Handoff complete"          │                        │
         │                              │                        │
         ·                              ·                        │
         ·  (Dev A done)                ·    "resume ANDROID-42"│
                                        │◄───────────────────────│
                                 Read status.json (1 file):     │
                                 → task: ANDROID-42             │
                                 → stage: 4, assignee: dev-b   │
                                 → branch: feature/ANDROID-42  │
                                 → blocker: null               │
                                        │                        │
                                 Read handoff.md (1 file):      │
                                 → What was done                │
                                 → Next action                  │
                                 → Files modified               │
                                 → Key decisions                │
                                        │                        │
                                 Resume Stage 4 from            │
                                 last successful compile point  │
                                        │────────────────────────►
                                        │  "Continue from LoginScreen"
```

### Artifacts involved in handoff

```
READ by incoming dev (by priority):

1.  .project-orchestration/status.json          ← project dashboard
    → all tasks: stage, assignee, blocker, branch, PR

2.  docs/ai/tasks/{task_id}/handoff.md          ← task snapshot
    → what was done, next action, files, decisions

3.  .project-orchestration/tasks/{task_id}/
    └── session.json                            ← full state if needed

4.  docs/ai/tasks/{task_id}/
    ├── requirements/<task>.md                  ← what to build
    ├── design/<task>.md                        ← how to build it
    └── clarification/context-pack.json         ← full context

5.  docs/ai/decisions/README.md                 ← GLOBAL: every decision made so far, any task
    → docs/ai/decisions/ADR-*.md                ← why (immutable once Accepted; superseded, not edited)

6.  docs/ai/architecture/README.md              ← GLOBAL: current shape of the system, by domain
    → docs/ai/architecture/<domain>.md          ← living doc, updated in place (not a task snapshot)
```

### status.json — project dashboard

```json
{
  "tasks": [
    {
      "task_id": "ANDROID-42",
      "title": "Login Flow",
      "stage_reached": 4,
      "stage_status": "in_progress",
      "assignee": "dev-b",
      "handoff_to": null,
      "branch": "feature/ANDROID-42-login",
      "pr_url": null,
      "blocker": null,
      "handoff_doc": "docs/ai/tasks/ANDROID-42/handoff.md"
    },
    {
      "task_id": "ANDROID-51",
      "title": "Profile Screen",
      "stage_reached": 2,
      "stage_status": "blocked",
      "assignee": "dev-c",
      "blocker": "waiting for human approval of requirements"
    },
    {
      "task_id": "ANDROID-55",
      "title": "Push Notifications",
      "stage_reached": 7,
      "stage_status": "complete",
      "assignee": "dev-a",
      "pr_url": "https://github.com/org/repo/pull/89"
    }
  ]
}
```

### handoff.md update triggers

```
Stage 3  → code_owner confirmed   → CREATE (initial)
Stage 4  → interrupt / stop       → UPDATE (files modified, next action)
Stage 4  → pr_url created         → UPDATE (add PR link)
Stage 5  → evidence collected     → UPDATE (evidence paths)
Stage 7  → task closed            → FINALIZE (status: complete)
```

---

## 14. Workflow modes

```
STAGE 0: Task description received
        │
        ▼
Preliminary mode estimate (from description + links)
        │
        ├── Single-file fix, no links, no ADR keywords  → preliminary: fast
        ├── Feature request, multi-file, one module     → preliminary: standard
        ├── Jira + Figma both present                   → preliminary: min standard
        ├── ADR keyword, migration, multi-module        → preliminary: governed
        └── Ambiguous                                   → preliminary: standard

        Write preliminary_mode → session.json
        │
        ▼
STAGE 1: Source reading + architecture map
        │
Finalize scores after reading all sources:
        │
        ├── complexity_score: 1-10
        │     1-2: single-file additive
        │     3-4: multi-file same layer
        │     5-6: multi-layer (ViewModel + Repository)
        │     7-8: multi-module
        │     9-10: migration / AGP / architecture
        │
        ├── risk_score: 1-10
        │     1-2: isolated logic, no ADR triggers
        │     3-4: shared ViewModel/Repository state
        │     5-6: auth / billing / permissions / DB migration
        │     7-8: API surface change / god nodes
        │     9-10: multiple high-risk signals
        │
        └── Apply override rules (in priority order):
              Any ADR trigger fires       → governed (hard floor)
              Jira + Figma both present   → min standard
              Human explicit mode request → use as stated
              Ambiguous/incomplete brief  → min standard

        ▼
Mode mapping:
  complexity ≤ 3 AND risk ≤ 3  →  fast
  complexity ≤ 7 AND risk ≤ 6  →  standard
  otherwise                     →  governed

  Write workflow_mode + scores → context-pack.json, session.json
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   FAST mode stage flow                      │
│                                                             │
│  -1 → 0 → 1 → 2(mini) → 2.5-lite → 3-lite →               │
│  4(TDD) → 5(lite) → 6(lite) → 7(lite)                      │
│                                                             │
│  Every stage runs. Only depth and selected steps differ:    │
│                                                             │
│  AUTO-SKIP within stages (written to skip-log.json):        │
│    Stage 1.5  — complexity/risk confirmed low at Stage 1    │
│    Stage 2.5  ADR creation — AUTO-SKIP only when no trigger │
│      fires (ADR trigger check MANDATORY; trigger → governed) │
│    Stage 3  design doc + Android memo — plan ≤ 5 tasks only │
│                                                             │
│  CONFIRM-SKIP (ask human first):                            │
│    Stage 6  full QA report — Karpathy diff review +         │
│      Gate G close remain MANDATORY regardless               │
│                                                             │
│  LITE (always runs, minimal output):                        │
│    Stage 2  — requirements ≤ 40 lines, ACs + facts only     │
│    Stage 5  — evidence gate; graph update skipped if low    │
│    Stage 7  — Task Changelog + Drift Check (MANDATORY);     │
│      no ADR status update when no ADR exists                │
│                                                             │
│  NEVER SKIPPED regardless of mode:                          │
│    Auth init, requirements approval, ADR trigger check,     │
│    TDD Gate E.5, Karpathy diff review, Gate G close,        │
│    session.json + skip-log.json writes, status.json updates │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                STANDARD mode stage flow                     │
│                                                             │
│  -1 → 0 → 1 → [1.5] → 2 → [2.5] → 3 → 4 → 5 → 6 → 7      │
│                                                             │
│  Full sequence; artifact depth bounded:                     │
│    requirements ≤ 120 lines                                 │
│    design ≤ 180 lines                                       │
│    implementation-plan ≤ 15 tasks                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                GOVERNED mode stage flow                     │
│                                                             │
│  Full -1 → 7 with no artifact restrictions                  │
│  Triggered by: migration / multi-module / ADR / Jira+Figma  │
└─────────────────────────────────────────────────────────────┘
```

### Mode upgrade rules

Mode can only be **upgraded** (fast → standard → governed) during a task. Downgrade requires explicit human confirmation.

```
Auto-upgrade triggers (logged to session.json + skip-log.json):
  - Acceptance criteria count > 5 while in fast mode → standard
  - ADR trigger fires during Stage 2.5 check → governed
  - Graph shows god nodes in change path → governed
  - Source reading reveals multi-module impact → governed

Human-requested downgrade flow:
  Agent: "Task is scored as [governed]. Downgrade to [standard]?
          This removes: ADR gate, full QA gate.
          Confirm? (y/n)"
  If y → log mode_override in session.json + skip-log.json
  If n → keep governed
```
