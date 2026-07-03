# Android Agent Orchestrator

> **A meta-skill for Android projects.**  
> Audit the tooling. Read the architecture map. Clarify the task. Approve requirements. Then code with one owner.

`android-agent-orchestrator` is a behavioral orchestration skill for AI coding agents working on Android projects. It coordinates setup, process control, Android domain guidance, runtime verification, architecture graphing, and code-quality guardrails into one disciplined workflow.

---

## What this repo is

This repository does **not** contain an Android app, Gradle plugin, SDK, or executable CLI. It is a reusable instruction pack for AI agents such as Claude Code, Cursor, Codex, and other tools that can consume markdown skill files.

The agent entry point is `SKILL.md`. The refs, templates, and examples support it — use the whole pack, not just this README.

---

## When to use

✅ Use when:
- You have an existing codebase and want AI to understand architecture before touching code
- You have raw input (Jira, Figma, Confluence, plain text) and need AI to generate proper requirements
- You need a full evidence trail for every decision and code change
- You are handing off a task between developers and need continuity

❌ Skip when:
- Single-file trivial edits with no architectural impact
- Quick prototype with no process discipline

---

## How to get started

See **[QUICKSTART.md](QUICKSTART.md)** for the 3-step setup.

The short version:

1. Run `templates/tooling-preflight.sh` once to audit what's installed
2. Tell the agent your task: `"Implement feature X. Jira: https://..."` or `"Fix bug: <repro>"`
3. Review and approve the requirements doc — the agent stops and waits at every gate

---

## How the workflow works

The skill runs through numbered stages. Each stage has a defined input, output, and gate:

```
Stage -1  Tooling Preflight     Audit tools, check auth, read architecture graph (Understand-Anything, or Graphify fallback)
Stage  0  Intake                Classify task, derive source mode (Jira / Figma / plain text)
Stage  1  Discovery             Run source readers, graph impact analysis
Stage  1.5 Clarification        Resolve ambiguities, conflicts, missing info (auto-skipped if clear)
Stage  2  Requirements          Write canonical requirements doc → STOP for human approval
Stage  2.5 Decision Gate        Check if ADR-lite is needed → STOP for human approval if yes
Stage  3  Design                Write design + executable implementation plan (tasks with test commands)
Stage  4  Implementation        TDD per task: RED → GREEN → spec review → quality review → commit
Stage  5  Verify                Collect all required evidence (build, tests, screenshots, Kotlin static analysis)
Stage  6  QA Gate               Karpathy diff review + acceptance, regression, security/performance coverage
Stage  7  Finalization          ADR status, impact closure, task summary, artifact integrity, handoff finalized
```

The agent **stops at Stage 2 and Stage 2.5** and will not write code without your explicit approval.

Stage 7 always runs the task artifact integrity check. The heavier skill drift check runs only when orchestration files such as `SKILL.md`, `refs/**`, `templates/**`, `docs/FLOW.md`, or `CHANGELOG.md` changed.

---

## Core principle

> **Audit first. Read the map. Read the task. Clarify before planning. Approve before coding.**

```
Parallel by lane, serial by file.
Parallel by worker, serial by decision.
```

One code owner at a time. All other agents are advisory only.

---

## TDD enforcement

Every task in the implementation plan follows this loop — no exceptions:

1. Write the failing test → run it → save `evidence/red-<task>.txt`
2. Write minimum code to pass → run → save `evidence/green-<task>.txt`
3. Run full module tests
4. Refactor while green
5. Commit
6. Spec-compliance review (does it meet acceptance criteria?)
7. Quality review (Karpathy guidelines)

For Kotlin product-code changes, the quality gate also requires the Kotlin / Android rule checklist and repo-native static analysis evidence (`lint`, `ktlint`, `detekt`, `spotless`, or the project's equivalent check tasks when configured).

Product code cannot be written before RED evidence exists for that task.

---

## Handoff between developers

When Dev A needs to stop and pass the task to Dev B:

```
Tell the agent: "dừng lại, bàn giao cho dev-b"
```

The agent writes `docs/ai/tasks/{task_id}/handoff.md` with current state, files modified, and next task. Dev B resumes with:

```
Tell the agent: "resume task ANDROID-42"
```

All active tasks are tracked in `.project-orchestration/status.json`.

---

## File structure

```text
QUICKSTART.md                     ← start here
SKILL.md                          ← agent entry point
.agent-auth.yaml                  ← gitignored; auto-created; all tokens
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
├── architecture-domain.md        ← docs/ai/architecture/<domain>.md template
├── preflight-report.md           ← preflight output template
├── start-task-prompts.md         ← copy/paste prompts for starting tasks
└── tooling-preflight.sh          ← parallel audit script
examples/
└── preflight-report.example.md   ← filled example with auth section
docs/
├── FLOW.md                       ← complete flow diagram, all use cases
└── ai/
    ├── decisions/                ← GLOBAL: project-wide ADR ledger (immutable once Accepted)
    │   ├── 0000-template.md      ← ADR-lite template
    │   ├── README.md             ← index of every decision made (auto-created)
    │   └── ADR-NNNN-*.md         ← sequential, project-wide numbering
    └── architecture/             ← GLOBAL: living knowledge base, updated in place over time
        ├── README.md             ← index of domain files (auto-created)
        └── <domain>.md           ← e.g. networking.md, billing.md
.project-orchestration/           ← runtime state (gitignored)
├── status.json                   ← all active tasks dashboard
├── memory/
│   └── tooling-cache.json        ← global Stage -1 cache
└── tasks/{task_id}/              ← task-scoped session/evidence/reports
```

---

## Runtime artifacts per task

```text
docs/ai/tasks/{task_id}/
├── requirements/<task>.md        ← canonical requirements (human-approved)
├── design/<task>.md              ← design doc
├── planning/implementation-plan.md  ← executable TDD plan (exact files + test commands)
├── handoff.md                    ← current task snapshot for incoming dev
└── task-summary.md               ← compact continuity summary for future tasks

docs/ai/decisions/                ← GLOBAL, not per-task — see File structure above
docs/ai/architecture/             ← GLOBAL, not per-task — see File structure above

.project-orchestration/tasks/{task_id}/
├── session.json                  ← stage state, assignee, branch, blocker
├── skip-log.json                 ← audit trail of every skipped step
└── evidence/                     ← build logs, test results, screenshots
    ├── red-<task>.txt            ← failing test output (before implementation)
    └── green-<task>.txt          ← passing test output (after implementation)
```

---

## License

MIT
