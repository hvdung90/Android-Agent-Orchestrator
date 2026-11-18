# Android Agent Orchestrator — Engineering Review & Improvement Backlog

> **Vulcanlabs Android Team | 2026-11-18 | Review v1.0**  
> Repository: https://github.com/hvdung90/Android-Agent-Orchestrator  
> Phạm vi: review tĩnh tài liệu, skill, stage contracts, policy và orchestration design trên nhánh `main` ở thời điểm đọc. **Chưa chạy end-to-end task trên Android codebase**; mọi nhận định về performance, token, race, runtime được ghi là giả thuyết/rủi ro, không phải bug đã tái hiện.

## 1. Executive summary

**Khuyến nghị: giữ Android-Agent-Orchestrator làm nền tảng nội bộ, nhưng phát triển theo hướng VADW Lite (adaptive, evidence-first, tool-agnostic) trước khi rollout toàn bộ Android team.**

Repository có các điểm mạnh đáng bảo tồn: (1) một code owner duy nhất, sub-agent advisory; (2) review requirement và ADR trước thay đổi rủi ro cao; (3) architecture discovery/impact graph; (4) deterministic evidence từ build/test; (5) handoff, resume và state reconciliation; (6) team coordination/cross-repo decisions. Điểm nghẽn chính là **quá nhiều gate và artifact bắt buộc ngay cả với ticket nhỏ**. Ngoài ra cần xử lý credential storage, độ tin cậy của team visibility, file locks, nhất quán schema/version và tính đúng của state khi resume.

**Phân loại đánh giá:**
- **Confirmed inconsistency:** mâu thuẫn hoặc tình trạng không đồng bộ nhìn thấy trực tiếp trong các file.
- **Design risk:** hệ quả có thể xảy ra từ kiến trúc hiện tại, chưa được tái hiện trên runtime.
- **Validation gap:** thiếu test/benchmark để xác nhận hành vi hoặc lợi ích.

Không nên coi điểm số hoặc tỷ lệ cải thiện trong tài liệu này là benchmark thực tế.

## 2. Những phần nên giữ

| Thành phần | Lý do | Khuyến nghị |
|---|---|---|
| One code owner, advisory workers | Giảm sửa trùng và xung đột agent | **Giữ** |
| Canonical requirement + acceptance criteria | Hạn chế code sai định nghĩa | **Giữ; điều kiện hóa approval theo risk** |
| ADR global ledger | Giữ dấu vết architectural decisions/cross-repo impact | **Giữ cho thay đổi có ADR trigger** |
| Architecture map + Gradle impact | Phù hợp Android multi-module codebase | **Giữ; truy xuất theo nhu cầu** |
| Evidence matrix | Tránh AI tuyên bố PASS khi chưa chạy | **Giữ; phụ thuộc change type** |
| Resume integrity reconciliation | Không tin `session.json` một cách mù quáng | **Giữ và test kỹ** |
| Handoff snapshot | Hữu ích khi đổi dev/model/session | **Giữ; giảm trùng lặp artifact** |
| Tooling preflight audit-only | Hạn chế tự động cài đặt trái ý | **Giữ; làm deterministic** |

## 3. Findings theo mức độ ưu tiên

### AOO-001 — [P0][Design risk] Quá nhiều mandatory gates cho `micro` / `fast`

**Evidence:** `SKILL.md` phần *Workflow Modes*, *Hard rules*, *Stage model*; `refs/compliance-policy.md` phần *Stage compliance matrix*; `refs/contracts-and-artifacts.md` phần *Artifact budget*. Trong `micro` vẫn bắt buộc Stage -1 → 7, requirements approval, ADR trigger check, E.5 RED evidence, Evidence Gate Matrix, diff review, session/status và finalization; plan 1 task vẫn bắt buộc.

**Impact:** Lượng quyết định, đọc policy, ghi status/skip-log và human interaction có thể lớn hơn thời gian sửa bug đơn giản; có nguy cơ giảm adoption và tăng token.

**Remediation:** Tạo `FAST PATH` thật sự: classify → inspect affected code → minimal change → targeted verify → PR. Với ticket đã có approved AC thì không thêm một human approval độc lập. `micro` là submode tự động của FAST, không phải lifecycle đầy đủ. Giữ escalations cho API/DB/Billing/OAuth/security, architecture, unclear AC.

