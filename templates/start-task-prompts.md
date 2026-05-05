# Start Task Prompt Templates

Copy one template, fill the placeholders, then send it to the agent.

Rule of thumb:
- Keep the first prompt focused on requirements and source discovery.
- Ask the agent to stop after Stage 2 unless the task is tiny and already approved.
- Put long notes in `docs/ai/inputs/<task>.md` and link that file in the prompt.

---

## 1. New Feature

```text
Start a new feature using the Android Agent Orchestrator flow.

Feature: <feature name>

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

## 2. Edit Existing Feature

```text
Start an existing-feature change using the Android Agent Orchestrator flow.

Feature area: <existing feature/module/screen>

Current behavior:
<What the app does today.>

Requested change:
<What should change.>

Sources:
- Jira: <link or none>
- Figma: <link or none>
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

## 3. Bug Fix

```text
Start a bug investigation using the Android Agent Orchestrator flow.

Bug: <short title>

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

Constraints:
- Keep the patch minimal.
- Do not refactor unrelated code.
- Preserve existing behavior outside the repro path.

Please run Stage -1 audit first, then proceed through Stage 0-2 only.
Write a minimal bug requirements doc with repro, suspected surface area, and verification plan.
Stop for my approval before implementation.
```

---

## 4. XML To Compose Migration

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

## 5. AGP Or Build Upgrade

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
- Internal doc: <link/path or none>
- Issue: <link or none>

Acceptance criteria:
- Project sync/build succeeds.
- Existing test tasks still run or documented blockers are captured.
- No unrelated dependency upgrades are made.

Please run Stage -1 audit first, then proceed through Stage 0-2 only.
Write an upgrade plan with risks, affected build files, and verification commands.
Stop for my approval before implementation.
```

---

## 6. Tooling Setup

```text
Set up agents for this repo using Android Agent Orchestrator bootstrap mode.

Goal:
Prepare the repo for future Android tasks.

Please run Stage -1 in bootstrap mode.
Create `.agent-auth.yaml` if missing, but do not print token values.
Install or initialize missing tools only when approval is required and granted.
Write `.project-orchestration/reports/preflight.md`.
Stop after reporting readiness and blockers.
```

---

## 7. Architecture Analysis

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

Please run Stage -1 audit first.
Read Graphify output if available.
Do not modify product code.
Return findings, risks, and recommended next steps.
```

