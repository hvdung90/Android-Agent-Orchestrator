# Team Docs Integration

_Skill version: 5.0.0_

## When active

Active only when project's `CLAUDE.md` defines `TEAM_DOCS_PATH`. Otherwise the skill runs solo-repo mode (existing behavior, no team docs I/O).

## Path resolution

`TEAM_DOCS_PATH` may be:
- Absolute: `/Users/dung/dev/vulcan-android-docs`
- `~`-prefixed: `~/dev/vulcan-android-docs` (expand `~` to `$HOME`)
- Relative to git root: `../vulcan-android-docs`

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

## File format spec

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

## Cross-repo Conflicts (File Locks)
| File Path | Status | Task ID | Owner | Since |
|---|---|---|---|---|
| commonLibrary/src/.../Foo.kt | ⏳ planning | AT-123 | @dunghoang | 2026-07-31T10:00Z |
| commonLibrary/src/.../Bar.kt | 🔒 locked | AT-124 | @alice | 2026-07-31T09:00Z |
```

Parse rules:
- `locked_files[]`: all rows in "Cross-repo Conflicts" with Status = `⏳ planning` **or** `🔒 locked`
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

Parse rules: each row is one active task. "Files Touched" column is used to match against planned scope.

---

## Reads (Stage -1, mandatory when active)

**IMPORTANT — anti-race protocol:** Stage -1 only reads. Stage 0 immediately writes pending locks.
If two devs start simultaneously and both pass Stage -1 (race window ~seconds), Stage 0 writes will create a conflict visible to the second dev when they re-read before Stage 3.

1. `git pull --rebase` on docs repo before reading any file.
2. Read `<TEAM_DOCS_PATH>/active-tasks/README.md` → parse `locked_files[]` and `cross_repo_impacts[]`.
3. Read `<TEAM_DOCS_PATH>/active-tasks/<repo-name>/README.md` → parse task table and per-repo locked paths.
4. Match planned scope against `locked_files[]`:
   - If overlap → HARD STOP, print conflict table with owner @github-handle and `Since` timestamp.
   - If clean → log `team_docs.conflict_check: clean` in `session.json`.

---

## Writes

### Stage 0 (task creation)

- `git pull --rebase` on docs repo before writing.
- If `active-tasks/TASK_TEMPLATE.md` exists → copy to `active-tasks/<repo>/<task-id>-<slug>.md`.
- If template NOT found → use embedded fallback below. Log warning: `TASK_TEMPLATE.md not found — used embedded fallback. Consider adding template to docs repo.`
- Fill: Task ID, Repo, Branch, Owner (ask user if not derivable from `git config user.name`), Started (ISO datetime), Mode.
- Append row to `active-tasks/<repo>/README.md`.
- Bump count in `active-tasks/README.md` Overview table.
- **Write pending lock entries** to `active-tasks/README.md § Cross-repo Conflicts` for all files likely to be touched. Status = `⏳ planning`. This is mandatory — do not defer to Stage 3. Only shared paths go in the global board (commonLibrary/*, shared Gradle modules).
- **`git push` docs repo after all writes complete.** Do NOT wait for other concurrent tasks on the same repo to finish — each task manages only its own rows/files. Other tasks will pick up changes via `git pull --rebase` before their next write.

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
- Upgrade pending lock entries from `⏳ planning` → `🔒 locked` with the final file list from `implementation-plan.md`.
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
- Remove lock entries owned by this task from Cross-repo Conflicts.
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
