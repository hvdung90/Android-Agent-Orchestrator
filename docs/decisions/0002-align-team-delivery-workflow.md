---
artifact: skill-adr
status: accepted
---

# ADR-0002 — Align AAO with the team Mobile AI Delivery Workflow v0.4

Status: Accepted
Date: 2026-11-23
Owner: repository owner (direction "gộp pilot, sửa P0" given explicitly on 2026-11-23)
Task: 6.3.0 — P0 conflicts between AAO 6.2.0 and the Confluence page "[Mobile] AI Delivery Workflow" v0.4
Supersedes: ADR-0001 decision 3 in part (trigger list and `governed` floor) and decision 7 in part (the separate AAO pilot)

## Context

The team adopted a tool-agnostic delivery workflow (Confluence "[Mobile] AI Delivery Workflow", v0.4) for Android and iOS. It sizes work as S / M / L / N and names AAO as one Android toolkit. A Dev using AAO 6.2.0 would break that workflow on the first ticket in four places:

1. **Commits.** The workflow says the Dev commits, pushes and opens the PR. AAO defaulted `commit_policy` to `per_task`, and the plan template had the agent run `git commit` after each task.
2. **Risk level.** The workflow makes a *behaviour* change in a sensitive area (transactions, entitlement, auth, migration, startup, permissions) tier L — Tech Lead approves the plan before code — even for a few lines. AAO only raised such changes to `standard`; only an ADR trigger reached `governed`. AAO also forced `standard` for any Jira + Figma task, which blocks an S UI tweak with a Figma frame from FAST, and its trigger list lacked startup / SDK init, BaseLib, Remote Config logic, deeplinks / push.
3. **Independent review.** The workflow requires an independent review for M / L: a new agent with its own context, or a human PR reviewer. AAO's Stage 6 review was done by the session that wrote the code.
4. **Pushing.** The workflow says AI never pushes. AAO pushes lock metadata to the team-docs repo.

AAO's own pilot (ADR-0001 decision 7) had not started; the team pilot will exercise AAO anyway.

## Decision

1. **The Dev commits.** `commit_policy` defaults to `no_commit`: the agent records a suggested commit message per task and never commits the product repo. `per_task` / `single_commit` only when the Dev asks for it in that task (`commit_policy_source: "human: <quote>"`), local commits only. (`refs/contracts-and-artifacts.md § Commit policy`)
2. **Sensitive behaviour changes are `governed`.** New `SKILL.md § Governed triggers`; presentation-only changes in those areas stay `standard`. `governed` needs `plan_approval` from the Tech Lead or a delegated senior, recorded with a Jira comment or PR link, before Stage 4; an AC or scope change re-opens it. The Jira + Figma floor is removed. Four escalation triggers are added. `SKILL.md § Team tiers` maps S → `fast` when it also fits FAST, else `standard`; M → `standard`; L → `governed`; N out of scope.
3. **Independent Reviewer at Stage 6** in `standard` / `governed`: a new read-only sub-agent given only AC, plan, revisions/diff and the evidence summary (`refs/sub-agents.md § Review worker`). If none can run, `independent_review.status: pending_pr_review` and the PR is not merge-ready until a human reviews it. `fast` keeps the Karpathy diff review, as tier S does.
4. **Never push the product repo** (hard rule 15). The single, documented exception is `team_docs_sync.py commit-push` to the team-docs coordination repo — lock and task metadata only — because a lock no one else can see prevents nothing. A team that wants no agent push uses `TEAM_DOCS_MODE: knowledge` or runs the printed command itself.
5. **One pilot.** The separate AAO pilot is dropped; AAO runs inside the team pilot. `aao-telemetry/1` stays as supplementary data for the team's per-ticket metrics (T12).

`scripts/lint-contracts.py` check `delivery-workflow` keeps decisions 1–4 from drifting back.

## Alternatives

- Keep `per_task` and ask the team to allow AI commits — rejected for now: the workflow text says the Dev commits; reopen through the workflow page, not inside AAO.
- Leave sensitive changes at `standard` and add a Lead approval flag there — rejected: two meanings for one mode; `governed` already carries the stricter path.
- Stop pushing team-docs entirely — rejected: locks would be invisible to other developers, which defeats the coordination mode.
- Keep the separate AAO pilot — rejected: it would measure an AAO that the team workflow does not allow.

## Consequences

- Positive: a Dev can follow the team workflow and AAO together; L-tier work gets a Lead-approved plan; M / L get a review that is not self-review.
- Negative: more tasks reach `governed` (heavier artifacts, a Lead wait); Devs commit by hand; one more sub-agent run per standard / governed task.
- Follow-up (P1, not in this ADR): PR description / QC handoff output (T10), keeping standard artifacts out of the app repo, CI links as evidence, the 2-round fix limit, fixed `blocked_reason` values.
