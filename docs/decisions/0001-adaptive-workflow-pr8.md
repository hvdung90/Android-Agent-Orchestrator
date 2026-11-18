---
artifact: skill-adr
status: accepted
---

# ADR-0001 — Adaptive workflow (PR8): FAST path, escalation, model routing

Status: Accepted
Date: 2026-11-18
Owner: repository owner (decisions 1, 3, 4, 5 answered explicitly; 2, 6, 7 accepted as proposed, not objected)
Task: PR8 of the implementation-readiness plan (AOO-001, AOO-009, AOO-011)
Supersedes: none

## Context

After PR1–PR7 (merged in `main` at `7711e6a`, CI green), the remaining backlog items change workflow policy rather than fix contradictions:

- **AOO-001** — `micro`/`fast` still run every stage; `SKILL.md` "Never skipped" makes them reduce artifact depth only. A one-line UI fix still needs a requirements approval stop, a 1-task `implementation-plan.md`, handoff, status, full finalization.
- **AOO-009** — a micro task points at ≈186 KB of policy before the first edit (heuristic, byte/4 ≈ 46K tokens; not measured on a real session).
- **AOO-011** — model routing pins model IDs, routes `micro` coding to Haiku while also saying "Sonnet is optimal for code", and README claims Codex/Cursor support that has never been tested.

No baseline has been measured on real Android tickets yet.

## Decision

1. **FAST may inherit approval from Jira.** A FAST task skips the separate Stage 2 human approval when: the Jira AC source and revision are recorded in `session.json`, the AC is testable, and no escalation trigger (3) fires. Any scope change re-opens approval. Briefs without Jira (Mode B/C) get a one-line scope confirmation instead of a full requirements approval.
2. **"Never skipped" splits into two layers.**
   - *Safety invariants* (every mode): no secret in context/output; one code owner; no PASS without evidence; ADR trigger check; Gate E.5 per `compliance-policy.md § TDD exemption table`; diff review.
   - *Process gates* (FAST may drop): separate requirements file, `implementation-plan.md`, `handoff.md` (unless the owner changes), full Stage 6 QA report, Stage 7 finalization artifacts beyond the task summary.
3. **Escalation triggers** — FAST auto-escalates to STANDARD (or GOVERNED where the existing rules say so) when the change touches: billing, auth/OAuth, security/privacy, DB migration, public API, release config, manifest permissions/components, more than one module, unclear AC, **ads SDK / mediation**, **paywall / subscription UI**. Remote Config keys and analytics events are *not* triggers on their own.
4. **`micro` is folded into FAST.** One lightweight path; no separate micro sequence, scoring band or Haiku route.
5. **Claude Code only.** Remove the Codex/Cursor support claim from README; no per-host adapters. Routing uses one default model with a step-up for GOVERNED reasoning stages; no pinned model IDs in `SKILL.md`.
6. **Incremental doc restructure.** First a self-contained `workflows/fast.md` that a FAST task can follow without loading the large refs; split further only after measurement.
7. **Targets are hypotheses.** FAST policy read ≤ 15 KB, ≥ 20% lead-time and ≥ 15% cost reduction per accepted change are pilot hypotheses, not acceptance criteria, until a baseline exists.

## Alternatives

- Always ask for Stage 2 approval in FAST — rejected: keeps the main AOO-001 overhead.
- PR review as the only gate for FAST — rejected: no checkpoint before code for tasks whose scope drifts.
- Keep `micro` — rejected: it currently saves almost nothing and doubles the paths to maintain and measure.
- Support Codex/Cursor now — deferred: needs capability tiers, host adapters and per-host fixtures.
- Remote Config / analytics as triggers — not chosen; can be added later if the pilot shows escapes there.

## Consequences

- Positive: a clear FAST path with fewer human stops; one place that defines what is never skipped; model routing that does not contradict itself.
- Negative: FAST relies on Jira AC quality; escalation triggers must be detected from the diff and task text, which can miss cases — the pilot must check escaped defects.
- Migration / rollback: sessions with `workflow_mode: micro` are read as FAST on resume. Rollback = revert the PR8 commits; contracts from PR1–PR7 are unaffected.

## Validation

- Contract linter rules for: no `micro` mode left in contracts; the two-layer never-skipped list; escalation trigger list present in one place; no pinned model IDs; README without the multi-host claim.
- Pilot (owner to schedule): same baseline commit, ≥ 5 FAST, ≥ 5 STANDARD, ≥ 3 GOVERNED tickets, before/after; record cycle time, time to first valid patch, human interrupts, policy bytes read, input/cached tokens, review iterations, escaped defects.

## Related

- `docs/Android-Agent-Orchestrator-Review-Vulcanlabs-2026-11-18.md` (AOO-001, 009, 011)
- `docs/Android-Agent-Orchestrator-Implementation-Readiness-2026-11-18.md` (PR8 row)
- Files expected to change: `SKILL.md`, `refs/compliance-policy.md`, `refs/contracts-and-artifacts.md` (artifact budget, scoring), `refs/stage-contracts.md`, `refs/playbooks.md`, `README.md`, `QUICKSTART.md`, `docs/FLOW.md`, new `workflows/fast.md`, `scripts/lint-contracts.py`
