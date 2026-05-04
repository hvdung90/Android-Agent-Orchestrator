# Changelog

## v4.2.0

### Added

- Stage -1 Tooling Preflight before Stage 0 Intake.
- Provisioning modes: `audit`, `bootstrap`, `update`, `refresh-graph`, `force-reinstall`.
- Install/update decision rules for AI DevKit, Android CLI, Android skills, Graphify, and Karpathy guidelines.
- `refs/provisioning-preflight.md`.
- `templates/preflight-report.md`.
- `templates/tooling-preflight.sh`.
- `examples/preflight-report.example.md`.
- Preflight artifact contract for `.project-orchestration/reports/preflight.md`.
- Graphify freshness policy.

### Changed

- README updated to v4.2.
- SKILL metadata updated to `4.2.0`.
- Stage model now starts with Tooling Preflight.
- Playbooks now include provisioning mode and preflight requirements.
- Contracts now include Gate -1.

### Safety

- Default provisioning mode is `audit`.
- No install/update/reinstall/rebuild unless explicitly requested.
- Existing `CLAUDE.md` must not be overwritten silently.
- Android skill names must not be guessed.
- `graphify-out/**` must never be hand-edited.
