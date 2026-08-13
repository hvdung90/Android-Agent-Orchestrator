# Playbooks

_Skill version: 6.1.3 — update this when SKILL.md bumps a minor or major version._

Each playbook maps a task type to the correct provisioning mode, stage sequence, source mode, clarification workers, and architecture-map queries (Understand-Anything checked first, Graphify fallback).

All `android` / `android studio` commands below are examples that must pass `refs/android-cli-compatibility.md` discovery/cache first. If unsupported, use that ref's fallback matrix or record an Unavailable-tool record.

---

## 0) Tooling Preflight

Use before every non-trivial task.

### Audit mode

```text
Stage -1 — Tooling Preflight
  - Check adb availability (primary Android device tool)
  - Probe android CLI (expected missing — non-blocking)
  - Check Understand-Anything plugin/skill and .understand-anything/knowledge-graph.json (checked first)
  - If Understand-Anything unavailable: check Graphify command/package and graphify-out/GRAPH_REPORT.md + graph.json (fallback)
  - Check Karpathy guidance/plugin signals
  - Write or report preflight summary
  - Do not install/update/rebuild
```

### Bootstrap mode

```text
Stage -1 — Tooling Preflight
  - Install missing approved tools only (adb via Platform-Tools if missing)
  - Note android CLI as aspirational; do not install
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
Stage -1 — audit tools and graph state
Stage 0 — collect source list and consume preflight report
Stage 1 — read graph if present; read docs/ai/inputs
Stage 1.5 — minimal clarification unless triggers fire
            android docs search on any unresolved Android API questions
Stage 2 — write requirements from clarification brief; STOP
Stage 2.5 — evaluate ADR-lite triggers; STOP again if ADR approval/deferral required
Stage 3 — design + Android memo
          android studio version-lookup agp kotlin compose — record versions in plan header
          Check Android Skills activation map: load applicable skills (see § Android Skills activation map)
Stage 4 — one code owner implements
Stage 5 — Android CLI evidence + architecture-map update
Stage 6 — Karpathy QA gate; android studio analyze-file on all changed files
Stage 7 — finalize ADR status + Task Changelog + Artifact Integrity; Skill Drift only if skill files changed
```

---

## 2) Weak Jira + partial Figma

```text
Stage -1 — audit or setup based on user intent
Stage 0 — collect Jira + Figma + linked docs
Stage 1 — source readers in parallel
          Figma Reader: self-check MCP tools first (get_metadata → scoped get_design_context);
                        PAT+REST fallback only if MCP absent
Stage 1.5 — Ambiguity + Conflict + Missing-info + State Extractor
Stage 2 — requirements from clarification brief; STOP
Stage 2.5 — evaluate ADR-lite triggers; STOP again if ADR approval/deferral required
Stages 3–7 — normal flow
```

---

## 3) Edit existing feature

```text
Stage -1 — audit architecture map (Understand-Anything → Graphify fallback)
Stage 1 — query architecture map / path if graph exists
Stage 1.5 — Ambiguity + Missing-info + Dependency Impact
Stage 2 — include graph path, caller count from graph, out-of-scope list; STOP
Stage 2.5 — evaluate ADR-lite triggers; STOP again if ADR approval/deferral required
Stage 4 — surgical changes only
Stage 5 — update graph and verify
Stage 7 — finalize ADR status + Task Changelog + Artifact Integrity; Skill Drift only if skill files changed
```

---

## 4) Bug investigation

```text
Stage -1 — audit Android CLI and architecture map (Understand-Anything → Graphify fallback)
Stage 0 — collect repro, device, version, expected behavior
Stage 1 — graph path + runtime evidence if available
Stage 1.5 — clarify only if repro unclear
Stage 2 — minimal bug requirements; include call chain from graph evidence
Stage 2.5 — evaluate ADR-lite triggers; usually not_required unless contract/state/schema changes
Stage 4 — smallest safe patch
Stage 5 — runtime evidence + graph update if graph exists
Stage 7 — finalize Task Changelog + Artifact Integrity; Skill Drift only if skill files changed
```

---

## 5) XML → Compose migration

```text
Stage -1 — check Android CLI, Android skills, architecture map (Understand-Anything → Graphify fallback)
Stage 1 — query "xml layout view fragment" if graph exists
          android skills add --skill=jetpack-compose/migration/migrate-xml-views-to-jetpack-compose
          android studio find-usages on Fragment/Activity being migrated
Stage 1.5 — Android Advisor + Dependency Impact + Rollout/Risk
Stage 2 — migration plan; include symbol surface from graph + android studio; STOP
Stage 2.5 — ADR-lite required for Compose/View migration strategy unless explicitly deferred
            If targetSdk ≥ 35: also load system/edge-to-edge
Stage 4 — per-batch single-owner implementation
          android studio render-compose-preview on each migrated Composable
Stage 5 — android screen capture --annotate + android layout + graph update
Stage 7 — accept/defer ADR + Task Changelog + Artifact Integrity; Skill Drift only if skill files changed
```

