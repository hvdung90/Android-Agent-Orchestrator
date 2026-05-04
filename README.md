# Android Agent Orchestrator

> **A meta-skill for Android projects.**  
> Read the architecture map. Clarify the task. Approve requirements. Then code with one owner.

`android-agent-orchestrator` is a **behavioral orchestration skill** for AI coding agents working on Android projects. It coordinates process, Android domain guidance, runtime verification, architecture graphing, and code-quality guardrails into one disciplined workflow.

Current skill version: **v4.1.0**

---

## What this repo is

This repository does **not** contain an Android app, Gradle plugin, SDK, or executable CLI.

It contains a reusable instruction pack for AI agents such as Claude Code, Cursor, Codex, AI DevKit-compatible agents, and other tools that can consume markdown skill files.

The main file is:

```text
SKILL.md
```

Supporting reference docs live under:

```text
refs/
├── clarification-workflow.md
├── sub-agents.md
├── contracts-and-artifacts.md
└── playbooks.md
```

Use the whole pack, not just the README.

---

## Why this exists

Multiple AI agents working on the same Android codebase often fail in predictable ways:

| Without orchestration | With Android Agent Orchestrator |
|---|---|
| Agent guesses at architecture | Graphify or discovery output is read before planning |
| Two agents edit the same file | Only one code owner edits at a time |
| Ticket, design, and code disagree silently | Conflicts are recorded and escalated |
| AI jumps from vague request to implementation | Clarification runs before requirements |
| Success is claimed without proof | Build logs, screenshots, graph queries, and reports are required |
| Requirements are invented from weak input | Canonical requirements are generated from synthesized evidence |

The goal is not to make agents faster at typing code. The goal is to make them **safer, more auditable, and less likely to damage an existing Android project**.

---

## Core principle

> **Read the map. Read the task. Clarify before planning. Approve before coding. Parallelize analysis, not authority.**

Two operating rules summarize the repo:

```text
Parallel by lane, serial by file.
Parallel by worker, serial by decision.
```

Agents may work in parallel when they are reading, analyzing, reviewing, or verifying. They must not make competing canonical decisions or simultaneous product-code edits.

---

## The five lanes

The orchestrator keeps five lanes. v4 does **not** add a sixth lane; sub-agents are internal workers, not independent authorities.

| Lane | Owner | Responsibility |
|---|---|---|
| **AI DevKit** | Process owner | Phase control, docs, synthesis, requirements, routing, go/no-go decisions |
| **Android skills** | Android domain owner | Compose, AGP, edge-to-edge, Navigation, R8, platform pitfalls, migration advice |
| **Android CLI** | Runtime/tooling executor | Builds, device evidence, screenshots, layout capture, runtime verification |
| **Graphify** | Architecture map | Knowledge graph, dependency paths, affected components, graph update after code changes |
| **Karpathy guidelines** | Quality gate | Surgical changes, simplicity, explicit assumptions, anti-overengineering review |

This orchestrator is the **control plane** that coordinates the lanes, records ownership, and synthesizes final artifacts.

---

## What changed in v4.1

v3 focused on orchestration after a task was understandable. v4 added a formal clarification flow. v4.1 tightens the model so weak or partial source material can be handled safely.

Key additions:

1. **Clarification & Synthesis subflow** for noisy or incomplete tasks.
2. **Source modes**:
   - Mode A: external sources such as Jira, Confluence, Figma.
   - Mode B: docs-only sources under `docs/ai/inputs/`.
   - Mode C: no source material; block and ask for a task brief.
3. **Doc Reader sub-agent** for local markdown input docs.
4. **Full sub-agent output contracts** for source readers, ambiguity detection, conflict detection, missing-info detection, state extraction, dependency analysis, and advisory workers.
5. **Generalized `context-pack.json` schema** that works with Jira, docs-only, graph-only, or mixed source inputs.
6. **Graphify stage trigger rules** integrated into the artifact and gate contracts.
7. **Expanded playbooks** for feature work, weak tickets, bug investigation, XML-to-Compose migration, AGP modernization, and unfamiliar codebases.

---

## When to use this skill

Use it when:

- You have an **existing Android codebase** and want AI to understand architecture before touching code.
- You have raw input docs, Jira tickets, feature lists, design notes, or Figma links that need to become proper requirements.
- You are migrating XML UI to Compose.
- You are upgrading AGP, Gradle, AndroidX, Navigation, edge-to-edge, or other platform-sensitive areas.
- You need a disciplined handoff between process, platform, runtime, and quality owners.
- You want an evidence trail for every stage.

