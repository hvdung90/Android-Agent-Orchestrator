---
name: android-agent-orchestrator
description: Meta-skill for Android projects coordinating auth bootstrap, provisioning preflight, AI DevKit, Android skills, Android CLI, Graphify, Karpathy, and Serena code analysis into one disciplined workflow. Single .agent-auth.yaml manages all tokens; just-in-time token check per tool.
license: MIT
metadata:
  version: 4.4.0
  category: orchestration
  lanes:
    - ai-devkit
    - android-skills
    - android-cli
    - graphify
    - karpathy
  workers:
    - serena-code-analysis
  refs:
    - refs/auth-bootstrap.md
    - refs/provisioning-preflight.md
    - refs/clarification-workflow.md
    - refs/sub-agents.md
    - refs/contracts-and-artifacts.md
    - refs/playbooks.md
---

# Android Agent Orchestrator v4.4.0

## Activation

Load this skill when the user asks to **start, plan, analyze, or implement an Android task**.

Trigger phrases: `start task` · `new feature` · `fix bug` · `analyze repo` · `migrate` · `upgrade` · `set up agents` · `implement` · `review architecture`

Do not load this skill for non-Android projects or purely conversational questions.

---

## TL;DR

**Five-lane skeleton. Stage -1 Tooling Preflight + Auth Bootstrap. Single `.agent-auth.yaml` quản lý tất cả token.**

- Stage -1 khởi tạo auth file, audit tool readiness, rồi mới vào Intake.
- `.agent-auth.yaml` là nguồn sự thật duy nhất cho mọi token (Atlassian, Figma, GitHub). Token được hỏi just-in-time khi tool cần dùng.
- AI DevKit remains the conductor and the only owner of requirements, synthesis, routing, and final go/no-go.
- Android skills remain Android advisory specialists.
- Android CLI remains runtime verification and official Android skill management.
- Graphify remains the architecture map.
- Karpathy remains the code-touching quality gate.
- **Serena is the Code Analysis Worker** — symbol-level code retrieval, activated after Graphify identifies affected areas. Read-only in Discovery, advisory in Implementation. Never owns decisions or edits.
- Sub-agents are internal workers used during Discovery and Clarification. They do not become independent lanes and they never own final decisions or product-code edits.
- Jira Reader tự động theo dõi `linked_docs` và `linked_designs` (1 level deep).

> **Auth first. Audit tools. Read the map. Analyze code surface. Clarify before planning. Approve before coding.**

---

## What changed in v4.2.x

**v4.2.0** — Stage -1 Tooling Preflight, provisioning modes (`audit`/`bootstrap`/`update`/`refresh-graph`/`force-reinstall`), Graphify freshness policy.

**v4.2.1** — README slim (human-facing only); SKILL.md explicit `→ Load refs/` per stage; Stage 1.5 binary trigger checklist; Mode C escape hatch; refs version headers; README_4.1.md archived.

**v4.2.2** — Source integrations: Jira/Figma/Confluence link-driven (không cần setup trước); source mode derivation table (A/B/C).

**v4.2.3** — `docs/FLOW.md`: complete ASCII flow diagram, all 10 use cases, worker matrix, Graphify map.

**v4.2.4** — Jira Reader auto-follow: tự đọc `linked_docs` và `linked_designs` (Confluence, Figma, Doc, Jira child — 1 level).

**v4.2.5** — `.gitignore`; `templates/agent-auth.example.yaml` (Level 1/2/3); auth check tại Stage -1; credential resolution per project key prefix.

**v4.2.6** — `docs/FLOW.md` rewrite phản ánh đầy đủ v4.2.5.

**v4.2.7** — `refs/auth-bootstrap.md`: auth management tập trung — Bước 1 (auto-create file), Bước 2 (just-in-time token check per tool), Bước 3 (Level 1/2/3 resolve), Bước 4 (lưu an toàn). MCP mapping table. Required auth per source reader.

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

## When to load refs

Load refs on demand — **do not load all refs upfront**. Match tier to task complexity.

