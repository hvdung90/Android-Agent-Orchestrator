# Playbooks

Each playbook maps a task type to the correct stage sequence, source mode, clarification workers, and Graphify queries.

---

## 1) New feature — good docs, existing codebase

**Source mode:** B (docs-only) or A (external sources)
**Clarification:** minimal unless triggers fire

```
Stage 0 — Intake
  - Collect source list
  - Check: graphify-out/ exists?

Stage 1 — Discovery
  # Graphify (if graph exists) — run in parallel with doc reading
  cat graphify-out/GRAPH_REPORT.md
  graphify query "<feature keyword>" --graph graphify-out/graph.json
  graphify path "<entry component>" "<target component>" --graph graphify-out/graph.json

  # Doc Reader
  - Read all docs/ai/inputs/ files

  # Android skills lane (in parallel)
  android skills find "<keyword>"

Stage 1.5 — Clarification (minimal — Mode B)
  Workers: Doc Reader output → Ambiguity Detector + Missing-info Detector
  Optional: Dependency Impact Analyzer if graph path is complex
  Exit: context-pack.json + clarification-brief.md + outcome = ready

Stage 2 — Requirements
  - Write from clarification-brief.md, not raw docs
  - Include graph path in affected components
  - STOP — wait for human approval

Stage 3 — Design split (parallel, no code)
  - AI DevKit: design + planning docs
    graphify explain "<ComponentName>" --graph graphify-out/graph.json   # understand rationale
  - Android skills: Android memo if Android-specialized

Stage 4 — Implementation lock
  - Single code owner only
  - No Graphify queries — map was read in Stage 1

Stage 5 — Verify
  android screen capture --output=.project-orchestration/evidence/screenshots/after.png
  ./gradlew clean build > .project-orchestration/evidence/logs/build.txt 2>&1
  /graphify . --update

Stage 6 — QA gate
  - Karpathy diff review
  - Acceptance coverage check
```

---

## 2) New feature — weak Jira + partial Figma

**Source mode:** A (external sources)
**Clarification:** full

```
Stage 0 — Intake
  - Collect Jira URL + Figma URL + any linked docs
  - Check: graphify-out/ exists?

Stage 1 — Discovery
  # Graphify (if graph exists)
  cat graphify-out/GRAPH_REPORT.md
  graphify query "<feature keyword>" --graph graphify-out/graph.json

  # Source readers (in parallel)
  Jira Reader + Figma Reader + Graph Impact Reader

Stage 1.5 — Clarification (full — Mode A)
  # Parallel group 1 (after source readers):
  Ambiguity Detector + Conflict Detector + Missing-info Detector + State Extractor

  # Optional parallel group 2:
  Research Advisor + Android Advisor

  # Parent synthesis:
  - Publish context-pack.json
  - Publish clarification-brief.md
  - Publish clarity-report.md
  - Choose outcome: ready | blocked | research-loop

  If blocked → present clarification-brief to human, list decisions_needed, wait.
  If research-loop → run Research Advisor, re-evaluate.
  If ready → proceed.

Stage 2 — Requirements
  - Write from clarification-brief.md
  - STOP — wait for human approval

Stages 3–6 — same as Playbook 1
```

---

## 3) Edit existing feature

**Source mode:** B (docs-only) or A
**Clarification:** minimal to standard depending on doc clarity

```
Stage 0 — Intake
  - Check: graphify-out/ exists?

Stage 1 — Discovery
  # Graphify — critical for edit tasks (know what you'd break)
  graphify query "<feature name>" --graph graphify-out/graph.json
  graphify path "<EntryPoint>" "<TargetComponent>" --graph graphify-out/graph.json

  # Doc/source reading (in parallel)
  Doc Reader (or Jira Reader if ticket exists)

Stage 1.5 — Clarification
  Workers: Ambiguity Detector + Missing-info Detector + Dependency Impact Analyzer
  Focus: what is the exact change boundary? what must not change?

Stage 2 — Requirements
  - Include graph path and impact analysis
  - List explicitly what is OUT of scope
  - STOP — wait for human approval

Stage 4 — Implementation lock
  - Surgical changes only within the graph path identified in Stage 1
  - Karpathy: do not touch nodes outside the path

Stage 5 — Verify
  /graphify . --update
  # Re-query to confirm path unchanged
  graphify query "<feature name>" --graph graphify-out/graph.json

Stages 3, 6 — same as Playbook 1
```

---

## 4) Bug investigation

**Source mode:** bug report / runtime evidence / docs
**Clarification:** minimal or skip if repro is clear

```
Stage 0 — Intake
  - Collect bug report, reproduction steps, affected device/version

Stage 1 — Discovery
  # Graphify — trace the failure path
  graphify path "<SymptomComponent>" "<SuspectedCause>" --graph graphify-out/graph.json

  # Runtime evidence (Android CLI)
  android layout --output=.project-orchestration/evidence/logs/layout-bug.json
  android screen capture --output=.project-orchestration/evidence/screenshots/bug.png

Stage 1.5 — Clarification (only if bug report is unclear)
  Workers: Ambiguity Detector + Missing-info Detector
  Focus: is repro clear? is expected behavior defined?
  Skip if: repro steps are deterministic and expected behavior is obvious.

Stage 2 — Requirements (minimal — bug scope)
  - Define: symptom, root cause hypothesis, fix boundary, regression test required
  - STOP — wait for human approval if fix is non-trivial

Stage 4 — Implementation
  - Smallest safe patch
  - Karpathy: no adjacent refactors

Stage 5 — Verify
  android screen capture --output=.project-orchestration/evidence/screenshots/fixed.png
  /graphify . --update
  # Confirm: is the graph path between symptom and cause now clean?

Stage 6 — QA gate
  - Regression test required
  - Karpathy diff: every line traces to the bug?
```

