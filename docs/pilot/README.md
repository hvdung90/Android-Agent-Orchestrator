# Pilot: current orchestration vs adaptive workflow (ADR-0001)

Goal: measure whether the PR8 changes (FAST path, model routing) reduce lead time and cost without more escaped defects. The targets are **hypotheses** (ADR-0001 decision 7), not acceptance criteria, until this pilot has run.

| Hypothesis (per mode, candidate vs baseline, medians) | Target |
|---|---|
| Lead time (`started_at` → `closed_at`) | ≥ 20 % lower |
| Cost (input + output tokens) | ≥ 15 % lower |
| Policy read by a FAST task | ≤ 15 KB |
| Escaped defects per task | not higher |

Minimum samples per cohort: **5 FAST, 5 STANDARD, 3 GOVERNED**. Below that the report says `insufficient data` — do not conclude from it.

## Fill in before starting

| Item | Value |
|---|---|
| Owner (decides rollout) | _ |
| Runner(s) | _ |
| Android app repo + baseline app commit | _ |
| Baseline skill commit | `7711e6a` (main before PR8) |
| Candidate skill commit | `v6.2.0` (main after PR8a + PR8b + PR8c) |
| Model / Claude Code version (same for both cohorts) | _ |
| Start / end date | _ |
| Escaped-defect window | 30 days after each merge |

## Choose tickets

- From the same app commit; comparable difficulty within each mode.
- FAST: isolated change, clear AC, ≤ 2 files, no escalation trigger (`SKILL.md § Escalation triggers`).
- STANDARD: feature with API + ViewModel + tests in one module.
- GOVERNED: billing, OAuth, ANR or Remote Config wiring, migration — anything with an ADR trigger.
- Prefer **paired runs**: each ticket once per cohort, from the same app commit, alternating which cohort goes first, a fresh Claude Code session each time.

## Run each ticket

1. Check out the app commit on a fresh branch; install the skill pack at the cohort's skill commit with `python3 scripts/install_skill.py --ref <skill commit>` and confirm with `--check --ref <skill commit>` (exit 0). The installed `commit` in `.aao-install.json` identifies the cohort; also set it as `skill_commit` in each telemetry line.
2. Start a new Claude Code session; same model for both cohorts.
3. Work the ticket as usual until Stage 7 closes or the task is abandoned.
4. **Candidate cohort:** the agent appends its telemetry line to `.project-orchestration/memory/retro-log.jsonl`. Set `"cohort": "candidate"` in that line.
5. **Baseline cohort:** the old skill writes no telemetry — write the line by hand (example below):
   - `policy_reads`: every Read of a skill-pack file in the transcript, in order (path relative to the pack; `section` null when the whole file was read).
   - `human_interrupts`: every time the agent stopped and waited for you, with the stage and kind.
   - `tokens`: from Claude Code's session usage, `"source": "manual"`; if not available, `null` values and `"source": "unavailable"`. Never estimate.
   - timestamps from the transcript.
6. Copy the line into `pilot/<YYYY-MM-DD>/retro-log.jsonl` (outside the app repo). Record paths and counts only — no brief text, code, names or tokens.

Example baseline line (one line in the file; wrapped here for reading):

```json
{"schema": "aao-telemetry/1", "task_id": "CA-42", "skill_version": "6.1.3", "skill_commit": "7711e6a", "cohort": "baseline", "workflow_mode": "fast", "mode_upgrades": [], "ref_tier": "LIGHT", "approval_source": null, "policy_reads": [{"path": "SKILL.md", "section": null}, {"path": "refs/stage-contracts.md", "section": null}], "human_interrupts": [{"stage_id": "2_requirements", "kind": "approval"}], "started_at": "2026-11-20T09:00:00Z", "first_patch_at": "2026-11-20T10:05:00Z", "closed_at": "2026-11-20T11:20:00Z", "tokens": {"input": 410000, "output": 21000, "cached": 300000, "source": "manual"}, "model_tiers": {"default": 10, "deep-reasoning": 0}, "evidence": {"pass": 3, "fail": 0, "not_run": 1, "blocked": 0}, "outcome": "closed", "review_iterations": null, "escaped_defects": null}
```

## Later

- After PR review: set `review_iterations` on that task's line.
- After the escaped-defect window: set `escaped_defects` (bugs traced back to the change). Lines with `null` are left out of the defect comparison.

## Report

```bash
python3 scripts/pilot_report.py --skill-root <path to a git checkout of this skill pack> pilot/*/retro-log.jsonl
```

`--skill-root` must be a git checkout so that each line's `policy_reads` is measured at its own `skill_commit`. Invalid lines are listed and excluded — fix them rather than ignoring the list. Add `--json` for machine-readable output.

## Stop and decide

- **Stop immediately** if a candidate run leaks a secret into the transcript or output, or produces a security finding the baseline did not.
- **Hold rollout** if escaped defects are higher for any mode.
- Roll out to the team only when every mode with enough samples meets its targets or the owner accepts a documented exception. Record the decision as a new ADR that supersedes or confirms ADR-0001 decision 7.
