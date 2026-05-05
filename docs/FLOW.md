# Android Agent Orchestrator — Complete Flow

_Phản ánh skill v4.3.0. Cập nhật khi SKILL.md thay đổi._

---

## 1. Entry point — Xác định task type

```
Developer đưa task
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│  Task này thuộc loại nào?                                 │
└───────────────────────────────────────────────────────────┘
        │
        ├── Phân tích / xem repo          ──► [A] Analyze repo
        ├── Setup / cài tool lần đầu      ──► [B] Bootstrap repo
        ├── Update tooling                ──► [C] Update tools
        ├── Rebuild architecture graph    ──► [D] Refresh graph
        ├── Feature mới                   ──► [E] New feature
        ├── Sửa feature có sẵn            ──► [F] Edit feature
        ├── Fix bug                       ──► [G] Bug fix
        ├── XML → Compose migration       ──► [H] Migration
        ├── AGP / build modernization     ──► [I] AGP upgrade
        └── Codebase lạ + brief thô       ──► [J] Unfamiliar codebase

Tất cả task type đều bắt đầu bằng Stage -1.
[A][B][C][D] kết thúc sau Stage -1.
[E]–[J] đi qua toàn bộ Stage 0–6.
```

---

## 2. Stage -1 — Tooling Preflight

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE -1: TOOLING PREFLIGHT                                    │
│  Ref: refs/provisioning-preflight.md                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Auth init (refs/auth-bootstrap.md Bước 1):           │
    │  .agent-auth.yaml present? No → auto-create           │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Cache check (tooling-cache.json):                    │
    │                                                       │
    │  valid_until in future                                │
    │  AND graph_commit == git rev-parse HEAD?              │
    │         │                                             │
    │    ┌────┴────┐                                        │
    │   Yes        No                                       │
    │    │          │                                       │
    │    ▼          ▼                                       │
    │  CACHE HIT   Run full preflight.sh (parallel)        │
    │  → skip tool  → write tooling-cache.json             │
    │    checks     → write/update session.json            │
    └───────────────────────────────────────────────────────┘
                            │
    ┌───────────────────────┴───────────────────────────────┐
    │  session.json: interrupted task present?              │
    │    Yes → offer user: "Resume <task_id> from Stage N?" │
    │    No  → continue                                     │
    └───────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴──────────────┐
              │  Developer yêu cầu gì?     │
              └─────────────┬──────────────┘
                            │
        ┌───────────────────┼──────────────────────────────┐
        │                   │                              │
   "analyze"/"xem"    "set up"/"init"             "update tools"
   (mặc định)               │                              │
        │                   ▼                              ▼
        ▼             mode=bootstrap                mode=update
   mode=audit               │                              │
        │             "rebuild graph"          "clean reset"
        │                   │                              │
        │                   ▼                              ▼
        │           mode=refresh-graph        mode=force-reinstall
        │                   │                              │
        └───────────────────┴──────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Auth init — Bước 1 (refs/auth-bootstrap.md):         │
    │                                                       │
    │  .agent-auth.yaml tồn tại?                           │
    │    Có  → Load; note tokens set vs empty               │
    │    Không → Auto-create từ template (tokens rỗng)      │
    │            Notify user                                │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Parallel checks (read-only, mọi mode):               │
    │                                                       │
    │  ① AI DevKit    — CLI present? .ai-devkit.json?       │
    │  ② Android CLI  — present? android info?             │
    │  ③ Android skills — list available?                   │
    │  ④ Graphify     — CLI/package? GRAPH_REPORT.md?       │
    │                   graph.json?                         │
    │  ⑤ Karpathy     — plugin / skill / CLAUDE.md?         │
    │  ⑥ Auth status  — tokens set / empty (từ Bước 1)      │
    └───────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
       mode=audit                  mode=bootstrap / update /
            │                      refresh-graph / force-reinstall
            ▼                               │
    Report gaps only                Apply tool actions
    (không cài gì)                  per decision tables
            │                               │
            └───────────────┬───────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Write: .project-orchestration/reports/preflight.md   │
    │                                                       │
    │  Ghi nhận:                                            │
    │  - provisioning mode                                  │
    │  - tool readiness (①–⑤)                              │
    │  - auth readiness (⑥)                                 │
    │  - blockers / warnings                                │
    │  - proceed to Stage 0: yes / no                      │
    └───────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
        Blocker exist?               No blocker
              │                           │
              ▼                           ▼
    STOP — fix first         [A][B][C][D] → DONE
    (mode không cho phép     [E]–[J]      → Stage 0
     hành động cần thiết)
