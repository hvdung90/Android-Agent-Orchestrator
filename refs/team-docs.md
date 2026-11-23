# Team Docs Integration

_Skill version: 6.3.0_

## Hybrid model — what goes where

**Decision rule:** if a doc answers *"what does this task / this code in this repo do?"* → keep it in the code repo. If it answers *"what standards does the Android team follow in general?"* → put it in `TEAM_DOCS_PATH`.

| Stays in code repo | Goes to `TEAM_DOCS_PATH` |
|---|---|
| `docs/ai/tasks/{task_id}/` (requirements, design, planning, clarification, handoff) | `standards/` — coding conventions, security, git workflow |
| `docs/ai/decisions/` — repo-level and task-level ADRs | `platform-adr/` — cross-repo or org-level decisions |
| `.project-orchestration/` — session state, memory, reports | `active-tasks/` — lock index + team coordination signals |
| `docs/architecture/` (when repo-scoped) | `shared-architecture/` — multi-repo architecture docs |
| Any doc that moves with a branch or PR | `templates/` — reusable task/ADR/contract templates |

**Why:** task docs co-locate with code so reviewers see requirements and design in the same PR. Agent reads/writes to the repo it's operating in, keeping context correct. Cross-repo knowledge (standards, platform decisions, onboarding) lives centrally because it applies regardless of which repo is active.

**What is NOT centralized:** `docs/ai/tasks/{task_id}/` is never replicated to `TEAM_DOCS_PATH`. The `active-tasks/<repo>/<task-id>-<slug>.md` coordination file is a lightweight visibility artifact (who, what files are locked, key decisions) — not the full task documentation.

---

## When active

Active only when project's `CLAUDE.md` defines `TEAM_DOCS_PATH`. Otherwise the skill runs solo-repo mode (existing behavior, no team docs I/O).

---

## TEAM_DOCS_MODE

Set in the consuming repo's `CLAUDE.md` alongside `TEAM_DOCS_PATH`. Controls how much of the team docs protocol runs.

```
TEAM_DOCS_MODE: coordination   # default when omitted
```

| Mode | Use when | Protocol |
|---|---|---|
| `coordination` | Multiple devs may work in parallel on the same repo (e.g. chatsmith) | Full: locks + boards + task files + ADRs + standards + archive |
| `knowledge` | One dev at a time; need historical context but no concurrent conflict risk (e.g. single-dev repos, library-vulcan) | Lite: ADRs + standards only; no locks, no boards, no task files |

**Omitting the field** is treated as `coordination` — the safe default.

What `knowledge` mode skips vs `coordination`:

| Operation | `coordination` | `knowledge` |
|---|---|---|
| `locks.json` conflict check | ✅ | ❌ skip |
| Planning locks write (Stage 0) | ✅ | ❌ skip |
| Task file + board maintenance (Stage 0, 3, 7) | ✅ | ❌ skip |
| Archive at Stage 7 | ✅ | ❌ skip (nothing to archive) |
| `ADRs/README.md` scan (Stage -1) | ✅ | ✅ |
| ADR creation when cross-repo decision | ✅ | ✅ |
| `ADRs/README.md` index update | ✅ | ✅ |
| Cross-repo Impacts table row | ✅ | ✅ (decision still visible) |
| `contracts/` writes | ✅ | ✅ |
| `standards/` reads | ✅ | ✅ |

**Switching modes mid-project:** change the flag in `CLAUDE.md` and commit. No migration needed — `knowledge` mode never created locks or task files, so there is nothing to clean up.

## Path resolution

`TEAM_DOCS_PATH` may be:
- Relative to git root (recommended): `../vulcan-android-docs`
- `~`-prefixed: `~/dev/vulcan-android-docs` (expand `~` to `$HOME`)
- Absolute: `/Users/dung/dev/vulcan-android-docs`

**Recommended convention:** docs repo and all Android repos are siblings in the same workspace folder. Using `../vulcan-android-docs` requires zero machine-specific config — works on any machine as long as the workspace layout is consistent.