---

## 5) XML → Compose migration

**Source mode:** B (docs) + graph
**Clarification:** standard

```
Stage 1 — Discovery
  # Graphify — list ALL xml components and their dependencies
  graphify query "xml layout view fragment" --graph graphify-out/graph.json
  graphify query "fragment activity adapter" --graph graphify-out/graph.json
  # Order by graph: leaf nodes (no dependents) first, god nodes last

  # Android skills
  android skills find "compose"
  android skills add --skill=compose-migration

Stage 1.5 — Clarification
  Workers: Android Advisor + Dependency Impact Analyzer + Rollout/Risk Advisor
  Focus: migration order, compatibility risks, visual parity criteria

Stage 2 — Requirements / Migration plan
  - Include: full component list from graph, ordered by dependency
  - Include: visual parity definition (screenshot diff threshold)
  - Include: cleanup checklist (remove xml files when?)
  - STOP — wait for human approval

Stage 3 — Design
  - AI DevKit: migration plan per batch
  - Android skills: Compose pattern memo

Stage 4 — Implementation (per batch, single owner)
  # Capture before state
  android screen capture --output=.project-orchestration/evidence/screenshots/before-compose.png

  # After each batch:
  /graphify . --update
  graphify query "xml layout" --graph graphify-out/graph.json
  # Verify: xml node count decreasing

Stage 5 — Final verify
  android screen capture --output=.project-orchestration/evidence/screenshots/after-compose.png
  # Visual parity check
  /graphify . --update
  graphify query "xml layout" --graph graphify-out/graph.json
  # Verify: 0 xml nodes in migration scope
```

---

## 6) AGP / build modernization

**Source mode:** B (docs) + graph
**Clarification:** standard

```
Stage 1 — Discovery
  graphify query "gradle build agp" --graph graphify-out/graph.json
  android skills add --skill=agp-9-upgrade
  ./gradlew --version > .project-orchestration/evidence/logs/gradle-before.txt
  ./gradlew dependencies > .project-orchestration/evidence/logs/deps-before.txt

Stage 1.5 — Clarification
  Workers: Dependency Impact Analyzer + Rollout/Risk Advisor + Android Advisor
  Focus: breaking changes, dependency impacts, rollback plan

Stage 2 — Requirements / Upgrade plan
  - List breaking changes expected
  - Define rollback trigger
  - STOP — wait for human approval

Stage 4 — Implementation (controlled, single owner)
Stage 5 — Verify
  ./gradlew clean build > .project-orchestration/evidence/logs/build-after.txt 2>&1
  /graphify . --update

Stage 6 — QA gate
  - New version baselines recorded
  - Follow-up items filed
```

---

## 7) Unfamiliar codebase + raw task brief

**Source mode:** docs + graph (graph must be built first)
**Clarification:** full

```
Stage 0 — Intake
  # Build graph first — this is the most important step for unfamiliar codebases
  pip install graphifyy && graphify install
  /graphify .

Stage 1 — Discovery
  cat graphify-out/GRAPH_REPORT.md
  # God nodes = what everything connects through
  # Surprising connections = non-obvious links
  # open graphify-out/graph.html for visual exploration

  graphify query "<entry point or feature area>" --graph graphify-out/graph.json

  # Then capture-knowledge for detail on specific entry point
  # ai-devkit capture-knowledge --entry-point=<file>

  # Doc Reader
  Doc Reader (read all docs/ai/inputs/)

Stage 1.5 — Clarification (full)
  Workers: Ambiguity Detector + Missing-info Detector + Graph Impact Reader + Dependency Impact Analyzer
  Focus: does the task brief match what the graph shows? what is assumed vs confirmed?

  Parent publishes context-pack.json + clarification-brief.md
  If blocked → ask human for missing decisions before routing

Stage 2 — Requirements
  - Write only after clarification outcome = ready
  - STOP — wait for human approval

Stages 3–6 — same as Playbook 1
```

---

## Quick decision table

| Situation | Source mode | Run Clarification? | Minimum workers |
|---|---|---|---|
| Clean ticket + strong docs | A | Light | Doc/Jira Reader + Graph Impact Reader |
| Docs-only, clear task | B | Minimal | Doc Reader + Ambiguity + Missing-info |
| Docs-only, vague task | B | Yes | Doc Reader + Ambiguity + Missing-info + Dependency Impact |
| Weak Jira ticket | A | Yes | Jira + Ambiguity + Missing-info + Graph Impact |
| UI-heavy task with Figma | A | Yes | Figma + State Extractor + Conflict Detector + Graph Impact |
| Architecture-affecting change | A or B | Yes | Graph Impact + Dependency Impact + Conflict Detector |
| Simple bug with clear repro | B | Maybe minimal | Graph path + runtime evidence |
| Migration (XML/AGP) | B | Standard | Graph Impact + Dependency Impact + Android Advisor |
| Unfamiliar codebase | B | Full | Graph Impact + Ambiguity + Missing-info + Dependency Impact |

---

## Graphify quick reference (all playbooks)

```bash
# Build (first time or new repo)
pip install graphifyy && graphify install
/graphify .

# Read overview — always first
cat graphify-out/GRAPH_REPORT.md

# Query affected area
graphify query "<keyword>" --graph graphify-out/graph.json

# Trace dependency path
graphify path "ComponentA" "ComponentB" --graph graphify-out/graph.json

# Understand design rationale
graphify explain "ComponentName" --graph graphify-out/graph.json

# Update after implementation
/graphify . --update

# Make Claude Code read graph automatically before every task
graphify claude install
```
