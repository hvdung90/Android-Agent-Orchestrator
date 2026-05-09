# RC Publish Checklist

Project:
Environment model: stg_prod | prod_only
Target env:
Changeset:
Manifest:
Branch / PR:

## Before Apply

- [ ] Requirements/design confirmed.
- [ ] Access readiness checked for requested operation.
- [ ] Manifest review passed.
- [ ] PR reviewed and merged or equivalent approval recorded.
- [ ] Target Firebase project id confirmed.
- [ ] `ONLY_READY=true` unless explicitly approved otherwise.
- [ ] `ALLOW_QA_CONDITIONS=false` for production unless approved.
- [ ] Validate-only succeeded.
- [ ] Backup path captured.
- [ ] Rollback plan prepared.
- [ ] Human approval recorded.

## Environment-Specific

- [ ] STG + PROD: staging evidence or explicit skip reason recorded.
- [ ] STG + PROD: STG/PROD diff or equivalent source recorded.
- [ ] PROD only: current PROD backup/export captured.
- [ ] PROD only: no-staging risk acknowledged.
- [ ] PROD only: ready-only or explicit override recorded.

## Command Plan

```text
MODE=PUBLISH
PROJECT=
CHANGESET=
PUBLISH_AFTER_VALIDATE=false
```

After validate:

```text
MODE=PUBLISH
PROJECT=
CHANGESET=
PUBLISH_AFTER_VALIDATE=true
```

## Post Apply

- [ ] Published ETag/version captured.
- [ ] App/Firebase behavior verified.
- [ ] Incident/release note updated.
