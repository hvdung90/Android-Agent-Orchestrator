# Changelog

## v4.9.0

### Added

- **Executable implementation plan** (`docs/ai/tasks/{task_id}/planning/implementation-plan.md`): Stage 3 now produces a per-task plan with exact files, exact test commands, expected outputs, and commit messages — no placeholders allowed.
- **Gate E.5 — per-task TDD gate**: RED evidence (`evidence/red-<task-id>.txt`) must exist before any product code is written for that task. Cannot be bypassed; CONFIRM-SKIP only with explicit human approval.
- **Android TDD mapping** in Stage 4: `change_type` → test-first target (`logic` → unit test, `ui` → Compose semantics test, `database` → `MigrationTest`, `network` → contract test, etc.).
- **Per-task TDD loop** in Stage 4: RED → GREEN → module tests → refactor → commit → spec-compliance review → quality review → next task.
- **Spec-compliance review before quality review**: spec-compliance (does it meet acceptance criteria?) is always done before quality/Karpathy review — order is enforced and non-reversible.
- **"Do not use this skill when"** section in `SKILL.md`.
- **Gate E.5** added to gate log, hard stop points, and compliance matrix.
- `tdd_evidence_complete: true` field in Stage 4 `state_on_complete`.

### Changed

- `SKILL.md`: version → 4.9.0; description rewritten to triggering-conditions only (superpowers pattern); Stage 3 mandates `implementation-plan.md`; Stage 4 rewritten with Android TDD Iron Law and per-task loop.
- `refs/stage-contracts.md`: Stage 3 `output_produces` adds `implementation-plan.md`; Stage 4 `input_requires` adds it; Stage 4 `output_produces` adds RED/GREEN evidence and per-task review records.
- `refs/compliance-policy.md`: 4 new MANDATORY rows (implementation-plan.md, Gate E.5 RED, GREEN, spec-compliance review); TDD CONFIRM-SKIP row added; never-bypass items 12–13 added; Gate E.5 in gate log example; 3 new violations.
- `docs/FLOW.md`: Stage 4 diagram updated with per-task TDD loop block; hard stops renumbered with Gate E and Gate E.5 entries.
- All `refs/*.md` version headers: 4.8.0 → 4.9.0.

---

## v4.8.0

### Added

- **`handoff.md` artifact** (`docs/ai/tasks/{task_id}/handoff.md`): generated at Stage 3 when `code_owner` is confirmed; updated on every Stage 4 interrupt. Gives any incoming developer a full snapshot of task state without reading session.json.
- **Project-level `status.json`** (`.project-orchestration/status.json`): global dashboard of all active tasks — `task_id`, `stage_reached`, `assignee`, `branch`, `pr_url`, `blocker`. Updated on every stage transition.
- **`assignee`, `handoff_to`, `branch`, `pr_url`** fields in `session.json`.
- **Graphify time-based staleness check**: two conditions now required — commit hash match AND `built_at + stale_after_days > now`. Catches projects with many small commits.
- **Hard rules 21–23**: handoff.md mandatory, status.json mandatory on every transition, single-task scope per session.
- **QUICKSTART.md Step 4**: handoff workflow with "dừng lại, bàn giao cho dev-b" and "resume task" instructions.

### Changed

- `refs/stage-contracts.md`: Stage -1 initializes `status.json`; Stage 3 produces `handoff.md` + sets `assignee`/`branch`; Stage 4 interrupt state mandates `handoff.md` update; Stages 5–7 update `status.json`.
- `refs/compliance-policy.md`: Stage 3 `handoff.md` MANDATORY row; Stage 4 interrupt mandatory rows; `status.json` and `handoff.md` in never-bypass list (items 10–11).
- `docs/FLOW.md`: `handoff.md` block in Stage 3; INTERRUPT/HANDOFF PATH box in Stage 4; Section 13 Handoff workflow added.
- All `refs/*.md` version headers: 4.7.0 → 4.8.0.

---

## v4.7.0

### Added

- **Stage 2.5 Decision Gate / ADR-lite** in `SKILL.md`, `refs/stage-contracts.md`, `refs/compliance-policy.md`, and `refs/contracts-and-artifacts.md`.
- **Stage 7 Docs/decision finalization** for ADR status updates, Task Changelog, and drift checks before close.
- **Task History Relevance Gate** at Stage 0: default skip for unrelated new tasks, metadata-only scan for continuation signals, and full history read only for explicit continuation or medium/high overlap.
- **`docs/ai/decisions/0000-template.md`**: global ADR-lite template for Android decisions.
- **Artifact version headers** for preflight, context-pack, requirements, Android memo, design, ADR-lite, and execution artifacts.
- **Affected Areas checklist** for requirements and design.
- **Decision Ownership matrix** mapping Android concern areas to owner lanes and required evidence.
- **AI-authored artifact rules**: human approval for requirements, facts vs assumptions, conflict preservation, ADR creation, and evidence-required success.

