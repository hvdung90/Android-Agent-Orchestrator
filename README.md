# android-agent-orchestrator

> **A meta-skill for Android projects.**  
> One continuous workflow. Zero role overlap. Full evidence trail.

---

## What is this?

`android-agent-orchestrator` is a **SKILL.md** — a behavioral instruction file for AI coding agents (Claude Code, Cursor, Codex, and compatible tools).

It solves a specific problem: when you have multiple AI agent systems working on the same Android project — AI DevKit for process, Android CLI for runtime, official Android skills for platform logic — they tend to step on each other. They invent commands. They edit the same files simultaneously. They claim success without proof.

This skill prevents that. It defines **who owns what**, **who runs when**, and **what evidence must exist** before any step is considered done.

---

## The problem it solves

```
Without this skill:                   With this skill:
─────────────────────────────────     ─────────────────────────────────────────
Agent A edits MainActivity.kt    →    Only one owner edits code at a time
Agent B also edits MainActivity  →    Others analyze, verify, or document only
Both break the build             →    Handoff is explicit and logged
Nobody knows what happened       →    Every step produces evidence
```

---

## Layers it orchestrates

| Layer | Owner | Owns |
|---|---|---|
| **AI DevKit** | Process | Phases, docs, memory, `dev-lifecycle`, `debug`, `capture-knowledge` |
| **Android CLI** | Runtime/Tooling | `android init`, `android update`, skill discovery, layout capture, screenshots |
| **Official Android Skills** | Android domain | Compose migration, AGP upgrade, edge-to-edge, Navigation 3, R8 |
| **Optional external skills** | Gap filler | KMP patterns, MCP bridge, community packs — only when official skills fall short |
| **This orchestrator** | Control plane | Provisioning, routing, handoff discipline, synthesis |

---

## How to use

### Option A — Claude Code (recommended)

Place the skill file in your Android project root as `CLAUDE.md`:

```bash
curl -o CLAUDE.md \
  https://raw.githubusercontent.com/YOUR_USERNAME/android-agent-orchestrator/main/SKILL.md
```

Claude Code will automatically read it. Then prompt naturally:

```
"Set up this Android project with AI DevKit and Android CLI"
"Add edge-to-edge support following the orchestrator workflow"
"Migrate XML layouts to Compose"
"Debug the tablet layout bug"
```

### Option B — AI DevKit

```bash
# Register as a local skill
ai-devkit skill add --local ./SKILL.md

# Or place in .skills/ directory
mkdir -p .skills/
cp SKILL.md .skills/android-agent-orchestrator.md
```

### Option C — Any compatible agent

Upload or paste `SKILL.md` and prefix your request:

```
"Using the orchestrator skill, set up this Android project..."
"Follow SKILL.md to route this migration task..."
```

---

## When to use this skill

✅ Use it when:

- You are bootstrapping an Android repo for multi-agent work
- You need to install or verify AI DevKit, Android CLI, or Android skills
- You are running a feature, bugfix, migration, or modernization workflow
- You need a disciplined handoff between process, platform, and runtime owners
- You want an evidence trail (logs, screenshots, reports) for every step

❌ Skip it when:

- The task is a single-file change or one-liner fix
- You are working with only one agent system
- The project is a quick prototype without orchestration needs

---

## What it enforces

**5 hard rules the skill never breaks:**

1. **One code owner at a time.** Parallelism is allowed for analysis, docs, and verification — never for simultaneous edits to the same implementation area.
2. **No invented commands.** Only documented CLI commands are used. No guessing, no fabricating flags.
3. **Deterministic setup.** If `.ai-devkit.json` exists, reconcile it. If not, initialize first. No shortcuts.
4. **No casual edits to install-managed artifacts.** Use `ai-devkit install` to reconcile what AI DevKit owns.
5. **No claimed success without evidence.** Every installation, update, and execution step produces observable, logged output.

---

## Workflow overview

Every orchestration run goes through 7 phases in order. No skipping.

