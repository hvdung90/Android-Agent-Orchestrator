# Changelog

## v4.2.8 — Doc sync

### Changed (doc-only, no behavior change)

- `SKILL.md`: version → 4.2.7; description updated; TL;DR rewritten; "What changed" table đầy đủ v4.2.0–4.2.7; hard rule #14 (auth); Minimal operating algorithm 11 bước có auth; directory layout thêm `.agent-auth.yaml`.
- `README.md`: version → 4.2.7; file map thêm `refs/auth-bootstrap.md` + `templates/agent-auth.example.yaml`; What changed → table format.
- `templates/preflight-report.md`: thêm section `## Auth`.
- `examples/preflight-report.example.md`: thêm section `## Auth` với dữ liệu mẫu thực tế; thêm "Tokens to request" vào Decisions.
- `refs/contracts-and-artifacts.md`: version → 4.2.7; Gate -1 thêm auth init requirement; preflight schema thêm `## Auth`; context-pack thêm `auth_status` field.
- `refs/sub-agents.md`, `refs/provisioning-preflight.md`, `refs/playbooks.md`, `refs/clarification-workflow.md`: version → 4.2.7.
- `docs/FLOW.md`: version header → 4.2.7.

---

## v4.2.7

### Added

- `refs/auth-bootstrap.md`: file ref mới — nguồn sự thật duy nhất cho auth management.
  - Bước 1: khởi tạo file auth tại Stage -1 (auto-create nếu chưa có).
  - Bước 2: just-in-time token check per tool (Jira, Confluence, Figma, GitHub) — hỏi user khi thiếu, lưu vào file.
  - Bước 3: credential resolution (Level 1/2/3) theo project key prefix.
  - Bước 4: lưu token an toàn, không log ra màn hình hay report.
  - MCP mapping table: token nào dùng cho MCP tool nào.

### Changed

- `templates/agent-auth.example.yaml`: thêm MCP provider comment cho từng tool; bỏ hướng dẫn copy thủ công (skill tự tạo file).
- `refs/provisioning-preflight.md`: thay auth check section bằng reference sang `refs/auth-bootstrap.md`; just-in-time model rõ ràng.
- `refs/sub-agents.md`: thêm `Required auth` cho Jira Reader, Confluence Reader, Figma Reader.
- `refs/clarification-workflow.md`: thay credential resolution inline bằng reference sang `refs/auth-bootstrap.md`.
- `SKILL.md`: thêm `refs/auth-bootstrap.md` vào metadata refs; Stage -1 load auth-bootstrap Bước 1 ngay đầu.
- `docs/FLOW.md`: Stage -1 thêm Auth init block; Stage 0 cập nhật credential resolution just-in-time.

---

## v4.2.6

### Changed

- `docs/FLOW.md`: rewrite hoàn toàn phản ánh v4.2.5.
  - Section 2 (Stage -1): thêm check ⑥ auth vào parallel checks; tách nhánh [A-D] done vs [E-J] continue.
  - Section 3 (Stage 0): thêm credential resolution step trước khi fetch link.
  - Section 4 (Stage 1): fix diagram auto-follow; gộp Mode A + Mode B vào cùng parallel block.
  - Section 7 (Auth): diagram mới thể hiện Level 1/2/3 + resolve flow.
  - Section 8 (Playbooks): thêm auth check vào tất cả playbook flows.
  - Section 9 (Worker matrix): thêm dòng `auto-follow` cho Jira Reader.
  - Section 12 (Hard stops): tách 8 điểm stop rõ ràng, thêm WARN cho auth missing.

---

## v4.2.5

### Added

- `.gitignore`: covers `.agent-auth.yaml`, `.DS_Store`, and agent runtime output dirs.
- `templates/agent-auth.example.yaml`: auth config template với 3 cấp:
  - **Level 1** workspace (default Jira project prefix)
  - **Level 2** tool credentials (Atlassian, Figma, GitHub)
  - **Level 3** per-project overrides (nhiều Atlassian instance)
- `refs/provisioning-preflight.md`: auth credentials check tại Stage -1 — detect `.agent-auth.yaml`, record trong preflight report, warn nếu thiếu khi có external links.
- `refs/clarification-workflow.md`: credential resolution rule — match ticket key prefix với `projects[]` override trước khi dùng top-level credentials.
- `docs/FLOW.md`: thêm check ⑥ `.agent-auth.yaml` vào Stage -1 parallel checks.

---

## v4.2.4

### Changed

- `refs/sub-agents.md` Jira Reader: added **auto-follow rule** — after reading a ticket, immediately fetch all `linked_docs` and `linked_designs` using the matching reader (Confluence Reader, Figma Reader, Doc Reader, or Jira Reader). One level deep only.
- `refs/clarification-workflow.md` Jira section: added auto-follow note inline.
- `docs/FLOW.md` Stage 1: updated Discovery diagram to show auto-follow branch.

---

## v4.2.3

### Added

- `docs/FLOW.md`: complete ASCII flow diagram covering all use cases.
  - Entry point decision tree (10 task types)
  - Stage -1 provisioning mode selection
  - Stage 0 source mode derivation (A/B/C)
  - Stage 1.5 clarification with worker activation per mode
  - Clarity score → outcome mapping
  - All 10 playbook flows (A–J)
  - Source mode × worker activation matrix
  - Graphify trigger map per stage
  - Parallel vs serial rule summary
  - Hard stop points list
- `README.md`: added `docs/FLOW.md` to file map.

---

## v4.2.2

### Added

- `refs/clarification-workflow.md`: **Source integrations** section.
  - Jira, Figma, Confluence are **link-driven** — no upfront config required.
  - Agent activates source readers only when developer provides a link.
  - Source mode derivation table (A / B / C) based on what developer provides.
- `SKILL.md` Stage 0: intake records developer-provided links and derives source mode.

---

## v4.2.1

### Changed

- README.md slimmed to human-facing overview only; removed content duplicated from SKILL.md.
- SKILL.md: added explicit `→ Load refs/<file>.md` instructions per stage — agent no longer has to guess when to load which ref.
- SKILL.md: added Sub-agents summary table with link to `refs/sub-agents.md`.
- SKILL.md: Stage 1.5 trigger replaced with binary checklist (6 measurable conditions).
- SKILL.md: Mode C now has an escape hatch for clearly bounded single-file tasks (treat as Mode B).
- All `refs/*.md` files now carry a `Skill version` line for drift detection.
- `README_4.1.md` archived to `docs/archive/README_4.1.md`.

---

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
