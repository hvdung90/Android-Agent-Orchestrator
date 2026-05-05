# Provisioning Preflight

_Skill version: 4.2.7 — update this when SKILL.md bumps a minor or major version._

## Purpose

Stage -1 Tooling Preflight ensures the agent knows whether required orchestration tools exist, are usable, and are allowed to be installed or updated before any task workflow begins.

It prevents agents from assuming tool availability, inventing commands, reading a stale graph, or mutating global tooling during a read-only analysis task.

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
| `refresh-graph` | No, except Graphify if explicitly allowed | Yes | Build/update graph |
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

## AI DevKit

Check:

```bash
command -v ai-devkit || true
test -f .ai-devkit.json && echo "present" || echo "missing"
```

Decision:

| State | Mode | Action |
|---|---|---|
| CLI missing | `audit` | Report missing |
| CLI missing | `bootstrap/update` | Install or use `npx ai-devkit@latest ...` |
| `.ai-devkit.json` missing | `bootstrap` | Run `ai-devkit init` |
| `.ai-devkit.json` exists | `bootstrap/update` | Run `ai-devkit install` |
| Existing config appears modified | Any | Do not overwrite silently; report |

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

## Graphify

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

## AI DevKit
## Android CLI
## Android skills
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
- optional Graphify is missing but docs/capture-knowledge can be used,
- Karpathy plugin is missing but principles can be applied manually,
- Android skills are missing but Android domain memo can still be written with caveat.

---

## Auth credentials check

→ **Load `refs/auth-bootstrap.md`** for full bootstrap procedure and just-in-time token check rules.

At Stage -1, run Bước 1 (auth init):

```bash
test -f .agent-auth.yaml && echo "present" || echo "missing"
```

- Present → load, note which tokens have values vs empty.
- Missing → auto-create from template (all tokens empty); notify user.

Token check cho từng tool xảy ra **just-in-time** tại thời điểm tool đó được gọi — không check trước toàn bộ tại Stage -1.

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

## Safety rules

- Never run global install/update in `audit`.
- Never overwrite `CLAUDE.md` without explicit permission.
- Never delete `graphify-out/` unless user asked for reset.
- Never hand-edit `graphify-out/**`.
- Never assume a skill name if `android skills find` did not confirm it.
- Never log or print token values from `.agent-auth.yaml`.
- Never commit `.agent-auth.yaml` (verify `.gitignore` covers it).
