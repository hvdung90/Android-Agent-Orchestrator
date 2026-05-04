# Clarification & Synthesis Workflow

## Purpose

This subflow converts noisy or incomplete inputs into a trustworthy development brief before requirements are written.

Raw Jira tickets, Confluence docs, Figma links, local markdown docs, and architecture reality often do not line up cleanly. This workflow surfaces conflicts, fills gaps, and produces one canonical artifact set the parent orchestrator uses to write requirements.

---

## Prerequisite

Stage -1 Tooling Preflight must be complete before Clarification.

Clarification should consume:
- source list from Intake,
- preflight report summary,
- Graphify availability and graph path if present,
- docs/tickets/design inputs.

---

## Source modes

### Mode A — External sources

Jira / Confluence / Figma present. Full clarification flow.

### Mode B — Docs-only

Only `docs/ai/inputs/` exists. Run:

```text
Doc Reader
Graph Impact Reader if graph exists
Ambiguity Detector
Missing-info Detector
```

### Mode C — No sources

Block and ask the human for a task brief.

---

## Trigger conditions

Run Clarification when:
- acceptance criteria are missing or vague,
- Jira says what to build but not behavior,
- Figma shows screens without state/edge-case rules,
- docs conflict,
- graph shows affected modules not mentioned in docs,
- graph god nodes are in the change path but not acknowledged,
- repo has an existing pattern that may change the recommendation.

Skip or minimize Clarification when:
- docs are detailed,
- acceptance criteria are testable,
- no conflicts exist,
- graph shows a clean isolated change surface.

---

## Sequence

1. Identify source mode and collect raw bundle.
2. Activate source readers.
3. Activate analysis workers.
4. Parent synthesizes:
   - `docs/ai/clarification/context-pack.json`
   - `docs/ai/clarification/clarification-brief.md`
   - `docs/ai/clarification/clarity-report.md` or embedded clarity section.
5. Parent decides outcome:
   - `ready`
   - `blocked`
   - `research-loop`

---

## Exit criteria

Mode A:
1. `clarity-report.md`
2. `context-pack.json`
3. `clarification-brief.md`
4. parent outcome selected

Mode B:
1. `context-pack.json`
2. `clarification-brief.md` with clarity section
3. parent outcome selected

---

## Waiting rule

Do not generate canonical requirements until Clarification is complete and outcome is `ready`.

If outcome is `blocked`, ask the human for missing decisions instead of fabricating answers.

---

## Clarity score guide

| Score | Meaning | Outcome |
|---|---|---|
| 8–10 | Fully clear, testable, no conflicts | `ready` |
| 6–7 | Mostly clear, minor gaps | `ready` with assumptions |
| 4–5 | Directionally clear, solution unclear | `research-loop` |
| 0–3 | Core behavior or scope unclear | `blocked` |