`REPOS_ROOT` (used when the skill needs to resolve sibling repo paths) = `$(git rev-parse --show-toplevel)/..` — derived at runtime, never hardcoded.

Resolve at Stage -1. If the resolved path doesn't exist → HARD STOP with instruction to either clone the docs repo or unset the variable.

---

## Zone structure

```
active-tasks/
├── shared/
│   └── README.md              ← Cross-repo Impacts — ALL repos read; lib writes here
└── <repo>/                    ← coordination zone (one per coordination-mode repo, e.g. chatsmith/)
    ├── README.md              ← per-repo board (Overview + File Locks)
    ├── locks.json             ← machine-readable lock index for this repo
    └── <task-files>
```

**Knowledge-mode repos** (single-dev apps, library-vulcan) have NO directory in `active-tasks/`. They read `shared/` and write to `ADRs/` and `shared/README.md § Cross-repo Impacts` only.

---

## File naming conventions

Rules that apply when creating or archiving any file in the docs repo:

| Directory | Pattern | Example |
|---|---|---|
| `active-tasks/<repo>/` | `<task-id>-<slug>.md` | `chatsmith/AT-42-new-feature.md` |
| `ADRs/` | `<repo>-<nnnn>-<slug>.md` | `library-vulcan-0004-new-cache.md` |
| `contracts/` | `<repo>-<slug>.md` | `library-vulcan-ump-consent.md` |
| `archive/YYYY-MM/` | `<repo>-<task-id>-<slug>.md` | `chatsmith-AT-42-new-feature.md` |

**Why:** ADRs, contracts, and archive are flat directories shared across all repos. The `<repo>` prefix prevents filename collisions and makes ownership obvious at a glance.

**When creating a new ADR or contract:** always prefix with the repo name that owns the decision, even if only one repo is currently active.

**Template 0000-template.md** in ADRs/ keeps its generic name (no repo prefix) — it is a template, not a decision.

---

## Repo-type conventions

Rules that apply **in addition to** the standard stage protocol, based on repo type.

### Library repo (e.g. library-vulcan)

| Trigger | Required |
|---|---|
| Feature branch task with app repos testing it | Add `Consumers: <repo-list>` to `## Cross-task Dependencies` in task file |
| Public API change (signature, interface, required param, removed method) | ADR mandatory + row in `§ Cross-repo Impacts` with Repos Affected = "all" |
| New API on open feature branch (not yet merged) | Create `contracts/<repo>-<slug>.md` with `Status: Draft (branch: feature/X)` |

### App repo

| Trigger | Required |
|---|---|
| Testing against a lib feature branch | Add to task file `## Cross-task Dependencies`: `library-vulcan AT-XX (feature/X) — <what you're testing>` |
| Need to check state of lib cross-repo decisions | Read `active-tasks/shared/README.md § Cross-repo Impacts` + `ADRs/README.md` (lib is knowledge mode — no task board exists) |
| Find lib ADRs related to current task | Keyword scan `ADRs/README.md` at Stage -1 (already part of standard read protocol) |

---

## File format spec

### `active-tasks/<repo>/locks.json` (conflict index — coordination zone only)

Per-repo machine-readable file. Path: `<TEAM_DOCS_PATH>/active-tasks/<repo>/locks.json` where `<repo>` is the coordination-mode repo slug (e.g. `chatsmith`). This is the first and usually only team-docs file read during preflight for coordination repos.

```json
{
  "version": 1,
  "locks": [
    {
      "file": "feature/auth/AuthViewModel.kt",
      "task_id": "ANDROID-42",
      "repo": "chatsmith",
      "owner": "@dunghoang",
      "status": "planning",
      "locked_at": "2026-08-11T09:00:00Z",
      "ttl_hours": 48
    }
  ]
}
```

