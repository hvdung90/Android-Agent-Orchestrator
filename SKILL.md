---
name: android-agent-orchestrator
description: Meta-skill for Android projects coordinating provisioning preflight, AI DevKit, Android skills, Android CLI, Graphify, and Karpathy guardrails into one disciplined workflow. v4.2 adds Stage -1 Tooling Preflight with audit/bootstrap/update/refresh-graph/force-reinstall modes and explicit install/update decision rules.
license: MIT
metadata:
  version: 4.2.0
  category: orchestration
  lanes:
    - ai-devkit
    - android-skills
    - android-cli
    - graphify
    - karpathy
  refs:
    - refs/provisioning-preflight.md
    - refs/clarification-workflow.md
    - refs/sub-agents.md
    - refs/contracts-and-artifacts.md
    - refs/playbooks.md
---

# Android Agent Orchestrator v4.2

## TL;DR

**Keep the five-lane skeleton. Add Stage -1 Tooling Preflight before Intake.**

- Stage -1 audits whether AI DevKit, Android CLI, Android skills, Graphify, and Karpathy guidelines exist, are usable, and need install/update/rebuild.
- AI DevKit remains the conductor and the only owner of requirements, synthesis, routing, and final go/no-go.
- Android skills remain Android advisory specialists.
- Android CLI remains runtime verification and official Android skill management.
- Graphify remains the architecture map.
- Karpathy remains the code-touching quality gate.
- Sub-agents are internal workers used during Discovery and Clarification. They do not become independent lanes and they never own final decisions or product-code edits.

> **Audit first. Parallel by lane, serial by file. Parallel by worker, serial by decision.**

---

## What changed in v4.2

1. Stage -1 Tooling Preflight added before Stage 0 Intake.
2. Provisioning modes are explicit: `audit`, `bootstrap`, `update`, `refresh-graph`, `force-reinstall`.
3. Safe default is `audit`; no install/update/reinstall unless the user explicitly requests it.
4. Tool lifecycle is formalized for AI DevKit, Android CLI, Android skills, Graphify, and Karpathy.
5. Graphify freshness is explicit.
6. Preflight report is canonical: `.project-orchestration/reports/preflight.md`.

---

## Core operating principle

> **Readiness before routing. Read the map before touching code. Clarify before planning. Approve before coding.**

| Moment | Parallel | Serial |
|---|---|---|
| Tooling Preflight | Safe read-only checks | Install/update only when mode allows |
| Intake | AI DevKit opens phase; Graphify existence check | No code touched |
| Discovery | Graphify read + source readers + Android domain tagging | No code touched |
| Clarification | Multiple sub-agents analyze in parallel | Parent synthesis waits for required outputs |
| Requirements | AI DevKit writes one canonical requirements doc | Single owner |
| Design split | AI DevKit writes plan; Android skills writes memo | Neither edits product code |
| Implementation | One code owner only | All other lanes advisory only |
| Verify | Android CLI runs build/device/capture; Graphify updates | Code frozen |
| QA gate | AI DevKit + Karpathy review diff | No new changes |

---

## Hard rules

1. Run Stage -1 before Stage 0 for every non-trivial task.
2. Default to `audit`.
3. Do not install, update, reinstall, rebuild graph, or mutate global tooling unless the user's request allows it.
4. One code owner at a time.
5. One canonical synthesizer.
6. Sub-agents are read-only or advisory.
7. Do not skip Clarification when source material is weak.
8. No success without evidence.
9. Read Graphify before touching code when `graphify-out/` exists.
10. Stop after requirements.
11. No invented commands.
12. Karpathy applies to every code-touching step.
13. If sources disagree, record the conflict.

---

## Lanes

### Lane A — AI DevKit
Owns phase control, `docs/ai/**`, routing, synthesis, final requirements, planning, and review gates.

### Lane B — Android skills
Owns Android advisory memos, platform guidance, migration notes, API pitfalls, and compatibility advice.

### Lane C — Android CLI
Owns runtime evidence, screenshots, layout capture, device actions, official Android skill management, and verification commands.

### Lane D — Graphify
Owns graph build/query/update and architecture evidence.

### Lane E — Karpathy guidelines
Owns code-touching behavior and diff review.

v4.2 does **not** add a sixth lane. Stage -1 is a stage.

---

## Stage model

### Stage -1 — Tooling Preflight

Run before Intake.

Determine:
- active provisioning mode,
- whether AI DevKit exists,
- whether `.ai-devkit.json` exists,
- whether Android CLI exists,
- whether Android skills can be listed/found/added,
- whether Graphify exists,
- whether `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` exist,
- whether graph must be built, updated, or only read,
- whether Karpathy guidelines exist as plugin, skill, or project instruction,
- what actions are allowed,
- what blockers prevent Stage 0.

