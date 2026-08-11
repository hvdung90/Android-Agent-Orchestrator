# Team Docs Integration

_Skill version: 6.1.1_

## When active

Active only when project's `CLAUDE.md` defines `TEAM_DOCS_PATH`. Otherwise the skill runs solo-repo mode (existing behavior, no team docs I/O).

## Path resolution

`TEAM_DOCS_PATH` may be:
- Relative to git root (recommended): `../vulcan-android-docs`
- `~`-prefixed: `~/dev/vulcan-android-docs` (expand `~` to `$HOME`)
- Absolute: `/Users/dung/dev/vulcan-android-docs`

**Recommended convention:** docs repo and all Android repos are siblings in the same workspace folder. Using `../vulcan-android-docs` requires zero machine-specific config — works on any machine as long as the workspace layout is consistent.

`REPOS_ROOT` (used when the skill needs to resolve sibling repo paths) = `$(git rev-parse --show-toplevel)/..` — derived at runtime, never hardcoded.

Resolve at Stage -1. If the resolved path doesn't exist → HARD STOP with instruction to either clone the docs repo or unset the variable.

---

## File naming conventions

Rules that apply when creating or archiving any file in the docs repo:

| Directory | Pattern | Example |
|---|---|---|
| `active-tasks/<repo>/` | `<task-id>-<slug>.md` | `AT-42-migrate-datastore.md` |
| `ADRs/` | `<repo>-<nnnn>-<slug>.md` | `library-vulcan-0004-new-cache.md` |
| `contracts/` | `<repo>-<slug>.md` | `library-vulcan-ump-consent.md` |
| `archive/YYYY-MM/` | `<repo>-<task-id>-<slug>.md` | `library-vulcan-AT-42-migrate-datastore.md` |

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
| Need to check state of a lib feature branch | Read `active-tasks/library-vulcan/README.md` → find task by branch → read task file |
| Find all tasks on a lib branch | `grep -rl "feature/X" active-tasks/library-vulcan/` |

---

## File format spec

### `active-tasks/locks.json` (conflict index)

Small machine-readable file used for Stage -1 conflict checks. This is the first and usually only team-docs file read during preflight.

```json
{
  "version": 1,
  "locks": [
    {
      "file": "feature/auth/AuthViewModel.kt",
      "task_id": "ANDROID-42",
      "repo": "android-app",
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

### `active-tasks/README.md` (global board)

```markdown
## Overview
| Repo | Active Tasks | Last Updated |
|---|---|---|
| chatgpt-android | 2 | 2026-07-31 |

## Cross-repo Impacts
| Date | Decision | Repos Affected | Owner | ADR |
|---|---|---|---|---|
| 2026-07-31 | Migrate SharedPrefs → DataStore | chatgpt-android, widget-sdk | @dunghoang | ADR-042 |

## Cross-repo Conflicts
See `active-tasks/locks.json` for the machine-readable lock index.
```

Parse rules:
- `cross_repo_impacts[]`: all rows in "Cross-repo Impacts"
- Do NOT edit rows from other tasks. Append-only for Cross-repo Impacts. Overwrite-in-place only for the Overview count table.

### `active-tasks/<repo>/README.md` (per-repo board)

```markdown
## Active Tasks
| Task ID | Branch | Owner | Status | Files Touched |
|---|---|---|---|---|
| AT-123 | feature/datastore-migration | @dunghoang | 🟡 in-progress | app/src/.../DataStoreManager.kt |
| AT-124 | fix/widget-crash | @alice | ⏳ planning | app/src/.../WidgetProvider.kt |
```

Parse rules: each row is one active task. Read this file only when task metadata or human-facing board state is needed; do not use it as the normal Stage -1 conflict source.

---

## Reads (Stage -1, mandatory when active)

**IMPORTANT — anti-race protocol:** Stage -1 only reads. Stage 0 immediately writes pending locks.
If two devs start simultaneously and both pass Stage -1 (race window ~seconds), Stage 0 writes will create a conflict visible to the second dev when they re-read before Stage 3.

1. `git pull --rebase` on docs repo before reading any file.
2. Read `<TEAM_DOCS_PATH>/active-tasks/locks.json` if present; if missing, treat as `{ "version": 1, "locks": [] }`.
3. Match planned scope against `locks[]`:
   - If overlap AND matching lock's `locked_at` is **not stale** (see § Stale lock reclaim policy) → HARD STOP, print conflict table with owner @github-handle and `locked_at` timestamp.
   - If overlap AND matching lock's `locked_at` **is stale** → do not hard-stop; follow § Stale lock reclaim policy (CONFIRM-SKIP, human must approve reclaim).
   - If clean → log `team_docs.conflict_check: clean` in `session.json`.
4. Load `<TEAM_DOCS_PATH>/standards/` only when `team_coordination` project policy is enabled, the task has cross-repo impact, or a matching lock/task file must be inspected. Apply loaded standards as active constraints for the task.
5. Read markdown boards (`active-tasks/README.md`, `active-tasks/<repo-name>/README.md`) only for writes, conflict details after a lock match, or explicit human-facing team status work.

---

## Stale lock reclaim policy

Locks are written once at Stage 0 and never touched again until Stage 3 (upgrade) or Stage 7 (removal) — a task that crashes, gets abandoned, or whose owner simply moves on leaves an orphaned lock forever unless something reclaims it.

**Staleness threshold:** a lock (`planning` or `locked`) is stale when `now - locked_at > ttl_hours` if present, otherwise `now - locked_at > 7 days`. The 7-day default is not a hard constant; a team may tune it in project policy.

**Reclaim flow (CONFIRM-SKIP — human must approve, never auto-reclaim):**
1. When Stage -1's conflict check finds an overlapping lock whose `locked_at` is stale, do not hard-stop. Instead ask:
   > "Lock on `<file>` by @`<owner>` (Task `<task-id>`) is `<N>` days old — stale threshold is `<threshold>`. It may be abandoned, or the owner may just not have reached Stage 7 yet. Reclaim this lock and proceed? (y/n)"
2. If the human confirms reclaim:
   - Remove the stale lock object from `active-tasks/locks.json` and let the current task's Stage 0 write its own lock.
   - Append an audit line to the current task file `## Notes/Gotchas`: `Reclaimed stale lock on <file> from <old-task-id> (@<old-owner>, locked since <old-locked_at>).`
   - `git push`.