| Tier | Condition | Load |
|---|---|---|
| **LIGHT** | Mode C · single-file fix · no external sources | SKILL.md only |
| **MEDIUM** | Mode B · docs-only · no Jira/Figma | + `refs/clarification-workflow.md` |
| **HEAVY** | Mode A (Jira/Figma links) | + `refs/sub-agents.md` |
| **FULL** | Migration · AGP · unfamiliar codebase · god nodes in path | + `refs/playbooks.md` + all refs |

Always load at Stage -1: `refs/auth-bootstrap.md`, `refs/provisioning-preflight.md`.  
Always load when writing artifacts: `refs/contracts-and-artifacts.md`.

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
14. `.agent-auth.yaml` is the single source of truth for all tokens. Never log token values. Never commit the file.
15. Serena is read-only and advisory. Never call Serena code-mutation tools (`rename_symbol`, `replace_symbol_body`, `insert_*`, `safe_delete_symbol`). Code owner owns all edits.

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

## Sub-agents

→ **Load `refs/sub-agents.md`** for the full worker catalog with YAML output contracts.

Sub-agents are internal workers activated by the parent orchestrator during Discovery and Clarification. They are **read-only or advisory** — they never own final decisions or product-code edits.

| Category | Workers |
|---|---|
| Source readers | Jira Reader, Confluence Reader, Figma Reader, Doc Reader, Graph Impact Reader |
| Analysis workers | Ambiguity Detector, Conflict Detector, Missing-info Detector, State Extractor, Dependency Impact Analyzer |
| Advisory workers | Research Advisor, Android Advisor, QA Scenario Advisor, Rollout/Risk Advisor |
| **Code Analysis** | **Code Analysis Worker (Serena)** — symbol-level queries; read-only; agent-decided activation |
| Preflight | Tooling Preflight Auditor |

**Serena activation matrix (summary):**

| Stage | Condition | Serena tool | Decided by |
|---|---|---|---|
| 1 Discovery | graph_impact ≥ medium OR symbol named | `get_symbols_overview`, `find_symbol` | Agent |
| 1.5 Clarification | Interface in change path / surprising connection | `find_implementations`, `find_referencing_symbols` | Agent |
| 4 Implementation | Code owner needs usage context | `find_declaration` | Code owner request |
| 5 Verify | graph_impact ≥ medium AND kotlin-ls stable | `get_diagnostics_for_file` | Agent |
| 6 QA | Scope discipline check | `find_referencing_symbols` | Agent (optional) |
| JetBrains backend | Android Studio running | all above tools | Dev opt-in |

---

## Stage model

### Stage -1 — Tooling Preflight

Run before Intake.

→ **Load `refs/auth-bootstrap.md`** — chạy Bước 1 (khởi tạo file auth) ngay đầu Stage -1.
→ **Load `refs/provisioning-preflight.md`** for full decision tables, cache check, and safety rules.

**Cache check first:** Read `.project-orchestration/memory/tooling-cache.json`. If `valid_until` is in the future AND `graph_commit` matches `git rev-parse HEAD` → skip tool checks, use cached result, go directly to Stage 0.

**Otherwise run:** `bash templates/tooling-preflight.sh` — all checks run in parallel; output is the preflight report draft.

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

### Stage 0 — Intake

Open the task, confirm source availability, determine whether external task/design sources exist, and consume Stage -1 findings.

→ **Load `refs/clarification-workflow.md` § Source integrations** for source mode derivation.

Intake must record:
- Jira / Figma / Confluence links provided by developer, if any
- Source mode (A / B / C) derived from what was provided

### Stage 1 — Discovery

Read `.project-orchestration/reports/preflight.md`, `graphify-out/GRAPH_REPORT.md` if present, docs in `docs/ai/inputs/` if present, and source material.

### Stage 1.5 — Clarification & Synthesis

→ **Load `refs/clarification-workflow.md`** for sequence, exit criteria, and clarity scoring.

Run Stage 1.5 if **ANY** of the following are true:
- [ ] Task brief is < 50 words and has no linked ticket or design source
- [ ] No acceptance criteria are explicitly stated
- [ ] Two or more sources contradict each other on behavior or scope
- [ ] Graph exists and shows affected components not mentioned in sources
- [ ] Graph shows god nodes in the change path
- [ ] API, state handling, or error behavior is unspecified

