# Manifest Schema

Remote Config manifests in the current tooling are YAML files with this shape:

```yaml
changeSet: RC-1234
summary: Draft manifest generated from STG vs PROD diff
owner:
  dev: ""
  qa: ""
issue: ""
createdAt: "2026-05-09"
scope:
  allowParamPrefixes: []
  parameters: []
  conditions:
    ensureOnStg: []
    mapForProd: {}
conditionOps: []
changes: []
removals:
  state: draft
  paramRules: []
  parameters: []
meta:
  appIdRewrite:
    mode: auto
    stgDetected: []
    prodDetected: []
    stgUsed:
    prodUsed:
```

## Item States

- `draft`: not publishable by `--only-ready`; safe default for generated changes.
- `ready`: explicitly reviewed and approved for apply.
- Missing `state`: treat as `draft` during review.

## Common Operations

| Field | Meaning | Risk |
|---|---|---|
| `conditionOps.ADD_CONDITION` | Add a missing PROD condition | Medium/high |
| `conditionOps.REMOVE_CONDITION` | Remove condition from target | High |
| `conditionOps.REORDER` | Change condition priority | Medium/high |
| `changes[].rules[]` | Set conditional parameter value | Depends on parameter |
| `rules.when=__DEFAULT__` | Change default value | High unless explicitly required |
| `removals.paramRules` | Remove conditional value | Medium/high |
| `removals.parameters` | Remove parameter | High |
| `scope.conditions.mapForProd` | Map STG condition to PROD condition | Medium |
| `meta.appIdRewrite` | Rewrite app ids between envs | Medium/high |

## Manifest Generation Rules

- Default generated items to `draft`.
- Mark `ready` only when the user confirms the specific item or delegates approval.
- Do not mutate default values unless the requirement explicitly says to.
- Preserve `forbidDefaultMutation: true` unless default mutation is intentionally approved.
- Record app id rewrite source/destination in `meta.appIdRewrite`.
- Keep `scope.parameters` restricted to changed parameters.
