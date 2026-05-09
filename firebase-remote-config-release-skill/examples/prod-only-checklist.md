# PROD-Only RC Checklist

Environment model: prod_only
Project: Android_ChatSmith
Target env: production
Changeset: RC-1234

## Required Before Publish

- [ ] Current PROD export/backup captured.
- [ ] Manifest generated against current PROD.
- [ ] Manifest review has no blocking findings.
- [ ] Validate-only succeeded.
- [ ] `ONLY_READY=true`.
- [ ] No default mutation unless explicitly approved.
- [ ] Rollback version or backup path recorded.
- [ ] Human acknowledges no staging verification exists.
- [ ] Post-publish verification owner assigned.

Risk floor: Medium
