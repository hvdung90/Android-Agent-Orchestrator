# Contracts, Artifacts, and Gates

---

## Canonical artifacts

### 1) `docs/ai/clarification/context-pack.json`
Purpose: normalized machine-readable context — source-agnostic.

**Schema (generalized — works with Jira, docs, or no external sources):**
```json
{
  "feature_id": "ANDROID-123 | task-brief | <slug>",
  "title": "",
  "sources": [
    {
      "type": "jira | confluence | figma | doc | ticket | note | graph",
      "ref": "<url or filename>",
      "summary": "<one-line summary of what this source contributed>"
    }
  ],
  "business_goal": "",
  "user_problem": "",
  "acceptance_criteria": [],
  "screens": [],
  "states": [],
  "dependencies": [],
  "facts": [],
  "assumptions": [
    {
      "assumption": "<statement>",
      "source": "<where it came from>",
      "risk": "low | medium | high"
    }
  ],
  "unknowns": [
    {
      "question": "<what is unknown>",
      "impact": "<what decision it blocks>",
      "severity": "blocker | major | minor"
    }
  ],
  "conflicts": [
    {
      "id": "conflict-1",
      "source_a": "<source type + field>",
      "source_b": "<source type + field>",
      "description": "<what they say differently>",
      "resolution": "pending | assumed | decided"
    }
  ],
  "decisions_needed": [],
  "recommended_v1_scope": [],
  "graph_path": "<ComponentA -> ComponentB -> ComponentC | none>",
  "god_nodes_touched": [],
  "blocked": false,
  "clarity_score": 0,
  "outcome": "ready | blocked | research-loop"
}
```

**Minimal valid context-pack (no external sources, docs-only flow):**
```json
{
  "feature_id": "<slug from task-brief>",
  "title": "",
  "sources": [
    { "type": "doc", "ref": "docs/ai/inputs/task-brief.md", "summary": "..." }
  ],
  "facts": [],
  "assumptions": [],
  "unknowns": [],
  "conflicts": [],
  "decisions_needed": [],
  "recommended_v1_scope": [],
  "blocked": false,
  "clarity_score": 0,
  "outcome": "ready | blocked | research-loop"
}
```

---

### 2) `docs/ai/clarification/clarity-report.md`
Must contain:
- clarity score (0–10),
- what is already well understood,
- what is missing,
- what conflicts exist,
- whether the feature is blocked,
- recommended outcome: ready | blocked | research-loop.

---

### 3) `docs/ai/clarification/clarification-brief.md`
Human-readable distilled brief used as the source for requirements.

Must show:
- feature summary,
- source documents used,
- confirmed facts,
- assumptions (with risk level),
- unknowns (with severity),
- conflicts and their resolution status,
- missing information,
- graph impact summary,
- research findings if any,
- recommendation for v1 scope,
- blockers before development.

---

### 4) `docs/ai/requirements/<task>.md`
Canonical requirements doc.

Must be generated from `clarification-brief.md`, not directly from raw external task text when any ambiguity trigger was active.

Required sections:
```markdown
# Requirements: [Feature Name]

## Source artifacts
- docs/ai/clarification/clarification-brief.md
- docs/ai/clarification/context-pack.json

## Context
- Graph path affected: <from Graph Impact Reader>
- Affected layers: UI / Domain / Data

## User stories
## Acceptance criteria
## Affected components
## Edge cases
## Open questions (for human to resolve)
```

---

### 5) `docs/ai/design/<task>.md`
Canonical design/planning doc.

---

### 6) `docs/ai/android-memo/<task>.md`
Android-specific advisory memo. Required only for Android-specialized tasks.

---

### 7) `.project-orchestration/reports/execution.md`
Final run report. See reporting contract in SKILL.md.

---

## Stage gates

### Gate A — Intake complete
Required:
- source list exists (Jira / Confluence / Figma / docs / none noted explicitly),
- graph availability checked (`graphify-out/` present or absent noted),
- initial task scope noted.

### Gate B — Discovery complete
Required:
- graph overview read if present (`GRAPH_REPORT.md`),
- raw sources read (all files in `docs/ai/inputs/` if present),
- discovery notes stored in `docs/ai/discovery/`.

### Gate C — Clarification complete
Required:
- `docs/ai/clarification/clarity-report.md` exists,
- `docs/ai/clarification/context-pack.json` exists,
- `docs/ai/clarification/clarification-brief.md` exists,
- parent outcome chosen: `ready | blocked | research-loop`.