Skip it when:

- The task is a one-line or single-file fix.
- You are using only one agent on a throwaway prototype.
- The codebase is tiny and has no meaningful architecture to discover.
- You do not need requirements, verification, or auditability.

---

## Installation

### Option A — Use the full pack in a project repo

Recommended when your agent can read local files and references.

```bash
mkdir -p .skills

git clone https://github.com/hvdung90/Android-Agent-Orchestrator.git \
  .skills/android-agent-orchestrator
```

Then ask your agent to use:

```text
.skills/android-agent-orchestrator/SKILL.md
```

This preserves the `refs/` directory, which is required for the full v4.1 workflow.

---

### Option B — Claude Code quick install

Claude Code commonly reads `CLAUDE.md` from the project root. If you use that pattern, copy the skill and its references into the project:

```bash
curl -L -o CLAUDE.md \
  https://raw.githubusercontent.com/hvdung90/Android-Agent-Orchestrator/main/SKILL.md

mkdir -p refs

curl -L -o refs/clarification-workflow.md \
  https://raw.githubusercontent.com/hvdung90/Android-Agent-Orchestrator/main/refs/clarification-workflow.md

curl -L -o refs/sub-agents.md \
  https://raw.githubusercontent.com/hvdung90/Android-Agent-Orchestrator/main/refs/sub-agents.md

curl -L -o refs/contracts-and-artifacts.md \
  https://raw.githubusercontent.com/hvdung90/Android-Agent-Orchestrator/main/refs/contracts-and-artifacts.md

curl -L -o refs/playbooks.md \
  https://raw.githubusercontent.com/hvdung90/Android-Agent-Orchestrator/main/refs/playbooks.md
```

Then prompt naturally:

```text
Using the Android Agent Orchestrator workflow, analyze this existing Android codebase before planning changes.
```

---

### Option C — AI DevKit-style local skill

```bash
mkdir -p .skills

git clone https://github.com/hvdung90/Android-Agent-Orchestrator.git \
  .skills/android-agent-orchestrator

ai-devkit skill add --local .skills/android-agent-orchestrator/SKILL.md
```

If your AI DevKit version handles skill directories differently, keep the same principle: install `SKILL.md` together with the `refs/` directory.

---

### Option D — Any compatible agent

Upload or paste:

1. `SKILL.md`
2. `refs/clarification-workflow.md`
3. `refs/sub-agents.md`
4. `refs/contracts-and-artifacts.md`
5. `refs/playbooks.md`

Then start with a prompt such as:

```text
Follow SKILL.md. First identify source mode, read available docs, check whether graphify-out exists, and do not write code until requirements are approved.
```

---

## Source modes

The clarification workflow starts by deciding what source material exists.

| Mode | Sources | Behavior |
|---|---|---|
| **Mode A — External sources** | Jira, Confluence, Figma, linked tickets, external PRDs | Run full clarification with source readers and analysis workers |
| **Mode B — Docs-only** | Local files under `docs/ai/inputs/` | Run minimal clarification with Doc Reader, graph impact if available, ambiguity detection, and missing-info detection |
| **Mode C — No sources** | No ticket, no docs, no design, no brief | Block and ask the human for a task brief before proceeding |

The orchestrator should never fabricate requirements from a vague or source-free request.

---

## Stage model

Every non-trivial task moves through these stages.

| Stage | Name | Purpose | Code changes? |
|---|---|---|---|
| 0 | Intake | Identify task, sources, graph availability, suspected scope | No |
| 1 | Discovery | Read graph, docs, tickets, designs, and source material | No |
| 1.5 | Clarification & Synthesis | Detect ambiguity, conflicts, missing information, and produce canonical context | No |
| 2 | Requirements | Write canonical requirements from synthesized context | No |
| 3 | Design split | Write design plan and Android memo | No |
| 4 | Implementation lock | One code owner edits product code | Yes, one owner only |
| 5 | Verify | Build, run, capture evidence, update graph | No new scope |
| 6 | QA gate | Review diff, evidence, acceptance coverage, and close readiness | No new scope |

Mandatory stop points:

1. Stop after requirements and wait for human approval.
2. Stop before implementation until design, Android memo when needed, and single code owner are recorded.
3. Stop before close until runtime evidence, graph update, acceptance coverage, and diff review are complete.

