---
name: firebase-remote-config-release-skill
description: Review, design, plan, and safely operate Firebase Remote Config releases. Use when tasks mention Firebase Remote Config, RC manifest YAML, STG vs PROD diff, config rollout, config publish, staging or production Remote Config, Jenkins RC pipeline logs, manifest PR review, ready/draft rule classification, qa_* condition safety, default value mutation, app id rewrite, LIST_VERSIONS, ROLLBACK, SYNC_STG, or production Remote Config release/rollback planning.
metadata:
  version: 1.0.0
---

# Firebase Remote Config Release Skill

## Core Principle

Treat Remote Config as production behavior. Read requirements and app context first, design the intended config change, generate a manifest, review it, validate it, and only then apply to a target environment with explicit approval.

Never publish, rollback, or sync RC by default. Production mutation requires human approval and confirmed target project, changeset, manifest, backup, and rollback plan.

This skill is standalone. It can use app code, Graphify output, Jenkins logs, GitHub PRs, Firebase backups, or manifests when provided, but it does not depend on Android Agent Orchestrator.

## Load Refs

Load only what the task needs:

| Need | Load |
|---|---|
| Start any RC task | `refs/flow.md`, `refs/rc-workflow.md`, `refs/auth-and-access.md` |
| Create/review manifest | `refs/manifest-schema.md`, `refs/safety-gates.md`, `refs/review-checklist.md` |
| Jenkins command/log help | `refs/jenkins-commands.md` |
| Rollback/incident | `refs/rollback-playbook.md`, `refs/jenkins-commands.md` |
| SYNC_STG | `refs/jenkins-commands.md § SYNC_STG`, `refs/flow.md § SYNC_STG Flow` |
| Debug Jenkins/Firebase error | `refs/review-checklist.md § Jenkins / Log Debug Signals`, `refs/flow.md § Debug Flow` |

Use templates from `templates/` for reports/checklists.

`examples/` contains concrete filled-in references:
- `sample-manifest.yaml` — shape reference for manifest YAML structure.
- `sample-review.md` — shape reference for a completed manifest review.
- `stg-prod-checklist.md` — actionable pre-publish checklist for `stg_prod` tasks.
- `prod-only-checklist.md` — actionable pre-publish checklist for `prod_only` tasks.

`agents/openai.yaml` defines the display name and default prompt for when this skill is surfaced as a chat agent interface (e.g. OpenAI GPT action or similar). It is not required for CLI/agent use.

## Workflow

1. **Intake and source discovery**
   - Classify task: `rc_design`, `rc_manifest`, `rc_review`, `rc_publish`, `rc_rollback`, `rc_sync_stg`, `rc_debug`. If the task spans multiple types, run them sequentially in order: design → manifest → review → publish. `rc_debug` and `rc_rollback` always take immediate priority. See `refs/rc-workflow.md § Multi-Task Classification`.
   - Identify `environment_model` (`stg_prod | prod_only`), project, source env, target env, changeset, ticket/PR/log links, manifest path, and authorization level.
   - Check required access for the task using `refs/auth-and-access.md`. If a local auth file is needed, follow the `.rc-agent-auth.yaml` structure defined there. Never request secrets unless the current operation requires them.
   - Read app requirements/ticket/design docs. If available, read code or Graphify to identify parameter names, conditions, feature flags, app ids, and rollout surfaces.

2. **RC state analysis**
   - For `stg_prod`, prefer STG as the tested source and PROD as the release target.
   - For `prod_only`, export/backup current PROD first and treat risk as at least medium for any production mutation.
   - Use existing repo tooling as reference or command plan:
     - `diff-stg-pro.py` for STG vs PROD export/diff/manifest draft.
     - `rc_publish_from_manifest.py` for validate/publish from manifest.
     - `rc_list_versions.py` and `rc_rollback.py` for rollback.
     - `rc_sync_prod_to_stg.py` for PROD to STG sync.
   - Compare desired behavior against current RC state from staging or production.

3. **Design before manifest**
   - Produce a short design: parameters, default behavior, conditional rules, rollout/QA conditions, app id rewrite needs, target env, validation evidence, rollback plan.
   - Stop for human confirmation unless authority has been explicitly delegated.

4. **Generate or update manifest**
   - Output manifest changes only after design is confirmed.
   - Default every new/changed rule to `draft` unless the user explicitly approves `ready`.
   - Preserve default values unless the requirement explicitly calls for default mutation.

5. **Review manifest**
   - Run RC safety gates before merge or publish.
   - Emit `RC Manifest Review` with risk, blocking findings, warnings, safe-to-publish decision, and required actions.
   - If risk is high or blocking findings exist, do not provide publish steps as executable instructions; provide remediation first.

6. **Review branch and apply**
   - Prefer Git review flow: push manifest to a changeset branch, open/review PR, merge to stable/main branch, then validate and apply.
   - For staging apply: require manifest review and target confirmation.
   - For production apply: require manifest review, validate-only result, backup path, rollback plan, and explicit human approval.

## Permission Levels

| Level | Allowed |
|---|---|
| `level_1_readonly` | Read manifest/Jenkinsfile/PR/logs/backup JSON; analyze RC state; generate review report |
| `level_2_prepare` | Generate manifest draft, suggest draft/ready changes, publish checklist, rollback plan |
| `level_3_mutation` | Trigger Jenkins publish, update manifest repo, rollback PROD, sync PROD to STG |

For `level_3_mutation`, require all confirmations:
- target Firebase project id,
- source and target env,
- changeset,
- manifest path and commit/PR,
- backup path or version number,
- rollback plan,
- explicit human approval.

If required credentials or repo access are missing, stop at the highest safe level and output the missing-access checklist from `refs/auth-and-access.md`.

## Outputs

Use the closest template:
- `templates/rc-design.md` for requirements-to-design.
- `templates/rc-release-report.md` for end-to-end planning.
- `templates/manifest-review.md` for PR/manifest review.
- `templates/publish-checklist.md` before staging/prod apply.
- `examples/stg-prod-checklist.md` as a ready-to-fill checklist for `stg_prod` pre-publish.
- `examples/prod-only-checklist.md` as a ready-to-fill checklist for `prod_only` pre-publish.

Final answer must state:
- task type,
- target env/project,
- risk level,
- safe-to-publish status,
- blockers,
- evidence present/missing,
- next command plan or why commands are blocked.
