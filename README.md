# android-agent-orchestrator

> **A meta-skill for Android projects.**  
> One architecture map. Five coordinated lanes. Zero role overlap. Full evidence trail.

---

## What is this?

`android-agent-orchestrator` is a **SKILL.md** — a behavioral instruction file for AI coding agents (Claude Code, Cursor, Codex, and compatible tools).

It solves a specific problem: when you have multiple AI agent systems working on the same Android project, they tend to step on each other. They guess at architecture. They invent commands. They edit the same files simultaneously. They claim success without proof.

This skill prevents that. It defines **who owns what**, **who runs when**, **what to read before touching code**, and **what evidence must exist** before any step is considered done.

---

## The problem it solves

```
Without this skill:                     With this skill:
───────────────────────────────────     ──────────────────────────────────────────
Agent guesses at architecture      →    Graphify graph is read first
Agent A edits MainActivity.kt      →    Only one owner edits code at a time
Agent B also edits MainActivity    →    Others analyze, verify, or document only
Both break the build               →    Handoff is explicit and logged
Nobody knows what happened         →    Every step produces evidence
```

---

## The five lanes

| Lane | Owner | Owns |
|---|---|---|
| **AI DevKit** | Process | Phases, docs, memory, `dev-lifecycle`, `debug`, `capture-knowledge` |
| **Android skills** | Android domain | Compose migration, AGP upgrade, edge-to-edge, Navigation 3, R8 |
| **Android CLI** | Runtime/Tooling | `android init`, `android update`, skill discovery, layout capture, screenshots |
| **Graphify** *(optional)* | Architecture map | Knowledge graph of the codebase — read before every task on existing code |
| **This orchestrator** | Control plane | Provisioning, routing, handoff discipline, synthesis |

Lanes run **in parallel** for analysis, review, and verification. Only **one lane edits code** at any given moment.

---

## How to use

### Option A — Claude Code (recommended)

```bash
curl -o CLAUDE.md \
  https://raw.githubusercontent.com/YOUR_USERNAME/android-agent-orchestrator/main/SKILL.md
```

Claude Code reads it automatically. Then prompt naturally:

```
"Set up this Android project with AI DevKit and Android CLI"
"Add edge-to-edge support following the orchestrator workflow"
"Migrate XML layouts to Compose"
"Debug the tablet layout bug"
"I have a task brief in docs/ai/inputs/ — generate requirements and wait for my review"
```

### Option B — AI DevKit

```bash
ai-devkit skill add --local ./SKILL.md

# Or file-based:
mkdir -p .skills/
cp SKILL.md .skills/android-agent-orchestrator.md
```

### Option C — Any compatible agent

Upload or paste `SKILL.md` then prefix your request:

```
"Using the orchestrator skill, help me understand this codebase architecture first"
"Follow SKILL.md to route this migration task"
```

---

## When to use

✅ Use it when:

- You have an **existing Android codebase** and want AI to understand architecture before touching code
- You have **raw input docs** (task briefs, feature lists, design notes) and need AI to generate proper requirements
- You are **bootstrapping** an Android repo for multi-agent work
- You need a **disciplined handoff** between process, platform, and runtime owners
- You want a full **evidence trail** (logs, screenshots, graph queries, reports) for every step

❌ Skip it when:

- The task is a single-file change or one-liner fix
- You are working with only one agent system
- The project is a quick prototype without orchestration needs

---

## Graphify: read the map before touching code

One of the key additions in v3 is **Graphify** — an optional but strongly recommended tool that turns your entire codebase into a queryable knowledge graph.

```bash
pip install graphifyy && graphify install
/graphify .                   # build the graph once
graphify claude install        # make Claude Code read it automatically
```

**Output:**
```
graphify-out/
├── GRAPH_REPORT.md   ← god nodes, communities, surprising connections — read this first
├── graph.json        ← full persistent graph, query without re-reading raw files
└── graph.html        ← interactive visual explorer
```

**Why it matters:** Graphify reads before you code, not after. The graph tells you what connects to what, why code was written a certain way, and which components will be affected by your change — at 71x fewer tokens than reading raw files.

**When the orchestrator reads the graph:**

| Stage | Graphify action |
|---|---|
| Intake | Check if graph exists |
| **Discovery** | Read `GRAPH_REPORT.md` + query affected area + trace dependency path |
| Design | `graphify explain` to understand design rationale |
| Implementation | No queries — map was read in Discovery |
| Verify | `--update` after implementation |
| QA gate | Compare graph before/after |

---

## Input-driven requirement workflow

When you already have docs (task briefs, architecture notes, feature lists), the skill follows this flow — it never generates requirements from scratch when source material exists:

```
Your docs in docs/ai/inputs/
        ↓
  Read Graphify graph first     ← understand real architecture
        ↓
  Read your input docs          ← understand your intent
        ↓
  Cross-check for conflicts
        ↓
  Research gaps (optional)      ← only if spec is too vague
        ↓
  Generate requirements doc     ← at docs/ai/requirements/
        ↓
  STOP — wait for your review
        ↓ Approved
  Route → Execute → Verify
```

---

## Six-stage workflow

Every task goes through these stages in order. No skipping.

