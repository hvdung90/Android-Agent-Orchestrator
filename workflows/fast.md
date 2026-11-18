# FAST workflow

_For `workflow_mode = fast` with `graph_impact = low` (ref tier LIGHT). Follow this file instead of loading the full refs; open a ref only where a step below points to it. Decision record: `docs/decisions/0001-adaptive-workflow-pr8.md`._

FAST is for an isolated change with clear acceptance criteria: a UI or resource tweak, a single-file bug fix, an isolated logic fix — at most 2 files in one module. Everything that keeps the work safe still applies; only process paperwork is dropped.

## Safety invariants — never dropped

- No secret in context or output: never open `.agent-auth.yaml`; use `python3 templates/agent_auth.py status` / `exec` (`refs/auth-bootstrap.md`).
- One code owner writes files; helpers only read.
- No PASS without evidence: every Evidence Gate Matrix item for the `change_type` is collected or recorded as unavailable.
- ADR trigger check runs (step 4).
- RED before product code, then GREEN — unless the diff fits a row of `refs/compliance-policy.md § TDD exemption table`.
- Karpathy diff review before close.
- `session.json` state written at every stage (`stage_id` + `stage_reached`), and the team-docs lock check when `TEAM_DOCS_PATH` is set.
- Telemetry counters in `session.json.telemetry`: every skill-pack file or section you open (`policy_reads`, this file included), every stop for a human, the first product-code edit. Paths and counts only.

## Escalation triggers

Leave FAST — re-score as `standard` (an ADR trigger means `governed`) — as soon as the task or the diff touches any of these. Record the trigger in `session.json.mode_reasons` and `skip-log.json`, then continue with `SKILL.md` and the full refs.

- Billing / in-app purchase
- Auth / OAuth / account
- Security / privacy / user data
- Database schema or migration
- Public API / shared module contract
- Release config (signing, build variants, ProGuard/R8, versioning)
- Manifest permissions, exported components, intent filters
- More than one module
- Unclear or untestable acceptance criteria
- Ads SDK / mediation
- Paywall / subscription UI

Also leave FAST when the change needs more than 2 files or more than 5 acceptance criteria, or reaches shared state or another feature. Remote Config keys and analytics events alone do not escalate.

## Steps

### -1 · Preflight

```bash
bash templates/tooling-preflight.sh --cache-check   # cache_reusable: true → skip the full run
bash templates/tooling-preflight.sh --json          # otherwise
```

Write `.project-orchestration/reports/preflight.md`: `tooling_ready` from the script and the final `ready_for_stage_0` (= `tooling_ready` AND no task-level blocker). If `TEAM_DOCS_PATH` is set, read shared impacts and locks with `python3 templates/team_docs_sync.py read <TEAM_DOCS_PATH> <paths>` — never pull or rebase here; `lock_freshness: unknown` means no lock writes until the human agrees.

### 0 · Intake

Create `.project-orchestration/tasks/{task_id}/session.json` with `stage_id: "0_intake"`, `source_mode`, `task_brief` (the user's message as given), `brief_usable`, `preliminary_mode: "fast"`, `preliminary_ref_tier: "LIGHT"`, and the `preflight` block copied from `preflight.md`. If the brief has no goal or no testable acceptance criterion, stop and ask only for the missing parts.

### 1 · Discovery (inline)

Targeted look only: grep the symbols, the module and its existing tests; open the architecture map only if the impact is uncertain. Record in `session.json`: findings, `context` (affected files, `change_type`, `graph_impact`), `workflow_mode: "fast"`, `ref_tier: "LIGHT"`, `mode_reasons`. Check the escalation triggers now and again whenever the diff grows.

### 2 · Approval (inline requirements)

Write a ≤ 40-line summary in `session.json`: goal, acceptance criteria, out of scope. Then record `approval_source`:

- `jira:<KEY>@<updated-timestamp>` — when the Jira issue's AC are recorded with that revision, every AC is testable and no trigger fires. Do not stop.
- `scope_confirmation` — Mode B / C: ask the human to confirm the scope in one line.
- `human` — anything else.

Set `requirements_approved: true` only with a non-null `approval_source`. A scope change re-opens approval.

### 2.5 · ADR trigger check

Ask: does the change touch a module boundary, navigation graph, public API or internal contract, persistence schema, DI graph, Gradle/AGP/Kotlin version, Compose/View migration, state ownership, background work, permissions, billing, auth, notifications, or broad test strategy? Any yes → `governed`; load `refs/stage-contracts.md § Stage 2.5`. Otherwise record `adr_required: false` with the reason.

### 3 · Owner and branch

Set `code_owner`, `assignee`, `branch`, `commit_policy` in `session.json`. No plan, design or handoff file: the whole change is one TDD task whose id is the `task_id`. If `TEAM_DOCS_PATH` is in coordination mode, write planning locks with `team_docs_sync.py begin` → edit `locks.json` → `commit-push -- <paths>`.

### 4 · Implement with TDD

1. Write the smallest failing test; save the run to `.project-orchestration/tasks/{task_id}/evidence/red-<task_id>.txt`. It must fail for the right reason.
2. Write the minimum code to pass; save `green-<task_id>.txt`; run the module's tests.
3. The diff fits a `build-only` or `resource-presentation` row exactly → AUTO-SKIP RED/GREEN, log it, collect that row's replacement evidence. Any other row (`ui-pixel-tweak`, `manifest-config`, …) → ask the human first. Rows and scope rules: `refs/compliance-policy.md § TDD exemption table`.
4. No unrelated refactors or dependencies.

If interrupted, write `handoff.md` and the interrupt state before stopping.

### 5 · Verify

Collect the Evidence Gate Matrix items for the `change_type` (`refs/contracts-and-artifacts.md § Evidence Gate Matrix`), plus Kotlin static analysis when Kotlin product code changed. Report each item as PASS, FAIL, NOT_RUN or BLOCKED with the evidence path; a tool that is not installed is recorded as unavailable, never as PASS.

### 6 · Diff review

Karpathy review of the diff: simplest change that meets the AC, nothing outside scope, no speculative code, tests assert behavior. Check every AC against the evidence. No separate QA report in FAST.

### 7 · Close

Write `docs/ai/tasks/{task_id}/task-summary.md`: what changed, AC → evidence, one line each for changelog, impact closure and Kotlin rule closure, follow-ups. Run the Artifact Integrity Check (`refs/contracts-and-artifacts.md § Artifact Integrity Check`). Release team-docs locks with `begin` → edit → `commit-push`. Append one telemetry line to `.project-orchestration/memory/retro-log.jsonl` (`refs/contracts-and-artifacts.md § retro-log.jsonl`; best-effort, never blocks). Set `stage_id: "7_docs_decision_finalization"`, `stage_status: complete`.

## What FAST does not produce

`requirements/<task>.md`, `discovery/<task>.md`, `context-pack.json`, `clarification-brief.md`, `design-doc.md`, `implementation-plan.md`, the full Stage 6 QA report, and `handoff.md` unless the owner changes or Stage 4 is interrupted.
