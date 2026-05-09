# Rollback Playbook

Use for bad publish, wrong values, rollout incident, or requested rollback.

## Steps

1. Stop further publishes for the same project/changeset.
2. Identify affected Firebase project id and environment.
3. Run or request `LIST_VERSIONS`.
4. Pick the version immediately before the bad publish.
5. Confirm target version with human.
6. Run or plan `ROLLBACK` with that `versionNumber`.
7. Capture returned ETag and verify Firebase console/app behavior.
8. Record incident notes:
   - bad version,
   - rollback version,
   - time,
   - actor,
   - affected parameters/conditions,
   - verification evidence.

## Rollback Approval

Rollback production is a production mutation. Require:
- target project id,
- rollback version number,
- reason,
- expected restored behavior,
- human approval.

## Common Errors

| Error | Meaning | Response |
|---|---|---|
| Missing `ROLLBACK_VERSION` | Jenkins/script cannot choose target | Run/list versions first |
| 403/401 | GCP credential issue | Check service account and scopes |
| 404 project/version | Wrong project id or version | Re-run LIST_VERSIONS for target project |
| API 5xx/timeout | Firebase transient | Retry only after checking no partial success |