Rules:
- `status`: `planning | locked`.
- `ttl_hours` is optional; if missing, use stale-lock policy default.
- Stage -1 reads only this file for conflict detection. Open markdown boards/task files only when a lock matches the planned scope, a write is needed, or the task explicitly needs team visibility.
- If `locks.json` is missing, Stage -1 treats it as empty and Stage 0 creates it on first write.
- Markdown boards remain human-readable mirrors; they are not the preflight conflict source of truth.

### `active-tasks/shared/README.md` (cross-repo signals — all repos read)

```markdown
# Shared — Cross-repo Signals

## Cross-repo Impacts
| Date | Decision | Repos Affected | Owner | ADR |
|---|---|---|---|---|
| 2026-07-31 | Migrate SharedPrefs → DataStore | chatsmith, widget-sdk | @dunghoang | ADR-042 |
```

Parse rules:
- All repos read this file at Stage -1 for cross-repo context.
- Append-only for rows — do NOT edit rows from other tasks/repos.
- Only lib and any repo making a cross-repo decision writes here.

### `active-tasks/<repo>/README.md` (per-repo board — coordination zone only)

```markdown
# <repo> — Active Tasks

## Overview
| Task ID | Branch | Owner | Status | Files Touched |
|---|---|---|---|---|
| AT-123 | feature/new-feature | @dunghoang | 🟡 in-progress | app/src/.../ViewModel.kt |
| AT-124 | fix/crash | @alice | ⏳ planning | app/src/.../Provider.kt |

## File Locks (Cross-dev Conflicts)
| File Path | Status | Task ID | Owner | Since |
|---|---|---|---|---|
| app/src/.../ViewModel.kt | 🔒 locked | AT-123 | @dunghoang | 2026-08-11T09:00Z |
```

Parse rules: human-readable mirror of locks.json. Read only when human-facing board state is needed; locks.json is the preflight conflict source of truth.

---

## Reads (Stage -1, mandatory when active)

**IMPORTANT — anti-race protocol (coordination mode only):** Stage -1 only reads. Stage 0 immediately writes pending locks. If two devs start simultaneously and both pass Stage -1 (race window ~seconds), Stage 0 writes will create a conflict visible to the second dev when they re-read before Stage 3.

Steps marked `[C]` run in `coordination` mode only. Steps marked `[both]` run in both modes.

1. `[both]` **Sync without touching the docs checkout** — one command for every file this stage reads:
   ```bash
   python3 templates/team_docs_sync.py read <TEAM_DOCS_PATH> active-tasks/shared/README.md active-tasks/<repo>/locks.json ADRs/README.md
   ```
   It runs `git fetch`, resolves the checked-out branch's upstream (never assumes `origin/main`) and reads each path with `git show <upstream>:<path>`; worktree, index and HEAD stay exactly as they were, so a dirty or diverged checkout is fine. A path missing on the ref comes back `present: false` (treat as a missing file).
   - `sync: fresh` → `lock_freshness: fresh`; use the returned contents.
   - `sync: no_upstream` or `sync: fetch_failed` → contents come from the local checkout and `lock_freshness: unknown`: nothing proves they match the team's current state. `[both]` reads continue with a warning. For the `[C]` lock check the result is `team_docs.conflict_check: unknown`, and Stage 0 must not write planning locks until the human confirms proceeding without fresh lock data.
   - `local_ahead > 0` → unpushed local commits may hold this developer's own locks; mention them in the conflict table.
   - Record `team_docs.sync` and `team_docs.local_ahead` in `reports/preflight.md § Stage -1 state`.
   - Never run `pull`, `rebase`, `merge`, `checkout`, `reset` or `stash` in this phase; those belong to § Writes.
2. `[both]` Read `<TEAM_DOCS_PATH>/active-tasks/shared/README.md` — scan Cross-repo Impacts for decisions affecting the current repo.
3. `[C]` Read `<TEAM_DOCS_PATH>/active-tasks/<repo>/locks.json` if present; if missing, treat as `{ "version": 1, "locks": [] }`.
   - **Legacy global index (pre-6.1.3):** if `<TEAM_DOCS_PATH>/active-tasks/locks.json` also exists, do **not** merge it in or use it as a silent fallback. Record `team_docs.legacy_lock_index: present` in `reports/preflight.md § Stage -1 state` (Stage 0 copies it into the task session), list any entries whose `repo` matches the current repo, and ask the human to move them into `active-tasks/<repo>/locks.json` (then delete the legacy file once no repo still references it). Until migrated, treat matching legacy entries as conflicts, not as clean.
