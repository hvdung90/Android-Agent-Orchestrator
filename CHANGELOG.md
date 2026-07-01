# Changelog

## v4.14.0

### Added

- **Figma MCP-first, PAT fallback** (`refs/clarification-workflow.md`, `refs/auth-bootstrap.md`, `SKILL.md`): Figma Reader now self-checks the agent's own tool list at Stage 1 activation for Figma Dev Mode MCP tools (`get_metadata`, `get_design_context`, `get_variable_defs`, `get_screenshot`, `get_code_connect_suggestions`, `search_design_system`, `download_assets`) — no token needed on this path, auth handled by the MCP server via the developer's logged-in Figma desktop app. `figma.personal_access_token` + REST API is now explicitly the fallback, used only when MCP tools are absent. Ordered tool-call procedure added: `get_metadata` first (never call `get_design_context` unscoped on a whole-file link), then scoped `get_design_context`, `get_variable_defs` once per file, `get_screenshot` on the top-level frame. New hard rule #26: MCP availability is self-checked by the agent, never assumed from Stage -1 preflight (a bash script cannot detect MCP tool presence) — **deliberate non-change:** no new field added to `preflight.json` for this.
- **Figma Reader extended output** (`refs/sub-agents.md`): gains `design_tokens[]` (raw colors/spacing/typography from `get_variable_defs`), `component_reuse[]` (from `get_code_connect_suggestions`/`search_design_system`), `assets_exported[]`, `screenshot_ref`, `node_id`, `candidate_frames[]`, `access_mode: mcp|rest_api`. These are raw Figma-side findings only — Figma Reader never checks the target codebase for existing resources.
- **Scope disambiguation before extraction** (`refs/clarification-workflow.md`, `refs/sub-agents.md`): a Figma page/section/frame can contain multiple distinct layouts (different screens, or multiple states/variants of one screen). Figma Reader must inspect `get_metadata`'s node tree before calling `get_design_context`/`get_variable_defs`/`get_screenshot` — if more than one plausible screen-level frame is found, match against the task description first; if ambiguous, stop and ask the developer which frame(s) are in scope rather than guessing or processing all of them. Unselected frames are recorded in `candidate_frames[]` for transparency.
- **Android Advisor gains `token_reuse_recommendation[]`** (`refs/sub-agents.md`): resolves Figma Reader's raw `design_tokens[]` against existing `colors.xml`/`dimens.xml`/`Theme.kt` when Android Advisor has codebase read access (Stage 1.5 or Stage 3 memo). Same "reader observes, advisor recommends" split already used by Graph Impact Reader vs. Android Advisor's existing `recommended_api_or_pattern`.
- **Figma reference screenshot formalized as a Stage 1 Discovery artifact** (`refs/contracts-and-artifacts.md`): `get_screenshot` output saves to `docs/ai/tasks/{task_id}/discovery/figma/<screen>.png` — explicitly a distinct artifact from `screenshot_before`/`screenshot_after` (ADB device captures, Gate F evidence at Stage 4/5). No change to the Evidence Gate Matrix's required/optional evidence lists.
- `refs/contracts-and-artifacts.md`: `context-pack.json` gains top-level `design_tokens: []` / `component_reuse: []` (sparse-rule-compliant, next to `screens`/`states`). Decision Ownership table gains a "Design tokens / component reuse" row. `## MCP mapping` table in `refs/auth-bootstrap.md` splits the old single "Figma REST API" row into MCP tools (no token) + REST fallback (PAT).
- `refs/playbooks.md`: playbook 2 ("Weak Jira + partial Figma") gains the MCP-first self-check step.

## v4.13.0

### Added

