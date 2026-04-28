# Clarification & Synthesis Workflow

## Purpose

This subflow converts noisy or incomplete inputs into a trustworthy development brief before requirements are written.

Raw Jira tickets, Confluence docs, Figma links, local markdown docs, and architecture reality often do not line up cleanly. This workflow surfaces conflicts, fills gaps, and produces one canonical artifact set the parent orchestrator uses to write requirements.

---

## Source modes

Before running clarification, identify which source mode applies. This determines which workers to activate.

### Mode A — External sources (Jira / Confluence / Figma present)
Full clarification flow. All source reader workers available.

### Mode B — Docs-only (only `docs/ai/inputs/` exists)
Minimal clarification flow. Skip Jira Reader, Confluence Reader, Figma Reader.
Run: **Doc Reader + Graph Impact Reader (if graph exists) + Ambiguity Detector + Missing-info Detector**.
Exit faster — `clarity-report.md` may be embedded as a section inside `clarification-brief.md` rather than a standalone file.

### Mode C — No sources (no docs, no external links)
The parent orchestrator must ask the human for a task brief before running clarification.
Do not proceed without at least one source.

---

## Trigger conditions

Run Clarification when one or more of these are true:

**From external sources:**
- acceptance criteria are missing, vague, or purely UI-level,
- Jira says what to build but not how behavior should work,
- Confluence contains narrative but not clear implementation boundaries,
- Figma shows screens without state/edge-case rules,
- linked sources disagree with each other.

**From docs/ai/inputs/ (Mode B):**
- task brief uses words like TBD, maybe, should, probably, later, confirm,
- architecture doc and feature list describe different scopes,
- design notes mention UI without behavior rules or state handling.

**From graph:**
- Graphify shows affected modules or dependencies not mentioned in any task doc,
- graph god nodes are in the change path but not acknowledged in docs.

**From repo:**
- the codebase already has a similar pattern that may change the recommendation.

**Skip or minimize Clarification when:**
- source docs are detailed, acceptance criteria are testable, no conflicts exist, graph shows a clean isolated change surface.

---

## Sequence

### Step 1 — Identify source mode and collect raw bundle

Collect all available sources:
- Jira ticket summary/description/comments/links (Mode A)
- Confluence pages (Mode A)
- Figma summary (Mode A)
- docs under `docs/ai/inputs/` (Mode B or alongside Mode A)
- Graphify report/query/path output (any mode, if graph exists)
- capture-knowledge output if used

Output:
- raw source list
- source excerpts
- unresolved source metadata

---

### Step 2 — Activate workers in parallel

**Mode A (external sources) — full set:**
```
Parallel group 1 (source readers):
  Jira Reader + Confluence Reader + Figma Reader + Graph Impact Reader

Parallel group 2 (analysis — after group 1 outputs exist):
  Ambiguity Detector + Conflict Detector + Missing-info Detector + State Extractor + Dependency Impact Analyzer

Parallel group 3 (advisory — optional):
  Research Advisor + Android Advisor + QA Scenario Advisor + Rollout/Risk Advisor
```

**Mode B (docs-only) — minimal set:**
```
Parallel group 1 (source readers):
  Doc Reader + Graph Impact Reader (if graphify-out/ exists)

Parallel group 2 (analysis):
  Ambiguity Detector + Missing-info Detector

Optional:
  Dependency Impact Analyzer (if graph path is complex)
  Android Advisor (if task is Android-specific)
```

Each worker produces a structured output per its contract in `refs/sub-agents.md`.

---

### Step 3 — Parent synthesis

The parent orchestrator merges worker outputs into:

**`docs/ai/clarification/context-pack.json`**
Use the generalized schema from `refs/contracts-and-artifacts.md`.
Separate clearly: facts / assumptions / unknowns / conflicts / decisions-needed / recommended v1 scope.

**`docs/ai/clarification/clarity-report.md`**
(may be embedded in clarification-brief in Mode B)
- clarity score 0–10
- what is well-understood
- what is missing
- what conflicts exist
- feature blocked? yes/no

**`docs/ai/clarification/clarification-brief.md`**
Human-readable distilled brief. This is the source document for requirements.

Must show:
- feature summary
- source documents used
- confirmed facts
- assumptions (with risk level)
- unknowns (with severity)
- conflicts and resolution status
- missing information
- graph impact summary
- research findings if any
- recommendation for v1 scope
- blockers before development

---

### Step 4 — Parent decides next step

The parent chooses exactly one outcome and records it in `context-pack.json → outcome`:

#### Outcome A — `ready`
Source material is sufficient. Proceed to requirements.

Use when:
- clarity score ≥ 7,
- no blocker-severity unknowns remain,
- acceptance criteria are testable,
- graph impact is understood.

#### Outcome B — `blocked`
Business rules, dependencies, or acceptance criteria are too incomplete to write safe requirements.

Use when:
- clarity score < 5,
- one or more blocker-severity unknowns or conflicts remain,
- the feature would require fabricating core business decisions.

**Action:** present the `clarification-brief.md` to the human and list specific decisions needed. Do not proceed until answers are received.

#### Outcome C — `research-loop`
Task direction is clear but solution choice needs comparison or repo research before a recommendation is safe.

Use when:
- clarity score 5–7,
- solution options exist but trade-offs are unclear,
- graph shows multiple viable patterns in the codebase.

**Action:** activate Research Advisor and/or Android Advisor. Merge findings into context-pack. Re-evaluate outcome.

---

## Exit criteria

Clarification is complete only when **all** of these exist:

**Mode A (full):**
1. `docs/ai/clarification/clarity-report.md`
2. `docs/ai/clarification/context-pack.json`
3. `docs/ai/clarification/clarification-brief.md`
4. parent outcome = `ready | blocked | research-loop`

**Mode B (minimal):**
1. `docs/ai/clarification/context-pack.json`
2. `docs/ai/clarification/clarification-brief.md` (with clarity section embedded)
3. parent outcome = `ready | blocked | research-loop`

---

## Explicit waiting rule

The parent must **not** generate canonical requirements until:
- Clarification is complete (all exit artifacts exist), **and**
- outcome = `ready` (or `research-loop` resolved to `ready`).

If outcome = `blocked`, the agent must ask the human for missing decisions rather than fabricate them.

---

## Human-in-the-loop boundary

If the task remains `blocked` after Clarification, the agent must:
1. Present `clarification-brief.md` to the human.
2. List exactly which decisions are needed (from `context-pack.json → decisions_needed`).
3. Wait. Do not fabricate answers, do not assume the less risky option, do not proceed.

---

## Clarity score guide

| Score | Meaning | Outcome |
|---|---|---|
| 8–10 | Fully clear, testable, no conflicts | `ready` |
| 6–7 | Mostly clear, minor gaps, safe assumptions possible | `ready` with documented assumptions |
| 4–5 | Directionally clear, solution unclear | `research-loop` |
| 0–3 | Core behavior or scope unclear | `blocked` |
