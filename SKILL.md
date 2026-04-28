---
name: android-agent-orchestrator
description: Meta-skill for Android projects coordinating AI DevKit (process), Android skills (domain), Android CLI (runtime), Graphify (architecture graph), and Karpathy guardrails (quality) into one disciplined workflow. v4.1 adds a Clarification & Synthesis subflow with source-mode-aware workers, generalized context-pack schema, full sub-agent output contracts, and Graphify stage trigger rules integrated into refs/.
license: MIT
metadata:
  version: 4.1.0
  category: orchestration
  lanes:
    - ai-devkit
    - android-skills
    - android-cli
    - graphify
    - karpathy
  refs:
    - refs/clarification-workflow.md
    - refs/sub-agents.md
    - refs/contracts-and-artifacts.md
    - refs/playbooks.md
---

# Android Agent Orchestrator v4

## TL;DR

**Keep the five-lane skeleton. Add one new subflow, not one new lane.**

- **AI DevKit** remains the conductor and the only owner of requirements, synthesis, routing, and final go/no-go.
- **Android skills** remain Android advisory specialists.
- **Android CLI** remains runtime verification.
- **Graphify** remains the architecture map.
- **Karpathy** remains the code-touching quality gate.
- **Sub-agents** are internal workers used during Discovery and Clarification. They do not become independent lanes and they never own final decisions or product-code edits.

> **Parallel by lane, serial by file. Parallel by worker, serial by decision.**

---

## What changed in v4.1

v3 was strong at orchestration after a task was already understandable.
v4 added a formal Clarification subflow for noisy or incomplete inputs.
v4.1 patches the gaps found in v4:

1. **Source modes** — Clarification now has three explicit modes: full (Jira/Figma/Confluence), minimal (docs-only), and blocked (no sources). Skipping source readers when you only have `docs/ai/inputs/` is now explicit and correct.
2. **Doc Reader** — new sub-agent (A4) for `docs/ai/inputs/` as a first-class source, not a fallback.
3. **Full output contracts** for all analysis workers — Ambiguity Detector, Conflict Detector, Missing-info Detector, State Extractor, Dependency Impact Analyzer now each have a YAML output schema.
4. **Generalized `context-pack.json` schema** — `sources` is now a typed array, not Jira/Confluence/Figma hardcoded fields. Works with any source combination including docs-only.
5. **Graphify stage trigger rules** restored in `refs/contracts-and-artifacts.md` — specifies which query to run at which stage for each task type.
6. **Clarity score guide** — explicit 0–10 scoring with outcome mapping so the parent does not guess when to proceed.
7. **Playbooks expanded** to 7 (was 5), each with specific Graphify queries inline.

---

## Core operating principle

> **Do not parallelize by file. Parallelize by lane and by read-only worker.**

| Moment | Parallel | Serial |
|---|---|---|
| Intake | AI DevKit opens phase; Graphify existence check | No code touched |
| Discovery | Graphify read + source readers + Android domain tagging | No code touched |
| Clarification | Multiple sub-agents analyze in parallel | Parent synthesis waits for required outputs |
| Requirements | AI DevKit writes one canonical requirements doc | Single owner |
| Design split | AI DevKit writes plan; Android skills writes memo | Neither edits product code |
| Implementation | One code owner only | All other lanes advisory only |
| Verify | Android CLI runs build/device/capture; Graphify updates | Code frozen |
| QA gate | AI DevKit + Karpathy review diff | No new changes |

**One artifact has exactly one owner.**
Sub-agents may propose or extract, but only the parent orchestrator publishes canonical artifacts.

---

## Hard rules (non-negotiable)

1. **One code owner at a time.** No simultaneous product-code edits.
2. **One canonical synthesizer.** Only the parent orchestrator publishes `context-pack`, `clarification brief`, `requirements`, and go/no-go decisions.
3. **Sub-agents are read-only or advisory.** They may extract, compare, score, or recommend. They do not publish final requirements or final design on their own.
4. **Do not skip Clarification when source material is weak.** If raw task/doc/design is ambiguous, contradictory, or missing acceptance criteria, run Clarification before requirements.
5. **No success without evidence.** All decisions that advance stages must be backed by artifacts under `docs/ai/` or `.project-orchestration/evidence/`.
6. **Read Graphify before touching code.** If `graphify-out/` exists, read it before planning or requirements.
7. **Stop after requirements.** Requirements generation is still a mandatory review gate.
8. **No invented commands.** Use only documented AI DevKit, Android CLI, and Graphify commands.
9. **Karpathy applies to every code-touching step.** Simplicity first, surgical changes, explicit assumptions, verified goals.
10. **If sources disagree, record the conflict.** Never silently pick one source truth unless the user or repo conventions already define precedence.

---

## The five lanes stay the same

### Lane A — AI DevKit: process owner
Owns phase control, `docs/ai/**`, routing, synthesis, final requirements, planning, and review gates.

### Lane B — Android skills: Android domain owner
Owns Android advisory memos, platform guidance, migration notes, API pitfalls, and compatibility advice.

### Lane C — Android CLI: runtime/tooling executor
Owns runtime evidence, screenshots, layout capture, device actions, and official Android skill management.

### Lane D — Graphify: architecture knowledge
Owns graph build/query/update and architecture evidence.

### Lane E — Karpathy guidelines: quality gate
Owns code-touching behavior and diff review.

**Important:** v4 does **not** add a sixth lane. Sub-agents are workers inside the process, mainly under AI DevKit-led Discovery/Clarification.

---

## v4 stage model

### Stage 0 — Intake
Open the task, confirm source availability, determine whether external task/design sources exist.

