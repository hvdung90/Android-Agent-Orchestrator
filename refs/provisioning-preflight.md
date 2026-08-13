# Provisioning Preflight

_Skill version: 6.1.3 — update this when SKILL.md bumps a minor or major version._

## Purpose

Stage -1 Tooling Preflight ensures the agent knows whether required orchestration tools exist, are usable, and are allowed to be installed or updated before any task workflow begins.

It prevents agents from assuming tool availability, inventing commands, reading a stale graph, or mutating global tooling during a read-only analysis task.

---

## Cache check (run before anything else)

Read `.project-orchestration/memory/tooling-cache.json`:

| Condition | Action |
|---|---|
| File missing | Run full preflight via `bash templates/tooling-preflight.sh` |
| `valid_until` expired | Run full preflight; overwrite cache |
| `graph_commit` ≠ `git rev-parse HEAD` | Run full preflight; overwrite cache |
| `valid_until` in future AND `graph_commit` matches | **Skip tool checks**; load cached values; write brief preflight.md noting "cache hit"; go to Stage 0 |

Cache TTL default: **24 hours**. Invalidated immediately after any install/update action.

---

## Default mode

```text
audit
```

In `audit`, the agent may check command availability and file existence, but must not install, update, reinstall, delete, or rebuild anything.

---

## Modes

| Mode | Global mutation | Project mutation | Purpose |
|---|---:|---:|---|
| `audit` | No | No, except optional report | Readiness check |
| `bootstrap` | Missing approved tools only | Yes | First setup |
| `update` | Yes, approved installed tools | Yes | Bring tools/config current |
| `refresh-graph` | No, except architecture-map tool if explicitly allowed | Yes | Build/update graph |
| `force-reinstall` | Yes | Yes | Explicit clean reinstall/reset |

---

## Mode selection

| User intent | Mode |
|---|---|
| Analyze repo | `audit` |
| Review setup | `audit` |
| Check readiness | `audit` |
| Set up repo | `bootstrap` |
| Bootstrap agents | `bootstrap` |
| Update tooling | `update` |
| Make tools latest | `update` |
| Refresh/rebuild graph | `refresh-graph` |
| Clean reinstall/reset | `force-reinstall` |

If intent is ambiguous, choose `audit`.

---

## Android CLI

Check:

```bash
command -v adb || true
adb version || true
command -v android || true   # aspirational CLI — expected to be missing in most environments
android --help || true
```

> **Note:** The `android` CLI (including `android studio *`, `android skills *`, `android run`, `android screen capture`) is aspirational tooling that does not ship with the standard Android SDK. In practice it will always be missing — this is expected and non-blocking. The fallback matrix in `refs/android-cli-compatibility.md` covers all evidence gates with real tools (`adb`, `./gradlew`, `rg`, Gradle tasks). Do **not** attempt to install the `android` CLI.

Decision:

| State | Mode | Action |
|---|---|---|
| `adb` missing | `audit` | Warn; runtime evidence (Gate F) cannot be collected |
| `adb` missing | `bootstrap/update` | Install via Android SDK Platform-Tools (https://developer.android.com/tools/releases/platform-tools) |
| `adb` present | Any | Record `adb: present` in tooling-cache.json |
| `android` CLI present | Any | Record capability; use optional subcommands only when discovery confirms they exist |
| `android` CLI missing | Any | **Non-blocking** — expected; all evidence gates use fallbacks per `refs/android-cli-compatibility.md` |
| Runtime evidence needed but `adb` missing | Any | Block Gate F; apply degraded-evidence rule per `refs/contracts-and-artifacts.md` |

Stage -1 also discovers optional Android/Android Studio subcommands and caches support in `tooling-cache.json`; see `refs/android-cli-compatibility.md`. Later stages must read the cached command support before calling `android studio version-lookup`, `render-compose-preview`, `analyze-file`, `find-usages`, `find-declaration`, `android screen capture --annotate`, `android layout`, or `android run`.

---

## Android skills

Android skills are delivered via the Claude Code skill system (not the `android` CLI, which is aspirational).

Check which companion skills are available in the agent's own skill list:

| Skill | Purpose |
|---|---|
| `kotlin-patterns` | Kotlin idioms, coroutines, flows |
| `android-clean-architecture` | Architecture layer rules |
| `compose-multiplatform-patterns` | Compose UI patterns |
| `kotlin-coroutines-flows` | Coroutine/flow patterns |
| `kotlin-testing` | Test patterns |

Decision:

| State | Mode | Action |
|---|---|---|
| Companion skills available | Any | List which are available; Android Advisor selects relevant ones at Stage 3 |
| Companion skills missing | Any | Note capability gap; Android Advisor writes memo from domain knowledge |
| `android` CLI skill management present | Any | Use it when confirmed available; do not assume |

---

## Understand-Anything

**Checked first for the architecture-map lane.** If found ready, this is the active tool and Graphify is not also checked.

Check:

```bash
test -d .claude/plugins && find .claude/plugins -maxdepth 3 -iname "*understand-anything*" || true
test -f .understand-anything/knowledge-graph.json && echo "knowledge-graph exists" || echo "knowledge-graph missing"
```

Decision:

| State | Mode | Action |
|---|---|---|
| Plugin/skill missing | `audit` | Report missing; fall through to check Graphify |
| Plugin/skill missing | `bootstrap/refresh-graph` | Install if approved: `/plugin marketplace add Egonex-AI/Understand-Anything` (Claude Code) or `curl -fsSL https://raw.githubusercontent.com/Egonex-AI/Understand-Anything/main/install.sh \| bash` |
| Knowledge graph missing | `audit` | Report missing; fall through to check Graphify |
| Knowledge graph missing | `bootstrap/refresh-graph` | Run `/understand` |
| Knowledge graph exists | Stage 1 Discovery | Read `.understand-anything/knowledge-graph.json`; this becomes the active architecture-map tool |
| Code changed and knowledge graph exists | Stage 5 Verify | Run `/understand`; use `/understand-diff` for impact analysis |
| User asks graph refresh | `refresh-graph` | Build if missing; update if present |

---

## Graphify (fallback — only checked when Understand-Anything is unavailable)

Check:

```bash
command -v graphify || true
python -m pip show graphify || true
test -f graphify-out/GRAPH_REPORT.md && echo "GRAPH_REPORT exists" || echo "GRAPH_REPORT missing"
test -f graphify-out/graph.json && echo "graph.json exists" || echo "graph.json missing"
```

Decision:

| State | Mode | Action |
|---|---|---|
| Graphify missing | `audit` | Report missing |
| Graphify missing | `bootstrap/refresh-graph` | Install if approved |
| Graph missing | `audit` | Report missing |
| Graph missing | `bootstrap/refresh-graph` | Run `/graphify .` |
| Graph exists | Stage 1 Discovery | Read `GRAPH_REPORT.md` |
| Code changed and graph exists | Stage 5 Verify | Run `/graphify . --update` |
| User asks graph refresh | `refresh-graph` | Build if missing; update if present |

---

## Karpathy

Check:

```bash
test -f CLAUDE.md && grep -i "karpathy" CLAUDE.md || true
test -d .claude/plugins && find .claude/plugins -maxdepth 3 -iname "*karpathy*" || true
test -d .agents/skills && find .agents/skills -maxdepth 4 -iname "*karpathy*" || true
```

Decision:

| State | Mode | Action |
|---|---|---|
| Missing | `audit` | Report missing |
| Missing | `bootstrap/update` | Install plugin or add project guidance if approved |
| `CLAUDE.md` exists | Any | Do not overwrite silently |
| Code-touching task | Any | Apply Karpathy principles manually even if install missing |

**Kotlin/Android convention check — not Stage -1 detectable:** whether the `kotlin-reviewer` agent or the companion skills (`kotlin-patterns`, `android-clean-architecture`, `compose-multiplatform-patterns`, `kotlin-coroutines-flows`, `kotlin-testing`) are available is checked by the agent's own tool/skill list at Stage 3/Stage 4 activation time — same reasoning as the Figma MCP and Karpathy-plugin checks. No new field is added to `preflight.json`/`preflight.md` for this; a bash script cannot introspect what the agent itself has loaded.

---

## Preflight report

Write to:

```text
.project-orchestration/reports/preflight.md
```

Required sections:

```markdown
# Tooling Preflight

## Mode
audit | bootstrap | update | refresh-graph | force-reinstall

## Summary
- Ready for Stage 0:
- Blocking gaps:
- Non-blocking gaps:

## Android CLI
## Android skills
## Understand-Anything
## Graphify
## Karpathy
## Decisions
```

---

## Blocking rules

Block Stage 0 when:
- no task/source exists and user expects requirements or implementation,
- required setup action is needed but active mode is `audit`,
- Android CLI is required for immediate runtime evidence and is missing,
- user asked to verify device/runtime but no evidence can be produced.

Do not block Stage 0 when:
- optional architecture-map tool (Understand-Anything or Graphify) is missing but docs/capture-knowledge can be used,
- Karpathy plugin is missing but principles can be applied manually,
- Android skills are missing but Android domain memo can still be written with caveat.

---

## Auth credentials check

→ **Load `refs/auth-bootstrap.md`** for full bootstrap procedure and just-in-time token check rules.

At Stage -1, run Step 1 (auth init):

```bash
test -f .agent-auth.yaml && echo "present" || echo "missing"
```

- Present → load, note which tokens have values vs empty.
- Missing → auto-create from template (all tokens empty); notify user.

Token checks for each tool happen **just-in-time** when that tool is called. Do not check everything up front at Stage -1.

Record in preflight report:

```markdown
## Auth
- .agent-auth.yaml: present | created-empty | missing
- atlassian.api_token: set | empty
- figma.personal_access_token: set | empty
- github.personal_access_token: set | empty
- project overrides: <count> defined
```

---

## Memory write — after preflight completes

After Stage -1 finishes (cache miss path only), write:

**`.project-orchestration/memory/tooling-cache.json`**
- `checked_at`: now (ISO 8601)
- `valid_until`: now + 24h
- `graph_commit`: output of `git rev-parse HEAD`
- tool versions/states from preflight results
- Android command discovery (`android_commands`, `android_studio_commands`, `adb`) from `refs/android-cli-compatibility.md`

**`.project-orchestration/memory/session.json`** — only if no existing session or user chose not to resume:
- `task_id`: from Intake (Stage 0) — write after source mode is determined
- `stage_reached`: -1
- `stage_status`: complete
- `requirements_approved`: false

---

## Safety rules

- Never run global install/update in `audit`.
- Never overwrite `CLAUDE.md` without explicit permission.
- Never delete `graphify-out/` or `.understand-anything/` unless user asked for reset.
- Never hand-edit `graphify-out/**` or `.understand-anything/**`.
- Never assume a Claude Code skill is available unless it appears in the agent's own skill list.
- Never log or print token values from `.agent-auth.yaml`.
- Never commit `.agent-auth.yaml` (verify `.gitignore` covers it).
