# Playbooks

_Skill version: 4.3.0 — update this when SKILL.md bumps a minor or major version._

Each playbook maps a task type to the correct provisioning mode, stage sequence, source mode, clarification workers, and Graphify queries.

---

## 0) Tooling Preflight

Use before every non-trivial task.

### Audit mode

```text
Stage -1 — Tooling Preflight
  - Check AI DevKit command
  - Check .ai-devkit.json
  - Check Android CLI command
  - Check android info if available
  - Check android skills list if available
  - Check Graphify command/package
  - Check graphify-out/GRAPH_REPORT.md and graph.json
  - Check Karpathy guidance/plugin signals
  - Write or report preflight summary
  - Do not install/update/rebuild
```

### Bootstrap mode

```text
Stage -1 — Tooling Preflight
  - Install missing approved tools only
  - Run ai-devkit init if .ai-devkit.json missing
  - Run ai-devkit install if config exists and reconciliation needed
  - Run android init if Android CLI exists and agent setup requested
  - Run android skills find/list before adding skills
  - Build Graphify only if approved and useful for existing codebase
  - Write preflight report
```

### Update mode

```text
Stage -1 — Tooling Preflight
  - Update approved installed tools
  - Reconcile project setup
  - Refresh skills list
  - Update Graphify package if approved
  - Update graph if requested or after implementation
  - Write preflight report
```

### Refresh graph mode

```text
Stage -1 — Tooling Preflight
  - Check Graphify
  - If graph missing: /graphify .
  - If graph exists: /graphify . --update
  - Do not touch product code
```

---

## 1) New feature

```text
Stage -1 — audit tools and graph state
Stage 0 — collect source list and consume preflight report
Stage 1 — read graph if present; read docs/ai/inputs
Stage 1.5 — minimal clarification unless triggers fire
Stage 2 — write requirements from clarification brief; STOP
Stage 3 — design + Android memo
Stage 4 — one code owner implements
Stage 5 — Android CLI evidence + Graphify update
Stage 6 — Karpathy QA gate
```

---

## 2) Weak Jira + partial Figma

```text
Stage -1 — audit or setup based on user intent
Stage 0 — collect Jira + Figma + linked docs
Stage 1 — source readers in parallel
Stage 1.5 — Ambiguity + Conflict + Missing-info + State Extractor
Stage 2 — requirements from clarification brief; STOP
Stages 3–6 — normal flow
```

---

## 3) Edit existing feature

```text
Stage -1 — audit Graphify state
Stage 1 — graphify query/path if graph exists
Stage 1.5 — Ambiguity + Missing-info + Dependency Impact
Stage 2 — include graph path and out-of-scope list; STOP
Stage 4 — surgical changes only
Stage 5 — update graph and verify
```

---

## 4) Bug investigation

```text
Stage -1 — audit Android CLI and Graphify
Stage 0 — collect repro, device, version, expected behavior
Stage 1 — graph path + runtime evidence if available
Stage 1.5 — clarify only if repro unclear
Stage 2 — minimal bug requirements
Stage 4 — smallest safe patch
Stage 5 — runtime evidence + graph update if graph exists
```

---

## 5) XML → Compose migration

```text
Stage -1 — check Android CLI, Android skills, Graphify
Stage 1 — query "xml layout view fragment" if graph exists; android skills find "compose"
Stage 1.5 — Android Advisor + Dependency Impact + Rollout/Risk
Stage 2 — migration plan; STOP
Stage 4 — per-batch single-owner implementation
Stage 5 — visual evidence + graph update
```

---

## 6) AGP / build modernization

```text
Stage -1 — check AI DevKit, Android CLI, Android skills, Gradle wrapper, Graphify
Stage 1 — graphify query "gradle build agp"; android skills find "agp"
Stage 1.5 — Dependency Impact + Rollout/Risk + Android Advisor
Stage 2 — upgrade plan; STOP
Stage 4 — controlled implementation
Stage 5 — clean build + graph update
```

---

## 7) Unfamiliar codebase + raw task brief

```text
Stage -1 — audit first; refresh graph only if approved
Stage 0 — collect task brief
Stage 1 — read GRAPH_REPORT.md if present; Doc Reader reads inputs
Stage 1.5 — Ambiguity + Missing-info + Graph Impact + Dependency Impact
Stage 2 — requirements after ready; STOP
```

---

## Quick decision table

| Situation | Provisioning mode | Source mode | Clarification |
|---|---|---|---|
| Analyze repo | audit | N/A | No, unless task docs are analyzed |
| Setup repo | bootstrap | N/A | No |
| Update tools | update | N/A | No |
| Refresh graph | refresh-graph | N/A | No |
| Clean ticket + strong docs | audit | A/B | Light |
| Docs-only vague task | audit | B | Yes |
| Weak Jira ticket | audit | A | Yes |
| Migration | audit/bootstrap | B | Standard |
| Unfamiliar codebase | audit/refresh-graph | B | Full |