```

---

## 3. Stage 0 — Intake + Source mode

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 0: INTAKE                                                │
│  Ref: refs/clarification-workflow.md § Source integrations      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Tiêu thụ preflight.md:                               │
    │  - tool readiness summary                             │
    │  - auth readiness (.agent-auth.yaml status)           │
    │  - graph present / absent                             │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    Developer cung cấp link nào?
                            │
        ┌───────────────────┼───────────────────────┐
        │                   │                       │
  Jira / Figma /       Chỉ có file            Không có gì
  Confluence link      docs/ai/inputs/
        │                   │                       │
        ▼                   ▼                       ▼
     Mode A              Mode B                  Mode C
  (External)           (Docs-only)        Task rõ ràng?
                                          (1-file refactor /
                                           rename / bug+repro)
                                                   │
                                         ┌─────────┴─────────┐
                                         │                   │
                                        Yes                  No
                                         │                   │
                                         ▼                   ▼
                                  Treat as Mode B       BLOCK —
                                  (message của dev      yêu cầu dev
                                   là sole doc)         cung cấp brief
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  Credential resolution (refs/auth-bootstrap.md Bước 3)│
    │  Xảy ra just-in-time khi reader được kích hoạt:       │
    │                                                       │
    │  1. Extract project key prefix (vd "CA" từ "CA-42")   │
    │  2. Match trong projects[] → dùng Level 3 override    │
    │     No match → dùng Level 2 top-level                 │
    │  3. Check token của tool đó (Bước 2):                 │
    │       Set   → proceed                                  │
    │       Empty → hỏi user → lưu vào file → proceed       │
    │       User từ chối → skip reader, ghi nhận report     │
    └───────────────────────────────────────────────────────┘
                            │
                            ▼
    Ghi lại: source mode (A/B/C), links, credential source
    → Stage 1
```

---

## 4. Stage 1 — Discovery

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: DISCOVERY                                             │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │           Parallel reads              │
        │                                       │
        ▼                                       ▼
  graphify-out/ present?               Source material
        │                                       │
   ┌────┴────┐                      ┌───────────┴───────────┐
  Yes        No                  Mode A                  Mode B
   │          │                     │                       │
   ▼          ▼                     ▼                       ▼
 Read        Skip            Jira Reader                Doc Reader
 GRAPH_                           │                   docs/ai/inputs/
 REPORT.md                        │
                        linked_docs / linked_designs?
                                  │
                    ┌─────────────┴─────────────┐
                    │  Auto-follow (1 level):    │
                    │  Confluence URL → Conf.Rdr │
                    │  Figma link    → Figma Rdr │
                    │  Doc / PDF     → Doc Rdr   │
                    │  Jira child    → Jira Rdr  │
                    │  Image/screenshot → ghi URL│
                    └─────────────┬─────────────┘
                                  │
                    (parallel với Jira Reader gốc)
                                  │
        └───────────────────┬─────┘
                            │
                            ▼
                  Store → docs/ai/discovery/
