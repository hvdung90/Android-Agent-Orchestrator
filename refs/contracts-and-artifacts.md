# Contracts, Artifacts, and Gates

_Skill version: 4.2.7 — update this when SKILL.md bumps a minor or major version._

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
## Decisions
- Tokens to request from user (just-in-time, khi cần):
```

Full template: `templates/preflight-report.md`  
Full example: `examples/preflight-report.example.md`

---

### 1) `docs/ai/clarification/context-pack.json`

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
    "karpathy": "installed | manual | missing | unknown"
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
  "blocked": false,
  "clarity_score": 0,
  "outcome": "ready | blocked | research-loop"
}
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
