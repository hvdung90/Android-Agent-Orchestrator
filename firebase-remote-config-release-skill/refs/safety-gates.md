# Safety Gates

## Blocking Findings

Block publish/apply when any of these are present:

- `qa_*` condition is used or created for production while QA conditions are not explicitly allowed.
- Default value changes without explicit requirement and approval.
- Parameter removal without explicit migration/rollback plan.
- Condition removal or reorder without reviewed blast radius.
- Missing condition expression for a condition that would be created.
- App id rewrite is missing, ambiguous, or maps production app id to staging app id for PROD.
- Manifest has invalid YAML/JSON values.
- Required item is still `draft` while publish command uses `--only-ready`.
- Target Firebase project id does not match requested environment.
- No backup path, version number, or rollback plan for production mutation.
- Validate-only failed or was not run before production publish.
- `prod_only` production mutation has no current PROD backup.
- Required access is missing for the requested operation.

## Warnings

Warn, but do not always block:

- New condition is `draft`.
- Reorder operation exists but `APPLY_REORDER=off`.
- `ALLOW_CREATE_CONDITIONS=true` is needed.
- `FILTER_BY_TICKET=true` expects a `.manifest.filter.yaml` not present in evidence.
- Manifest branch already exists.
- README/Jenkinsfile parameters differ.

## Risk Level

| Risk | Conditions |
|---|---|
| Low | Ready-only conditional value changes; no defaults/removals/reorder/new conditions |
| Medium | New conditions, app id rewrite, rollout condition changes, mapped conditions |
| High | PROD publish, default mutation, removals, condition reorder/removal, rollback/sync |

For `prod_only`, production mutation risk floor is `medium`. Escalate to `high` when default values, removals, condition reorder/removal, app id rewrite, rollback, or sync are involved.

## Production Mutation Requirements

Before any production publish/rollback:

- human approval,
- target project id confirmation,
- changeset confirmation,
- manifest commit/PR confirmation,
- validate-only success,
- backup path or rollback version,
- rollback plan,
- post-publish verification plan.

## Environment-Specific Gates

### STG + PROD

Require before production publish:
- STG evidence or explicit reason STG was skipped,
- STG/PROD diff or equivalent manifest source,
- app id rewrite review when STG and PROD app ids differ.

### PROD Only

Require before production publish:
- current PROD backup/export,
- manifest generated against current PROD,
- validate-only success,
- ready-only apply unless explicitly overridden,
- smaller rollout or kill switch when behavior affects users broadly,
- explicit acknowledgment that no staging verification exists.
