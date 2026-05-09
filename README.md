# Android Agent Orchestrator

> **A meta-skill for Android projects.**  
> Audit the tooling. Read the architecture map. Clarify the task. Approve requirements. Then code with one owner.

`android-agent-orchestrator` is a behavioral orchestration skill for AI coding agents working on Android projects. It coordinates setup/provisioning, process control, Android domain guidance, runtime verification, architecture graphing, and code-quality guardrails into one disciplined workflow.

Current skill version: **v4.7.0**

---

## What this repo is

This repository does **not** contain an Android app, Gradle plugin, SDK, or executable CLI. It contains a reusable instruction pack for AI agents such as Claude Code, Cursor, Codex, AI DevKit-compatible agents, and other tools that can consume markdown skill files.

The agent entry point is `SKILL.md`. The refs, templates, and examples support it — use the whole pack, not just this README.

```text
QUICKSTART.md                     ← start here (3 steps)
SKILL.md                          ← agent entry point
.agent-auth.yaml                  ← gitignored; auto-created; all tokens
firebase-remote-config-release-skill/
└── SKILL.md                      ← companion skill for Firebase RC design/review/release
refs/
├── auth-bootstrap.md             ← auth init + just-in-time token check
├── provisioning-preflight.md     ← Stage -1: cache check, decision tables
├── clarification-workflow.md     ← Stage 1.5 sequence, triggers, scoring
├── sub-agents.md                 ← worker catalog with YAML output contracts
├── contracts-and-artifacts.md    ← artifact schemas, memory schemas, stage gates
├── stage-contracts.md            ← typed stage input/output/resume contracts
├── compliance-policy.md          ← skip rules, mandatory gates, audit trail
└── playbooks.md                  ← task-type → workflow mapping
templates/
├── agent-auth.example.yaml       ← auth file template (Level 1/2/3)
├── preflight-report.md           ← preflight output template
├── start-task-prompts.md         ← copy/paste prompts for starting tasks
└── tooling-preflight.sh          ← parallel audit script (runs in background jobs)
examples/
└── preflight-report.example.md   ← filled example with auth section
docs/
├── FLOW.md                       ← complete flow diagram, all use cases
└── ai/
    └── decisions/
        └── 0000-template.md      ← ADR-lite template
.project-orchestration/           ← runtime state (gitignored)
├── memory/
│   └── tooling-cache.json        ← global Stage -1 cache
└── tasks/{task_id}/              ← task-scoped session/evidence/reports
```

---

## What changed in v4.2.x → v4.7.0

v4.1 formalized Clarification & Synthesis. v4.2.x builds the full orchestration infrastructure. v4.3–4.4 add performance, memory, and code-analysis layers. v4.5–4.7 add evidence, compliance, task isolation, and decision governance.

| Version | Key addition |
|---|---|
| **v4.2.0** | Stage -1 Tooling Preflight; provisioning modes; Graphify freshness |
| **v4.2.1** | README slim; explicit `→ Load refs/` per stage; Stage 1.5 binary trigger; Mode C escape hatch |
| **v4.2.2** | Jira/Figma/Confluence link-driven (no upfront setup required); source mode derivation |
| **v4.2.3** | `docs/FLOW.md` complete flow diagram |
| **v4.2.4** | Jira Reader auto-follow linked_docs/linked_designs (1 level) |
| **v4.2.5** | `.agent-auth.yaml` Level 1/2/3; credential resolution per project key |
| **v4.2.6** | FLOW.md rewrite — fully reflects v4.2.5 |
| **v4.2.7** | `refs/auth-bootstrap.md`: auth init + just-in-time token check per tool; MCP mapping; hard rule #14 |
| **v4.3.0** | Activation trigger; `QUICKSTART.md`; lazy-load ref tiers (LIGHT/MEDIUM/HEAVY/FULL); parallel `tooling-preflight.sh`; `graph_impact` field + Stage 5 skip; local memory layer (`tooling-cache.json`, `session.json`, `graph-stamp.json`); cache-first Stage -1; sparse context-pack rule |
| **v4.4.0** | **Serena Code Analysis Worker**: symbol-level LSP queries (not a lane); agent-decided activation per stage; mandatory/optional/never tool classification; JetBrains backend dev opt-in; Kotlin LS stability gate; hard rule #15 |
| **v4.5.0** | Gradle Module Impact Analyzer + Evidence Gate Matrix + typed stage output contracts |
| **v4.6.0** | Compliance Policy + task-scoped storage under `.project-orchestration/tasks/{task_id}/` and `docs/ai/tasks/{task_id}/` |
| **v4.7.0** | Stage 2.5 Decision Gate / ADR-lite; Stage 7 docs finalization; artifact version headers; Affected Areas; owner matrix; task changelog; drift checks |

---

## Core principle

> **Audit first. Read the map. Read the task. Clarify before planning. Approve before coding. Parallelize analysis, not authority.**

```text
Parallel by lane, serial by file.
Parallel by worker, serial by decision.
```

---

## When to use

✅ Use when:
- You have an existing codebase and want AI to understand architecture before touching code
- You have raw input docs (any format) and need AI to generate proper requirements
- You are coordinating more than one agent system on the same Android project
- You need a full evidence trail for every decision and code change

❌ Skip when:
- Single-file edits or trivial fixes with no architectural impact
- Only one agent system in use
- Quick prototype with no process discipline

---

## License

MIT
