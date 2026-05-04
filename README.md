# Android Agent Orchestrator

> **A meta-skill for Android projects.**  
> Audit the tooling. Read the architecture map. Clarify the task. Approve requirements. Then code with one owner.

`android-agent-orchestrator` is a behavioral orchestration skill for AI coding agents working on Android projects. It coordinates setup/provisioning, process control, Android domain guidance, runtime verification, architecture graphing, and code-quality guardrails into one disciplined workflow.

Current skill version: **v4.2.0**

---

## What this repo is

This repository does **not** contain an Android app, Gradle plugin, SDK, or executable CLI. It contains a reusable instruction pack for AI agents such as Claude Code, Cursor, Codex, AI DevKit-compatible agents, and other tools that can consume markdown skill files.

Main file:

```text
SKILL.md
```

Supporting docs:

```text
refs/
├── provisioning-preflight.md
├── clarification-workflow.md
├── sub-agents.md
├── contracts-and-artifacts.md
└── playbooks.md
```

Templates:

```text
templates/
├── preflight-report.md
└── tooling-preflight.sh
```

Use the whole pack, not just the README.

---

## What changed in v4.2

v4.1 formalized Clarification & Synthesis. v4.2 adds a mandatory setup lifecycle before task execution.

Key additions:

1. **Stage -1 — Tooling Preflight** before Stage 0 Intake.
2. **Provisioning modes**: `audit`, `bootstrap`, `update`, `refresh-graph`, `force-reinstall`.
3. **Idempotent install/update decision rules** for AI DevKit, Android CLI, Android skills, Graphify, and Karpathy guidelines.
4. **Graph freshness policy** for missing, existing, stale, and post-implementation graph state.
5. **Preflight evidence contract** at `.project-orchestration/reports/preflight.md`.
6. **Safe default**: `audit`. No global install/update/reinstall unless explicitly requested.

---

## Core principle

> **Audit first. Read the map. Read the task. Clarify before planning. Approve before coding. Parallelize analysis, not authority.**

```text
Parallel by lane, serial by file.
Parallel by worker, serial by decision.
```

Agents may work in parallel when reading, analyzing, reviewing, or verifying. They must not make competing canonical decisions or simultaneous product-code edits.

---

## Stage model

| Stage | Name | Purpose | Code changes? |
|---|---|---|---|
| -1 | Tooling Preflight | Audit/install/update required agent tooling and graph state | No product code |
| 0 | Intake | Identify task, sources, graph availability, suspected scope | No |
| 1 | Discovery | Read graph, docs, tickets, designs, source material | No |
| 1.5 | Clarification & Synthesis | Detect ambiguity, conflicts, missing information, produce canonical context | No |
| 2 | Requirements | Write canonical requirements from synthesized context | No |
| 3 | Design split | Write design plan and Android memo | No |
| 4 | Implementation lock | One code owner edits product code | Yes, one owner only |
| 5 | Verify | Build, run, capture evidence, update graph | No new scope |
| 6 | QA gate | Review diff, evidence, acceptance coverage, close readiness | No new scope |

Mandatory stop points:

1. Stop after preflight if required tooling is missing and the active mode does not allow install/update.
2. Stop after requirements and wait for human approval.
3. Stop before implementation until design, Android memo when needed, and single code owner are recorded.
4. Stop before close until runtime evidence, graph update, acceptance coverage, and diff review are complete.

---

## Stage -1: Tooling Preflight

Before Stage 0 Intake, determine:

1. Is AI DevKit installed?
2. Does `.ai-devkit.json` exist?
3. Should AI DevKit run `init`, `install`, or no action?
4. Is Android CLI installed?
5. Has `android update` been requested or allowed?
6. Are required Android skills available/installed?
7. Is Graphify installed?
8. Does `graphify-out/GRAPH_REPORT.md` exist?
9. Does `graphify-out/graph.json` exist?
10. Should Graphify build, update, or remain read-only?
11. Are Karpathy guidelines available as plugin, skill, or project guidance?
12. Which provisioning mode applies?

