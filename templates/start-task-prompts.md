# Start Task Prompt Templates

Copy one template, fill the placeholders, then send it to the agent.

Rule of thumb:
- Pick exactly one task type `[A]` through `[J]` from `docs/FLOW.md`.
- Keep the first prompt focused on source discovery, requirements, and the intended stop point.
- Ask the agent to stop after Stage 2 unless implementation is already explicitly approved.
- Put long notes in `docs/ai/inputs/<task>.md` and link that file in the prompt.
- Use `none` or `unknown` explicitly when a source is unavailable.

Source modes:
- Mode A: provide at least one Jira, Figma, or Confluence link.
- Mode B: provide local docs only, usually under `docs/ai/inputs/`.
- Mode C: provide no docs; the prompt itself is the only source.

---

## [A] Analyze Repo

```text
Analyze this repo using the Android Agent Orchestrator flow.

Goal:
Understand the architecture before starting implementation work.

Focus areas:
- <module/package/screen/flow>
- <state management/API/build area>

Questions to answer:
- <question 1>
- <question 2>
- <question 3>

Please run Stage -1 in audit mode.
Read Graphify output if available.
Do not modify product code.
Return findings, risks, and recommended next steps.
```

---

## [B] Bootstrap Repo

```text
Set up agents for this repo using Android Agent Orchestrator bootstrap mode.

Goal:
Prepare the repo for future Android tasks.

Expected setup:
- Create `.agent-auth.yaml` if missing, but do not print token values.
- Initialize or reconcile AI DevKit project setup if needed.
- Check Android CLI and Android skills availability.
- Build Graphify output only if useful for this codebase and approved.

Please run Stage -1 in bootstrap mode.
Install or initialize missing tools only when approval is required and granted.
Write `.project-orchestration/reports/preflight.md`.
Stop after reporting readiness, blockers, and next steps.
```

---

## [C] Update Tools

```text
Update Android Agent Orchestrator tooling for this repo.

Goal:
Bring existing orchestration tools and skill setup up to date without changing product code.

Update scope:
- AI DevKit: <update/reconcile/none>
- Android CLI and skills: <update/list/reconcile/none>
- Graphify package: <update/none>
- Serena: <check/update/none>

Constraints:
- Do not reinstall tools that are already healthy.
- Do not rebuild the architecture graph unless it is stale or explicitly needed.
- Do not modify product code.

Please run Stage -1 in update mode.
Write `.project-orchestration/reports/preflight.md`.
Stop after reporting updated tools, skipped tools, blockers, and follow-up actions.
```

---

## [D] Refresh Graph

```text
Refresh the architecture graph for this repo using Android Agent Orchestrator.

Goal:
Update Graphify output so later tasks can use current architecture context.

Graph target:
- Scope: <whole repo or specific module/path>
- Existing graph path: graphify-out/ or none
- Reason: <stale graph/new codebase/pre-implementation analysis/post-implementation update>

Constraints:
- Do not modify product code.
- Do not install or update unrelated tools.

Please run Stage -1 in refresh-graph mode.
Run `/graphify .` if the graph is missing, or `/graphify . --update` if it exists.
Write `.project-orchestration/reports/preflight.md`.
Stop after reporting graph status, freshness, and any blockers.
```

---

## [E] New Feature

```text
Start a new feature using the Android Agent Orchestrator flow.

Feature:
<feature name>

Context:
<Short description of the user problem and desired behavior.>

Sources:
- Jira: <link or none>
- Figma: <link or none>
- Confluence/spec: <link or none>
- Local docs: docs/ai/inputs/<file>.md or none

Acceptance criteria:
- <Testable behavior 1>
- <Testable behavior 2>
- <Testable behavior 3>

Out of scope:
- <Explicit non-goal 1>
- <Explicit non-goal 2>

Constraints:
- <API, compatibility, rollout, analytics, performance, or UI constraints>

Please run Stage -1 audit first, then proceed through Stage 0-2 only.
Write the canonical requirements doc and stop for my approval before design or implementation.
```

---

## [F] Edit Existing Feature