4. `[C]` Match planned scope against `locks[]`:
   - If overlap AND matching lock's `locked_at` is **not stale** (see § Stale lock reclaim policy) → HARD STOP, print conflict table with owner @github-handle and `locked_at` timestamp.
   - If overlap AND matching lock's `locked_at` **is stale** → do not hard-stop; follow § Stale lock reclaim policy (CONFIRM-SKIP, human must approve reclaim).
   - Record the result (`team_docs.conflict_check: clean | conflict | stale-reclaim-pending`) in `reports/preflight.md § Stage -1 state`; Stage 0 copies it into the task session. Stage -1 never writes a task `session.json`.
5. `[both]` Read `<TEAM_DOCS_PATH>/ADRs/README.md` when `workflow_mode ≥ standard`. Scan the index for ADRs whose repo prefix matches the current repo OR whose title keywords overlap with the task brief. Load the full ADR file only for matches. Record loaded ADRs in `context-pack.json → relevant_adrs[]`. Skip for `fast` mode. This is the primary mechanism for surfacing historical decisions and rationale before planning — do not wait for an ADR conflict to discover that a past decision exists.
6. `[both]` Load `<TEAM_DOCS_PATH>/standards/` when the task has cross-repo impact, `team_coordination` is enabled in project policy, or a matching lock/task file must be inspected. Apply loaded standards as active constraints for the task.
7. `[C]` Read per-repo board (`active-tasks/<repo>/README.md`) only for writes, conflict details after a lock match, or explicit human-facing team status work.

---

## Stale lock reclaim policy

Locks are written once at Stage 0 and never touched again until Stage 3 (upgrade) or Stage 7 (removal) — a task that crashes, gets abandoned, or whose owner simply moves on leaves an orphaned lock forever unless something reclaims it.

**Staleness threshold:** a lock (`planning` or `locked`) is stale when `now - locked_at > ttl_hours` if present, otherwise `now - locked_at > 7 days`. The 7-day default is not a hard constant; a team may tune it in project policy.

**Reclaim flow (CONFIRM-SKIP — human must approve, never auto-reclaim):**
1. When Stage -1's conflict check finds an overlapping lock whose `locked_at` is stale, do not hard-stop. Instead ask:
   > "Lock on `<file>` by @`<owner>` (Task `<task-id>`) is `<N>` days old — stale threshold is `<threshold>`. It may be abandoned, or the owner may just not have reached Stage 7 yet. Reclaim this lock and proceed? (y/n)"
2. If the human confirms reclaim:
   - Remove the stale lock object from `active-tasks/<repo>/locks.json` and let the current task's Stage 0 write its own lock.
   - Append an audit line to the current task file `## Notes/Gotchas`: `Reclaimed stale lock on <file> from <old-task-id> (@<old-owner>, locked since <old-locked_at>).`
   - `python3 templates/team_docs_sync.py commit-push <TEAM_DOCS_PATH> -m "team-docs: reclaim stale lock <file>" -- active-tasks/<repo>/locks.json <task file>` (after `begin`).