---

## Sub-agent model

Sub-agents are workers, not authorities.

Allowed:

- read source material,
- extract facts,
- compare sources,
- score ambiguity,
- identify missing information,
- map affected components,
- recommend Android or QA considerations.

Not allowed:

- publish final requirements,
- publish final design,
- make final go/no-go decisions,
- edit product code independently,
- compete with the parent orchestrator as a second decision maker.

The parent orchestrator is the only canonical synthesizer.

---

## Canonical artifacts

A typical run produces or updates these files inside the target Android project:

```text
.project-orchestration/
├── vendor/
├── reports/
│   ├── provisioning.md
│   ├── routing.md
│   └── execution.md
└── evidence/
    ├── logs/
    └── screenshots/

docs/ai/
├── inputs/                 # raw human-provided docs; never overwrite
├── discovery/              # raw graph/source findings
├── clarification/          # context-pack, clarity report, clarification brief
├── requirements/           # canonical requirements only
├── design/
├── planning/
├── testing/
└── android-memo/

graphify-out/               # Graphify output; never hand-edit
.skills/                    # optional local skill storage
.ai-devkit.json             # optional AI DevKit config
```

Important canonical artifacts:

| Artifact | Owner | Purpose |
|---|---|---|
| `docs/ai/clarification/context-pack.json` | Parent orchestrator / AI DevKit | Machine-readable facts, assumptions, unknowns, conflicts, graph impact, outcome |
| `docs/ai/clarification/clarification-brief.md` | Parent orchestrator / AI DevKit | Human-readable synthesized brief |
| `docs/ai/clarification/clarity-report.md` | Parent orchestrator / AI DevKit | Clarity score and proceed/block/research-loop recommendation |
| `docs/ai/requirements/<task>.md` | Parent orchestrator / AI DevKit | Canonical requirements for human approval |
| `docs/ai/design/<task>.md` | Parent orchestrator / AI DevKit | Design and planning document |
| `docs/ai/android-memo/<task>.md` | Android skills | Android-specific advisory memo |
| `.project-orchestration/reports/execution.md` | Orchestrator | Final report with evidence and synthesis |

---

## Graphify policy

Graphify is optional, but strongly recommended for existing Android codebases.

The core rule:

```text
If graphify-out/ exists, read the graph before planning or requirements.
```

Typical setup:

```bash
pip install graphifyy

graphify install

/graphify .
```

Expected output:

```text
graphify-out/
├── GRAPH_REPORT.md
├── graph.json
└── graph.html
```

Stage triggers:

| Stage | Graphify behavior |
|---|---|
| Intake | Check whether `graphify-out/GRAPH_REPORT.md` exists |
| Discovery | Read `GRAPH_REPORT.md`; query affected feature area; trace paths when needed |
| Clarification | Feed graph impact into `context-pack.json` |
| Design | Use `graphify explain` when design rationale matters |
| Implementation | Do not query while coding; discovery already mapped impact |
| Verify | Run graph update after implementation |
| QA gate | Compare graph impact and check god nodes when relevant |

Do not hand-edit `graphify-out/**`.

---

## Built-in playbooks

The reference docs include playbooks for:

1. New feature with good docs and existing codebase.
2. New feature with weak Jira and partial Figma.
3. Edit existing feature.
4. Bug investigation.
5. XML to Compose migration.
6. AGP / build modernization.
7. Unfamiliar codebase with raw task brief.

Each playbook defines:

- source mode,
- discovery steps,
- clarification workers,
- Graphify queries,
- required artifacts,
- stage gates,
- verification evidence.

See:

```text
refs/playbooks.md
```

---

## Task routing examples

| Task type | Graphify first? | Primary code owner | Supporting lanes |
|---|---|---|---|
| New feature in existing codebase | Yes | AI DevKit | Android skills, Android CLI, Graphify |
| Edit existing feature | Yes | AI DevKit | Android skills, Android CLI, Graphify |
| Bug investigation | Yes, if graph exists | AI DevKit debug flow | Android CLI for evidence |
| XML to Compose migration | Yes | Android skills or selected code owner | AI DevKit, Android CLI, Graphify |
| AGP / build modernization | Yes | Android skills or selected code owner | AI DevKit, Android CLI |
| Unfamiliar codebase | Build/read graph first | AI DevKit capture/discovery | Android skills, Graphify |
| Docs-only requirements generation | If graph exists | No code owner yet | Doc Reader, Ambiguity Detector, Missing-info Detector |

