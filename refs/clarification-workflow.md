# Clarification & Synthesis Workflow

_Skill version: 4.8.0 — update this when SKILL.md bumps a minor or major version._

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
- Serena availability (`serena: ready | missing`) from preflight,
- docs/tickets/design inputs.

---

## Source integrations

Jira and Figma are **link-driven** — the agent activates a source reader only when the developer provides a link.

→ **Load `refs/auth-bootstrap.md`** for full token check and credential resolution procedure.

Before running any source reader:
1. Resolve credentials (Step 3 in auth-bootstrap.md): match project key prefix → Level 3 override or Level 2 top-level.
2. Check that reader's token (Step 2): if empty → ask user → save → continue.
3. If the user refuses to provide it → skip reader, record it in the report.

### Jira

If the developer provides a Jira ticket URL:

```
https://<domain>.atlassian.net/browse/ANDROID-123
```

The agent fetches the ticket and runs the Jira Reader. Extracts: summary, acceptance criteria, linked docs, linked designs, status signals, open questions.

**Auto-follow attachments:** After reading the ticket, immediately fetch every item in `linked_docs` and `linked_designs` using the matching reader — Confluence Reader for Confluence pages, Figma Reader for Figma links, Doc Reader for other docs. One level deep only.

If no link is provided → Jira Reader does not run. Treat as Mode B or Mode C depending on other sources.

### Figma

If the developer provides a Figma share link:

```
https://www.figma.com/design/<file-id>/<name>?node-id=<frame-id>
```

To get a share link: Figma → right-click frame → Copy link.

The agent fetches the frame and runs the Figma Reader. Extracts: screens, components, visible states, CTA labels, notes, missing states.

If only a link is provided with no annotations: Missing-info Detector will flag missing UI states as a Clarification gap.

If no link is provided → Figma Reader does not run.

### Confluence

If the developer provides a Confluence page URL, the agent fetches and runs the Confluence Reader. If no link → skip.

---

### Source mode derivation at Intake

| Developer provides | Source mode |
|---|---|
| At least one Jira / Figma / Confluence link | Mode A |
| Only local docs in `docs/ai/inputs/` | Mode B |
| Nothing | Mode C |

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

## Code Analysis Worker (Serena) — activation in Clarification

Serena is activated **after** source readers and Graphify Impact Reader produce their outputs. It does not replace them — it drills into specific symbols they surface.

**Agent-decided activation rules for Stage 1.5:**

| Trigger from prior worker | Serena tool |
|---|---|
| Graph Impact Reader: `affected_components` list populated | `find_symbol` for each component |
| Graph Impact Reader: `surprising_connections` non-empty | `find_referencing_symbols` on the connecting symbol |
| Dependency Impact Analyzer: interface/abstract class in `direct_changes` | `find_implementations` |
| Missing-info Detector: unknown implementation pattern flagged | `find_referencing_symbols` |

If Serena is `missing` or `not-configured` in preflight → skip silently; note in clarification-brief.

**Output of Code Analysis Worker feeds into `context-pack.json` fields:**
- `dependencies[]` — add concrete implementors / callers found
- `facts[]` — add "N callers of X found" evidence
- `graph_impact` — may be upgraded if Serena reveals wider call surface than Graphify showed

---

## Sequence

1. Identify source mode and collect raw bundle.
2. Activate source readers in parallel.
3. Activate analysis workers in parallel.
4. **If Serena ready:** activate Code Analysis Worker based on triggers above (runs after step 3 outputs available).
5. Parent synthesizes:
   - `docs/ai/tasks/{task_id}/clarification/context-pack.json`
   - `docs/ai/tasks/{task_id}/clarification/clarification-brief.md`
   - `docs/ai/tasks/{task_id}/clarification/clarity-report.md` or embedded clarity section.
6. Parent decides outcome:
   - `ready`
   - `blocked`
   - `research-loop`

---

## Exit criteria

Mode A:
1. `clarity-report.md`
2. `context-pack.json`
3. `clarification-brief.md`
4. Serena YAML outputs (if Serena ready) attached or summarized in brief
5. parent outcome selected

Mode B:
1. `context-pack.json`
2. `clarification-brief.md` with clarity section
3. Serena YAML outputs (if Serena ready and triggers fired) attached or summarized
4. parent outcome selected

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