### Changed

- `SKILL.md`: version → 4.7.0; stage order now `-1 → 0 → 1 → [1.5] → 2 → 2.5 → 3 → 4 → 5 → 6 → 7`.
- `README.md`: version → 4.7.0; file map and change table synced with task-scoped storage and ADR-lite governance.
- `docs/FLOW.md` and all `refs/*.md` version headers synced to 4.7.0.

## v4.6.0

### Added

- **Compliance Policy** (`refs/compliance-policy.md`): stage compliance matrix, confirmation protocol, never-bypassable rules, skip-log audit trail, stage order enforcement, and task isolation rules.
- **Task-scoped storage** under `.project-orchestration/tasks/{task_id}/` and `docs/ai/tasks/{task_id}/`.

## v4.5.0

### Added

- **Gradle Module Impact Analyzer** worker.
- **Evidence Gate Matrix** keyed by `context-pack.json → change_type`.
- **Stage Output Contracts** (`refs/stage-contracts.md`) for typed inputs, outputs, interrupt state, and resume entry points.

## v4.4.0

### Added

- **Serena Code Analysis Worker** (`refs/sub-agents.md` — new "Code Analysis workers" category):
  - Symbol-level LSP queries via `get_symbols_overview`, `find_symbol`, `find_implementations`, `find_referencing_symbols`, `find_declaration`, `get_diagnostics_for_file`.
  - Activation is **agent-decided** based on per-stage conditions — no manual trigger needed.
  - **Mandatory** check: Stage -1 preflight (always non-blocking).
  - **Agent-decided** tools: `get_symbols_overview` (Discovery, graph_impact ≥ medium); `find_symbol` / `find_implementations` / `find_referencing_symbols` (Clarification, per trigger); `get_diagnostics_for_file` (Verify, kotlin-ls stable only).
  - **Code-owner request only**: `find_declaration` (Stage 4 advisory).
  - **Never called by agent**: `rename_symbol`, `replace_symbol_body`, `insert_*`, `safe_delete_symbol`, all `jet_brains_*` mutation tools.
  - **Dev-decided**: JetBrains backend (Android Studio IDE engine, opt-in only; agent uses LSP default).
  - Kotlin LS stability gate: diagnostics disabled until dev confirms `kotlin_ls_stable: true`.
  - YAML output contract defined; feeds `context-pack.json → dependencies`, `facts`, may upgrade `graph_impact`.
  - Install command (bootstrap/update if approved): `uv tool install oraios-serena`.

- **`refs/provisioning-preflight.md`**: new `## Serena` section — decision table, backend note, Kotlin LS stability note, blocking rule (always non-blocking).

- **`templates/tooling-preflight.sh`**: ⑧ Serena parallel check — `uv` presence + `uvx serena --version`; prints LSP default note + Kotlin LS pre-alpha caveat.

- **`templates/preflight-report.md`**: new `## Serena` section template.

- **`examples/preflight-report.example.md`**: filled Serena section with realistic data.

- **`refs/clarification-workflow.md`**: Code Analysis Worker activation rules in Stage 1.5 — per-trigger table; Serena YAML outputs included in Gate C exit criteria.

- **`refs/playbooks.md`**: all 7 playbooks updated with `[Serena: agent]` / `[Serena: code-owner request]` / `[Serena: optional]` annotations per stage.

- **`refs/contracts-and-artifacts.md`**: `tooling_readiness.serena` field in context-pack schema; Gate -1 and Gate C updated; `## Serena` in preflight report required sections.

- **`SKILL.md`**: version 4.4.0; Serena in TL;DR; hard rule #15 (no mutation tools); `serena-code-analysis` in metadata workers; Serena activation matrix table in Sub-agents section; `### Serena` in Tool action rules.

### Changed

- All `refs/` version headers: 4.3.0 → 4.4.0.
- `README.md`: version → 4.4.0; changelog table updated with v4.4.0 row.

---

## v4.3.0

### Added

