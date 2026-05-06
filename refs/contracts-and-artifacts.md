# Contracts, Artifacts, and Gates

_Skill version: 4.4.0 — update this when SKILL.md bumps a minor or major version._

---

## Canonical artifacts

### 0) `.project-orchestration/reports/preflight.md`

Purpose: records Stage -1 Tooling Preflight.

Required sections:

```markdown
# Tooling Preflight

## Mode
audit | bootstrap | update | refresh-graph | force-reinstall

## Summary
- Ready for Stage 0:
- Blocking gaps:
- Non-blocking gaps:

## Auth
- .agent-auth.yaml: present | created-empty | missing
- atlassian.api_token: set | empty
- figma.personal_access_token: set | empty
- github.personal_access_token: set | empty
- Project overrides defined: <count>

## AI DevKit
## Android CLI
## Android skills
## Graphify
## Karpathy
## Serena
## Decisions
- Tokens to request from user (just-in-time, khi cần):
```

Full template: `templates/preflight-report.md`  
Full example: `examples/preflight-report.example.md`

---

### 1) `docs/ai/clarification/context-pack.json`

**Sparse format rule:** Only include keys that have actual values. Omit keys with empty arrays `[]`, `null`, `false` (defaults), or `0`. This reduces token cost when context-pack is re-read in later stages.

Exception: always include `feature_id`, `clarity_score`, `outcome`, `blocked`, `graph_impact`, `auth_status.file`.

```json
{
  "feature_id": "ANDROID-123 | task-brief | <slug>",
  "title": "",
  "sources": [
    {
      "type": "jira | confluence | figma | doc | ticket | note | graph | preflight",
      "ref": "<url or filename>",
      "summary": "<one-line summary>"
    }
  ],
  "business_goal": "",
  "user_problem": "",
  "acceptance_criteria": [],
  "screens": [],
  "states": [],
  "dependencies": [],
  "facts": [],
  "assumptions": [],
  "unknowns": [],
  "conflicts": [],
  "decisions_needed": [],
  "recommended_v1_scope": [],
  "tooling_readiness": {
    "mode": "audit | bootstrap | update | refresh-graph | force-reinstall",
    "ai_devkit": "ready | missing | unknown",
    "android_cli": "ready | missing | unknown",
    "android_skills": "ready | partial | missing | unknown",
    "graphify": "ready | graph-missing | cli-missing | stale | unknown",
    "karpathy": "installed | manual | missing | unknown",
    "serena": "ready | missing | not-configured"
  },
  "auth_status": {
    "file": "present | created-empty | missing",
    "atlassian": "set | empty",
    "figma": "set | empty",
    "github": "set | empty",
    "active_project_override": "<name> | none"
  },
  "graph_path": "<ComponentA -> ComponentB -> ComponentC | none>",
  "god_nodes_touched": [],
  "graph_impact": "low | medium | high",
  "blocked": false,
  "clarity_score": 0,
  "outcome": "ready | blocked | research-loop"
}

// graph_impact guidance:
// low    — change is isolated (1 component, no shared dependencies, no god nodes)
//          → skip /graphify . --update in Stage 5
// medium — change touches 2-4 components or one shared utility
//          → run /graphify . --update in Stage 5
// high   — change touches god nodes, crosses layer boundaries, or affects >4 components
//          → run /graphify . --update in Stage 5; optional before/after compare in Stage 6
```

---

## Stage gates

### Gate -1 — Tooling Preflight complete

Required:
- `.agent-auth.yaml` initialized (present or auto-created),
- token status recorded (set / empty) for atlassian, figma, github,
- provisioning mode recorded,
- AI DevKit checked,
- Android CLI checked,
- Android skills checked if Android CLI exists,
- Graphify checked,
- graph state recorded,
- Karpathy state recorded,
- Serena checked (uv present, MCP configured or not; always non-blocking),
- action permissions recorded,
- blockers recorded,
- decision: proceed to Stage 0 yes/no.

### Gate A — Intake complete

Required:
- source list exists,
- graph availability checked,
- preflight report consumed,
- initial task scope noted.

### Gate B — Discovery complete

Required:
- graph overview read if present,
- raw sources read,
- discovery notes stored in `docs/ai/discovery/`.

### Gate C — Clarification complete

