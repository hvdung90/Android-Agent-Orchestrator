# RC Manifest Review

Manifest: RC-1234.manifest.yaml
Project: Android_ChatSmith
Target env: production
Changeset: RC-1234
Risk: Medium

## Blocking

- None.

## Warnings

- New condition `rollout_10_percent` is `draft`; it will not publish with `ONLY_READY=true`.

## Checks

- [x] condition_added
- [ ] condition_removed
- [ ] condition_reordered
- [ ] default_value_changed
- [ ] qa_condition_on_prod
- [ ] app_id_rewrite
- [ ] parameter_removed
- [x] rollout_condition_changed
- [x] json_value_valid
- [ ] only_ready_safe

## Draft / Ready Classification

| Item | Current state | Recommendation | Reason |
|---|---|---|---|
| ADD-rollout_10_percent | draft | keep draft until reviewed | New PROD condition |
| R-1 paywall_config rollout_10_percent | draft | ready after QA signoff | Conditional value only |

Safe to publish: No

Required action: approve and mark intended items as `ready`, then run validate-only.
