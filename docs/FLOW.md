# Android Agent Orchestrator — Complete Flow

_Reflects skill v4.8.0. Update when SKILL.md changes._

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
    │  Graphify time-based staleness check:                 │
    │  (independent of cache + commit check)                │
    │                                                       │
    │  graph-stamp.json → built_at + stale_after_days > now?│
    │    Yes → graph is fresh (time)                        │
    │    No  → flag graphify: stale-time (non-blocking)    │
    │          surface as warning in preflight.md           │
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
    │  ① AI DevKit    — CLI present? .ai-devkit.json?       │
    │  ② Android CLI  — present? android info?             │
    │  ③ Android skills — list available?                   │
    │  ④ Graphify     — CLI/package? GRAPH_REPORT.md?       │
    │                   graph.json?                         │
    │  ⑤ Karpathy     — plugin / skill / CLAUDE.md?         │
    │  ⑥ Auth status  — tokens set / empty (from Step 1)    │
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
    │  - tool readiness (①–⑤)                              │
    │  - auth readiness (⑥)                                 │
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
  graphify-out/ present?               Source material
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
       - decisions/ADR-*.md
       - design/*.md
       - reports/execution.md
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
    │            Figma Reader         │ (credentials from │
    │            Graph Impact Reader  ┘  .agent-auth.yaml)│
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
  AI DevKit writes docs/ai/tasks/{task_id}/requirements/<task>.md
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
  Create     Record adr_required=false
  Proposed   + reason in session.json
  ADR-lite
   │
   ▼
  ██████████████████████████████████████████████
  █  MANDATORY STOP — Human approve/defer ADR  █
  ██████████████████████████████████████████████
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: DESIGN SPLIT                                          │
│  Ref: refs/playbooks.md                                         │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Parallel (no code changes):
  ┌────────────────────────┬──────────────────────────────┐
  │  AI DevKit             │  Android skills              │
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
  Exactly ONE code owner edits code
  All other lanes: advisory only, no edits
        │
        │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
        │           INTERRUPT / HANDOFF PATH
        │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤
        │  Developer stops and wants to hand off:          │
        │                                                  │
        │  ① Update handoff.md (MANDATORY before stop):   │
        │    - What was done                               │
        │    - Files modified so far                       │
        │    - Next action for incoming dev                │
        │    - Notes / WIP warnings                        │
        │                                                  │
        │  ② Update status.json → blocker + handoff_to    │
        │  ③ Write session.json interrupt state            │
        │                                                  │
        │  Incoming dev runs: "resume task ANDROID-XX"     │
        │  Skill reads handoff.md → continues Stage 4     │
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
  │  Android CLI             │  Graphify (if graph exists)   │
  │  build + device tests    │  /graphify . --update         │
  │  screenshots + logs  →   │  graphify-out/ updated        │
  │  .project-orchestration/ │                               │
  │  evidence/               │                               │
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
  │  AI DevKit               │  Karpathy guidelines          │
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
  Finalize ADR status, Task Changelog, Gate log, Drift Check.
  No product-code changes.
        │
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
  → ai-devkit init / android init
  → Build graph if codebase exists + approved
  → Write preflight.md
→ DONE
```

### [C] Update tools
```
Stage -1 (update)
  → android update / ai-devkit install
  → Refresh skills list
  → Update Graphify package if approved
  → Write preflight.md
→ DONE
```

### [D] Refresh graph
```
Stage -1 (refresh-graph)
  → /graphify .          (graph missing)
  → /graphify . --update (graph exists)
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
→ 1 (graphify path query if graph exists + source readers)
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
-1 (audit Android CLI + Graphify + auth check + status.json init)
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
-1 (check Android CLI + Android skills + Graphify + auth + status.json init)
→ 0 (collect migration target, sources, constraints)
→ 1 (graphify query "xml layout view fragment"
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
-1 (check AI DevKit + Android CLI + Android skills
     + Gradle wrapper + Graphify + auth + status.json init)
→ 0 (collect upgrade target, constraints, source docs)
→ 1 (graphify query "gradle build agp"
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

## 10. Graphify trigger map

```
Stage -1   → check CLI + graph files + freshness (2 checks):
              ① commit check: graph_commit == git rev-parse HEAD?
              ② time check:   built_at + stale_after_days (7) > now?
              Either fails → flag stale (non-blocking, surface in preflight.md)
Stage 0    → note graph present / absent + staleness flag from -1
Stage 1    → READ GRAPH_REPORT.md (if present)
Stage 1.5  → Graph Impact Reader feeds context-pack
Stage 3    → use graph rationale for design decisions
Stage 4    → DO NOT query graph while coding
Stage 5    → /graphify . --update (if graph_impact >= medium)
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
Design split (AI DevKit + Android)   Stage gates (wait for gate pass)
Verify (Android CLI + Graphify)
QA review (AI DevKit + Karpathy)
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
⑧  Stage 4 interrupt   :  handoff.md not updated before stopping (MANDATORY)
⑨  Stage 5 → Stage 6   :  Missing runtime evidence + graph update
⑩  Stage 6 → Stage 7   :  Karpathy review has not passed
⑪  Stage 7 → Close     :  Missing ADR final status, Task Changelog, or Drift Check
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
    ├── decisions/ADR-*.md                      ← why decisions were made
    └── clarification/context-pack.json         ← full context
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