```text
Start an existing-feature change using the Android Agent Orchestrator flow.

Feature area:
<existing feature/module/screen>

Current behavior:
<What the app does today.>

Requested change:
<What should change.>

Sources:
- Jira: <link or none>
- Figma: <link or none>
- Confluence/spec: <link or none>
- Local docs: docs/ai/inputs/<file>.md or none

Acceptance criteria:
- <Expected updated behavior 1>
- <Expected updated behavior 2>

Do not change:
- <Existing behavior that must remain stable>
- <Modules/screens/APIs outside the feature scope>

Please run Stage -1 audit first, inspect graph context if available, and proceed through Stage 0-2 only.
Include an out-of-scope list and affected-component summary in the requirements doc.
Stop for my approval before implementation.
```

---

## [G] Bug Fix

```text
Start a bug investigation using the Android Agent Orchestrator flow.

Bug:
<short title>

Observed behavior:
<What actually happens.>

Expected behavior:
<What should happen instead.>

Reproduction steps:
1. <step 1>
2. <step 2>
3. <step 3>

Environment:
- App version/build: <value or unknown>
- Device/OS: <value or unknown>
- Account/state: <value or none>

Evidence:
- Logs: <path/link or none>
- Screenshot/video: <path/link or none>
- Jira: <link or none>
- Local docs: docs/ai/inputs/<file>.md or none

Constraints:
- Keep the patch minimal.
- Do not refactor unrelated code.
- Preserve existing behavior outside the repro path.

Please run Stage -1 audit first, then proceed through Stage 0-2 only.
Write a minimal bug requirements doc with repro, suspected surface area, and verification plan.
Stop for my approval before implementation.
```

---

## [H] XML To Compose Migration

```text
Start an XML to Jetpack Compose migration using the Android Agent Orchestrator flow.

Migration target:
- XML layout: <res/layout/file.xml>
- Fragment/Activity/View: <class name/path>
- Related ViewModel/state: <class name/path or unknown>

Current behavior:
<What this screen or component does today.>

Migration goal:
<What should be migrated and what should remain unchanged.>

Sources:
- Jira: <link or none>
- Design/Figma: <link or none>
- Local docs: docs/ai/inputs/<file>.md or none

Acceptance criteria:
- Visual behavior matches the current screen unless explicitly changed.
- Existing navigation, state, analytics, and accessibility behavior are preserved.
- <Additional criterion>

Constraints:
- Use existing theme/design system.
- Keep interoperability where a full migration is risky.
- Do not migrate unrelated screens.

Please run Stage -1 audit first, then proceed through Stage 0-2 only.
Write a migration requirements doc and stop for my approval before implementation.
```

---

## [I] AGP Or Build Modernization

```text
Start a build modernization task using the Android Agent Orchestrator flow.

Upgrade target:
<AGP/Kotlin/Gradle/dependency target version or goal>

Current problem:
<Why this upgrade is needed.>

Known constraints:
- <CI requirement>
- <Minimum Android Studio/JDK/Gradle requirement>
- <Release timeline or branch constraints>

Sources:
- Jira: <link or none>
- Internal doc: <link/path or none>
- Local docs: docs/ai/inputs/<file>.md or none

Acceptance criteria:
- Project sync/build succeeds.
- Existing test tasks still run or documented blockers are captured.
- No unrelated dependency upgrades are made.

Please run Stage -1 audit first, then proceed through Stage 0-2 only.
Write an upgrade plan with risks, affected build files, and verification commands.
Stop for my approval before implementation.
```

---

## [J] Unfamiliar Codebase + Raw Brief

```text
Start work on an unfamiliar Android codebase using the Android Agent Orchestrator flow.

Raw task brief:
<Describe the desired change, investigation, or outcome. Include all known facts.>

Known entry points:
- Module/package/screen: <path/name or unknown>
- Related files: <paths or unknown>
- Runtime flow: <known flow or unknown>

Sources:
- Jira: <link or none>
- Figma: <link or none>
- Confluence/spec: <link or none>
- Local docs: docs/ai/inputs/<file>.md or none

Questions I need answered before implementation:
- <question 1>
- <question 2>
- <question 3>

Constraints:
- Do not implement until the architecture surface and requirements are clear.
- Refresh Graphify only if approved.
- Stop if clarification outcome is blocked.

Please run Stage -1 audit first, then proceed through Stage 0-2 only.
Run full clarification if the brief is weak, sources conflict, or graph impact is unclear.
Write requirements after outcome=ready and stop for my approval.
```