**Acceptance:** ticket UI/resource đơn giản hoàn thành không cần tạo requirements/design/handoff riêng; vẫn có summary, targeted evidence và PR; benchmark thời gian + token cho ít nhất 5 tickets tương đương.

### AOO-002 — [P0][Security design risk] Central plaintext credentials `.agent-auth.yaml`

**Evidence:** `refs/auth-bootstrap.md` nói `.agent-auth.yaml` là single source of truth cho Jira/Figma/API tokens và copy từ `templates/agent-auth.example.yaml`; `SKILL.md` hard rule #1. File gitignored nhưng vẫn là plaintext.

**Impact:** Lộ secrets qua local backups, file permissions, accidental context ingestion hoặc các tools/agents có quyền đọc file. `gitignore` chỉ ngăn commit thông thường, không phải secret store.

**Remediation:** Dùng OS Keychain/credential store, OAuth hoặc integration gốc khi khả thi; chỉ inject secrets lúc sử dụng; không đổ secret vào prompt/log. Nếu cần file local, chỉ lưu reference/key names, giảm quyền `chmod 600`, scan/pre-commit secret detector và document rotation.

**Acceptance:** no persisted plaintext credentials by default; verify no secret leakage in preflight reports, AI context, git diff và logs; test missing/revoked token behavior.

### AOO-003 — [P0][Validation gap] Chưa có end-to-end compatibility & correctness test cho orchestration

**Evidence:** repo là instruction pack, không phải executable CLI (`README.md`). Các stage contracts và evidence gates mô tả hành vi agent, nhưng review này chưa có execution proof khi chạy với project thực tế/multiple AI agents.

**Impact:** Agent có thể skip gate sai, ghi state không nhất quán, báo test pass thiếu evidence hoặc lặp đọc references.

**Remediation:** Bổ sung test fixture/simulation cho 4 modes, 3 change types, interrupted/resume flows và validation scripts cho JSON/artifact schemas; chạy pilot thật.

**Acceptance:** có automated contract checks + recorded end-to-end transcripts/artifacts cho FAST, STANDARD, GOVERNED; báo cáo pass/fail công khai trong repo.

### AOO-004 — [P1][Confirmed inconsistency] Version drift trong cùng repository

**Evidence:** tại thời điểm review, `README.md` và heading `SKILL.md` ghi `6.1.1` trong khi frontmatter `SKILL.md` và `refs/stage-contracts.md` ghi `6.1.3`.

**Impact:** Developer và agent không biết semantics/version nào chính xác; khó điều tra behavior change hoặc support.

**Remediation:** Single version source (manifest hoặc frontmatter), generate/sync docs và kiểm tra bằng CI.

**Acceptance:** một lệnh CI fail khi version khác nhau; README, changelog, metadata, refs đồng bộ với release tag.

### AOO-005 — [P1][Design risk] Local `status.json` không phải shared dashboard

**Evidence:** `README.md` trình bày `.project-orchestration/status.json` như task dashboard; đồng thời `.project-orchestration/` được gitignore. `refs/team-docs.md` có coordination mode dùng repo docs riêng.

**Impact:** Dev B/Tech Lead/PM không mặc nhiên xem được trạng thái local Dev A; dễ có hai nguồn trạng thái (local và shared) lệch nhau.

**Remediation:** Define single shared source of truth: Jira Issue + GitHub PR/CI. Local JSON chỉ dùng resume/cache. Đồng bộ state qua explicit events/webhook, có reconciliation và timestamp.

**Acceptance:** xem được assignee, phase, blocker, PR, verification từ một shared view; khi local state mất vẫn khôi phục được từ PR/Jira; không cần đồng bộ bằng tay.

### AOO-006 — [P1][Concurrency design risk] File lock qua Git chưa atomic

**Evidence:** `refs/team-docs.md` định nghĩa `locks.json` với `planning|locked`, `git pull --rebase`, `git push`, stale threshold và earliest `locked_at` tiebreak. Tài liệu có xử lý race window nhưng lock không phải transaction atomic.

**Impact:** 2 dev có thể lock chồng, mất update hoặc bị block sai khi cùng file nhưng branch thay đổi độc lập; lock orphan nếu task bị bỏ dở.

**Remediation:** Mặc định advisory file-conflict warning, không hard-stop. Chỉ hard lock các shared/release resources đặc biệt. Nếu cần exclusive ownership: use transactional backend/API, lock lease/heartbeat, compare-and-swap và explicit release.

