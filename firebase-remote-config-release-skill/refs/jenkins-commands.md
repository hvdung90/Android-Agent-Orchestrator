# Jenkins Commands and Repo Tooling

Use these as command plans. Do not trigger Jenkins or mutate Firebase unless permission level is `level_3_mutation` and confirmations are complete.

## Jenkins Modes

```text
MODE=EXPORT
MODE=PUBLISH
MODE=LIST_VERSIONS
MODE=ROLLBACK
MODE=SYNC_STG
```

## EXPORT Plan

```text
PROJECT=<Android_ChatSmith|Android_Alpha_GBA|Android_Alpha_IPTV|IOS_ChatSmith>
CHANGESET=<RC-ticket-or-slug>
MODE=EXPORT
FORCE_BRANCH=false
FILTER_BY_TICKET=false
```

Expected artifacts:
- `<CHANGESET>.manifest.yaml`
- `<CHANGESET>.stg.json`
- `<CHANGESET>.prod.json`
- branch `<CHANGESET>` in manifest repo
- PR into stable branch

## PUBLISH Validate Plan

```text
PROJECT=<project>
CHANGESET=<changeset>
MODE=PUBLISH
FILTER_BY_TICKET=false
ONLY_READY=true
ALLOW_CREATE_CONDITIONS=<true|false>
ALLOW_QA_CONDITIONS=false
PUBLISH_AFTER_VALIDATE=false
APPLY_REORDER=<off|ready|all>
```

Expected evidence:
- validate-only success,
- backup path,
- merged template path,
- diff summary.

## PUBLISH Apply Plan

Only after validate and approval:

```text
PROJECT=<project>
CHANGESET=<changeset>
MODE=PUBLISH
ONLY_READY=true
PUBLISH_AFTER_VALIDATE=true
ALLOW_QA_CONDITIONS=false
```

## LIST_VERSIONS

```text
PROJECT=<project>
MODE=LIST_VERSIONS
```

Equivalent script:

```bash
python3 rc_list_versions.py --project-id <prod_project_id> --page-size 50 --limit 100 --raw-json
```

## ROLLBACK

```text
PROJECT=<project>
MODE=ROLLBACK
ROLLBACK_VERSION=<versionNumber>
```

Equivalent script:

```bash
python3 rc_rollback.py --project-id <prod_project_id> --version <versionNumber>
```

## SYNC_STG

Syncs PROD RC state to STG. This overwrites STG — any active STG experiment or in-progress QA config will be lost.

**Safety requirements before running:**
- Confirm no active STG experiment or QA test is running.
- Export and backup current STG state before sync.
- Export and backup current PROD state before sync.
- Human explicitly approves overwrite of STG.
- Record pre-sync STG backup path.

```text
PROJECT=<project>
MODE=SYNC_STG
```

Equivalent script:

```bash
python3 rc_sync_prod_to_stg.py --prod-project-id <prod_project_id> --stg-project-id <stg_project_id>
```

Expected outcome:
- STG RC state matches PROD RC state at time of sync.
- Previous STG state is only recoverable from the backup captured before sync.

Risk: **Medium** — mutates STG; destroys active STG-only conditions/values not present in PROD.

## Known Jenkins Risks To Check

- Groovy interpolation inside `sh '''...'''` does not expand Jenkins/Groovy variables.
- README params may drift from Jenkinsfile params.
- `GITHUB_TOKEN` must be bound or globally available.
- `ONLY_READY`, `ALLOW_CREATE_CONDITIONS`, `ALLOW_QA_CONDITIONS`, `APPLY_REORDER` must exist before relying on them.
- Stable branch must match project config.
