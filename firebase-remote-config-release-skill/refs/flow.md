# Firebase Remote Config Skill Flow

This is the standalone flow for RC work. Use it even when no Android Agent Orchestrator context exists.

## End-to-End Flow

```text
User task / ticket / PR / log / manifest
        |
        v
[0] Intake
    - task_type
    - environment_model: stg_prod | prod_only
    - project / source env / target env
    - changeset
    - authority level
    - sources available
    - auth/access readiness
        |
        v
[1] Context Discovery
    - requirements / ticket / design docs
    - app code or Graphify if provided
    - existing manifest / backup JSON / Firebase export
    - Jenkinsfile/log/PR if relevant
        |
        v
[2] RC State Analysis
    - current STG/PROD values
    - params and conditions in scope
    - default values
    - app id rewrite needs
    - rollout/QA exposure
        |
        v
[3] RC Design
    - intended behavior
    - param/rule/default changes
    - draft vs ready proposal
    - target env
    - validation evidence
    - rollback plan
        |
        v
Human confirmation or delegated approval?
        |
   +----+----+
   |         |
  no        yes
   |         |
   v         v
Stop    [4] Manifest Draft
        - generate/update manifest
        - default changed items to draft
        - preserve defaults unless approved
        |
        v
[5] Manifest Review
    - safety gates
    - blocking/warnings
    - draft/ready classification
    - safe-to-publish decision
        |
        v
Review passed?
        |
   +----+----+
   |         |
  no        yes
   |         |
   v         v
Fix    [6] Git Review Flow
        - push changeset branch or prepare PR content
        - review manifest
        - merge to stable/main after approval
        |
        v
[7] Validate Target
    - staging: validate/apply plan
    - production: validate-only required first
        |
        v
Explicit apply approval?
        |
   +----+----+
   |         |
  no        yes
   |         |
   v         v
Stop    [8] Apply / Rollback / Sync
        - execute only at approved permission level
        - capture backup/version/ETag
        |
        v
[9] Post-Apply Evidence
    - app/Firebase behavior verified
    - release/incident notes
    - rollback path remains available
```

## Output by Stage

| Stage | Artifact |
|---|---|
| Intake | Task classification |
| Context Discovery | Context summary |
| RC State Analysis | Parameter/condition inventory |
| RC Design | `templates/rc-design.md` |
| Manifest Draft | Manifest YAML |
| Manifest Review | `templates/manifest-review.md` |
| Git Review | PR summary/checklist |
| Validate Target | Validate-only evidence |
| Apply | Publish/rollback/sync evidence |

## Environment Model Detection

Use `stg_prod` when:
- both staging and production Firebase project ids exist,
- source env is staging and target env is production,
- STG/PROD backup JSON or export can be produced,
- the team expects QA in staging before production.

Use `prod_only` when:
- only production Firebase project id exists,
- no staging project is configured,
- user says the project has production only,
- changes must be designed directly against current production state.

If unclear, ask before manifest generation.

## STG + PROD Flow

```text
Requirement
→ read code/docs/Graphify if needed
→ inspect current STG
→ inspect current PROD
→ design RC change
→ apply/test on STG or use STG as source of truth
→ export STG vs PROD diff
→ generate manifest
→ manifest review
→ branch/PR review
→ merge stable/main
→ validate-only PROD
→ publish PROD after approval
→ verify + keep rollback evidence
```

Required evidence:
- STG behavior/evidence or explicit reason STG was not applied,
- STG/PROD diff or equivalent manifest source,
- manifest review,
- production validate-only result,
- backup path/version,
- rollback plan.

## PROD-Only Flow

```text
Requirement
→ read code/docs/Graphify if needed
→ export/backup current PROD
→ design RC change against PROD
→ generate manifest draft
→ manifest review
→ branch/PR review or equivalent approval
→ validate-only PROD
→ publish ready-only after approval
→ verify + keep rollback evidence
```

Default safety for `prod_only`:
- risk floor is `medium` for production mutation,
- do not claim `low` risk for publish/rollback,
- require current PROD backup before manifest apply,
- prefer small rollout or kill-switch behavior,
- require explicit approval for any `ready` item and production apply.

## Stop Points

Stop and ask when:
- target env/project is unclear,
- `environment_model` is unclear,
- required auth/access is missing for the requested operation,
- parameter/condition name is inferred but not confirmed,
- design changes default values,
- manifest touches production,
- manifest review has blocking findings,
- validate-only evidence is missing before production apply,
- rollback version/plan is missing for production mutation.