**Acceptance:** concurrency test với 2–3 dev tasks chạy đồng thời không mất lock; stale/orphan recovery; branch-independent edits không bị chặn không cần thiết.

### AOO-007 — [P1][Policy overhead] Universal RED/GREEN TDD evidence

**Evidence:** `README.md` nói TDD per task “no exceptions”; `refs/contracts-and-artifacts.md` Gate E.5 yêu cầu failing test trước product code; exemption cần human confirm/skip-log; `refs/compliance-policy.md` yêu cầu mandatory RED/GREEN.

**Impact:** Hợp lý cho behavior changes nhưng có thể tạo artificial failing tests hoặc overhead cho resource/XML/text/build config changes. Wording “no exceptions” xung đột nhẹ với explicit exemption policy (tài liệu không thể hiện cùng sắc thái).

**Remediation:** TDD mandatory theo risk/change type: logic/Billing/security/coroutine behavior → RED/GREEN; UI/resource-only → screenshot/UI test/manual evidence; config/migration → validation/smoke + rollback. Bất kỳ ngoại lệ nào vẫn yêu cầu evidence, không tự khai PASS.

**Acceptance:** evidence policy matrix rõ change type; 3 task samples có correct verification pathway; không bắt tạo test giả.

### AOO-008 — [P1][State correctness risk] Substage 1.5 biểu diễn bởi `stage_reached: 1`

**Evidence:** `refs/stage-contracts.md` phần Stage 1.5 đặt `stage_reached: 1`, `stage_status: complete`; resume logic nhấn mạnh reconciliation stages, Stage 2.5 được coi là stage riêng.

**Impact:** Nếu process crash giữa discovery/clarification, stage number đơn lẻ không đủ biểu diễn vị trí chính xác; có thể duplicate hoặc bỏ qua work nếu artifact/skip state không hòa giải đầy đủ.

**Remediation:** explicit `stage_id` enum (`discovery`, `clarification`, `requirements`, `adr_gate`…), `phase_status` và `checkpoint_version`; idempotent resume; validate artifact hashes/mtime where needed.

**Acceptance:** test interruption ở mỗi boundary và mid-stage, resume lặp nhiều lần không skip gate, không duplicate decisions, không ghi đè approved artifacts.

### AOO-009 — [P1][Token/maintenance risk] Tham chiếu nhiều file policy cỡ lớn

**Evidence:** `SKILL.md` yêu cầu load stage refs trước hành động; `refs/contracts-and-artifacts.md` khoảng 70 KB, `docs/FLOW.md` khoảng 64 KB, `refs/compliance-policy.md` ~24 KB, `refs/stage-contracts.md` ~28 KB theo Git tree; governed mode nạp all refs.

**Impact:** Lazy loading có ích nhưng vẫn có nhiều token đọc policy và re-reading giữa stage/model; nội dung trùng lặp, drift và overhead khó kiểm soát.

**Remediation:** Thin router + dedicated mode files + compact machine-readable contracts. Summarize decisions in short checkpoint; tool-call outputs được lọc; chỉ load refs liên quan. Bỏ duplicate prose khi có validator.

**Acceptance:** đo prompt/cache tokens và số reference reads mỗi task; version mới giảm context overhead nhưng không giảm AC coverage.

### AOO-010 — [P1][Observability gap] Tracking task/team thiếu consistency contract rõ

**Evidence:** local `session.json`, `status.json`, `handoff.md`, `task-summary.md`; optional `TEAM_DOCS_PATH` boards, locks, ADRs; GitHub/Jira đứng ngoài core state trong README.

**Impact:** Có nguy cơ disagreement: PR merged nhưng local stage chưa DONE, Jira still in progress hoặc team board stale.

**Remediation:** Define event schema (`task.scoped`, `code.started`, `verify.passed`, `pr.opened`, `blocked`, `merged`) cùng system authority per field; idempotent sync, manual reconciliation.

**Acceptance:** bất kỳ nguồn state lỗi/không kết nối đều hiện `unknown/stale`, không tự hiện DONE; PR/Jira có links/evidence.

### AOO-011 — [P2][Design risk] Model routing hard-coded và không vendor-neutral

**Evidence:** `SKILL.md` gắn stage vào Haiku 4.5 / Sonnet 4.6 / Opus 5 và có câu tuyệt đối “Sonnet is optimal for code”. README mô tả support Codex, Cursor, Claude.

