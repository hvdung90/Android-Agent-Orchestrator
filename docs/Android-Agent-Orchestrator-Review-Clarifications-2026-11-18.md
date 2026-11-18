# Android Agent Orchestrator — Làm rõ các finding của Review v1.0

> **Bổ sung cho:** `docs/Android-Agent-Orchestrator-Review-Vulcanlabs-2026-11-18.md`
> **Ngày:** 2026-11-18 · **Commit đối chiếu:** `8f50b7f` (nhánh `main`)
> **Phương pháp:** đối chiếu từng finding với file thực tế (có số dòng); chạy thử `templates/tooling-preflight.sh` logic trên template auth rỗng. Vẫn **chưa chạy task end-to-end trên Android codebase**.

## 0. Tóm tắt thay đổi phân loại

| Finding | Phân loại ban đầu | Sau khi làm rõ | Ghi chú |
|---|---|---|---|
| AOO-001 | Design risk | **Confirmed** (mức overhead) + 2 mâu thuẫn mới | Danh sách "never skipped" + ref tier/source mode không khớp |
| AOO-002 | Security design risk | **Confirmed, nghiêm trọng hơn** | Token được yêu cầu **paste vào chat** → đi qua transcript LLM |
| AOO-004 | Confirmed inconsistency | **Confirmed, phạm vi rộng hơn** | Thêm `docs/FLOW.md` lệch version |
| AOO-007 | Policy overhead | **Confirmed** | CHANGELOG tự thừa nhận mâu thuẫn "no exceptions"; README chưa sửa |
| AOO-008 | State correctness risk | **Confirmed inconsistency** | State Stage 1 và 1.5 giống hệt nhau, không phân biệt được |
| AOO-006 | Concurrency risk | Design risk + **Confirmed path inconsistency** | `locks.json` có 2 đường dẫn khác nhau |
| AOO-011 | Design risk | Design risk + **Confirmed tension** | micro → Haiku cho cả Stage 4 code |
| AOO-012 | Validation gap | **Confirmed bug (tái hiện được)** | Template rỗng → preflight báo token `set` |
| AOO-013 | Workflow friction | **Confirmed** | `git pull --rebase` chạy cả trong mode `knowledge` |

Các finding còn lại (AOO-003, 005, 009, 010) giữ nguyên phân loại; bên dưới bổ sung số liệu/bằng chứng.

---

## 1. Chi tiết từng finding

### AOO-001 — Gate quá nhiều cho `micro`/`fast` → **Confirmed**

**Bằng chứng cụ thể**
- `SKILL.md:73` — *"Never skipped in any mode: auth init, team docs lock check…, human requirements approval, ADR trigger check, Gate E.5 RED evidence, Evidence Gate Matrix, Karpathy diff review, `session.json`, `status.json`… Micro/fast reduce artifact depth only."* → micro chỉ giảm **độ dày** artifact, không giảm **số gate**.
- `SKILL.md:66` — micro vẫn chạy 10 stage (`-1 → 0 → 1 → 2 → 2.5-lite → 3-micro → 4 → 5 → 6 → 7`) và `implementation-plan.md` *"still mandatory with exactly 1 task"*.
- Ít nhất **2 điểm dừng chờ người** trong micro: requirements approval (Stage 2) + RED-evidence exemption confirm nếu là resource/text change (Stage 4).

**Ước lượng token đọc policy cho 1 ticket micro** (byte/4, chỉ refs bắt buộc theo stage pointer):

| Stage | Ref bắt buộc | Kích thước |
|---|---|---|
| luôn | `SKILL.md` | 23.5 KB |
| -1 | auth-bootstrap + provisioning-preflight + android-cli-compatibility + stage-contracts | 5.7 + 11.1 + 3.8 + 27.9 KB |
| 0 | clarification-workflow | 8.3 KB |
| 2 / mọi artifact | contracts-and-artifacts (*"Load before writing any artifact"* — `SKILL.md:97`) | 70.2 KB |
| mọi skip | compliance-policy (*"Load before any skip"*) | 23.6 KB |
| **Tổng** | | **≈174 KB ≈ 40–45K tokens** trước khi viết dòng code đầu tiên |

→ Tier `LIGHT` không thực sự "light": nó chỉ bỏ refs *optional*, còn refs *mandatory* của stage đã chiếm gần hết.