```

---

## 5. Stage 1.5 — Clarification & Synthesis

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1.5: CLARIFICATION & SYNTHESIS                           │
│  Ref: refs/clarification-workflow.md                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
    Cần chạy Clarification không?
    Chạy nếu BẤT KỲ điều nào dưới đây đúng:
    ┌───────────────────────────────────────────────────┐
    │  ☐ Brief < 50 words, không có ticket/design       │
    │  ☐ Không có acceptance criteria                   │
    │  ☐ ≥2 sources mâu thuẫn nhau                     │
    │  ☐ Graph có component không được đề cập trong doc │
    │  ☐ Graph có god node trong change path            │
    │  ☐ API / state / error behavior không rõ          │
    └───────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
      ≥1 điều đúng                  Không điều nào đúng
            │                               │
            ▼                               ▼
    Chạy Clarification                Skip / minimize
            │                          → Stage 2 trực tiếp
            ▼
    ┌─────────────────────────────────────────────────────┐
    │  Parallel workers (theo Source mode):               │
    │                                                     │
    │  Mode A ─► Jira Reader          ┐                   │
    │            Confluence Reader    │ parallel          │
    │            Figma Reader         │ (credentials từ   │
    │            Graph Impact Reader  ┘  .agent-auth.yaml)│
    │            ─────────────────────────────────────    │
    │            Ambiguity Detector   ┐                   │
    │            Conflict Detector    │ parallel          │
    │            Missing-info Det.    │                   │
    │            State Extractor      │                   │
    │            Dependency Impact    ┘                   │
    │                                                     │
    │  Mode B ─► Doc Reader           ┐ parallel          │
    │            Graph Impact Reader  │                   │
    │            Ambiguity Detector   │                   │
    │            Missing-info Det.    ┘                   │
    │                                                     │
    │  Advisory (on demand, bất kỳ mode):                 │
    │            Android Advisor                          │
    │            Research Advisor                         │
    │            QA Scenario Advisor                      │
    │            Rollout/Risk Advisor                     │
    └─────────────────────────────────────────────────────┘
                            │
                            ▼
    Parent synthesizes (serial — 1 owner):
    ┌───────────────────────────────────────────────────┐
    │  docs/ai/clarification/                           │
    │  ├── context-pack.json                            │
    │  ├── clarification-brief.md                       │
    │  └── clarity-report.md  (Mode A) /                │
    │       embedded clarity section (Mode B)           │
    └───────────────────────────────────────────────────┘
                            │
                            ▼
                  Clarity score (0–10)
                            │
        ┌───────────┬───────┴────────┬───────────┐
        │           │                │           │
      8–10        6–7              4–5          0–3
        │           │                │           │
        ▼           ▼                ▼           ▼
      ready    ready +           research-   blocked
               assumptions         loop         │
        │           │                │      Ask human
        └─────┬─────┘           Loop thêm   (không
              │                 research    fabricate)
              ▼
          Stage 2
```

---

## 6. Stage 2–6 — Requirements → Close

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: REQUIREMENTS                                          │
│  Ref: refs/contracts-and-artifacts.md                           │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  AI DevKit viết docs/ai/requirements/<task>.md
        │
        ▼
  ██████████████████████████████████████████████
  █  MANDATORY STOP — Human approval           █
  █  Không tiếp tục nếu chưa approve          █
  ██████████████████████████████████████████████
        │
        │  Human approves
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: DESIGN SPLIT                                          │
│  Ref: refs/playbooks.md                                         │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Parallel (không có code changes):
  ┌────────────────────────┬──────────────────────────────┐
  │  AI DevKit             │  Android skills              │
  │  docs/ai/design/       │  docs/ai/android-memo/       │
  │  docs/ai/planning/     │  <task>.md                   │
  └────────────────────────┴──────────────────────────────┘
        │
        ▼
  Single code owner selected + recorded
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4: IMPLEMENTATION LOCK                                   │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Exactly ONE code owner edits code
  Tất cả lanes khác: advisory only, không edit
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 5: VERIFY                                                │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Parallel:
  ┌──────────────────────────┬───────────────────────────────┐
  │  Android CLI             │  Graphify (nếu graph tồn tại) │
  │  build + device tests    │  /graphify . --update         │
  │  screenshots + logs  →   │  graphify-out/ updated        │
  │  .project-orchestration/ │                               │
  │  evidence/               │                               │
  └──────────────────────────┴───────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 6: QA GATE                                               │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  Parallel review:
  ┌──────────────────────────┬───────────────────────────────┐
  │  AI DevKit               │  Karpathy guidelines          │
  │  - diff review           │  - surgical changes           │
  │  - acceptance coverage   │  - no over-engineering        │
  │  - scope discipline      │  - explicit assumptions       │
  └──────────────────────────┴───────────────────────────────┘
        │
        ▼
  Write: .project-orchestration/reports/execution.md
        │
        ▼
  ✅ DONE — Task closed