**Impact:** Vendor preference và fixed model identifiers có thể lỗi thời, không portable; stage-based routing có thể gây context transfer không cần thiết; mọi task nhỏ cũng bị route qua nhiều tiers.

**Remediation:** Capability tiers (`cheap`, `coding`, `reasoning`, `independent-review`) và adapter map theo provider, route theo risk/uncertainty và measured benchmark; single-agent default.

**Acceptance:** workflow hoạt động với tối thiểu Claude và Codex, không cần chỉnh core rules; log model/provider/estimated cost; config fallback khi model unavailable.

### AOO-012 — [P2][Validation gap] Tooling preflight độ chính xác và cache invalidation

**Evidence:** `templates/tooling-preflight.sh` kiểm tra `android --help`, command existence, auth file presence, text detection cho token, và `tooling-cache.json`; `SKILL.md` quy định audit mode mặc định.

**Impact:** `command -v`/help text không đảm bảo lệnh thực sự chạy được; token present không chứng minh quyền scope hợp lệ; cache gắn HEAD có thể invalidation quá thường xuyên, hoặc bỏ sót thay đổi môi trường ngoài Git.

**Remediation:** Chia availability / capability / auth-scope / execution probe; timeout, non-destructive check; cache key theo tool version + relevant config + TTL. Không dump token values.

**Acceptance:** matrix present-but-broken, stale-cache, missing scopes, unsupported subcommands; báo `UNVERIFIED` khi chưa test được.

### AOO-013 — [P2][Workflow friction] Git pull/rebase/push trong preflight của team docs

**Evidence:** `refs/team-docs.md` mô tả `git pull --rebase` trước đọc và `git push` cho lock writes.

**Impact:** Preflight đọc thông tin có thể bị chặn bởi network/git conflicts hoặc dirty working tree; agent thực hiện mutation git trong một bước người dùng tưởng chỉ read-only.

**Remediation:** Preflight read-only; remote fetch/read without mutating checked-out worktree; pushes phải là explicit coordination action, có retry và conflict recovery.

**Acceptance:** chỉ “audit tools/start task” không thay đổi git worktree; dirty team-docs repo không làm mất state; fetch failure có non-blocking/fail-closed rule theo risk.

## 4. Proposed VADW Lite workflow

### Mode & approvals

| Mode | Apply | Required outputs | Approval |
|---|---|---|---|
| **FAST** | UI/style/simple isolated fix, clear AC | short scope, diff, targeted verification, PR summary | PR review; extra approval only if scope/risk changes |
| **STANDARD** | Normal feature, multi-file/single module | one task.md with AC+plan, tests/build evidence, PR | approve scope when ambiguous; PR review |
| **GOVERNED** | Billing, OAuth, security, multi-module migration, release config, destructive operations | requirements, ADR/design if triggered, explicit test plan, rollout/rollback, evidence | requirements/design checkpoint + PR review |

**Risk overrides:** Any security/privacy/payment/data-loss/public API/release-related change can escalate to governed, even if one line. FAST auto-escalates when assumptions invalidated.

### Execution sequence

1. **Intake & classification:** task ID, approved AC, risk/change type, owner.
2. **Targeted discovery:** grep symbols/module/tests, architecture graph only if impact uncertain or cross-module.
3. **Plan:** concise path for FAST, short task.md for STANDARD, design/ADR for GOVERNED.
4. **Implement:** one code owner; read-only auxiliary agents where justified; no unrelated refactor/dependency.
5. **Verify:** deterministic commands; `PASS | FAIL | NOT_RUN | BLOCKED` with exact evidence.
6. **Handoff/PR:** summary, affected modules, QA checklist, known risks, links to Jira/CI.

### Shared state policy

- **Jira/GitHub PR/CI:** canonical cross-team tracking.
- **Local state JSON:** resumability/cache, not dashboard for teammates.
- **docs/ai:** decisions/requirements for STANDARD/GOVERNED when truly useful; do not commit generated runtime logs by default.
- **Security:** credentials in trusted providers/OS store, secrets never in prompts or artifacts.

### Suggested repository refactor (target, not current)

```text
Android-Agent-Orchestrator/
├── SKILL.md                 # thin router
├── workflows/
│   ├── fast.md
│   ├── standard.md
│   └── governed.md
├── rules/
│   ├── android.md
│   ├── security.md
│   └── quality.md
├── skills/
│   ├── analyze/
│   ├── implement/
│   ├── debug/
│   ├── verify/
│   └── review/
├── scripts/
│   ├── preflight.sh
│   ├── validate-state.py
│   └── verify.sh
├── adapters/
│   ├── codex/
│   └── claude/
└── templates/
    ├── task.md
    └── pr-summary.md
```