3. If the human declines → treat as a normal HARD STOP; do not proceed with the overlapping file.
4. **Never reclaim silently.** A false "abandoned" read (owner is mid-task but simply hasn't touched that file in days) is a real conflict risk — staleness is a prompt to ask, not a license to proceed.

**Tiebreak for genuine concurrent races** (both locks fresh — this is the residual window described in the anti-race protocol above, where two devs start within seconds of each other and both pass Stage -1 before either's Stage 0 write lands):
- **Earliest `locked_at` wins.** The task with the later `locked_at` timestamp must yield: replan scope to avoid the contested file(s), or pause and contact the earlier owner directly.
- **Post-push re-verification (closes the residual window):** immediately after Stage 0's `commit-push` succeeds, re-read `active-tasks/<repo>/locks.json` with `python3 templates/team_docs_sync.py read`. If an object for the same file now has an earlier `locked_at` than the current task's own lock → the current task lost the tiebreak; remove its own pending lock (`begin` → edit → `commit-push`), and follow the tiebreak rule above.

---

## Writes

Steps marked `[C]` run in `coordination` mode only. Steps marked `[both]` run in both modes.

**Push scope.** `commit-push` is the only push the agent ever makes, and only to the team-docs repo at `TEAM_DOCS_PATH`: lock entries, task files, boards and ADR index rows — coordination metadata, never product code. It is an explicit exception to the product-repo rule (`SKILL.md` hard rule 15): a lock that stays local cannot warn another developer, so the push is what makes the lock work. It never pushes the product repository. A team that wants the Dev to push team-docs too sets `TEAM_DOCS_MODE: knowledge` (no lock writes) or runs the printed `commit-push` command itself.

**Write lifecycle (every write step below):** `begin` → write this step's files → `commit-push` with exactly those paths.

```bash
python3 templates/team_docs_sync.py begin <TEAM_DOCS_PATH>
# … write this step's files …
python3 templates/team_docs_sync.py commit-push <TEAM_DOCS_PATH> -m "team-docs: <task-id> <stage> <what>" -- <every path this step wrote>
```

- `begin` requires a clean checkout before the task writes anything — changes already there are not this task's to commit (exit 3: ask the human; never stash, commit or discard them) — then `git pull --rebase`.
- `commit-push` stages **only** the listed paths (`git add -- <paths>`, never `git add .` / `-A`), and stops (exit 3) if any other path changed meanwhile; then commit, check the checkout is clean, push. A rejected push gets one `pull --rebase` + retry; a second rejection is exit 5.
- Rebase conflict (exit 4) → the helper has already run `git rebase --abort`; report the conflicting paths and ask the human. Never resolve `locks.json` conflicts automatically.
- List deleted and moved paths too (Stage 7 archive moves a file: list both the old and the new path).

### Stage 0 (task creation)

`[C]` All steps in this section are coordination-mode only. In `knowledge` mode, Stage 0 makes no writes to the docs repo.

- `python3 templates/team_docs_sync.py begin <TEAM_DOCS_PATH>`.
- **Bootstrap per-repo board if missing:** if `active-tasks/<repo>/README.md` does not exist → copy `active-tasks/REPO_BOARD_TEMPLATE.md`, replace `<REPO_SLUG>` placeholder with actual slug, create the file. This happens once per repo, not per task.
- If `active-tasks/TASK_TEMPLATE.md` exists → copy to `active-tasks/<repo>/<task-id>-<slug>.md`.
- If template NOT found → use embedded fallback below. Log warning: `TASK_TEMPLATE.md not found — used embedded fallback. Consider adding template to docs repo.`
- Fill: Task ID, Repo, Branch, Owner (ask user if not derivable from `git config user.name`), Started (ISO datetime), Mode.
- Append row to `active-tasks/<repo>/README.md § Overview`.
- **Write pending lock objects** to `active-tasks/<repo>/locks.json` for all files likely to be touched. Status = `planning`. This is mandatory — do not defer to Stage 3.
- **`commit-push` with the paths this step wrote** (task file, `active-tasks/<repo>/README.md`, `active-tasks/<repo>/locks.json`, and the board template copy if it was bootstrapped). Do NOT wait for other concurrent tasks on the same repo to finish — each task manages only its own rows/files.
- **Post-push re-verify (mandatory, closes the residual race window):** `python3 templates/team_docs_sync.py read <TEAM_DOCS_PATH> active-tasks/<repo>/locks.json`. If any object for a file this task just locked has an earlier `locked_at` than this task's own → apply § Stale lock reclaim policy's tiebreak rule (earliest `locked_at` wins; this task yields).

### Stage 2.5 (decision affecting other repos)

When a decision matches the "affects other repos" heuristic (see SKILL.md § Stage 2.5):

`[both]` — knowledge mode still deposits decisions as cross-repo knowledge:
- `python3 templates/team_docs_sync.py begin <TEAM_DOCS_PATH>`.
- Create ADR in `<TEAM_DOCS_PATH>/ADRs/<repo>-<nnnn>-<slug>.md` (see `docs/ai/decisions/` schema for format).
- Update `<TEAM_DOCS_PATH>/ADRs/README.md` index with the new row.
- Append row to `active-tasks/shared/README.md § Cross-repo Impacts`.
- **`commit-push`** with the ADR file, `ADRs/README.md` and `active-tasks/shared/README.md`.

`[C]` — coordination mode additionally writes to the task file:
- Append to team task file `## Decisions`:
```
- [YYYY-MM-DD] [@owner] <decision one-liner>
  → Impact: <repo/task affected>
  → ADR: <link if created>
```

### Stage 3 (files locked)

`[C]` All steps in this section are coordination-mode only. In `knowledge` mode, Stage 3 makes no writes to the docs repo.

- `python3 templates/team_docs_sync.py begin <TEAM_DOCS_PATH>`.
- Upgrade pending lock objects from `planning` → `locked` in `active-tasks/<repo>/locks.json` with the final file list from `implementation-plan.md`.
- Add any new files not in the pending list; remove entries for files that won't be touched.
- Update team task file `## Scope > Files sẽ touch (LOCKED)` from `implementation-plan.md`.
- **`commit-push`** with `active-tasks/<repo>/locks.json` and the task file.

### Stage 7 (archive)

`[C]` All steps in this section are coordination-mode only. In `knowledge` mode, Stage 7 makes no writes to the docs repo (nothing was created to clean up).

- `python3 templates/team_docs_sync.py begin <TEAM_DOCS_PATH>`.
- Update team task file status → `✅ done`.
- Create `archive/YYYY-MM/` directory if it doesn't exist.
- Move file: `active-tasks/<repo>/<task-id>-<slug>.md` → `archive/YYYY-MM/<repo>-<task-id>-<slug>.md`.
- Remove row from `active-tasks/<repo>/README.md § Overview`.
- Remove lock objects owned by this task from `active-tasks/<repo>/locks.json`.
- **`commit-push`** with the old and new task-file paths, `active-tasks/<repo>/README.md` and `active-tasks/<repo>/locks.json`.

---

## Fallback template

Used when `TASK_TEMPLATE.md` is not found in the docs repo.

```markdown
# <TASK_ID> — <slug>

**Owner:** @<github-handle>
**Repo:** <repo-name>
**Branch:** <branch>
**Status:** ⬜ not-started
**Mode:** standard
**Started:** <ISO-datetime>
**Last updated:** <ISO-datetime>

## Goal
<one-liner>

## Scope
### Files sẽ touch (LOCKED)
- (pending — upgraded to 🔒 at Stage 3)

### Files KHÔNG touch
-

### Out of scope
-

## Approach
-

## Decisions
<!-- append-only -->

## Cross-task Dependencies
-

## Progress
-

## Notes/Gotchas
-

## Audit Trail
| Stage | Timestamp | Notes |
|---|---|---|
```

---

## What NOT to do

- Do NOT write `session.json`, `context-pack.json`, or other operational artifacts into `TEAM_DOCS_PATH`. Those stay in `.project-orchestration/`.
- Do NOT rewrite historical entries in `active-tasks/shared/README.md`. Append-only for Cross-repo Impacts; overwrite-in-place only for the Overview count table.
- Do NOT create files in `TEAM_DOCS_PATH/orchestration/` (that path does not exist — team docs is human-readable coordination, not agent state).
- Do NOT commit docs repo changes with `--no-verify` or force-push. Treat docs repo the same as any production branch.
