# Android Agent Orchestrator

_Current skill version: 6.1.3_

> **A meta-skill for Android projects.**  
> Audit the tooling. Read the architecture map. Clarify the task. Approve requirements. Then code with one owner.

`android-agent-orchestrator` is a behavioral orchestration skill for AI coding agents working on Android projects. It coordinates setup, process control, Android domain guidance, runtime verification, architecture graphing, and code-quality guardrails into one disciplined workflow.

---

## What this repo is

This repository does **not** contain an Android app, Gradle plugin, SDK, or executable CLI. It is a reusable instruction pack for **Claude Code**: written for and tested with Claude Code only (`docs/decisions/0001-adaptive-workflow-pr8.md`). Other agents may be able to read the markdown, but they are not supported — their skill loading, sub-agents and tools behave differently and are untested.

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
Stage -1  Tooling Preflight     Audit tools, discover Android commands, check auth/team locks, read architecture graph
Stage  0  Intake                Classify task, derive source mode (Jira / Figma / plain text)
Stage  1  Discovery             Run source readers, graph impact analysis
Stage  1.5 Clarification        Resolve ambiguities, conflicts, missing info (auto-skipped if clear)
Stage  2  Requirements          Write canonical requirements doc → STOP for human approval
Stage  2.5 Decision Gate        Check if ADR-lite is needed → STOP for human approval if yes
Stage  3  Design                Write design + executable implementation plan (tasks with discovered/fallback commands)
Stage  4  Implementation        TDD per task: RED → GREEN → spec review → quality review → commit
Stage  5  Verify                Collect all required evidence (build, tests, screenshots, Kotlin static analysis)
Stage  6  QA Gate               Karpathy diff review + acceptance, regression, security/performance coverage
Stage  7  Finalization          ADR status, impact closure, task summary, artifact integrity, handoff finalized
```

The agent **stops at Stage 2 and Stage 2.5** and will not write code without your explicit approval.

Stage 7 always runs the task artifact integrity check. The heavier skill drift check runs only when orchestration files such as `SKILL.md`, `refs/**`, `templates/**`, `docs/FLOW.md`, or `CHANGELOG.md` changed.

Android CLI commands are discovered at Stage -1 and cached in `tooling-cache.json`; unsupported commands must use the documented fallback matrix. When `TEAM_DOCS_PATH` is active, Stage -1 reads `active-tasks/<repo>/locks.json` first (coordination mode) and opens markdown boards only when needed.

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

Every task in the implementation plan follows this loop. The only exceptions are the rows of `refs/compliance-policy.md § TDD exemption table` (e.g. a pure Gradle version bump or a colour/dimen-only resource change); an exempt task still records the replacement evidence that row requires:

1. Write the failing test → run it → save `evidence/red-<task>.txt`
2. Write minimum code to pass → run → save `evidence/green-<task>.txt`
3. Run full module tests
4. Refactor while green
5. Commit
6. Spec-compliance review (does it meet acceptance criteria?)
7. Quality review (Karpathy guidelines)

For Kotlin product-code changes, the quality gate also requires the Kotlin / Android rule checklist and repo-native static analysis evidence (`lint`, `ktlint`, `detekt`, `spotless`, or the project's equivalent check tasks when configured).

Product code cannot be written before RED evidence exists for that task, unless an exemption from that table is recorded in `skip-log.json`.

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
├── agent_auth.py                 ← only reader of .agent-auth.yaml: init / status / exec (agent never sees tokens)
├── architecture-domain.md        ← docs/ai/architecture/<domain>.md template
├── preflight-report.md           ← preflight output template
├── start-task-prompts.md         ← copy/paste prompts for starting tasks
├── tooling-preflight.sh          ← preflight entrypoint (thin wrapper, needs python3)
├── tooling_preflight.py          ← preflight core: one implementation, Markdown or --json
└── team_docs_sync.py            ← team-docs git sync: read (no checkout changes) / begin / commit-push
workflows/
└── fast.md                       ← self-contained FAST path (LIGHT tier): what to do, when to escalate
examples/
└── preflight-report.example.md   ← filled example with auth section
scripts/
└── lint-contracts.py             ← contract drift lint (paths, field names, version headers)
tests/
├── preflight/test_preflight.py  ← fixture-based regression tests (python3 -m unittest discover -s tests/preflight)
├── auth/test_agent_auth.py      ← credential helper tests (python3 -m unittest discover -s tests/auth)
├── contracts/test_lint_contracts.py ← linter regression tests (python3 -m unittest discover -s tests/contracts)
└── team_docs/test_team_docs_sync.py ← real-git tests for the team-docs sync helper (python3 -m unittest discover -s tests/team_docs)
docs/
├── FLOW.md                       ← complete flow diagram, all use cases
├── decisions/                    ← decisions about this skill pack itself (ADR-0001: adaptive workflow)
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
├── design/design-doc.md          ← design doc when trigger requires it
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