```

---

## 7. Auth credential resolution

```
┌─────────────────────────────────────────────────────────────────┐
│  .agent-auth.yaml  (gitignored — không commit)                  │
│  Template: templates/agent-auth.example.yaml                    │
└─────────────────────────────────────────────────────────────────┘

  Level 1 — Workspace
  ├── workspace.name
  └── workspace.default_jira_project   (vd: "ANDROID")

  Level 2 — Tool credentials (mặc định toàn bộ session)
  ├── atlassian.domain / email / api_token   ← Jira + Confluence chung
  ├── figma.personal_access_token
  └── github.personal_access_token           (tuỳ chọn)

  Level 3 — Per-project overrides            (tuỳ chọn)
  └── projects[]
      ├── name: "client-alpha"
      ├── jira_project_key: "CA"
      ├── atlassian.*                        ← override Level 2
      └── figma.*                            ← nếu không set → fallback Level 2

Resolve flow khi agent nhận link:
  ─────────────────────────────────────────────────────────────
  Dev cung cấp "CA-42"
        │
        ▼
  Extract prefix → "CA"
        │
        ▼
  Tìm trong projects[].jira_project_key
        │
   ┌────┴────┐
  Match    No match
   │          │
   ▼          ▼
  Dùng      Dùng Level 2
  Level 3   (top-level)
  override       │
   │             │
   └──────┬──────┘
          │
          ▼
  Fetch source với credentials đúng

  .agent-auth.yaml missing + link provided:
  → WARN trong preflight.md
  → Source reader skip
  → Không fabricate content
```

---

## 8. Playbook flows — All use cases

### [A] Analyze repo
```
Stage -1 (audit) → report gaps → DONE
Không chạy Stage 0–6 trừ khi task docs cũng được phân tích
```

### [B] Bootstrap repo
```
Stage -1 (bootstrap)
  → Install missing tools
  → ai-devkit init / android init
  → Build graph nếu codebase tồn tại + approved
  → Write preflight.md
→ DONE
```

### [C] Update tools
```
Stage -1 (update)
  → android update / ai-devkit install
  → Refresh skills list
  → Update Graphify package nếu approved
  → Write preflight.md
→ DONE
```

### [D] Refresh graph
```
Stage -1 (refresh-graph)
  → /graphify .          (graph missing)
  → /graphify . --update (graph exists)
  → Không touch product code
→ DONE
```

### [E] New feature
```
-1 (audit + auth check)
→ 0 (collect links → Mode A/B/C → resolve credentials)
→ 1 (read graph + source readers + auto-follow Jira attachments)
→ 1.5 (minimal clarification, chỉ chạy nếu trigger fire)
→ 2 (requirements) → STOP human approval
→ 3 (design + Android memo)
→ 4 (one owner implements)
→ 5 (CLI evidence + graph update)
→ 6 (Karpathy QA)
```

### [F] Edit existing feature
```
-1 (audit + auth check)
→ 0 (collect links)
→ 1 (graphify path query nếu graph exists + source readers)
→ 1.5 (Ambiguity + Missing-info + Dependency Impact)
→ 2 (requirements: graph path + out-of-scope list) → STOP
→ 4 (surgical changes only — Karpathy)
→ 5 (update graph + verify)
→ 6 (QA gate)
```

### [G] Bug fix
```
-1 (audit Android CLI + Graphify + auth check)
→ 0 (collect: repro steps, device, version, expected behavior)
→ 1 (graph path + runtime evidence nếu available)
→ 1.5 (clarify chỉ khi repro không rõ)
→ 2 (minimal bug requirements) → STOP
→ 4 (smallest safe patch)
→ 5 (runtime evidence + graph update nếu graph exists)
→ 6 (QA gate)
```

### [H] XML → Compose migration
```
-1 (check Android CLI + Android skills + Graphify + auth)
→ 1 (graphify query "xml layout view fragment"
      android skills find "compose")