**Minimal clarification (docs-only, no Jira/Figma):**
- Run: Doc Reader + Ambiguity Detector + Missing-info Detector + Graph Impact Reader (if graph exists).
- Required artifacts: `context-pack.json` + `clarification-brief.md`.
- `clarity-report.md` may be embedded inside `clarification-brief.md` as a section.

### Gate D — Requirements complete
Required:
- canonical requirements doc exists at `docs/ai/requirements/<task>.md`,
- human approval recorded (explicit confirmation in conversation or commit).

### Gate E — Design ready
Required:
- design doc exists,
- Android memo exists if Android-specific,
- single code owner selected and recorded.

### Gate F — Verification ready
Required:
- build/runtime evidence captured,
- Graphify `--update` run if graph exists,
- acceptance coverage checked against requirements.

### Gate G — Close ready
Required:
- Karpathy diff review passed,
- final execution report written,
- no unresolved blockers remain.

---

## Graphify stage trigger rules

Read this when deciding whether and how to use Graphify at each stage.

| Stage | Trigger | Action |
|---|---|---|
| Intake (Stage 0) | Check existence | `ls graphify-out/GRAPH_REPORT.md` — note present/absent |
| Discovery (Stage 1) | Graph exists | Read `GRAPH_REPORT.md`; run `graphify query "<task keyword>"`; run `graphify path "<entry>" "<target>"` |
| Clarification (Stage 1.5) | Graph exists | Graph Impact Reader consumes graph; feeds `undocumented_dependencies` into context-pack |
| Design split (Stage 3) | Graph exists | `graphify explain "<ComponentName>"` to understand rationale before writing plan |
| Implementation (Stage 4) | — | No queries during coding — map was read in Stage 1 |
| Verify (Stage 5) | Graph exists | `/graphify . --update` after implementation |
| QA gate (Stage 6) | Graph exists | Optional: compare `GRAPH_REPORT.md` before/after; check god nodes |

**Graphify queries by task type:**

| Task type | Stage 1 query | Stage 5 verify |
|---|---|---|
| New feature | `graphify query "<feature keyword>"` | `--update` |
| Edit existing feature | `graphify query "<feature name>"` + `graphify path "<entry>" "<target>"` | `--update` + re-query to confirm path unchanged |
| Bug investigation | `graphify path "<symptom>" "<suspected cause>"` | `--update` |
| XML → Compose migration | `graphify query "xml layout view fragment"` → ordered list (leaf nodes first) | `--update` + `graphify query "xml layout"` to verify 0 xml nodes remain |
| AGP upgrade | `graphify query "gradle build agp"` | `--update` |
| Unfamiliar codebase | `/graphify .` build → `cat GRAPH_REPORT.md` → `graphify query "<entry point>"` | N/A (read-only orientation) |

**When NOT to use Graphify:**
- Graph does not exist AND task is a new standalone file with no existing dependencies.
- Codebase is very small (< 10 files).
- Task is purely additive with no connection to existing components.

---

## Ownership rules

| Artifact | Owner | Others may |
|---|---|---|
| `context-pack.json` | Parent orchestrator / AI DevKit | propose raw fields via worker output contracts only |
| `clarity-report.md` | Parent orchestrator / AI DevKit | supply findings |
| `clarification-brief.md` | Parent orchestrator / AI DevKit | recommend wording |
| `requirements/<task>.md` | Parent orchestrator / AI DevKit | review only |
| `android-memo/<task>.md` | Android skills | supply advice only |
| runtime evidence | Android CLI | request commands |
| `graphify-out/**` | Graphify | consume/query only |
| `docs/ai/inputs/**` | You (human) | never overwritten by agent |

---

## Source precedence rule

When sources disagree and no project convention defines precedence:
1. Record the conflict in `context-pack.json → conflicts[]`.
2. Do not decide silently.
3. Block if the conflict changes scope, behavior, or API assumptions.
4. Proceed with explicit assumption if severity is `minor` and assumption is documented.

---

## Approval rule

The system must not proceed from Requirements (Gate D) to Design/Implementation (Gate E) without explicit human approval.

---

## Sub-agent listening rule

When one worker depends on another's output, it must consume the prior worker's artifact rather than re-derive it loosely.

| Worker | Must consume |
|---|---|
| State Extractor | Figma Reader output + Jira/Confluence/Doc Reader behavior notes |
| Android Advisor | `context-pack.json` — not raw Jira alone |
| QA Scenario Advisor | requirements doc or `clarification-brief.md` — not isolated raw snippets |
| Dependency Impact Analyzer | Graph Impact Reader output + source reader outputs |
| Conflict Detector | Two or more source reader outputs |