- **Global ADR ledger** (`SKILL.md`, `refs/contracts-and-artifacts.md`, `refs/stage-contracts.md`, `refs/compliance-policy.md`, `docs/ai/decisions/0000-template.md`, `docs/FLOW.md`, `README.md`): ADRs move from per-task `docs/ai/tasks/{task_id}/decisions/ADR-NNNN-<slug>.md` to a **global, sequentially-numbered, immutable** ledger at `docs/ai/decisions/ADR-NNNN-<slug>.md`, with a new auto-created `docs/ai/decisions/README.md` index (same lazy-create pattern as `status.json`). Stage 2.5 now checks the index for an existing covering `Accepted` ADR before creating a new one — link to it (`adr_required: false, reason: "covered by ADR-NNNN"`) or supersede it (`supersedes:`/`superseded_by:`) instead of duplicating. Numbering is derived by reading the highest existing `ADR-NNNN` and incrementing (no counter file). An `Accepted` ADR is never hand-edited in place — new hard rule #25 and compliance-policy §3 item 15 make this explicit.
- **Persistent architecture knowledge base** (`SKILL.md`, `refs/contracts-and-artifacts.md`, `refs/stage-contracts.md`, `refs/compliance-policy.md`, `templates/architecture-domain.md` (new file), `docs/FLOW.md`, `README.md`): new global, domain-organized, **updated-in-place** folder `docs/ai/architecture/<domain>.md` (+ auto-created `README.md` index) — unlike everything else under `docs/ai/tasks/`, this is not a per-task snapshot. Domain names are project-specific (e.g. `networking.md`, `billing.md`), not fixed by the skill. Stage 7 creates-or-updates a domain file **iff** `adr_required: true` OR `module_impact_chain.estimated_build_scope` is `local-chain`/`full-project` OR `change_type: architecture_change` — otherwise AUTO-SKIP (most tasks never touch it; `workflow_mode` is deliberately not part of the trigger). Updates are **section-level patches** (rewrite only the affected `##` section(s), append one row to a trailing `## Change Log`), never a whole-file rewrite.
- `refs/contracts-and-artifacts.md`: new §§ 4b (decisions/README.md schema), 4c (numbering allocation rule), 4d (duplicate-ADR detection procedure), 4e (architecture-domain schema + trigger), 4f (architecture/README.md schema). Ownership rules table gains 4 new global-path rows. Gate D.5 and Gate G gain required items for the two new checks so a task cannot close Stage 7 without evaluating them.
- `refs/compliance-policy.md`: Stage compliance matrix gains "Stage 2.5 duplicate-ADR check" (MANDATORY) and "Stage 7 architecture-doc update" (AUTO-SKIP, condition given). §6 Task isolation rule gains a second "shared global paths" category — writable only by Stage 2.5/Stage 7 of the *active* task (not Stage-(-1)-only like the existing global paths), explicitly patching the wording that would otherwise forbid these writes under hard rule #18.

### Migration note

Projects with pre-existing per-task ADRs from before v4.13.0 should be offered a one-time migration into the global ledger the next time Stage 2.5 or Drift Check runs — ask first (CONFIRM-SKIP style), never migrate silently.

## v4.12.0

### Added