Default mode is `audit`.

Deliverable:
- `.project-orchestration/reports/preflight.md`

See `refs/provisioning-preflight.md`.

### Stage 0 — Intake

Open the task, confirm source availability, determine whether external task/design sources exist, and consume Stage -1 findings.

### Stage 1 — Discovery

Read `.project-orchestration/reports/preflight.md`, `graphify-out/GRAPH_REPORT.md` if present, docs in `docs/ai/inputs/` if present, and source material.

### Stage 1.5 — Clarification & Synthesis

Run when ambiguity, conflicts, missing acceptance criteria, or graph/source mismatches exist.

Source modes:
- Mode A: Jira/Figma/Confluence.
- Mode B: docs-only.
- Mode C: no sources; block and ask for a brief.

### Stage 2 — Requirements

AI DevKit writes canonical requirements from synthesized context. Stop for human review.

### Stage 3 — Design split

AI DevKit writes design/planning docs. Android skills write Android memo. No product-code changes.

### Stage 4 — Implementation lock

Exactly one code owner edits code.

### Stage 5 — Verify

Android CLI gathers runtime evidence. Graphify runs update after implementation if graph exists.

### Stage 6 — QA gate

AI DevKit + Karpathy review diff, evidence, graph update, acceptance coverage, and scope discipline.

---

## Provisioning modes

| Mode | Meaning | May install/update? |
|---|---|---|
| `audit` | Check readiness only | No |
| `bootstrap` | Install missing approved tools and initialize missing project setup | Yes, missing only |
| `update` | Update approved installed tools and reconcile project setup | Yes |
| `refresh-graph` | Build/update Graphify output | Graph only |
| `force-reinstall` | Clean reinstall/reset when explicitly requested | Yes |

If unsure, choose `audit`.

---

## Tool action rules

### AI DevKit
- If CLI missing in `audit`, report missing.
- If `.ai-devkit.json` missing and setup requested, run `ai-devkit init`.
- If `.ai-devkit.json` exists and setup/update requested, prefer `ai-devkit install`.
- Use `npx ai-devkit@latest ...` only as fallback or when global install is not desired.

### Android CLI
- If CLI missing in `audit`, report missing.
- If update requested, run `android update`.
- If agent setup requested, run `android init`.
- If verification requires Android CLI and it is missing, block runtime verification.

### Android skills
- Run `android skills list --long` before deciding which Android skills are available.
- Use `android skills find "<keyword>"` for task-specific discovery.
- Use `android skills add --skill=<skill-name>` only when the skill name is confirmed.
- Use `android skills add --all` only when explicitly requested.

### Graphify
- If `graphify-out/` exists, read it in Discovery.
- If graph is missing, build only in `bootstrap` or `refresh-graph`.
- If implementation changed code and graph exists, update in Verify.
- Never hand-edit `graphify-out/**`.

### Karpathy
- Check whether guidelines are installed or present.
- If missing in `audit`, record the gap.
- If code is touched, apply the principles even if the plugin is not installed, and record how the gate was applied.
- Do not overwrite existing `CLAUDE.md` unless explicitly requested.

---

## Waiting rules

The parent orchestrator must wait:
1. Before Stage 0: wait for Stage -1 result.
2. Before Requirements: wait for required Clarification outputs if any trigger fires.
3. Before Design: wait for human approval of requirements.
4. Before Implementation: wait for approved requirements, design doc, Android memo if Android-specific, and chosen single code owner.
5. Before Close: wait for runtime evidence, graph update if graph exists, Karpathy diff review, and acceptance coverage check.

---

## Directory layout

```text
.project-orchestration/
├── reports/
│   ├── preflight.md
│   └── execution.md
└── evidence/
    ├── logs/
    └── screenshots/

docs/ai/
├── inputs/
├── discovery/
├── clarification/
├── requirements/
├── design/
├── planning/
├── testing/
└── android-memo/

graphify-out/
.skills/
.ai-devkit.json
```

---

## Minimal operating algorithm

1. Run Stage -1 Tooling Preflight.
2. Choose provisioning mode; default `audit`.
3. Record tool readiness and graph state.
4. Intake sources.
5. Read Graphify if present.
6. Read raw docs and task/design sources.
7. If source clarity is weak, run Clarification.
8. Synthesize one `context-pack` and one `clarification brief`.
9. Generate one canonical requirements doc.
10. Stop for human review.
11. Resume with design split.
12. Lock one code owner for implementation.
13. Verify with Android CLI and Graphify update.
14. Run QA gate.
15. Publish final report.

---

## Final operating principle

> **Audit first. Read the map. Read the task. Clarify before planning. Approve before coding. Parallelize analysis, not authority.**