Không cần xóa toàn bộ `refs/**`; dùng như advanced references cho governed mode rồi thu gọn dần trên cơ sở benchmark.

## 5. Implementation backlog theo thứ tự

| Sprint | Ticket | Priority | Owner suggestion | Deliverable |
|---|---|---|---|---|
| 1 | AOO-001 | P0 | Workflow owner | FAST path, risk escalation |
| 1 | AOO-002 | P0 | Security/infra | Keychain/credential strategy |
| 1 | AOO-003 | P0 | Android TL + QA | E2E golden scenarios, contract validator |
| 1 | AOO-004 | P1 | Maintainer | Version-sync CI |
| 2 | AOO-007 | P1 | Android QA | Change-type verification matrix |
| 2 | AOO-008 | P1 | Maintainer | Explicit stage IDs + recovery tests |
| 2 | AOO-009 | P1 | Agent infra | Thin router + lazy refs optimization |
| 2 | AOO-005 / 010 | P1 | Dev productivity | GitHub/Jira state integration |
| 3 | AOO-006 / 013 | P1–P2 | Dev productivity | Advisory locks + safe coordination |
| 3 | AOO-011 / 012 | P2 | Agent infra | Vendor-neutral routing, improved preflight |

## 6. Pilot/benchmark plan

Chọn cùng một commit baseline và loại ticket có độ khó tương đương để so **current orchestration vs VADW Lite**:

1. **FAST:** XML UI/bug logic cục bộ (5+ samples).
2. **STANDARD:** feature có API + ViewModel + tests (5+ samples).
3. **GOVERNED:** Billing/OAuth/ANR/Remote Config (3+ samples, review chuyên sâu).

Đo `cycle_time`, `time_to_first_valid_patch`, số approval/human interrupts, number of tool calls, `input/output/cache tokens`, cost/accepted change, acceptance criteria coverage, build/test success, review iterations, escaped defects, rate of unauthorized scope changes. Baseline theo độ khó và cùng model/environment; đừng kết luận từ một ticket.

**Provisional success targets (pilot hypotheses, not observed):** giảm ≥20% lead time và ≥15% AI cost/accepted change, không làm tăng escaped defects hoặc security findings; QA gate vẫn đáp ứng chất lượng.

## 7. Những điểm cần kiểm tra thêm bằng thực nghiệm

- Rà kỹ shell script và script supply chain, test behavior offline/non-interactive, permissions và command injection; review hiện tại chưa phải audit security hoàn chỉnh.
- Test parallel file-lock conflicts, orphan lock, network outage và concurrent git pushes.
- Test resume interruption ở từng stage, đặc biệt Stage 1.5 và Stage 2.5; test missing/corrupted artifacts.
- Validate AI không tự báo PASS khi command unavailable hoặc tool output bị lỗi.
- Test `SKILL.md` behavior trên Claude Code và Codex CLI (cách load skill/sub-agents có thể khác nhau).
- Đo số token tiêu thụ bởi rule files trong 4 modes; kiểm tra adaptive loading thực sự giảm token.

## 8. Source references

- [README.md](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/README.md)
- [SKILL.md](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/SKILL.md)
- [QUICKSTART.md](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/QUICKSTART.md)
- [refs/contracts-and-artifacts.md](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/refs/contracts-and-artifacts.md)
- [refs/stage-contracts.md](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/refs/stage-contracts.md)
- [refs/compliance-policy.md](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/refs/compliance-policy.md)
- [refs/team-docs.md](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/refs/team-docs.md)
- [refs/auth-bootstrap.md](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/refs/auth-bootstrap.md)
- [templates/tooling-preflight.sh](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/templates/tooling-preflight.sh)
- [docs/FLOW.md](https://github.com/hvdung90/Android-Agent-Orchestrator/blob/main/docs/FLOW.md)

---

**Bottom line:** Phát triển tiếp repository thay vì thay thế. Ưu tiên sửa P0: FAST path, credential handling, executable validation. Giữ chất lượng của governed mode; không đưa toàn bộ compliance overhead vào mọi bug fix. Sau khi có golden tests và pilot metrics mới quyết định rollout toàn team.
