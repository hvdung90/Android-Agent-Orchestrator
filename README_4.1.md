# android-agent-orchestrator v4.1

A control-plane skill for Android projects. Five lanes. One clarification subflow. Zero role overlap.

## What's new in v4.1

Fixes the gaps identified in v4:

- **Source modes** — Clarification now has explicit modes: full (Jira/Figma/Confluence), minimal (docs-only), blocked (no sources). No more guessing which workers to run.
- **Doc Reader** — new sub-agent for `docs/ai/inputs/` as a first-class source, not a fallback.
- **Full output contracts** — Ambiguity Detector, Conflict Detector, Missing-info Detector, State Extractor, Dependency Impact Analyzer now each have a YAML output schema. Agents no longer invent formats.
- **Generalized `context-pack.json`** — `sources` is now a typed array, works with any combination of Jira, docs, notes, or no external sources.
- **Graphify stage trigger rules** — table specifying which query to run at which stage for each task type, restored from v3.
- **Clarity score guide** — 0–10 scoring with explicit outcome mapping (ready / research-loop / blocked).
- **7 playbooks** (was 5), each with specific Graphify queries inline.

## Files

- `SKILL.md` — main operating contract
- `refs/clarification-workflow.md` — source modes, triggers, sequence, exit criteria, clarity scoring
- `refs/sub-agents.md` — full worker catalog with YAML output contracts for every worker
- `refs/contracts-and-artifacts.md` — artifact schemas, Graphify stage trigger table, gate definitions, ownership rules
- `refs/playbooks.md` — 7 task-type playbooks with inline Graphify queries

## Core idea

```
Your sources (Jira / docs / Figma / none)
        ↓  source mode detection
  Discovery (Graphify + source readers in parallel)
        ↓
  Clarification (analysis workers in parallel)
        ↓  context-pack + clarification-brief
  Requirements (single owner, human review gate)
        ↓  approved
  Design split (parallel, no code)
        ↓
  Implementation (single code owner)
        ↓
  Verify (Android CLI + Graphify --update)
        ↓
  QA gate (Karpathy diff review)
```

External sources are treated as raw context — read first, clarified second, synthesized into one canonical requirements doc. The orchestrator stops for human approval before any code work begins.

## Five lanes (unchanged)

| Lane | Owner |
|---|---|
| AI DevKit | Process, phases, docs, synthesis, requirements |
| Android skills | Android domain advisory |
| Android CLI | Runtime, device, build verification |
| Graphify *(optional)* | Architecture knowledge graph |
| Karpathy guidelines | Code-touching quality gate |

## When to use

✅ Use when:
- You have an existing codebase and want AI to understand architecture before touching code
- You have raw input docs (any format) and need AI to generate proper requirements
- You are coordinating more than one agent system on the same Android project
- You need a full evidence trail for every decision and code change

❌ Skip when:
- Single-file edits or trivial fixes
- Only one agent system in use
- Quick prototype with no process discipline

## License

MIT
