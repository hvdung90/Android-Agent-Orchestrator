# Playbooks

_Skill version: 4.12.0 — update this when SKILL.md bumps a minor or major version._

Each playbook maps a task type to the correct provisioning mode, stage sequence, source mode, clarification workers, and architecture-map queries (Understand-Anything checked first, Graphify fallback).

---

## 0) Tooling Preflight

Use before every non-trivial task.

### Audit mode

```text
Stage -1 — Tooling Preflight
  - Check Spec Kit command
  - Check .specify/
  - Check Android CLI command
  - Check android info if available
  - Check android skills list if available
  - Check Understand-Anything plugin/skill and .understand-anything/knowledge-graph.json (checked first)
  - If Understand-Anything unavailable: check Graphify command/package and graphify-out/GRAPH_REPORT.md + graph.json (fallback)
  - Check Karpathy guidance/plugin signals
  - Write or report preflight summary
  - Do not install/update/rebuild
```

### Bootstrap mode

```text
Stage -1 — Tooling Preflight
  - Install missing approved tools only
  - Run `specify init --here --integration <agent>` if `.specify/` missing
  - Run `specify self upgrade` if `.specify/` exists and a newer release is confirmed
  - Run android init if Android CLI exists and agent setup requested
  - Run android skills find/list before adding skills
  - Install/build Understand-Anything only if approved and useful for existing codebase; build Graphify instead only if Understand-Anything is unavailable
  - Write preflight report
```

### Update mode

```text
Stage -1 — Tooling Preflight
  - Update approved installed tools
  - Reconcile project setup
  - Refresh skills list
  - Update Understand-Anything if approved; update Graphify package instead only if Understand-Anything is unavailable
  - Update graph if requested or after implementation
  - Write preflight report
```

### Refresh graph mode

```text
Stage -1 — Tooling Preflight
  - Check Understand-Anything first; check Graphify only if Understand-Anything is unavailable
  - Understand-Anything: run /understand (builds or rebuilds); /understand-diff for impact analysis
  - Graphify (fallback): if graph missing, /graphify .; if graph exists, /graphify . --update
  - Do not touch product code
```

---

## 1) New feature

```text
Stage -1 — audit tools and graph state; check Serena (non-blocking)
Stage 0 — collect source list and consume preflight report
Stage 1 — read graph if present; read docs/ai/inputs
          [Serena: agent] get_symbols_overview on affected area if graph_impact ≥ medium
Stage 1.5 — minimal clarification unless triggers fire
            [Serena: agent] find_implementations / find_referencing_symbols if triggers fire
Stage 2 — write requirements from clarification brief; STOP
Stage 2.5 — evaluate ADR-lite triggers; STOP again if ADR approval/deferral required
Stage 3 — design + Android memo
Stage 4 — one code owner implements
          [Serena: code-owner request] find_declaration / find_implementations advisory
Stage 5 — Android CLI evidence + architecture-map update
          [Serena: agent] get_diagnostics_for_file if graph_impact ≥ medium AND kotlin-ls stable
Stage 6 — Karpathy QA gate
          [Serena: optional] find_referencing_symbols scope check
Stage 7 — finalize ADR status + Task Changelog + Drift Check
```

---

## 2) Weak Jira + partial Figma

```text
Stage -1 — audit or setup based on user intent; check Serena (non-blocking)
Stage 0 — collect Jira + Figma + linked docs
Stage 1 — source readers in parallel
          [Serena: agent] find_symbol for key components named in Jira ticket
Stage 1.5 — Ambiguity + Conflict + Missing-info + State Extractor
            [Serena: agent] find_implementations for any interface flagged by Missing-info
Stage 2 — requirements from clarification brief; STOP
Stage 2.5 — evaluate ADR-lite triggers; STOP again if ADR approval/deferral required
Stages 3–7 — normal flow
```

---

## 3) Edit existing feature