→ 1.5 (Android Advisor + Dependency Impact + Rollout/Risk)
→ 2 (migration plan) → STOP
→ 4 (per-batch, single owner mỗi batch)
→ 5 (visual evidence + graph update)
→ 6 (QA gate)
```

### [I] AGP / Build modernization
```
-1 (check AI DevKit + Android CLI + Android skills
     + Gradle wrapper + Graphify + auth)
→ 1 (graphify query "gradle build agp"
      android skills find "agp")
→ 1.5 (Dependency Impact + Rollout/Risk + Android Advisor)
→ 2 (upgrade plan) → STOP
→ 4 (controlled implementation)
→ 5 (clean build + graph update)
→ 6 (QA gate)
```

### [J] Unfamiliar codebase + raw brief
```
-1 (audit + auth check; refresh-graph chỉ khi approved)
→ 0 (collect task brief)
→ 1 (read GRAPH_REPORT.md + Doc Reader reads docs/ai/inputs/)
→ 1.5 (Ambiguity + Missing-info + Graph Impact
         + Dependency Impact — full clarification)
→ 2 (requirements sau khi outcome=ready) → STOP
→ 3–6 (normal flow)
```

---

## 9. Source mode × Worker activation matrix

```
                      Mode A           Mode B          Mode C
                   (links provided)  (docs-only)    (msg as doc)
                   ──────────────────────────────────────────────
Jira Reader             ✓                –               –
  └─ auto-follow        ✓                –               –
Confluence Reader       ✓                –               –
Figma Reader            ✓                –               –
Doc Reader              –                ✓               ✓
Graph Impact Reader     ✓ (if graph)     ✓ (if graph)    ✓ (if graph)
Ambiguity Detector      ✓                ✓               ✓
Conflict Detector       ✓                –               –
Missing-info Det.       ✓                ✓               ✓
State Extractor         ✓ (Figma)        –               –
Dependency Impact       ✓ (if graph)     ✓ (if graph)    –
Android Advisor         on demand        on demand        –
QA Scenario Adv.        on demand        on demand        –
Rollout/Risk Adv.       on demand        on demand        –
```

---

## 10. Graphify trigger map

```
Stage -1   → check CLI + graph files + freshness
Stage 0    → note graph present / absent
Stage 1    → READ GRAPH_REPORT.md (nếu present)
Stage 1.5  → Graph Impact Reader feeds context-pack
Stage 3    → dùng graph rationale cho design decisions
Stage 4    → KHÔNG query graph trong khi coding
Stage 5    → /graphify . --update (nếu graph exists)
Stage 6    → optional before/after compare; check god nodes
```

---

## 11. Parallel vs Serial

```
PARALLEL được phép                   SERIAL bắt buộc
─────────────────────────────────    ──────────────────────────────────
Tooling read-only checks (Stage -1)  Install/update cùng 1 tool
Auth check (Stage -1)                2 workers publish requirements
Source readers (Stage 1 / 1.5)       2 workers edit cùng file code
Auto-follow readers (Stage 1)        Credential resolution (per link)
Analysis workers (Stage 1.5)         Parent synthesis
Advisory workers (Stage 1.5)         Requirements → human approval
Lane reads in Discovery              Code ownership (1 owner only)
Design split (AI DevKit + Android)   Stage gates (wait for gate pass)
Verify (Android CLI + Graphify)
QA review (AI DevKit + Karpathy)
```

---

## 12. Hard stop points

```
①  Stage -1 → Stage 0  :  Blocker trong preflight chưa giải quyết
②  Stage -1 → Stage 0  :  .agent-auth.yaml thiếu + external links có → WARN
                           (không block, nhưng source readers sẽ skip)
③  Stage 0  (Mode C)   :  Task không rõ ràng → yêu cầu dev cung cấp brief
④  Stage 1.5 outcome   :  blocked → hỏi human, không fabricate requirements
⑤  Stage 2 → Stage 3   :  MANDATORY human approval requirements
⑥  Stage 3 → Stage 4   :  Chưa có design doc + single code owner
⑦  Stage 5 → Stage 6   :  Chưa có runtime evidence + graph update
⑧  Stage 6 → Close     :  Karpathy review chưa pass
```
