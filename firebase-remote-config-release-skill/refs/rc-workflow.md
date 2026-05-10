# RC Workflow

## Task Types

| task_type | Meaning | Typical output |
|---|---|---|
| `rc_design` | Requirements to RC design | RC design + confirmation request |
| `rc_manifest` | Generate/update manifest | Manifest draft + review notes |
| `rc_review` | Review manifest or PR | Manifest review report |
| `rc_publish` | Plan/apply manifest | Publish checklist + command plan |
| `rc_rollback` | Recover bad RC publish | Rollback plan |
| `rc_sync_stg` | Sync PROD to STG (destructive STG overwrite) | Sync plan + STG backup + safety checks |
| `rc_debug` | Explain Jenkins/Firebase error | Cause + fix + retry plan |

## Requirements to Manifest Flow

1. Read requirement/ticket/design.
2. If available, read app code or Graphify to find:
   - RC parameter keys,
   - conditions referenced by app behavior,
   - default fallback behavior,
   - app id/package/bundle constraints,
   - rollout or QA exposure surfaces.
3. Read current RC state from staging or production, or use provided backup JSON/manifest.
4. Propose RC design:
   - parameter changes,
   - default values,
   - conditional rules,
   - draft/ready state,
   - target env,
   - validation and rollback evidence.
5. Stop for confirmation unless authority is explicitly delegated.
6. Generate manifest after confirmation.
7. Review manifest.
8. Prefer branch/PR review before apply.
9. Validate-only before publish.
10. Apply only after explicit approval for the target env.

## Standalone Operating Stages

### Stage 0 — Intake

Record:
- task type,
- environment model (`stg_prod | prod_only`),
- product/project,
- source env (`staging | production | backup | manifest | unknown`),
- target env (`staging | production | unknown`),
- changeset,
- manifest repo/branch/PR if present,
- authority level.
- access readiness (docs, manifest repo, Git push, Jenkins, Firebase read/write).

If target env is production and authority is not explicit, stop after planning/review.
If environment model is unclear, ask before manifest generation.

### Stage 1 — Understand Requirement and App Context

Read the task source first. Use code or Graphify only when needed to identify:
- RC parameter keys,
- conditions used by feature behavior,
- fallback/default behavior,
- app id/package/bundle boundaries,
- whether the change affects rollout, paywall, onboarding, experiments, auth, billing, or kill switches.

Do not infer parameter names silently. If names are not found in task/code/current RC state, ask.

### Stage 2 — Analyze RC State

For `stg_prod`, compare current STG and PROD whenever possible.

For `prod_only`, export/backup current PROD before any design is treated as actionable.

Use one of:
- provided manifest YAML,
- provided STG/PROD backup JSON,
- Firebase export/diff output,
- Jenkins EXPORT output,
- direct command plan using `diff-stg-pro.py`.

Classify each affected parameter:
- unchanged,
- conditional value change,
- default value change,
- new condition,
- condition reorder/remove,
- rule removal,
- parameter removal,
- app id rewrite.

### Stage 3 — Design and Confirm

Write `templates/rc-design.md`.

Design must answer:
- environment model,
- what behavior changes,
- which parameters/conditions change,
- whether defaults change,
- which items remain `draft`,
- which items can become `ready`,
- target environment,
- validation evidence,
- rollback plan.

Stop for confirmation unless delegated approval is explicit.

For `prod_only`, confirmation must explicitly acknowledge there is no staging verification and must approve the chosen rollout/rollback safeguards.

### Stage 4 — Manifest Draft

Generate or update manifest only after design confirmation.

Rules:
- new changes default to `draft`,
- `ready` requires explicit approval,
- default mutation requires explicit approval,
- qa conditions are blocked for production unless explicitly allowed,
- app id rewrite must be recorded in `meta.appIdRewrite`.

### Stage 5 — Manifest Review

Use `refs/review-checklist.md` and `refs/safety-gates.md`. Output `templates/manifest-review.md`.

Decision:
- `Safe to publish: No` if blocking findings exist.
- `Safe to publish: Yes` only if target/env/project are confirmed and safety gates pass.

### Stage 6 — Git Review

Preferred path:

```text
manifest draft → changeset branch → PR → review → merge stable/main → validate target → apply
```

If the user asks to skip PR review, require explicit confirmation and record the consequence.

### Stage 6.5 — SYNC_STG (when task_type = rc_sync_stg)

Run instead of Stages 4–7 when the only goal is to sync PROD to STG.

Before executing:
- confirm no active STG experiment or QA test is running,
- export and record current STG backup path,
- export and record current PROD backup path,
- require human approval of STG overwrite,
- load `refs/jenkins-commands.md § SYNC_STG`.

After executing:
- verify STG spot-check matches expected PROD state,
- record pre-sync STG backup path in evidence,
- record outcome: STG-only conditions/values that were overwritten.

### Stage 7 — Validate and Apply

For staging:
- manifest review required,
- target staging project confirmation required,
- rollback/sync note required.

For production:
- manifest review required,
- validate-only success required,
- backup path or rollback version required,
- rollback plan required,
- human approval required.

For prod-only production:
- current PROD backup required before apply,
- risk floor is medium,
- ready-only publish is preferred,
- small rollout or kill-switch behavior is preferred,
- post-publish verification is mandatory.

### Stage D — Debug (when task_type = rc_debug)

Run when task is to diagnose a Jenkins or Firebase RC error. Skip Stages 1–7.

Steps:
1. Read provided log text, screenshot, or error message.
2. Identify: error code, pipeline stage of failure, parameters/conditions involved.
3. Map signal to likely cause using `refs/review-checklist.md § Jenkins / Log Debug Signals`.
4. Explain root cause in plain language.
5. Produce fix plan at current permission level.
6. If fix requires re-publish: produce command plan from `refs/jenkins-commands.md`.
7. If partial publish occurred: escalate to `rc_rollback` flow before retry.
8. Confirm no additional mutation is needed beyond the fix.

Output: diagnosis note + fix plan. No manifest generated unless the fix requires one.

## Multi-Task Classification

When a single request spans multiple task types (e.g. "update the RC for feature X and publish to production"):

Run task types sequentially in this order:

```
rc_design → rc_manifest → rc_review → rc_publish
```

Complete each stage and its required stop/approval before starting the next. Do not skip ahead. Record combined output in `templates/rc-release-report.md`.

Exception: `rc_debug` and `rc_rollback` are always run immediately regardless of other in-progress task types. Diagnosis and incident recovery take priority.

## Git Review Flow

Use the current RC repo workflow as an implementation option, not as the only source of truth:

```text
EXPORT/design → manifest branch → PR review → merge stable/main → PUBLISH validate-only → apply with approval
```

If manifest was generated outside Jenkins, still require PR review or equivalent human review before production apply.