**Mâu thuẫn mới phát hiện**
1. **LIGHT tier không thể đạt được.** `SKILL.md:93`: LIGHT yêu cầu `source_mode = C`. Nhưng `SKILL.md:151` và `refs/clarification-workflow.md:118-120`: *Mode C → BLOCK, ask human for task brief*. Trong khi `refs/stage-contracts.md:125` lại nói *"C: user message only"* (tức không block). Ba file mô tả Mode C theo hai cách khác nhau.
2. **Ref tier được quyết định trước khi có input.** `refs/stage-contracts.md:89` — *"ref tier determined (LIGHT / MEDIUM / HEAVY / FULL)"* ở **Stage 0**, nhưng điều kiện LIGHT cần `workflow_mode` final và `graph_impact` — cả hai chỉ có ở **Stage 1** (`refs/stage-contracts.md:135`).

**Đề xuất làm rõ remediation**
- Tách danh sách "never skipped" thành 2 lớp: **Safety invariants** (không bao giờ bỏ: không log secret, one code owner, no success without evidence, ADR trigger check) và **Process gates** (bỏ được theo mode).
- Với FAST: thay `human requirements approval` bằng *AC đã approved trên Jira* (nếu có) → không thêm stop.
- Sửa Mode C: "plain-text brief = Mode C hợp lệ; chỉ block khi brief rỗng".
- Chuyển việc chọn ref tier sang cuối Stage 1, Stage 0 chỉ có *preliminary tier*.

---

### AOO-002 — Plaintext credentials → **Confirmed, nghiêm trọng hơn review gốc**

**Bằng chứng**
- `refs/auth-bootstrap.md:7` — `.agent-auth.yaml` là *single source of truth*.
- `refs/auth-bootstrap.md:54-59, 73-80, 88-94` — khi thiếu token agent hỏi *"…Copy → **Paste it here:**"* rồi *"Receive token → save to .agent-auth.yaml"*.

**Điểm review gốc chưa nêu:** token được **dán vào hội thoại với LLM**. Nghĩa là secret:
- nằm trong transcript/session log local (`~/.claude/projects/...`), có thể nằm trong session summary/hook output (như hook `SessionStart` lưu tóm tắt tasks);
- được gửi tới model provider;
- có thể bị compaction/summary chép lại.

`.gitignore` chỉ chặn commit, không chặn bất kỳ kênh nào ở trên.

**Remediation cụ thể hơn**
1. **Không bao giờ yêu cầu paste token vào chat.** Thay bằng: hướng dẫn user tự chạy lệnh ngoài agent, ví dụ:
   ```bash
   security add-generic-password -s aao-atlassian -a "$USER" -w
   ```
   và agent chỉ đọc qua wrapper lúc chạy (`security find-generic-password -s aao-atlassian -w`), không echo.
2. Ưu tiên MCP/OAuth (Atlassian MCP, Figma MCP, `gh auth`) — `auth-bootstrap.md:68` đã làm vậy cho Figma, mở rộng cho Jira/GitHub.
3. Nếu vẫn giữ file: `chmod 600` khi tạo, preflight cảnh báo nếu permission rộng hơn; file chỉ chứa *tên key* trỏ tới keychain.
4. Thêm hard rule: "Nếu user dán secret vào chat, cảnh báo và khuyên rotate".

---

### AOO-003 — Thiếu E2E validation → giữ nguyên, bổ sung phạm vi tối thiểu

Hiện repo **không có thư mục test, không có CI** (`git ls-files` không có `.github/`, `tests/`). Đề xuất bộ "golden" tối thiểu cho Sprint 1:
- `scripts/validate-state.py`: JSON schema cho `session.json`, `status.json`, `skip-log.json`, `locks.json`, `context-pack.json`.
- `tests/preflight/`: chạy `tooling-preflight.sh` trên fixture (xem bug AOO-012 — đây là test đầu tiên nên có).
- `tests/docs-lint/`: version sync (AOO-004), dead cross-reference (`§ section` trỏ tới heading không tồn tại).
- Transcript fixtures: 1 FAST, 1 STANDARD, 1 GOVERNED + 1 resume-mid-stage.

---

### AOO-004 — Version drift → **Confirmed, rộng hơn**

| File | Version |
|---|---|
| `SKILL.md:6` (frontmatter) | 6.1.3 |
| `SKILL.md:29` (heading) | **6.1.1** |
| `README.md:3` | **6.1.1** |
| `docs/FLOW.md:3` | **6.1.1** (*"Update when SKILL.md changes"*) — review gốc chưa nêu |
| `CHANGELOG.md:3` | 6.1.3 |
| 10 file `refs/*.md` dòng 3 | 6.1.3 |

Check CI đơn giản (đủ cho acceptance):
```bash
v=$(sed -n 's/^  version: //p' SKILL.md); ! grep -rnE '6\.[0-9]+\.[0-9]+' SKILL.md README.md docs/FLOW.md refs | grep -v "$v" | grep -vi changelog
```

---

### AOO-005 / AOO-010 — `status.json` không phải shared state → giữ nguyên, làm rõ authority