```
Stage 0 — Intake        →  Open task, check if Graphify graph exists
Stage 1 — Discovery     →  Read graph + run capture-knowledge (in parallel)
Stage 2 — Design split  →  AI DevKit writes plan; Android skills writes memo (no code)
Stage 3 — Implement     →  Single code owner; Karpathy guardrails active
Stage 4 — Verify        →  Android CLI runs build/screenshots; Graphify --update
Stage 5 — QA gate       →  Karpathy diff review; close only when all criteria met
```

---

## Task routing at a glance

| Task type | Graphify first? | Primary code owner | Support |
|---|---|---|---|
| New feature (existing codebase) | ✅ Yes | AI DevKit | Android skills, Android CLI |
| Edit existing feature | ✅ Yes — `query + path` | AI DevKit | Android skills, Android CLI |
| Bug investigation | ✅ Yes — `path` to trace | AI DevKit `debug` | Android CLI (evidence) |
| XML → Compose migration | ✅ Yes — list all xml nodes | Android skill | AI DevKit (plan), Android CLI |
| AGP / build modernization | ✅ Yes — scope impact | Android skill | AI DevKit (plan), Android CLI |
| Unfamiliar codebase | ✅ Yes — build graph first | AI DevKit `capture-knowledge` | Android skill |

---

## Project structure it creates

```
.project-orchestration/
├── vendor/
│   ├── ai-devkit/
│   ├── android-skills/
│   └── optional/
│       ├── andrej-karpathy-skills/
│       ├── rcosteira79-android-skills/
│       └── android-skills-mcp/
├── reports/
│   ├── provisioning.md
│   ├── routing.md
│   └── execution.md
└── evidence/
    ├── logs/
    └── screenshots/

docs/ai/
├── inputs/           ← your raw docs (never overwritten)
├── requirements/     ← agent-generated from your inputs
├── discovery/        ← graphify queries + capture-knowledge merged
├── design/
├── planning/
├── testing/
└── android-memo/     ← Android skills review memos

graphify-out/         ← Graphify territory (never hand-edit)
```

---

## Playbooks included

| Playbook | Graphify step |
|---|---|
| Feature: edge-to-edge | `query "window insets edge"` |
| Bug: layout broken on tablets | `path "LayoutComponent" "TabletTarget"` |
| Migration: XML → Compose | `query "xml layout view fragment"` → ordered migration list |
| AGP 9 upgrade | `query "gradle build agp"` → scope impact |
| First contact: unfamiliar codebase | `/graphify .` → read `GRAPH_REPORT.md` → then `capture-knowledge` |

---

## Hard rules (never broken)

1. **One code owner at a time** — parallelism for analysis only, never for simultaneous code edits.
2. **Read the map before touching code** — if `graphify-out/` exists, read it before requirements or planning.
3. **No invented commands** — only documented CLI commands; no fabricated flags.
4. **Reconcile, don't hand-edit** — use `ai-devkit install` for AI DevKit-managed files.
5. **No success without evidence** — every step produces observable output in `evidence/`.
6. **Stop after generating requirements** — wait for human review before proceeding to implementation.

---

## Optional integrations

| Tool | Purpose | Recommended |
|---|---|---|
| [safishamsi/graphify](https://github.com/safishamsi/graphify) | Architecture knowledge graph | ✅ Yes — for any existing codebase |
| [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) | Anti-overengineering behavioral rules | ✅ Yes — always |
| [rcosteira79/android-skills](https://github.com/rcosteira79/android-skills) | Broader Android/KMP patterns | When official skills fall short |
| [skydoves/android-skills-mcp](https://github.com/skydoves/android-skills-mcp) | MCP bridge for Android skills | When agent consumes MCP better |

---

## Failure handling

| Failure | Response |
|---|---|
| AI DevKit unavailable | Fallback to `npx ai-devkit@latest` |
| Android CLI unavailable | Stop — request official install, never fabricate path |
| Graphify not installed | Proceed with `capture-knowledge` only, note in report |
| Graphify graph stale | Run `--update` before querying |
| Official Android skill unavailable | `--agent` flag → `.skills/` import → MCP bridge → community pack |
| Two lanes want to edit code | Stop — pick one owner, other writes advisory memo |

---

## Reporting contract

Every run ends with a 6-section report in `.project-orchestration/reports/execution.md`:

1. **Provisioning summary** — what was cloned, installed, updated, Graphify graph status
2. **Capability summary** — active skills, Graphify node count and god nodes, optional packs
3. **Ownership summary** — code owner, support owners, graph path touched, overlaps avoided
4. **Execution evidence** — commands run, logs, screenshots, **graph queries and key findings**
5. **Karpathy diff review** — surgical changes? simplicity? assumptions documented? success verified?
6. **Final synthesis** — what changed, why each lane was involved, graph before/after, follow-up

---

## Final operating principle

> **Parallel by lane, serial by file. Read the map before touching code.**

- **AI DevKit** owns process, phase, docs, memory, requirements.
- **Android skills** own Android domain guidance.
- **Android CLI** owns runtime, device, and skill management.
- **Graphify** owns architecture understanding — read before every task on existing code.
- **Karpathy guidelines** own behavior on every code-touching step.
- **This orchestrator** owns setup, routing, handoff, and synthesis.

---

## Repository contents

```
android-agent-orchestrator/
├── SKILL.md        # The orchestrator skill — the main file (v3.0.0)
└── README.md       # This file
```

---

## License

MIT