Skip or minimize when: docs are detailed, acceptance criteria are testable, no conflicts exist, and graph shows a clean isolated change surface.

Source modes:
- **Mode A** — Jira/Figma/Confluence present: run full clarification with source readers and analysis workers.
- **Mode B** — docs-only (`docs/ai/inputs/`): run Doc Reader + Graph Impact Reader + Ambiguity Detector + Missing-info Detector.
- **Mode C** — no sources:
  - If task is clearly bounded (single-file refactor, rename, or documented bug with reproduction steps): treat as Mode B using the user's message as the sole doc.
  - Otherwise: block and ask the human for a task brief before proceeding.

### Stage 2 — Requirements

AI DevKit writes canonical requirements from synthesized context. Stop for human review.

→ **Load `refs/contracts-and-artifacts.md`** for `requirements/<task>.md` schema and Gate D criteria.

### Stage 3 — Design split

AI DevKit writes design/planning docs. Android skills write Android memo. No product-code changes.

→ **Load `refs/playbooks.md`** to select the correct workflow for the task type.

### Stage 4 — Implementation lock

Exactly one code owner edits code.

### Stage 5 — Verify

Android CLI gathers runtime evidence. Graphify runs update after implementation if graph exists.

**Graphify skip condition:** If `context-pack.json → graph_impact` is `low`, skip `/graphify . --update`. Record skip reason in execution report. Run update only when `graph_impact` is `medium` or `high`.

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

### Serena
- Check `uv` presence and `uvx serena` availability in Stage -1 (non-blocking).
- If missing: record `serena: not-configured`; never block Stage 0.
- If ready: activate Code Analysis Worker automatically per stage conditions.
- JetBrains backend is dev opt-in only — agent does not detect or start Android Studio.
- Kotlin LS diagnostics are disabled until dev confirms `kotlin_ls_stable: true`.
- Never call mutation tools: `rename_symbol`, `replace_symbol_body`, `insert_before_symbol`, `insert_after_symbol`, `safe_delete_symbol`, or any `jet_brains_*` refactoring tool.
- Serena outputs feed `context-pack.json → dependencies`, `facts`, and may upgrade `graph_impact`.
- Install command (bootstrap/update mode, if approved): `uv tool install oraios-serena`

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
├── memory/
│   ├── tooling-cache.json  ← skip Stage -1 nếu valid
│   ├── session.json        ← resume interrupted task
│   └── graph-stamp.json    ← graph freshness check
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
.agent-auth.yaml        ← gitignored; tạo tự động; chứa tất cả token
```

---

## Minimal operating algorithm

1. **Auth init** — check `.agent-auth.yaml`; auto-create if missing (refs/auth-bootstrap.md Bước 1).
2. **Cache check** — read `tooling-cache.json`; if valid → skip to step 4. If `session.json` shows interrupted task → offer resume.
3. **Tooling Preflight** — run `bash templates/tooling-preflight.sh`; write `preflight.md`; write `tooling-cache.json`.
4. **Intake** — collect links; derive source mode (A/B/C); resolve credential set; write/update `session.json`.
5. **Determine ref tier** — LIGHT / MEDIUM / HEAVY / FULL; load only needed refs.
6. **Discovery** — read Graphify if present; activate source readers; auto-follow Jira attachments (1 level).
7. **Token check** — just before each source reader, verify its token; hỏi user nếu thiếu.
8. **Clarification** — if any trigger fires, run workers in parallel; parent synthesizes context-pack + brief (sparse format).
9. **Requirements** — AI DevKit writes canonical doc; **stop for human approval**; update `session.json → requirements_approved: true`.
10. **Design split** — AI DevKit + Android skills in parallel; select code owner; update `session.json`.
11. **Implementation** — one owner edits code; all other lanes advisory only.
12. **Verify** — Android CLI gathers evidence; Graphify updates graph only if `graph_impact` is medium/high.
13. **QA gate** — AI DevKit + Karpathy review diff; write execution report; mark `session.json → stage_status: complete`.

---

## Final operating principle

> **Audit first. Read the map. Read the task. Clarify before planning. Approve before coding. Parallelize analysis, not authority.**