`.gitignore` chứa `.project-orchestration/` → `status.json` chỉ tồn tại trên máy dev. Đề xuất **bảng authority theo field** (để AOO-010 có acceptance đo được):

| Field | Authority | Local cache được phép? |
|---|---|---|
| assignee, ticket status | Jira | có, có `synced_at` |
| branch, PR, review state | GitHub | có |
| verification result | CI (GitHub Checks) | local evidence chỉ là pre-CI |
| stage nội bộ, resume point | `session.json` local | là nguồn chính |
| file locks | team-docs (advisory) | — |

Quy tắc: field nào đọc từ cache quá TTL → hiển thị `stale`, không bao giờ suy ra `DONE`.

---

### AOO-006 — Git file lock → Design risk + **Confirmed path inconsistency**

**Bằng chứng mới**
- Đường dẫn lock không thống nhất: `refs/team-docs.md:135, 255, 283` dùng `active-tasks/<repo>/locks.json`; còn `SKILL.md:112` (hard rule 11) và `refs/team-docs.md:229` dùng `active-tasks/locks.json`. Hai dev đọc hai file khác nhau thì conflict check luôn `clean`.
- `locked_at` do agent tự ghi theo đồng hồ máy local → tiebreak "earliest wins" (`team-docs.md:236`) phụ thuộc clock skew giữa các máy.
- Mọi dev cùng append vào **một mảng JSON** → `git pull --rebase` dễ ra textual conflict ngay cả khi lock khác file; tài liệu không mô tả cách agent resolve conflict JSON.
- Stale mặc định **7 ngày** (`team-docs.md:223`) → lock mồ côi chặn file cả tuần.

**Remediation làm rõ:** (a) chuẩn hóa 1 path; (b) mỗi task 1 file `locks/<task_id>.json` thay vì một mảng chung (hết conflict textual); (c) dùng thứ tự commit trên remote (thời gian push do server ghi) làm tiebreak thay vì `locked_at` client; (d) mặc định advisory.

---

### AOO-007 — TDD "no exceptions" → **Confirmed**

- `README.md:87` — *"follows this loop — no exceptions"*.
- `CHANGELOG.md:69` — chính maintainer đã ghi nhận: *"fixes a real contradiction where Stage 4's 'no exceptions' iron law…"* và thêm category `build-only`. Nhưng README **chưa được cập nhật** theo.
- Category `build-only` mới cover build/config; **resource/XML/string/layout-only** vẫn phải xin human confirm từng lần.

**Remediation:** sửa README; thêm category `resource-only` auto-qualify (diff chỉ chạm `res/**`, không chạm `.kt/.java`) với evidence thay thế là screenshot/Paparazzi/Roborazzi hoặc `lint` + build.

---

### AOO-008 — Stage 1.5 dùng `stage_reached: 1` → **Nâng lên Confirmed inconsistency**

`refs/stage-contracts.md`:

| | Stage 1 | Stage 1.5 |
|---|---|---|
| `state_on_complete` (dòng 140 / 183) | `stage_reached: 1, stage_status: complete` | `stage_reached: 1, stage_status: complete` |
| `state_on_interrupt` (dòng 148 / 189) | `stage_reached: 1, stage_status: in_progress` | `stage_reached: 1, stage_status: in_progress` |
| `resume_entry_point` | re-run failed **source reader** | re-run blocked **analysis worker** |

Hai stage ghi **state giống hệt** nhưng có resume point khác nhau → lúc resume agent không thể biết nên chạy lại source reader hay clarification worker. Integrity reconciliation (`stage-contracts.md:11`) chỉ tách riêng `2.5`, không tách `1.5`, nên `clarification-brief.md` thiếu sẽ không bị phát hiện.

Phụ: Stage 1.5 `input_requires` file `discovery/<task>.md` (dòng 166), nhưng micro AUTO-SKIP file này (dòng 130). Hiện micro không chạy 1.5 nên chưa vỡ, nhưng nếu micro escalate giữa chừng lên fast/standard sẽ thiếu input.

**Remediation:** thêm `stage_id: "1_discovery" | "1.5_clarification"` (đã có sẵn ở field `stage:` của contract, chỉ cần ghi vào session); reconciliation coi 1.5 như 2.5.

---

### AOO-009 — Token/maintenance → giữ nguyên, có số liệu

Xem bảng ở AOO-001: ≈174 KB policy cho micro. Với governed (FULL tier, *all refs*): toàn bộ `refs/` + `SKILL.md` ≈ 214 KB ≈ 55K tokens, chưa tính `docs/FLOW.md` (64 KB). Acceptance nên đặt ngưỡng cụ thể: FAST ≤ 15 KB policy đọc mỗi task.

---

### AOO-011 — Model routing → Design risk + **Confirmed tension**

