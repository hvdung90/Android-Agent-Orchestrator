# Review Checklist

Use this for manifest PRs, generated manifests, or pre-publish checks.

## Required Checks

- [ ] `changeSet` matches ticket/branch.
- [ ] Target project/environment is confirmed.
- [ ] All publishable items are `ready`; unreviewed items remain `draft`.
- [ ] No `qa_*` condition is used on production unless explicitly allowed.
- [ ] No default value mutation unless explicitly required.
- [ ] No parameter removal without rollback/migration plan.
- [ ] Condition add/remove/reorder reviewed for priority and blast radius.
- [ ] JSON values parse when value type is JSON.
- [ ] App id rewrite maps STG app ids to PROD app ids for production.
- [ ] `scope.parameters` includes only intended parameters.
- [ ] `mapForProd` is explicit for STG-only conditions.
- [ ] Validate-only result is present before production publish.
- [ ] Backup path or rollback version is present.
- [ ] Rollback plan exists.

## Jenkins / Log Debug Signals

| Signal | Likely cause |
|---|---|
| `412` / ETag mismatch | PROD changed since fetch; refetch/revalidate |
| `Refusing to use qa_*` | QA condition blocked for PROD |
| `Missing expression to create condition` | Manifest lacks condition definition |
| `manifest missing` | Wrong branch, changeset, filter flag, or file path |
| `manifest root must be a mapping` | Invalid YAML root |
| `Failed to fetch RC` | Firebase project id/auth/scope issue |
| PR creation failed | Existing PR, branch conflict, token permission |