3. If the human declines → treat as a normal HARD STOP; do not proceed with the overlapping file.
4. **Never reclaim silently.** A false "abandoned" read (owner is mid-task but simply hasn't touched that file in days) is a real conflict risk — staleness is a prompt to ask, not a license to proceed.

**Tiebreak for genuine concurrent races** (both locks fresh — this is the residual window described in the anti-race protocol above, where two devs start within seconds of each other and both pass Stage -1 before either's Stage 0 write lands):
- **Earliest `locked_at` wins.** The task with the later `locked_at` timestamp must yield: replan scope to avoid the contested file(s), or pause and contact the earlier owner directly.
- **Post-push re-verification (closes the residual window):** immediately after Stage 0's `git push` succeeds, re-`git pull --rebase` and re-read `active-tasks/locks.json`. If an object for the same file now has an earlier `locked_at` than the current task's own lock → the current task lost the tiebreak; remove its own pending lock, `git push`, and follow the tiebreak rule above.

---

## Writes

### Stage 0 (task creation)

- `git pull --rebase` on docs repo before writing.
- **Bootstrap per-repo board if missing:** if `active-tasks/<repo>/README.md` does not exist → copy `active-tasks/REPO_BOARD_TEMPLATE.md`, replace `<REPO_SLUG>` placeholder with actual slug, create the file. This happens once per repo, not per task.
- If `active-tasks/TASK_TEMPLATE.md` exists → copy to `active-tasks/<repo>/<task-id>-<slug>.md`.
- If template NOT found → use embedded fallback below. Log warning: `TASK_TEMPLATE.md not found — used embedded fallback. Consider adding template to docs repo.`
- Fill: Task ID, Repo, Branch, Owner (ask user if not derivable from `git config user.name`), Started (ISO datetime), Mode.
- Append row to `active-tasks/<repo>/README.md`.
- Bump count in `active-tasks/README.md` Overview table.
- **Write pending lock objects** to `active-tasks/locks.json` for all files likely to be touched. Status = `planning`. This is mandatory — do not defer to Stage 3.
- **`git push` docs repo after all writes complete.** Do NOT wait for other concurrent tasks on the same repo to finish — each task manages only its own rows/files. Other tasks will pick up changes via `git pull --rebase` before their next write.
- **Post-push re-verify (mandatory, closes the residual race window):** `git pull --rebase`, re-read `active-tasks/locks.json`. If any object for a file this task just locked has an earlier `locked_at` than this task's own → apply § Stale lock reclaim policy's tiebreak rule (earliest `locked_at` wins; this task yields).

### Stage 2.5 (decision affecting other repos)

When a decision matches the "affects other repos" heuristic (see SKILL.md § Stage 2.5):
- `git pull --rebase` on docs repo before writing.
- Append to team task file `## Decisions`:

```
- [YYYY-MM-DD] [@owner] <decision one-liner>
  → Impact: <repo/task affected>
  → ADR: <link if created>
```

- If decision impacts other repo → append row to `active-tasks/README.md § Cross-repo Impacts`.

### Stage 3 (files locked)

- `git pull --rebase` on docs repo before writing.
- Upgrade pending lock objects from `planning` → `locked` with the final file list from `implementation-plan.md`.
- Add any new files not in the pending list; remove entries for files that won't be touched.
- Update team task file `## Scope > Files sẽ touch (LOCKED)` from `implementation-plan.md`.
- **`git push` docs repo after all writes complete.**

### Stage 7 (archive)

- `git pull --rebase` on docs repo before writing.
- Update team task file status → `✅ done`.
- Create `archive/YYYY-MM/` directory if it doesn't exist.
- Move file: `active-tasks/<repo>/<task-id>-<slug>.md` → `archive/YYYY-MM/<repo>-<task-id>-<slug>.md`.
- Remove row from `active-tasks/<repo>/README.md`.
- Decrement count in `active-tasks/README.md` Overview table.
- Remove lock objects owned by this task from `active-tasks/locks.json`.
- **`git push` docs repo after all writes complete.**

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
- Do NOT rewrite historical entries in `active-tasks/README.md`. Append-only for Cross-repo Impacts; overwrite-in-place only for the Overview count table.
- Do NOT create files in `TEAM_DOCS_PATH/orchestration/` (that path does not exist — team docs is human-readable coordination, not agent state).
- Do NOT commit docs repo changes with `--no-verify` or force-push. Treat docs repo the same as any production branch.
