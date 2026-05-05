# Auth Bootstrap & Token Management

_Skill version: 4.3.0 — update this when SKILL.md bumps a minor or major version._

## Nguyên tắc

`.agent-auth.yaml` là **nguồn sự thật duy nhất** cho tất cả token/secret.  
Khi skill bắt đầu → đọc file này.  
Khi cần tool nào → kiểm tra token của tool đó tại thời điểm đó.  
Nếu thiếu → hỏi user ngay, lưu vào file, tiếp tục.

---

## Bước 1 — Khởi tạo file auth (chạy tại Stage -1)

```
check: .agent-auth.yaml tồn tại?
        │
   ┌────┴────┐
  Có        Không
   │          │
   ▼          ▼
  Load      Tạo file rỗng từ template:
  file        cp templates/agent-auth.example.yaml .agent-auth.yaml
              (tất cả token để trống "")
              → Thông báo cho user:
                "Đã tạo .agent-auth.yaml.
                 Token sẽ được hỏi khi cần dùng tool tương ứng."
   │          │
   └────┬─────┘
        │
        ▼
  Ghi vào preflight.md:
  - file_present: true
  - tokens_loaded: [list các key đã có giá trị]
  - tokens_missing: [list các key còn trống]
```

---

## Bước 2 — Kiểm tra token khi dùng tool (Just-in-time)

Trước khi chạy bất kỳ source reader nào, kiểm tra token tương ứng.  
Nếu thiếu → hỏi user → lưu → thử lại. Không skip, không fabricate.

### Jira Reader

Cần: `atlassian.domain`, `atlassian.email`, `atlassian.api_token`

```
Check từng field:
  atlassian.domain   → trống? → hỏi: "Atlassian domain của bạn? (vd: mycompany.atlassian.net)"
  atlassian.email    → trống? → hỏi: "Email đăng nhập Atlassian?"
  atlassian.api_token→ trống? → hỏi:
    "Cần Atlassian API token để đọc Jira.
     Lấy tại: https://id.atlassian.com/manage-profile/security/api-tokens
     → Create API token → Copy → Paste vào đây:"

Nhận token → lưu vào .agent-auth.yaml → chạy Jira Reader
```

### Confluence Reader

Cùng token với Jira (`atlassian.*`). Nếu Jira đã xác thực → Confluence dùng lại, không hỏi lại.

### Figma Reader

Cần: `figma.personal_access_token`

```
figma.personal_access_token → trống? → hỏi:
  "Cần Figma Personal Access Token để đọc design.
   Lấy tại: Figma → Account Settings → Security → Personal access tokens → Generate new token
   Quyền cần: File content (read-only)
   Paste token vào đây:"

Nhận token → lưu vào .agent-auth.yaml → chạy Figma Reader
```

### GitHub (tuỳ chọn)

Cần: `github.personal_access_token`

```
github.personal_access_token → trống? → hỏi:
  "Cần GitHub token để đọc private repo.
   Lấy tại: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained
   Quyền cần: Contents (read-only), Metadata (read-only)
   Paste token vào đây:"

Nhận token → lưu vào .agent-auth.yaml → chạy reader
```

---

## Bước 3 — Resolve credentials (khi có nhiều project)

```
Developer cung cấp link (vd: "CA-42" hoặc URL)
        │
        ▼
Extract project key prefix → "CA"
        │
        ▼
Tìm trong .agent-auth.yaml → projects[].jira_project_key
        │
   ┌────┴────┐
  Match    No match
   │          │
   ▼          ▼
  Dùng      Dùng Level 2
  Level 3   (top-level atlassian / figma)
  override
        │
        ▼
Kiểm tra token của override/top-level (Bước 2)
Nếu thiếu → hỏi user → lưu vào đúng block (Level 3 hoặc Level 2)
```

---

## Bước 4 — Lưu token vào file

Khi user cung cấp token, agent cập nhật `.agent-auth.yaml`:

- Tìm đúng field trong file
- Ghi giá trị vào
- Không xoá các field khác
- Không log giá trị token ra màn hình hay vào report
- Xác nhận với user: "Đã lưu. Token sẽ được dùng cho session này và các lần sau."

---

## MCP mapping

Các MCP tool dùng trong Claude Code và token tương ứng trong `.agent-auth.yaml`:

| MCP Tool                        | Auth source trong .agent-auth.yaml     |
|---------------------------------|----------------------------------------|
| `mcp__claude_ai_Atlassian__*`   | `atlassian.domain` + `atlassian.email` + `atlassian.api_token` |
| Figma REST API                  | `figma.personal_access_token`          |
| `mcp__plugin_*_github__*`       | `github.personal_access_token`         |

Khi MCP tool yêu cầu authenticate, dùng token từ `.agent-auth.yaml` tương ứng.  
Không dùng OAuth interactive nếu token đã có trong file.

---

## Safety rules

- Không in token ra màn hình hay report bất kỳ lúc nào.
- Không commit `.agent-auth.yaml` (đã có trong `.gitignore`).
- Không lưu token vào bất kỳ file nào khác ngoài `.agent-auth.yaml`.
- Không tự tạo token — chỉ hỏi user cung cấp.
- Nếu user từ chối cung cấp token → skip tool đó, ghi nhận trong report, tiếp tục với dữ liệu có sẵn.