---

## 6) AGP / build modernization

```text
Stage -1 — check Android CLI, Android skills, Gradle wrapper, architecture map (Understand-Anything → Graphify fallback)
Stage 1 — query architecture map "gradle build agp"
          android studio version-lookup agp kotlin compose
          android skills add --skill=build-system/agp/agp-9-upgrade
Stage 1.5 — Dependency Impact + Rollout/Risk + Android Advisor
Stage 2 — upgrade plan; STOP
Stage 2.5 — ADR-lite required for AGP/Gradle/Kotlin version decision
Stage 4 — controlled implementation
Stage 5 — clean build + graph update; android run to verify deploy
          android studio analyze-file on changed build files
Stage 7 — accept/defer ADR + Task Changelog + Artifact Integrity; Skill Drift only if skill files changed
```

---

## 7) Unfamiliar codebase + raw task brief

```text
Stage -1 — audit first; refresh graph only if approved
Stage 0 — collect task brief
Stage 1 — read GRAPH_REPORT.md if present; Doc Reader reads inputs
          android studio find-usages on codebase entry points
Stage 1.5 — Ambiguity + Missing-info + Graph Impact + Dependency Impact
            android studio find-declaration / find-usages for key domain symbols
Stage 2 — requirements after ready; include codebase surface summary from graph; STOP
Stage 2.5 — evaluate ADR-lite triggers; STOP again if ADR approval/deferral required
```

---

## Android Skills activation map

Android skills are Claude Code companion skills — loaded from the agent's own skill list, not via `android skills add`.
Activate the relevant skill only when its signal is confirmed.

### Broadly applicable (check for any Android project)

| Signal | Skill | Stage |
|---|---|---|
| No test framework detected + new feature | `testing/testing-setup` | Stage 3 |
| Any UI task + `targetSdk ≥ 35` (Android 15+) | `system/edge-to-edge` | Stage 2.5 + Stage 4 |
| Task touches Activity, Service, BroadcastReceiver, or PendingIntent | `security/android-intent-security` | Stage 2.5 + Stage 6 |
| `change_type = dependency_change` + AGP version in build files | `build-system/agp/agp-9-upgrade` | Stage 3–4 |
| "Compose migration" / "Views to Compose" in brief or ADR trigger | `jetpack-compose/migration/migrate-xml-views-to-jetpack-compose` | Stage 3–4 |
| Navigation graph appears in ADR trigger list | `navigation/navigation-3` | Stage 3 |
| Tablet / foldable / multi-form-factor in Figma or task brief | `jetpack-compose/adaptive` | Stage 3 |
| Task destined for Play Store release | `play/play-policy-insights` | Stage 5–6 |
| Task touches billing code | `play/play-billing-library-version-upgrade` | Stage 3–4 |
| ProGuard / R8 rules in scope or APK size concern | `performance/r8-analyzer` | Stage 5 |
| Performance regression flagged in Stage 5 verification | `profilers/perfetto-trace-analysis` | Stage 5 |

### Platform-specific (load only when platform confirmed)

| Signal | Skill |
|---|---|
| Camera feature in brief | `camera/camerax` |
| Cast / streaming | `media/media3-cast-integration` |
| D-pad navigation / TV layout | `tv/leanback-to-compose-tv-migration` |
| "Wear OS" in brief | `wear/wear-compose-m3` |
| "AppFunctions" / on-device AI agent exposure (targetSdk 36+) | `device-ai/appfunctions` |
| OTP-less email verification | `identity/verified-email` |

---

## Quick decision table

| Situation | Provisioning mode | Source mode | Clarification |
|---|---|---|---|
| UI copy/pixel tweak (no layout/logic change) | audit | N/A | No — fast-eligible; see the pixel-tweak TDD exemption in `refs/compliance-policy.md` § TDD exemption categories |
| Dependency patch/minor version bump (no code change) | audit | N/A | No — fast-eligible; see `dependency_change` in the Evidence Gate Matrix (`refs/contracts-and-artifacts.md`) |
| Analyze repo | audit | N/A | No, unless task docs are analyzed |
| Setup repo | bootstrap | N/A | No |
| Update tools | update | N/A | No |
| Refresh graph | refresh-graph | N/A | No |
| Clean ticket + strong docs | audit | A/B | Light |
| Docs-only vague task | audit | B | Yes |
| Weak Jira ticket | audit | A | Yes |
| Migration | audit/bootstrap | B | Standard |
| Unfamiliar codebase | audit/refresh-graph | B | Full |