- **QUICKSTART.md**: new file — 3-step quick start for humans; ref-load tier table; key files; common commands.
- **`templates/tooling-preflight.sh`**: rewritten with parallel bash checks (7 checks run concurrently via background jobs + temp files); auth token presence check; memory cache read (`tooling-cache.json`, `session.json`).
- **Local memory layer** (`.project-orchestration/memory/`):
  - `tooling-cache.json` — 24h TTL cache of Stage -1 results; skip preflight if `valid_until` in future AND `graph_commit` matches HEAD.
  - `session.json` — interrupted-task resume state (task_id, stage_reached, stage_status, code_owner, requirements_approved).
  - `graph-stamp.json` — Graphify freshness tracking (built_at, commit_sha, god_nodes, component_count).
- **`refs/contracts-and-artifacts.md`**: local memory schemas section (tooling-cache, session, graph-stamp); `graph_impact: low|medium|high` field in context-pack with Stage 5 skip guidance; sparse format rule for context-pack.
- **`SKILL.md` § Activation**: trigger phrases section so agents know when to load the skill.
- **`SKILL.md` § When to load refs**: LIGHT/MEDIUM/HEAVY/FULL tier table — lazy-load refs on demand.
- **`SKILL.md` § Minimal operating algorithm**: step 2 cache check + session resume; step 5 ref tier determination; step 12 `graph_impact`-gated Graphify update.
- **Stage -1 cache-first path**: read `tooling-cache.json` before running any tool checks; write cache after preflight completes.
- **Stage 5 `graph_impact` skip condition**: if `graph_impact` is `low`, skip `/graphify . --update`; record skip reason in execution report.

### Changed

- All `refs/` version headers: 4.2.7 → 4.3.0.
- `SKILL.md`: version → 4.3.0; directory layout added `.project-orchestration/memory/`; Stage -1 added cache check + `bash templates/tooling-preflight.sh` explicit call.
- `README.md`: version → 4.3.0; file map added `QUICKSTART.md` + memory dir; What changed table added v4.3.0 row.
- `docs/FLOW.md`: Stage -1 block updated — auth init → cache HIT/MISS branch → session resume offer → provisioning mode → parallel checks → apply actions.

---

## v4.2.8 — Doc sync

### Changed (doc-only, no behavior change)

- `SKILL.md`: version → 4.2.7; description updated; TL;DR rewritten; "What changed" table complete for v4.2.0–4.2.7; hard rule #14 (auth); Minimal operating algorithm 11 steps with auth; directory layout added `.agent-auth.yaml`.
- `README.md`: version → 4.2.7; file map added `refs/auth-bootstrap.md` + `templates/agent-auth.example.yaml`; What changed → table format.
- `templates/preflight-report.md`: added section `## Auth`.
- `examples/preflight-report.example.md`: added section `## Auth` with realistic sample data; added "Tokens to request" to Decisions.
- `refs/contracts-and-artifacts.md`: version → 4.2.7; Gate -1 added auth init requirement; preflight schema added `## Auth`; context-pack added `auth_status` field.
- `refs/sub-agents.md`, `refs/provisioning-preflight.md`, `refs/playbooks.md`, `refs/clarification-workflow.md`: version → 4.2.7.
- `docs/FLOW.md`: version header → 4.2.7.

---

## v4.2.7

### Added

- `refs/auth-bootstrap.md`: new ref file — single source of truth for auth management.
  - Step 1: initialize auth file at Stage -1 (auto-create if not present).
  - Step 2: just-in-time token check per tool (Jira, Confluence, Figma, GitHub) — prompt user when missing, save to file.
  - Step 3: credential resolution (Level 1/2/3) by project key prefix.
  - Step 4: save token securely; do not log to screen or report.
  - MCP mapping table: which token is used for which MCP tool.

### Changed

- `templates/agent-auth.example.yaml`: added MCP provider comment for each tool; removed manual copy instructions (skill auto-creates the file).
- `refs/provisioning-preflight.md`: replaced auth check section with reference to `refs/auth-bootstrap.md`; just-in-time model made explicit.
- `refs/sub-agents.md`: added `Required auth` for Jira Reader, Confluence Reader, Figma Reader.
- `refs/clarification-workflow.md`: replaced inline credential resolution with reference to `refs/auth-bootstrap.md`.
- `SKILL.md`: added `refs/auth-bootstrap.md` to metadata refs; Stage -1 loads auth-bootstrap Step 1 at the start.
- `docs/FLOW.md`: Stage -1 added Auth init block; Stage 0 updated credential resolution to just-in-time.

---

## v4.2.6

### Changed

