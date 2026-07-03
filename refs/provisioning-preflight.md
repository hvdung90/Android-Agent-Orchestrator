# Provisioning Preflight

_Skill version: 4.16.0 — update this when SKILL.md bumps a minor or major version._

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

## Spec Kit

Check:

```bash
command -v specify || true
test -d .specify && echo "present" || echo "missing"
specify self check || true
```

Decision:

| State | Mode | Action |
|---|---|---|
| CLI missing | `audit` | Report missing |
| CLI missing | `bootstrap/update` | Install with `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z`, or use `uvx --from git+https://github.com/github/spec-kit.git specify ...` ephemerally |
| `.specify/` missing | `bootstrap` | Run `specify init --here --integration <agent>` |
| `.specify/` exists, update requested | `update` | Run `specify self check`; only `specify self upgrade` if newer release confirmed |
| Existing `.specify/memory/constitution.md` appears modified | Any | Do not overwrite silently; report |

---

## Android CLI

Check:

```bash
command -v android || true
android info || true
```

Decision:

| State | Mode | Action |
|---|---|---|
| CLI missing | `audit` | Report missing |
| CLI present | `update` | Run `android update` |
| Agent setup requested | `bootstrap/update` | Run `android init` |
| Runtime evidence needed but CLI missing | Any | Block verification |

---

## Android skills

Check:

```bash
android skills list --long
```

Find task-specific skills:

```bash
android skills find "compose"
android skills find "edge-to-edge"
android skills find "performance"
android skills find "agp"
```

Decision:

| State | Mode | Action |
|---|---|---|
| Android CLI missing | Any | Cannot manage Android skills |
| Skill list unavailable | Any | Report capability gap |
| Needed skill found | `bootstrap/update` | Add with confirmed `--skill` name |
| Skill name unknown | Any | Do not guess; run `find` or record unknown |
| User asks all skills | `bootstrap/update` | `android skills add --all` |

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
python -m pip show graphifyy || true
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

## Serena

Check:

```bash
command -v uv >/dev/null 2>&1 && echo "uv: present" || echo "uv: missing"
uvx serena --version 2>/dev/null | head -1 || echo "serena: not available"
```

Decision:

| State | Mode | Action |
|---|---|---|
| uv missing | Any | Report missing; Serena unavailable; non-blocking |
| uv present, Serena not runnable | `audit` | Report not-installed; non-blocking |
| uv present, Serena not runnable | `bootstrap/update` | Install: `uv tool install oraios-serena` if approved |
| Serena runnable | Any | Record ready; no further action in audit |

**Backend note:** Default backend is LSP (no IDE required). JetBrains backend (Android Studio IDE engine) is opt-in by dev — agent does not start the IDE. Record backend as `unknown` unless dev specifies.

**Kotlin LS stability note:** Kotlin Language Server is pre-alpha. Record `kotlin_ls_stable: unknown` unless dev confirms. Agent skips `get_diagnostics_*` calls when stability is unknown.

**Blocking rule:** Serena missing is **never a blocker**. Always record as non-blocking gap.

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

## Spec Kit
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
- Never assume a skill name if `android skills find` did not confirm it.
- Never log or print token values from `.agent-auth.yaml`.
- Never commit `.agent-auth.yaml` (verify `.gitignore` covers it).