- `SKILL.md:214` — Stage 4: *"Never — Sonnet is optimal for code"*.
- `SKILL.md:220` — *"micro mode: tất cả stages → Haiku 4.5"* → Stage 4 code của micro chạy trên Haiku, trái tinh thần dòng 214.
- `SKILL.md:222` hard-code ID `claude-haiku-4-5-20251001 · claude-sonnet-4-6 · claude-opus-5` — không áp dụng cho Codex/Cursor mà README nói hỗ trợ; và đã cũ so với model family hiện tại.
- Mỗi stage đổi model = đổi context → mất cache, phải re-read refs (khuếch đại AOO-009).

**Remediation:** giữ nguyên đề xuất capability tiers; thêm quy tắc "không đổi model trong cùng một task trừ khi escalate mode".

---

### AOO-012 — Preflight → **Confirmed bug, tái hiện được**

**Tái hiện:** copy `templates/agent-auth.example.yaml` (mọi token = `""`) thành `.agent-auth.yaml`, chạy logic detect của `templates/tooling-preflight.sh`:

```
bash  (dòng 224-229): atlassian=set, figma=set
python (dòng 76-77):  api_token=set, personal_access_token=set
```

**Nguyên nhân:**
1. Regex `api_token:.*[^"' ]` match cả **comment cùng dòng** (`api_token: ""   # https://id.atlassian.com/...`).
2. Không bỏ qua dòng comment (`#       api_token: ""` ở block override).
3. `personal_access_token:` dùng chung cho Figma **và** GitHub → token GitHub có giá trị sẽ báo `figma_token: set`.

**Hệ quả:** preflight báo sẵn sàng, agent bỏ qua bước xin token, tới Stage 1 mới fail → đúng loại "báo PASS thiếu evidence" mà repo muốn tránh.

**Thêm:** `valid_until`/`graph_commit` của cache chỉ được **đọc và in ra** (dòng 178-179, 371-372), script không so sánh với thời gian hiện tại hay `git rev-parse HEAD` → invalidation phụ thuộc hoàn toàn vào agent diễn giải.

**Fix đề xuất:** parse YAML thật (`python3 -c 'import yaml'` hoặc fallback parser đơn giản bỏ comment), detect theo **đường dẫn key** (`atlassian.api_token`, `figma.personal_access_token`, `github.personal_access_token`); script tự tính `cache_status: fresh|stale|missing`.

---

### AOO-013 — Git mutation trong preflight → **Confirmed**

`refs/team-docs.md:206` — bước 1 của Stage -1 gắn nhãn `[both]`: *"`git pull --rebase` on docs repo before reading any file"* → chạy cả ở mode `knowledge` (vốn chỉ đọc ADR/standards). `pull --rebase` trên team-docs repo đang dirty sẽ fail hoặc để lại trạng thái rebase dở.

**Remediation:** Stage -1 dùng `git fetch` + `git show origin/main:active-tasks/.../locks.json` (không chạm worktree); chỉ `pull --rebase` ngay trước một write có chủ đích.

---

## 2. Backlog cập nhật (thêm ticket mới từ phần làm rõ)

| Ticket | Priority | Loại | Nội dung |
|---|---|---|---|
| AOO-002a | **P0** | Security | Bỏ luồng "paste token vào chat" trong `auth-bootstrap.md` |
| AOO-012a | **P0** | Bug | Sửa token detection preflight (false `set`) + test fixture |
| AOO-014 | P1 | Confirmed inconsistency | Mode C: block hay "user message only"; LIGHT tier không đạt được |
| AOO-015 | P1 | Confirmed inconsistency | Ref tier quyết định ở Stage 0 nhưng phụ thuộc output Stage 1 |
| AOO-016 | P1 | Confirmed inconsistency | Hai đường dẫn `locks.json` khác nhau |
| AOO-017 | P2 | Docs | README "no exceptions" chưa sync với CHANGELOG v6.1.x |

Thứ tự Sprint 1 đề xuất: **AOO-002a → AOO-012a → AOO-004 → AOO-016** (đều nhỏ, sửa được trong ngày, rủi ro thấp) rồi mới tới AOO-001/003 (thay đổi thiết kế).

## 3. Câu hỏi mở cần owner quyết định

1. Team chấp nhận **Jira AC đã approve** thay cho Stage 2 human approval trong FAST không?
2. File lock: chuyển hẳn sang advisory, hay giữ hard-stop cho một danh sách path đặc biệt (ví dụ `build.gradle*`, `libs.versions.toml`, billing module)?
3. Repo có cần hỗ trợ Codex/Cursor thật sự trong 6.2 không? Nếu không, bỏ claim khỏi README để giảm phạm vi AOO-011.