- `docs/FLOW.md`: complete rewrite fully reflecting v4.2.5.
  - Section 2 (Stage -1): added check ⑥ auth to parallel checks; separated branches [A-D] done vs [E-J] continue.
  - Section 3 (Stage 0): added credential resolution step before fetching links.
  - Section 4 (Stage 1): fixed diagram auto-follow; merged Mode A + Mode B into shared parallel block.
  - Section 7 (Auth): new diagram showing Level 1/2/3 + resolve flow.
  - Section 8 (Playbooks): added auth check to all playbook flows.
  - Section 9 (Worker matrix): added `auto-follow` row for Jira Reader.
  - Section 12 (Hard stops): separated 8 stop points clearly; added WARN for auth missing.

---

## v4.2.5

### Added

- `.gitignore`: covers `.agent-auth.yaml`, `.DS_Store`, and agent runtime output dirs.
- `templates/agent-auth.example.yaml`: auth config template with 3 levels:
  - **Level 1** workspace (default Jira project prefix)
  - **Level 2** tool credentials (Atlassian, Figma, GitHub)
  - **Level 3** per-project overrides (multiple Atlassian instances)
- `refs/provisioning-preflight.md`: auth credentials check at Stage -1 — detect `.agent-auth.yaml`, record in preflight report, warn if missing when external links are present.
- `refs/clarification-workflow.md`: credential resolution rule — match ticket key prefix with `projects[]` override before using top-level credentials.
- `docs/FLOW.md`: added check ⑥ `.agent-auth.yaml` to Stage -1 parallel checks.

---

## v4.2.4

### Changed

- `refs/sub-agents.md` Jira Reader: added **auto-follow rule** — after reading a ticket, immediately fetch all `linked_docs` and `linked_designs` using the matching reader (Confluence Reader, Figma Reader, Doc Reader, or Jira Reader). One level deep only.
- `refs/clarification-workflow.md` Jira section: added auto-follow note inline.
- `docs/FLOW.md` Stage 1: updated Discovery diagram to show auto-follow branch.

---

## v4.2.3

### Added

- `docs/FLOW.md`: complete ASCII flow diagram covering all use cases.
  - Entry point decision tree (10 task types)
  - Stage -1 provisioning mode selection
  - Stage 0 source mode derivation (A/B/C)
  - Stage 1.5 clarification with worker activation per mode
  - Clarity score → outcome mapping
  - All 10 playbook flows (A–J)
  - Source mode × worker activation matrix
  - Graphify trigger map per stage
  - Parallel vs serial rule summary
  - Hard stop points list
- `README.md`: added `docs/FLOW.md` to file map.

---

## v4.2.2

### Added

- `refs/clarification-workflow.md`: **Source integrations** section.
  - Jira, Figma, Confluence are **link-driven** — no upfront config required.
  - Agent activates source readers only when developer provides a link.
  - Source mode derivation table (A / B / C) based on what developer provides.
- `SKILL.md` Stage 0: intake records developer-provided links and derives source mode.

---

## v4.2.1

### Changed

- README.md slimmed to human-facing overview only; removed content duplicated from SKILL.md.
- SKILL.md: added explicit `→ Load refs/<file>.md` instructions per stage — agent no longer has to guess when to load which ref.
- SKILL.md: added Sub-agents summary table with link to `refs/sub-agents.md`.
- SKILL.md: Stage 1.5 trigger replaced with binary checklist (6 measurable conditions).
- SKILL.md: Mode C now has an escape hatch for clearly bounded single-file tasks (treat as Mode B).
- All `refs/*.md` files now carry a `Skill version` line for drift detection.

---

## v4.2.0

### Added

- Stage -1 Tooling Preflight before Stage 0 Intake.
- Provisioning modes: `audit`, `bootstrap`, `update`, `refresh-graph`, `force-reinstall`.
- Install/update decision rules for AI DevKit, Android CLI, Android skills, Graphify, and Karpathy guidelines.
- `refs/provisioning-preflight.md`.
- `templates/preflight-report.md`.
- `templates/tooling-preflight.sh`.
- `examples/preflight-report.example.md`.
- Preflight artifact contract for `.project-orchestration/reports/preflight.md`.
- Graphify freshness policy.

### Changed

- README updated to v4.2.
- SKILL metadata updated to `4.2.0`.
- Stage model now starts with Tooling Preflight.
- Playbooks now include provisioning mode and preflight requirements.
- Contracts now include Gate -1.

### Safety

- Default provisioning mode is `audit`.
- No install/update/reinstall/rebuild unless explicitly requested.
- Existing `CLAUDE.md` must not be overwritten silently.
- Android skill names must not be guessed.
- `graphify-out/**` must never be hand-edited.
