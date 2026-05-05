# Android Agent Orchestrator

> **A meta-skill for Android projects.**  
> Audit the tooling. Read the architecture map. Clarify the task. Approve requirements. Then code with one owner.

`android-agent-orchestrator` is a behavioral orchestration skill for AI coding agents working on Android projects. It coordinates setup/provisioning, process control, Android domain guidance, runtime verification, architecture graphing, and code-quality guardrails into one disciplined workflow.

Current skill version: **v4.2.7**

---

## What this repo is

This repository does **not** contain an Android app, Gradle plugin, SDK, or executable CLI. It contains a reusable instruction pack for AI agents such as Claude Code, Cursor, Codex, AI DevKit-compatible agents, and other tools that can consume markdown skill files.

The agent entry point is `SKILL.md`. The refs, templates, and examples support it — use the whole pack, not just this README.

```text
SKILL.md                          ← agent entry point
.agent-auth.yaml                  ← gitignored; tạo tự động; tất cả token
refs/
├── auth-bootstrap.md             ← auth init + just-in-time token check
├── provisioning-preflight.md     ← Stage -1 full decision tables
├── clarification-workflow.md     ← Stage 1.5 sequence, triggers, scoring
├── sub-agents.md                 ← worker catalog with YAML output contracts
├── contracts-and-artifacts.md    ← artifact schemas and stage gates
└── playbooks.md                  ← task-type → workflow mapping
templates/
├── agent-auth.example.yaml       ← auth file template (Level 1/2/3)
├── preflight-report.md           ← preflight output template
└── tooling-preflight.sh          ← idempotent audit script
examples/
└── preflight-report.example.md   ← filled example with auth section
docs/
├── FLOW.md                       ← complete flow diagram, all use cases
└── archive/
    └── README_4.1.md             ← previous version docs
```

---

## What changed in v4.2.x

v4.1 formalized Clarification & Synthesis. v4.2.x builds the full orchestration infrastructure.

| Version | Key addition |
|---|---|
| **v4.2.0** | Stage -1 Tooling Preflight; provisioning modes; Graphify freshness |
| **v4.2.1** | README slim; explicit `→ Load refs/` per stage; Stage 1.5 binary trigger; Mode C escape hatch |
| **v4.2.2** | Jira/Figma/Confluence link-driven (không cần setup trước); source mode derivation |
| **v4.2.3** | `docs/FLOW.md` complete flow diagram |
| **v4.2.4** | Jira Reader auto-follow linked_docs/linked_designs (1 level) |
| **v4.2.5** | `.agent-auth.yaml` Level 1/2/3; credential resolution per project key |
| **v4.2.6** | FLOW.md rewrite đầy đủ |
| **v4.2.7** | `refs/auth-bootstrap.md`: auth init + just-in-time token check per tool; MCP mapping; hard rule #14 |

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