**Inputs may include:**
- Jira URL or ticket brief
- Confluence URL or PRD
- Figma URL
- docs in `docs/ai/inputs/`
- existing graph in `graphify-out/`

**Deliverable:** intake note with source list and suspected scope.

### Stage 1 — Discovery
Run the read-only map phase.

Required actions:
- Read `graphify-out/GRAPH_REPORT.md` if present.
- Read existing docs in `docs/ai/inputs/` if present.
- Trigger source-reading sub-agents when raw external sources exist.
- Trigger Android classification if task is Android-specialized.

**Deliverable:** raw discovery bundle in `docs/ai/discovery/`.

### Stage 1.5 — Clarification & Synthesis

Run when any ambiguity trigger fires (see `refs/clarification-workflow.md`).

**Source mode determines the worker set and exit artifacts:**
- Mode A (Jira/Figma/Confluence): full worker set, all 3 exit artifacts required.
- Mode B (docs/ai/inputs/ only): minimal worker set — Doc Reader + Ambiguity Detector + Missing-info Detector. `clarity-report.md` may be embedded in `clarification-brief.md`.
- Mode C (no sources): block immediately, ask human for task brief.

Required outputs before proceeding (Mode A):
- `context-pack.json`
- `clarification-brief.md`
- `clarity-report.md`

Required outputs before proceeding (Mode B):
- `context-pack.json`
- `clarification-brief.md` (with clarity section embedded)

Only after these exist and `outcome = ready` may the parent generate requirements.

### Stage 2 — Requirements
AI DevKit writes the canonical requirements doc from the synthesized context, not from raw ticket text alone.

**Mandatory stop:** wait for human review before routing or implementation.

### Stage 3 — Design split
- AI DevKit writes design/planning docs.
- Android skills write Android memo.
- No product-code changes.

### Stage 4 — Implementation lock
Exactly one code owner edits code.
Sub-agents and advisory lanes may not create parallel patches.

### Stage 5 — Verify
Android CLI gathers runtime evidence.
Graphify runs `--update` after implementation.

### Stage 6 — QA gate
AI DevKit + Karpathy review diff, evidence, graph update, acceptance coverage, and scope discipline.

---

## Sub-agent policy

Use sub-agents only for work that is:
- independent,
- read-only or advisory,
- bounded by a clear input/output contract,
- mergeable by the parent orchestrator.

**Source mode determines which sub-agents activate:**
- **Mode A (Jira/Figma/Confluence present):** full source reader set + full analysis workers.
- **Mode B (docs/ai/inputs/ only):** Doc Reader + Graph Impact Reader + Ambiguity Detector + Missing-info Detector. Skip Jira Reader, Confluence Reader, Figma Reader.
- **Mode C (no sources):** ask the human for a task brief before running any workers.

Use sub-agents heavily in:
- source reading (including Doc Reader for local markdown),
- ambiguity/conflict detection,
- missing-information analysis,
- state extraction,
- advisory research.

Do **not** use sub-agents as parallel final decision makers for:
- canonical requirements,
- canonical design,
- product-code implementation,
- final go/no-go gates.

Detailed worker definitions and output contracts live in **`refs/sub-agents.md`**.

---

## Waiting rules before advancing

The parent orchestrator must **wait** at these points:

1. **Before Requirements**
   Wait for required Clarification outputs when any ambiguity trigger is hit.

2. **Before Design split**
   Wait for human approval of requirements.

3. **Before Implementation**
   Wait for:
   - approved requirements,
   - design doc,
   - Android memo if Android-specific,
   - chosen single code owner.

4. **Before Task close**
   Wait for:
   - runtime evidence,
   - graph update if graph exists,
   - Karpathy diff review,
   - acceptance coverage check.

Detailed dependency matrix lives in **`refs/contracts-and-artifacts.md`**.

---

## Directory layout (v4)

```text
.project-orchestration/
├── vendor/
├── reports/
└── evidence/

.docs/                      # optional extra repo docs if project uses it

docs/ai/
├── inputs/                 ← raw docs and raw task material
├── discovery/              ← raw findings + source extracts + graph notes
├── clarification/          ← clarity report, clarification brief, context pack
├── requirements/           ← canonical requirements docs only
├── design/
├── planning/
├── testing/
└── android-memo/

graphify-out/
.skills/
.ai-devkit.json
```

**Ownership**
- `docs/ai/clarification/**` is owned by AI DevKit as parent synthesizer.
- Sub-agent raw outputs may live temporarily under `docs/ai/discovery/raw/` or be embedded into the clarification docs, but they are not canonical until synthesized.

---

## Reference docs

Read these only when relevant:

- **`refs/clarification-workflow.md`** — triggers, sequence, and exit criteria for Clarification & Synthesis.
- **`refs/sub-agents.md`** — worker catalog, allowed responsibilities, and dependency graph.
- **`refs/contracts-and-artifacts.md`** — artifact schemas, waiting rules, approval gates, ownership, and stage exit conditions.
- **`refs/playbooks.md`** — how to run new feature, unclear feature, bug, migration, and unfamiliar-codebase flows.

---

## Minimal operating algorithm

1. Intake sources.
2. Read Graphify if present.
3. Read raw docs and task/design sources.
4. If source clarity is weak, run Clarification subflow.
5. Synthesize one `context-pack` and one `clarification brief`.
6. Generate one canonical requirements doc.
7. Stop for human review.
8. Resume with design split.
9. Lock one code owner for implementation.
10. Verify with Android CLI and Graphify update.
11. Run QA gate.
12. Publish final report.

---

## Final operating principle

> **Read the map. Read the task. Clarify before planning. Approve before coding. Parallelize analysis, not authority.**