Required:
- `context-pack.json`,
- `clarification-brief.md`,
- clarity report or embedded clarity section,
- Serena Code Analysis Worker outputs attached or summarized (if Serena ready and triggers fired),
- parent outcome chosen.

### Gate D — Requirements complete

Required:
- canonical requirements doc exists,
- human approval recorded.

### Gate E — Design ready

Required:
- design doc exists,
- Android memo exists if Android-specific,
- single code owner selected.

### Gate F — Verification ready

Required:
- build/runtime evidence captured,
- Graphify update run if graph exists,
- acceptance coverage checked.

### Gate G — Close ready

Required:
- Karpathy diff review passed,
- final execution report written,
- no unresolved blockers remain.

---

---

## Local memory schemas

Stored in `.project-orchestration/memory/` (gitignored). Agent reads on startup, writes on completion.

### `tooling-cache.json`

Cache kết quả Stage -1 để skip preflight nếu tooling không đổi.

```json
{
  "checked_at": "2026-05-05T09:00:00Z",
  "valid_until": "2026-05-06T09:00:00Z",
  "graph_commit": "abc1234",
  "ai_devkit": "2.1.0 | missing",
  "android_cli": "present | missing",
  "android_cli_version": "34",
  "graphify": "0.9.1 | missing",
  "karpathy": "installed | manual | missing",
  "auth_file": "present | missing"
}
```

**Skip rule:** If `valid_until` > now AND `graph_commit` == `git rev-parse HEAD` → skip Stage -1 tool checks entirely. Load cached values into preflight context and proceed to Stage 0.  
**Invalidate when:** any tool is installed/updated, or TTL expires (default 24h).

### `session.json`

Trạng thái task đang dở — cho phép resume sau khi bị interrupt.

```json
{
  "task_id": "ANDROID-42 | task-slug",
  "started_at": "2026-05-05T09:00:00Z",
  "updated_at": "2026-05-05T11:30:00Z",
  "stage_reached": -1,
  "stage_status": "complete | in_progress | blocked",
  "code_owner": "agent-name | null",
  "source_mode": "A | B | C",
  "requirements_approved": false,
  "blocker": "waiting for human approval at Stage 2 | null"
}
```

**Resume rule:** At Stage -1, if `session.json` exists and `stage_reached >= 0` and `stage_status != complete` → ask user: "Resume task `<task_id>` from Stage `<stage_reached>`?" If yes, skip stages already completed. If no, overwrite session.

### `graph-stamp.json`

Metadata về lần chạy Graphify gần nhất.

```json
{
  "built_at": "2026-05-05T08:00:00Z",
  "commit_sha": "abc1234",
  "graph_report": "graphify-out/GRAPH_REPORT.md",
  "god_nodes": ["AppModule", "NetworkClient"],
  "component_count": 42
}
```

**Freshness rule:** If `commit_sha` == `git rev-parse HEAD` → graph is fresh; skip rebuild check. If commits have landed since `built_at` → flag graph as potentially stale in preflight.

---

## Graphify stage trigger rules

| Stage | Trigger | Action |
|---|---|---|
| Stage -1 | Always | Check Graphify CLI/package and graph files |
| Intake | Check existence | Note graph present/absent |
| Discovery | Graph exists | Read `GRAPH_REPORT.md`; query affected area |
| Clarification | Graph exists | Graph Impact Reader feeds dependencies into context-pack |
| Design split | Graph exists | Use graph rationale if needed |
| Implementation | — | No graph queries during coding |
| Verify | Graph exists | `/graphify . --update` after implementation |
| QA gate | Graph exists | Optional compare before/after; check god nodes |

---

## Ownership rules

| Artifact | Owner | Others may |
|---|---|---|
| `preflight.md` | Parent orchestrator | provide raw audit output |
| `context-pack.json` | Parent orchestrator / AI DevKit | propose raw fields |
| `clarification-brief.md` | Parent orchestrator / AI DevKit | recommend wording |
| `requirements/<task>.md` | Parent orchestrator / AI DevKit | review only |
| `android-memo/<task>.md` | Android skills | supply advice only |
| runtime evidence | Android CLI | request commands |
| `graphify-out/**` | Graphify | consume/query only |
| `docs/ai/inputs/**` | Human | never overwritten by agent |

---

## Approval rule

Do not proceed from Requirements to Design/Implementation without explicit human approval.