```
Phase 1 — Inventory     →  What exists? What's missing?
Phase 2 — Provision     →  Install or reconcile missing components
Phase 3 — Refresh       →  Update tools and registries
Phase 4 — Route         →  Assign exactly one code owner
Phase 5 — Execute       →  Run through the chosen workflow
Phase 6 — Verify        →  Collect logs, screenshots, command output
Phase 7 — Synthesize    →  Connect all outputs into one result narrative
```

---

## Task routing at a glance

| Task type | Primary owner | Support owners |
|---|---|---|
| New Android feature | Official Android skill | AI DevKit (planning), Android CLI (verify) |
| Bug investigation | AI DevKit `debug` | Android CLI (evidence), Android skill (if domain-specific) |
| XML → Compose migration | Official Android skill | AI DevKit (plan + risk log), Android CLI (verify) |
| AGP / build modernization | Official Android skill | AI DevKit (migration plan), Android CLI (build verify) |
| Unfamiliar codebase | AI DevKit `capture-knowledge` | Android skill (if Android entry point), Android CLI (runtime) |

---

## Project structure it creates

```
.project-orchestration/
├── vendor/
│   ├── ai-devkit/              # Mirror of AI DevKit source
│   ├── android-skills/         # Mirror of official Android skills
│   └── optional/               # Approved external skill packs
├── reports/
│   ├── provisioning.md         # What was installed and when
│   ├── routing.md              # Who owns what for this run
│   └── execution.md            # Results and follow-up items
└── evidence/
    ├── logs/                   # Command output, build logs, layout JSON
    └── screenshots/            # Before/after runtime captures
```

---

## Execution playbooks included

- **Playbook 1** — Feature implementation
- **Playbook 2** — Bug investigation
- **Playbook 3** — XML to Compose migration
- **Playbook 4** — AGP / build modernization

Each playbook specifies: who runs first, what commands to use, what evidence to collect, and how to synthesize the result.

---

## Failure handling

| Failure | Response |
|---|---|
| AI DevKit unavailable | Fallback to `npx ai-devkit@latest` |
| Android CLI unavailable | Stop. Request official bootstrap. Do not fabricate install path. |
| Official Android skill unavailable | Try CLI file-based install → `.skills/` import → MCP bridge → community pack |
| Owner conflict | Priority: safety → official Android skill → AI DevKit workflow → project conventions → optional skills |

---

## Optional external skills

The skill supports extending coverage with approved external packs — but only when official skills are insufficient.

**Community Android skill pack** (broader KMP/architecture/testing coverage):
```bash
git clone https://github.com/rcosteira79/android-skills.git \
  .project-orchestration/vendor/optional/rcosteira79-android-skills
```

**Android Skills MCP bridge** (for MCP-capable agents):
```bash
git clone https://github.com/skydoves/android-skills-mcp.git \
  .project-orchestration/vendor/optional/android-skills-mcp
```

**Karpathy coding guidelines** (anti-overengineering behavioral rules for any coding agent):
```bash
git clone https://github.com/forrestchang/andrej-karpathy-skills.git \
  .project-orchestration/vendor/optional/karpathy-guidelines
```

---

## Reporting contract

Every orchestration run ends with a 5-section report:

1. **Provisioning summary** — what was cloned, installed, updated
2. **Capability summary** — active AI DevKit skills, Android skills, optional packs
3. **Ownership summary** — code owner, support owners, forbidden overlaps avoided
4. **Execution evidence** — commands run, logs, screenshots, blockers
5. **Final synthesis** — what changed, why each owner was involved, follow-up work

---

## Final operating principle

> **Run in parallel by lane, not by file.**

- AI DevKit owns workflow and docs.
- Android CLI owns Android tooling and runtime evidence.
- Official Android skills own Android-specific guidance.
- Optional external skills fill gaps only.
- This orchestrator owns setup, routing, and synthesis.

**At all times, keep exactly one active code owner.**

---

## Repository contents

```
android-agent-orchestrator/
├── SKILL.md        # The orchestrator skill — the main file
└── README.md       # This file
```

---

## License

MIT