Default mode:

```text
audit
```

In audit mode, the agent may check files and command availability, but must not install, update, reinstall, or mutate global tooling.

---

## Provisioning modes

| Mode | Mutates global tools? | Mutates project files? | When to use |
|---|---:|---:|---|
| `audit` | No | No, except optional preflight report | Analyze readiness, review repo, start task safely |
| `bootstrap` | Only missing approved tools | Yes | User asks to set up the repo for agents |
| `update` | Yes, approved installed tools | Yes, if tool update regenerates project files | User asks to update tooling |
| `refresh-graph` | No, except Graphify install if explicitly allowed | Yes, graph files | User asks to rebuild/update architecture graph |
| `force-reinstall` | Yes | Yes | User explicitly asks for clean reinstall/reset |

If user intent is ambiguous, choose `audit`.

---

## Tooling checks

### AI DevKit

Check:

```bash
command -v ai-devkit || true
test -f .ai-devkit.json && echo "AI DevKit project config exists" || echo "AI DevKit project config missing"
```

Install missing:

```bash
npm install -g ai-devkit
```

Initialize new project:

```bash
ai-devkit init
```

Reconcile existing config:

```bash
ai-devkit install
```

Fallback:

```bash
npx ai-devkit@latest init
npx ai-devkit@latest install
```

Decision rule:

| State | Action |
|---|---|
| CLI missing, mode is `audit` | Report missing; do not install |
| CLI missing, mode is `bootstrap` or `update` | Install or use `npx ai-devkit@latest ...` |
| `.ai-devkit.json` missing, setup requested | Run `ai-devkit init` |
| `.ai-devkit.json` exists | Prefer `ai-devkit install` over re-init |

---

### Android CLI

Check:

```bash
command -v android || true
android info || true
```

Update when allowed:

```bash
android update
```

Set up agent skill:

```bash
android init
```

Decision rule:

| State | Action |
|---|---|
| Android CLI missing, mode is `audit` | Report missing; do not install |
| Android CLI present, mode is `update` | Run `android update` |
| Agent skill not initialized and setup requested | Run `android init` |
| Runtime evidence required but CLI missing | Block verification; do not fabricate screenshots/layout evidence |

---

### Android skills

List skills:

```bash
android skills list --long
```

Find skills:

```bash
android skills find "compose"
android skills find "edge-to-edge"
android skills find "performance"
android skills find "agp"
```

Install confirmed skill:

```bash
android skills add --skill=<skill-name>
```

Install all only when explicitly requested:

```bash
android skills add --all
```

Never guess skill names silently.

---

### Graphify

Check:

```bash
command -v graphify || true
python -m pip show graphifyy || true
test -f graphify-out/GRAPH_REPORT.md && echo "GRAPH_REPORT exists" || echo "GRAPH_REPORT missing"
test -f graphify-out/graph.json && echo "graph.json exists" || echo "graph.json missing"
```

Install when allowed:

```bash
pip install graphifyy
graphify install
```

Or isolated:

```bash
pipx install graphifyy
graphify install
```

Build graph when missing and allowed:

```bash
/graphify .
```

Update graph when present and allowed:

```bash
/graphify . --update
```

Decision rule:

| State | Action |
|---|---|
| Graphify missing, mode is `audit` | Report missing; use docs/capture-knowledge only |
| `graphify-out/` missing, existing codebase, graph allowed | Build graph |
| `graphify-out/GRAPH_REPORT.md` and `graph.json` exist | Read graph in Discovery |
| Graph may be stale after code changes | Run `/graphify . --update` during Verify |
| User asks to refresh graph | Use `refresh-graph` mode |

---

### Karpathy guidelines

Check:

```bash
test -f CLAUDE.md && grep -i "karpathy" CLAUDE.md || true
test -d .claude/plugins && find .claude/plugins -iname "*karpathy*" -maxdepth 3 || true
test -d .agents/skills && find .agents/skills -iname "*karpathy*" -maxdepth 4 || true
```

Claude Code plugin path:

```text
/plugin marketplace add forrestchang/andrej-karpathy-skills
/plugin install andrej-karpathy-skills@karpathy-skills
```

Project-local `CLAUDE.md` path:

```bash
curl -o CLAUDE.md   https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md
```

Append only when explicitly allowed:

```bash
printf "\n\n" >> CLAUDE.md
curl https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

Never overwrite an existing `CLAUDE.md` silently.

---

## The five lanes

| Lane | Owner | Responsibility |
|---|---|---|
| **AI DevKit** | Process owner | Phase control, docs, synthesis, requirements, routing, go/no-go decisions |
| **Android skills** | Android domain owner | Compose, AGP, edge-to-edge, Navigation, R8, platform pitfalls, migration advice |
| **Android CLI** | Runtime/tooling executor | Builds, device evidence, screenshots, layout capture, runtime verification |
| **Graphify** | Architecture map | Knowledge graph, dependency paths, affected components, graph update after code changes |
| **Karpathy guidelines** | Quality gate | Surgical changes, simplicity, explicit assumptions, anti-overengineering review |

v4.2 does **not** add a sixth lane. Preflight is a stage, not a lane.

---

## Source modes

| Mode | Sources | Behavior |
|---|---|---|
| **Mode A — External sources** | Jira, Confluence, Figma, linked tickets, external PRDs | Run full clarification with source readers and analysis workers |
| **Mode B — Docs-only** | Local files under `docs/ai/inputs/` | Run minimal clarification with Doc Reader, graph impact if available, ambiguity detection, missing-info detection |
| **Mode C — No sources** | No ticket, no docs, no design, no brief | Block and ask human for a task brief before proceeding |

The orchestrator should never fabricate requirements from a vague or source-free request.

---

## Canonical artifacts

```text
.project-orchestration/
├── vendor/
├── reports/
│   ├── preflight.md
│   ├── provisioning.md
│   ├── routing.md
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

| Artifact | Owner | Purpose |
|---|---|---|
| `.project-orchestration/reports/preflight.md` | Orchestrator | Tooling audit, install/update decisions, blockers |
| `docs/ai/clarification/context-pack.json` | Parent orchestrator / AI DevKit | Facts, assumptions, unknowns, conflicts, graph impact, outcome |
| `docs/ai/clarification/clarification-brief.md` | Parent orchestrator / AI DevKit | Human-readable synthesized brief |
| `docs/ai/requirements/<task>.md` | Parent orchestrator / AI DevKit | Canonical requirements for human approval |
| `docs/ai/android-memo/<task>.md` | Android skills | Android-specific advisory memo |
| `.project-orchestration/reports/execution.md` | Orchestrator | Final report with evidence and synthesis |

---

## Hard rules

1. **Preflight before Intake.**
2. **Default to audit.**
3. **One code owner at a time.**
4. **One canonical synthesizer.**
5. **Sub-agents are read-only or advisory.**
6. **Clarify weak source material before requirements.**
7. **No success without evidence.**
8. **Read Graphify before touching existing code when graph exists.**
9. **Stop after requirements.**
10. **No invented commands.**
11. **Karpathy guardrails apply to every code-touching step.**
12. **Record conflicts.**

---

## Repository layout

```text
Android-Agent-Orchestrator/
├── README.md
├── SKILL.md
├── CHANGELOG.md
├── LICENSE
├── refs/
│   ├── provisioning-preflight.md
│   ├── clarification-workflow.md
│   ├── sub-agents.md
│   ├── contracts-and-artifacts.md
│   └── playbooks.md
├── templates/
│   ├── preflight-report.md
│   └── tooling-preflight.sh
└── examples/
    └── preflight-report.example.md
```

---

## License

MIT