```text
Stage -1 — audit architecture map (Understand-Anything → Graphify fallback) + Serena state
Stage 1 — query architecture map / path if graph exists
          [Serena: agent] find_referencing_symbols on the symbol being edited
Stage 1.5 — Ambiguity + Missing-info + Dependency Impact
            [Serena: agent] find_implementations if abstract/interface involved
Stage 2 — include graph path, caller count from Serena, out-of-scope list; STOP
Stage 2.5 — evaluate ADR-lite triggers; STOP again if ADR approval/deferral required
Stage 4 — surgical changes only
          [Serena: code-owner request] find_declaration for usage pattern
Stage 5 — update graph and verify
          [Serena: agent] get_diagnostics_for_file if kotlin-ls stable
Stage 7 — finalize ADR status + Task Changelog + Drift Check
```

---

## 4) Bug investigation

```text
Stage -1 — audit Android CLI and architecture map (Understand-Anything → Graphify fallback); check Serena (non-blocking)
Stage 0 — collect repro, device, version, expected behavior
Stage 1 — graph path + runtime evidence if available
          [Serena: agent] find_symbol on crash site / reported component
          [Serena: agent] find_referencing_symbols to trace callers
Stage 1.5 — clarify only if repro unclear
Stage 2 — minimal bug requirements; include Serena call chain evidence
Stage 2.5 — evaluate ADR-lite triggers; usually not_required unless contract/state/schema changes
Stage 4 — smallest safe patch
          [Serena: code-owner request] find_declaration for context
Stage 5 — runtime evidence + graph update if graph exists
          [Serena: agent] get_diagnostics_for_file on patched file if kotlin-ls stable
Stage 7 — finalize Task Changelog + Drift Check
```

---

## 5) XML → Compose migration

```text
Stage -1 — check Android CLI, Android skills, architecture map (Understand-Anything → Graphify fallback), Serena
Stage 1 — query "xml layout view fragment" if graph exists; android skills find "compose"
          [Serena: agent] get_symbols_overview on XML-bound view layer
          [Serena: agent] find_referencing_symbols on Fragment/Activity being migrated
Stage 1.5 — Android Advisor + Dependency Impact + Rollout/Risk
            [Serena: agent] find_implementations of ViewBinding / Fragment interfaces
Stage 2 — migration plan; include Serena symbol surface; STOP
Stage 2.5 — ADR-lite required for Compose/View migration strategy unless explicitly deferred
Stage 4 — per-batch single-owner implementation
Stage 5 — visual evidence + graph update
Stage 7 — accept/defer ADR + Task Changelog + Drift Check
```

---

## 6) AGP / build modernization

```text
Stage -1 — check Spec Kit, Android CLI, Android skills, Gradle wrapper, architecture map (Understand-Anything → Graphify fallback), Serena
Stage 1 — query architecture map "gradle build agp"; android skills find "agp"
          [Serena: agent] find_symbol for build-related symbols if Kotlin DSL in use
Stage 1.5 — Dependency Impact + Rollout/Risk + Android Advisor
Stage 2 — upgrade plan; STOP
Stage 2.5 — ADR-lite required for AGP/Gradle/Kotlin version decision
Stage 4 — controlled implementation
Stage 5 — clean build + graph update
          [Serena: agent] get_diagnostics_for_file on changed build files if kotlin-ls stable
Stage 7 — accept/defer ADR + Task Changelog + Drift Check
```

---

## 7) Unfamiliar codebase + raw task brief

```text
Stage -1 — audit first; refresh graph only if approved; check Serena (non-blocking)
Stage 0 — collect task brief
Stage 1 — read GRAPH_REPORT.md if present; Doc Reader reads inputs
          [Serena: agent] get_symbols_overview on codebase entry points (if Serena ready)
Stage 1.5 — Ambiguity + Missing-info + Graph Impact + Dependency Impact
            [Serena: agent] find_symbol / find_implementations for key domain symbols
Stage 2 — requirements after ready; include Serena codebase surface summary; STOP
Stage 2.5 — evaluate ADR-lite triggers; STOP again if ADR approval/deferral required
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
