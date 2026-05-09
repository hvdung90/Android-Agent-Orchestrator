# STG + PROD RC Checklist

Environment model: stg_prod
Project: Android_ChatSmith
Source env: staging
Target env: production
Changeset: RC-1234

## Required Before Publish

- [ ] STG behavior tested or skip reason recorded.
- [ ] STG export captured.
- [ ] PROD export/backup captured.
- [ ] STG vs PROD diff reviewed.
- [ ] Manifest review has no blocking findings.
- [ ] App id rewrite reviewed.
- [ ] PR reviewed and merged.
- [ ] PROD validate-only succeeded.
- [ ] Rollback plan ready.
- [ ] Human approval recorded.