- **Understand-Anything as primary architecture map** (`SKILL.md`, `refs/*.md`, `templates/*`, `docs/FLOW.md`, `.gitignore`): [Understand-Anything](https://github.com/Egonex-AI/Understand-Anything) (`/understand`, `.understand-anything/knowledge-graph.json`) is now checked **first** at Stage -1 for the architecture-map lane. Graphify becomes the **fallback** — only checked/used when Understand-Anything's plugin/skill is not installed and `.understand-anything/knowledge-graph.json` does not exist. Lane D renamed from "Graphify" to "Architecture Map (Understand-Anything primary, Graphify fallback)".
- `templates/tooling-preflight.sh`: new Understand-Anything detection block (plugin search under `.claude/plugins`, `.understand-anything/knowledge-graph.json` presence) in both `--json` and markdown modes. `preflight.json` gains `tools.understand_anything` and a new `architecture_map` object (`active_tool`, `understand_anything_graph_present`, `graphify_report_present`, `graphify_json_present`) replacing the old Graphify-only `graph` object. Non-blocking gap renamed `graphify_missing`/`graph_report_missing` → `architecture_map_missing`/`architecture_map_graph_missing`.
- `refs/contracts-and-artifacts.md`: `context-pack.json → tooling_readiness.graphify` replaced with `tooling_readiness.architecture_map { active_tool, state }`. `owner:` enum gains `understand-anything`. Decision Ownership and stage-trigger tables updated to show Understand-Anything as primary owner of architecture impact.
- `refs/sub-agents.md`: Tooling Preflight Auditor YAML contract gains `architecture_map { active_tool, understand_anything, graphify }` replacing the flat `graphify:` block. Graph Impact Reader `source_type` generalized from `graphify` to `architecture-map` with a `tool` field.

### Changed

- All prose referring to "Graphify" as *the* architecture-map check (Stage -1 determine list, Discovery reads, Verify updates, staleness checks, playbooks, `docs/FLOW.md` diagrams) now describes the priority-checked pair: Understand-Anything first, Graphify fallback. Graphify's own behavior when it is the active tool is unchanged.

## v4.11.0

### Changed

- **Replaced AI DevKit with Spec Kit as Lane A** (`SKILL.md`, `refs/*.md`, `templates/*`, `docs/FLOW.md`, `docs/ai/decisions/0000-template.md`, `.gitignore`): Lane A conductor is now [Spec Kit](https://github.com/github/spec-kit) (`specify` CLI). Tooling check switched from `command -v ai-devkit` + `.ai-devkit.json` (file) to `command -v specify` + `.specify/` (directory, produced by `specify init`). Install/update rules now use the real Spec Kit commands: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z` (or ephemeral `uvx --from git+https://github.com/github/spec-kit.git specify ...`) to install, `specify init --here --integration <agent>` to bootstrap, and `specify self check` / `specify self upgrade` to update. `.specify/memory/constitution.md` (produced by `/speckit.constitution`) is treated as human-approved and must never be hand-edited or silently overwritten.
- All `owner: ai-devkit` artifact-contract fields renamed to `owner: spec-kit`; the `Tooling Preflight Auditor` output contract in `refs/sub-agents.md` renamed `ai_devkit` → `spec_kit`.
- Orchestrator's own `docs/ai/**` artifact contract (requirements, design, planning, ADRs) is unchanged — Spec Kit's native `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, and `/speckit.clarify` commands may be used as the underlying mechanism for those stages, but the canonical human-reviewed artifact still lives under `docs/ai/tasks/{task_id}/**`.


### Added

- **TDD exemption categories** (`refs/compliance-policy.md`): Concrete table defining the only four cases where Gate E.5 CONFIRM-SKIP is reasonable — pure UI pixel/layout tweak (screenshot substitute), legacy untestable code (characterization test required first), pure refactor with no behavior change (existing suite must pass), and spike/investigation (no product code allowed). For each case: why TDD-first is impractical, allowed alternative, and what is still required. Invalid exemption reasons (hard-to-test, time pressure) listed explicitly. Every exemption still writes a structured record to `skip-log.json`.
- **Preflight JSON output** (`templates/tooling-preflight.sh --json`): New `--json` flag emits machine-readable JSON to stdout. Schema: `ready_for_stage_0` (boolean gate), `blocking_gaps` (array), `non_blocking_gaps` (array), `tools` (per-tool status), `graph` (report/json present), `cache` (valid_until, graph_commit). Existing markdown behavior unchanged. Python 3 implementation; runs same checks as bash path.
- **`preflight.json` schema** (`refs/contracts-and-artifacts.md`): Formal schema and agent decision rule added under the preflight artifact section. Rule: use `preflight.json → ready_for_stage_0` for boolean gate decisions; treat `preflight.md` as human-readable only.

### Changed

- `SKILL.md`: Stage -1 run command updated to generate both `preflight.json` (JSON flag) and `preflight.md`; minimal operating algorithm step 3 updated to reference `preflight.json` gate.
- `templates/tooling-preflight.sh`: Added arg parsing for `--json` and `MODE` flags; JSON mode uses Python 3 for structured output; markdown mode is backward-compatible and unchanged.

### Fixed (Codex review — 6 bugs)

- **Bug 1 — circular dependency (High)**: `workflow_mode` was being finalized inside Stage 1.5, which also reads `workflow_mode` to decide whether to AUTO-SKIP — a circular read-before-write. Fixed: `workflow_mode` is now finalized at the **end of Stage 1** (after all sources read). Stage 1.5 only reads the mode; it never writes it. `SKILL.md` Stage 1 body, Stage 1.5 body, minimal algorithm step 8, and `refs/stage-contracts.md` Stage 1 / Stage 1.5 output + state blocks all updated.
- **Bug 2 — Stage 2.5 full bypass (High)**: Compliance matrix had `Stage 2.5 Decision Gate (fast mode) | AUTO-SKIP` with no caveat, violating the hard rule "Decision Gate evaluation always mandatory". Fixed: split into two rows — ADR trigger check is **MANDATORY** regardless of mode; ADR creation + approval is AUTO-SKIP only if no trigger fires. If a trigger fires in fast mode → mode upgrades to governed.
- **Bug 3 — Stage 3 skipped but Stage 4 needs its outputs (High)**: Fast mode sequence previously showed `-1→0→1→2→4`, skipping Stage 3 entirely, yet Stage 4 requires `implementation-plan.md`, `code_owner`, `branch`, and `handoff.md` from Stage 3. Fixed: fast mode now always runs **Stage 3-lite** (implementation-plan.md ≤ 5 tasks, code_owner, branch, minimal handoff.md). Only the design doc and Android memo are skipped. Fast mode sequence in `SKILL.md` corrected to `-1→0→1→2(mini)→2.5-lite→3-lite→4→5(lite)`.
- **Bug 4 — Stage 6 Karpathy contradiction (Medium)**: Stage 6 CONFIRM-SKIP row implied the entire Stage 6 could be skipped in fast mode, contradicting hard rule "Stage 6 Karpathy diff review: never skippable". Fixed: row renamed to "Stage 6 full QA report" and clarified that Karpathy diff review + Gate G close remain MANDATORY.
- **Bug 5 — handoff_md: skip contradicts hard rule (Medium)**: `artifact_budget.fast.handoff_md: skip` contradicted hard rule #11 (mandatory when code_owner confirmed). Fixed: changed to `handoff_md: minimal` with comment that minimal = code_owner, branch, next step only.
- **Bug 6 — version drift (Low)**: All refs/*.md and docs/FLOW.md still showed `4.10.0` while SKILL.md and CHANGELOG referenced `4.10.1`. Fixed: all files bumped to `4.10.1`.

---

## v4.10.0

### Added

- **Three workflow modes (fast / standard / governed)**: Derived automatically from `complexity_score` + `risk_score`. Fast mode uses sequence -1→0→1→2(mini)→2.5-lite→3-lite→4→5(lite) for small isolated tasks; governed mode is the existing full workflow; standard is everything in between. (Note: fast mode sequence corrected in v4.10.1.)
- **Scoring system**: `complexity_score` (1–10) and `risk_score` (1–10) computed at Stage 0 (preliminary) and finalized at **end of Stage 1** (after all sources read). Written to `context-pack.json` + `session.json`. Mode mapping: complexity ≤ 3 AND risk ≤ 3 → fast; complexity ≤ 7 AND risk ≤ 6 → standard; otherwise → governed.
- **Override rules**: ADR trigger fires → minimum governed; Jira + Figma both present → minimum standard; human explicit request → use as stated; artifact count > 5 ACs in fast mode → auto-upgrade to standard.
- **Artifact budget** (`refs/contracts-and-artifacts.md § Artifact budget`): fast: requirements ≤ 40 lines, design doc skip, implementation-plan ≤ 5 tasks, execution report minimal, handoff minimal; standard: requirements ≤ 120 lines, design ≤ 180 lines, plan ≤ 15 tasks; governed: unrestricted.
- **Fast mode stage skips** (all written to skip-log.json): Stage 1.5 (AUTO-SKIP), Stage 2.5 ADR creation only if no trigger (AUTO-SKIP), Stage 3 design doc (AUTO-SKIP), Stage 6 full QA report (CONFIRM-SKIP — Karpathy still MANDATORY).
- **`preliminary_mode`** field in `session.json` (set at Stage 0); **`workflow_mode`**, **`complexity_score`**, **`risk_score`**, **`mode_reasons`**, **`mode_override`** fields in `context-pack.json` and `session.json`.
- **Hard rule #24**: mode gates artifact depth; mode can only be upgraded, never downgraded without human confirmation.
- **Section 14 "Workflow modes"** in `docs/FLOW.md`: preliminary scoring flow, mode stage diagrams for fast / standard / governed, upgrade/downgrade rules.

### Changed

- `SKILL.md`: version → 4.10.0; added "Workflow Modes" section with scoring tables, mode mapping, fast-mode skip table, override rules; updated Stage 0 (preliminary_mode), Stage 1.5 (finalize scores), Stage 3 (fast mode lite note); updated minimal operating algorithm step 5 and step 8.
- `refs/contracts-and-artifacts.md`: context-pack.json schema adds `preliminary_mode`, `complexity_score`, `risk_score`, `workflow_mode`, `mode_reasons`, `mode_override`; session.json schema adds same; adds `## Artifact budget` section; Gate E split into mode-specific requirements.
- `refs/compliance-policy.md`: 4 new mode-based rows in compliance matrix (fast-mode AUTO-SKIP for Stage 1.5, 2.5, 3 design, Stage 6 CONFIRM-SKIP); mode downgrade added to CONFIRM-SKIP table; never-bypass item 14 added; 3 new violations for mode enforcement.
- `refs/stage-contracts.md`: Stage 0 output/state adds `preliminary_mode`; Stage 1.5 output/state adds `workflow_mode`, `complexity_score`, `risk_score`; session.json schema updated with mode fields.
- `docs/FLOW.md`: version → v4.10.0; preliminary mode scoring block added to Stage 0 diagram; Section 14 "Workflow modes" added.
- All `refs/*.md` version headers: 4.9.0 → 4.10.0.

---

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
- Install/update decision rules for Spec Kit, Android CLI, Android skills, Graphify, and Karpathy guidelines.
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