---

## Hard rules

These rules are non-negotiable:

1. **One code owner at a time.** No simultaneous product-code edits.
2. **One canonical synthesizer.** Only the parent orchestrator publishes `context-pack`, clarification brief, requirements, and go/no-go decisions.
3. **Sub-agents are read-only or advisory.** They do not publish final requirements, final design, or product-code patches.
4. **Clarify weak source material before requirements.** Do not skip clarification when sources are vague, contradictory, or missing acceptance criteria.
5. **No success without evidence.** Every stage advancement must be backed by artifacts, logs, screenshots, graph output, or review notes.
6. **Read Graphify before touching existing code.** If `graphify-out/` exists, it must be consumed before planning or requirements.
7. **Stop after requirements.** Human approval is mandatory before design/implementation.
8. **No invented commands.** Use documented commands for the installed tool versions only.
9. **Karpathy guardrails apply to every code-touching step.** Keep changes surgical, simple, and explicitly verified.
10. **Record conflicts.** If sources disagree, write the conflict down and block when it changes scope, behavior, API, or architecture.

---

## Failure handling

| Failure | Required response |
|---|---|
| No source material exists | Block and ask the human for a task brief |
| Acceptance criteria are missing | Run Clarification; block if core behavior is unknowable |
| Jira / Figma / docs conflict | Record conflict; request decision if severity is major or blocker |
| Graphify is absent | Proceed with docs and capture-knowledge, but note missing graph evidence |
| Graphify is stale | Update graph before relying on it |
| Android CLI unavailable | Do not fabricate runtime evidence; record missing tool and ask for install/fix |
| Two lanes want to edit code | Stop, choose one code owner, make the other advisory only |
| Build fails | Preserve logs, summarize failure, do not claim success |
| Verification evidence is missing | Do not close task |

---

## Reporting contract

Every substantial run should end with a report at:

```text
.project-orchestration/reports/execution.md
```

The final report should include:

1. **Provisioning summary** — tools, skills, graph status, setup results.
2. **Capability summary** — active lanes and optional integrations.
3. **Ownership summary** — code owner, support owners, overlaps avoided.
4. **Execution evidence** — commands, logs, screenshots, graph queries, key findings.
5. **Karpathy diff review** — simplicity, scope discipline, assumptions, verification.
6. **Final synthesis** — what changed, why, evidence, graph before/after if relevant, follow-ups.

---

## Example prompts

```text
Using Android Agent Orchestrator, inspect this repo first and produce a discovery summary. Do not write code.
```

```text
Follow SKILL.md. I have task docs in docs/ai/inputs/. Generate requirements and stop for my review.
```

```text
Use the XML to Compose migration playbook. Read Graphify first, list migration order, write requirements, and wait for approval.
```

```text
Debug the tablet layout bug using the orchestrator workflow. Capture runtime evidence and do not make adjacent refactors.
```

```text
Modernize this project for a newer AGP version. Start with dependency/build discovery and produce an upgrade plan before code changes.
```

---

## Repository layout

```text
Android-Agent-Orchestrator/
├── README.md
├── SKILL.md
└── refs/
    ├── clarification-workflow.md
    ├── sub-agents.md
    ├── contracts-and-artifacts.md
    └── playbooks.md
```

---

## Compatibility notes

This skill references external tools and ecosystems whose command syntax may evolve:

- AI DevKit
- Android CLI / Android skills
- Graphify
- Claude Code or other markdown-skill consumers
- Android Gradle Plugin / Gradle / AndroidX tooling

Before executing commands, agents must verify that the command exists for the installed tool version. The orchestrator explicitly forbids invented flags, guessed paths, and fabricated success claims.

---

## Contributing

Useful contributions include:

- keeping README and `SKILL.md` version references in sync,
- adding real-world Android playbooks,
- improving artifact schemas,
- adding example outputs under an `examples/` directory,
- documenting compatibility with specific AI DevKit, Android CLI, Graphify, or agent versions,
- tightening failure handling and stage gates.

When changing the workflow, preserve these invariants:

```text
One code owner at a time.
One canonical synthesizer.
Clarify before requirements.
Approve before coding.
No success without evidence.
```

---

## License

MIT
