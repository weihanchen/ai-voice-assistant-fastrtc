# 任務清單：Flow Builder Agent Skill

**輸入**: 設計文件 `/specs/010-flow-builder-skill/`
**前置條件**: plan.md（必要）、spec.md（必要，含 User Story）、research.md、data-model.md、quickstart.md

**測試**: 此功能產出為靜態 Markdown 檔案，不涉及 Python 測試。驗證方式為人工確認 Skill 格式正確、可被 OpenCode 載入。

**組織**: 任務依 User Story 分組，支援獨立實作與驗證。

## 格式：`[ID] [P?] [Story] 描述`

- **[P]**: 可平行執行（不同檔案、無相依性）
- **[Story]**: 對應的 User Story（如 US1, US2, US3）
- 描述中包含確切的檔案路徑

---

## Phase 1: 設定（基礎準備）

**目的**: 建立目錄結構與 Skill 檔案骨架

- [x] T001 建立 `.opencode/skills/flow-builder/` 目錄
- [x] T002 建立 `.opencode/skills/flow-builder/SKILL.md` 檔案骨架，包含 YAML frontmatter（name、description、allowed-tools）

**檢查點**: 骨架檔案已建立，可被 OpenCode 偵測到

---

## Phase 2: 基礎設施（所有 Story 的前置條件）

**目的**: 撰寫 Skill 的共用基礎區段

**⚠️ 關鍵**: 此階段完成後，各 User Story 才可開始

- [x] T003 撰寫 SKILL.md 的觸發條件區段，列出觸發關鍵字清單（「建立流程」、「新增 flow」、「設計工作流」等）於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T004 撰寫 SKILL.md 的架構參考區段，摘要說明 009 架構（BaseFlowExecutor、FlowRegistry、FlowState、節點工廠模式）於 `.opencode/skills/flow-builder/SKILL.md`

**檢查點**: Skill 檔案具備基本的觸發條件與架構參考，但尚無工作流程和模板

---

## Phase 3: User Story 1 — Skill 基礎框架與工作流程（優先級: P1）🎯 MVP

**目標**: 定義完整的 10 步工作流程，讓 agent 可以依步驟引導開發者完成流程產生

**獨立測試**: 載入 Skill 後，確認 10 個步驟的輸入/動作/輸出皆完整定義

### User Story 1 實作

- [x] T005 [US1] 撰寫步驟 1（需求解析）：定義如何從自然語言提取流程目標、步驟、資料流，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T006 [US1] 撰寫步驟 2（現有工具盤點）：定義如何掃描 `src/voice_assistant/tools/` 識別可重用工具，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T007 [US1] 撰寫步驟 3（整合策略判斷）：定義獨立 Executor vs 子流程的決策規則，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T008 [US1] 撰寫步驟 4-6（設計階段）：定義如何設計 FlowState、節點、StateGraph，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T009 [US1] 撰寫步驟 7-9（程式碼產生階段）：定義如何產生 FlowState、節點、Graph + Executor 程式碼，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T010 [US1] 撰寫步驟 10（測試與驗證）：定義如何產生測試並執行驗證命令，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T011 [US1] 新增模糊描述處理指引：當開發者描述不夠具體時，列出 agent 應詢問的關鍵問題，於 `.opencode/skills/flow-builder/SKILL.md`

**檢查點**: Skill 的 10 步工作流程完整可用，agent 可依步驟引導開發者

---

## Phase 4: User Story 2 — 程式碼模板系統（優先級: P1）

**目標**: 在 Skill 中嵌入 5 種程式碼模板，確保產生的程式碼與 009 架構一致

**獨立測試**: 檢查每個模板的佔位符標記完整、語法正確、型別標註正確

### User Story 2 實作

- [x] T012 [P] [US2] 撰寫 FlowState TypedDict 模板：包含 `total=False` 模式、子流程巢狀、Pydantic 輔助模型範例，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T013 [P] [US2] 撰寫 Node 工廠函式模板（3 種類型）：LLM 節點、工具節點、純函式節點，各含閉包注入與 `dict[str, Any]` 回傳，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T014 [P] [US2] 撰寫 StateGraph 定義模板：包含 `add_node`、`add_edge`、`add_conditional_edges`、條件路由函式、`compile()`，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T015 [P] [US2] 撰寫 BaseFlowExecutor 子類別模板：包含 `flow_name`、`execute`、`get_visualization`、`_NODE_LABELS`，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T016 [P] [US2] 撰寫 pytest 測試模板：包含 pytest-asyncio、mock 外部依賴、正常/異常情境覆蓋，於 `.opencode/skills/flow-builder/SKILL.md`

**檢查點**: 5 種模板皆使用佔位符（`<DOMAIN>`、`<NodeName>` 等），語法正確可直接替換使用

---

## Phase 5: User Story 3 — 現有工具整合指引（優先級: P2）

**目標**: 說明如何識別和重用已註冊工具，避免功能重複

**獨立測試**: 確認 Skill 中包含工具查詢方法和調用模式的說明

### User Story 3 實作

- [x] T017 [US3] 撰寫工具查詢指引：說明如何掃描 `ToolRegistry` 和 `src/voice_assistant/tools/` 識別可重用工具，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T018 [US3] 撰寫工具調用模式：說明節點中如何正確調用 `tool_registry.get()` 和 `tool.execute()`，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T019 [US3] 撰寫新工具需求處理指引：當流程需要的功能不在現有工具中時，提醒開發者先建立工具，於 `.opencode/skills/flow-builder/SKILL.md`

**檢查點**: 工具整合指引完整，涵蓋查詢、重用、新增三種場景

---

## Phase 6: User Story 4 — 驗證與品質保證流程（優先級: P2）

**目標**: 定義產生程式碼後的驗證步驟和常見錯誤清單

**獨立測試**: 確認 Skill 中包含明確的驗證命令和自動修復指引

### User Story 4 實作

- [x] T020 [P] [US4] 撰寫驗證步驟區段：定義 `uv run ruff check`、`uv run ruff format`、`uv run pytest` 的執行順序和預期結果，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T021 [P] [US4] 撰寫常見錯誤檢查清單：列出 import 路徑、型別標註、async/await、`total=False` 等常見問題與修復方式，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T022 [US4] 撰寫完成後回報格式：定義 agent 產生完成後應列出的檔案清單與摘要格式，於 `.opencode/skills/flow-builder/SKILL.md`

**檢查點**: 驗證流程完整，agent 可依指引自動修復常見問題

---

## Phase 7: 收尾與跨 Story 整合

**目的**: Edge Case 處理、最終格式檢查

- [x] T023 撰寫 Edge Case 處理指引：功能重疊提醒、節點數超過 10 的拆分建議、繁體中文輸出規則，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T024 最終格式檢查：確認 YAML frontmatter 正確、所有 section 連貫、佔位符統一使用 `<>` 標記，於 `.opencode/skills/flow-builder/SKILL.md`
- [x] T025 執行 quickstart.md 驗證：依照 `specs/010-flow-builder-skill/quickstart.md` 的步驟確認 Skill 可正常使用

---

## 相依性與執行順序

### Phase 相依性

- **設定（Phase 1）**: 無相依性 — 可立即開始
- **基礎設施（Phase 2）**: 依賴 Phase 1 完成 — 阻斷所有 User Story
- **User Story（Phase 3-6）**: 皆依賴 Phase 2 完成
  - US1 和 US2 都是 P1，US1 定義工作流程、US2 定義模板，兩者互相補充
  - US3 和 US4 是 P2，可在 US1/US2 完成後進行
- **收尾（Phase 7）**: 依賴所有 User Story 完成

### User Story 相依性

- **User Story 1（P1）**: Phase 2 完成後即可開始，無其他 Story 相依
- **User Story 2（P1）**: Phase 2 完成後即可開始，與 US1 獨立但在同一檔案中
- **User Story 3（P2）**: 建議在 US1/US2 之後，因工具指引會引用工作流程步驟
- **User Story 4（P2）**: 建議在 US1/US2 之後，因驗證步驟會引用模板

### 各 Story 內部

- 同一 Story 中標記 [P] 的任務可平行執行
- US2 的 5 個模板任務（T012-T016）皆可平行撰寫

### 平行機會

- Phase 2 中的 T003 和 T004 可平行執行
- US2 的 T012-T016 模板任務皆可平行執行（不同 code block）
- US4 的 T020 和 T021 可平行執行

---

## 平行執行範例：User Story 2

```bash
# 同時啟動 5 個模板任務：
Task: "撰寫 FlowState TypedDict 模板"
Task: "撰寫 Node 工廠函式模板"
Task: "撰寫 StateGraph 定義模板"
Task: "撰寫 BaseFlowExecutor 子類別模板"
Task: "撰寫 pytest 測試模板"
```

---

## 實作策略

### MVP 優先（僅 User Story 1 + 2）

1. 完成 Phase 1: 設定
2. 完成 Phase 2: 基礎設施
3. 完成 Phase 3: User Story 1（10 步工作流程）
4. 完成 Phase 4: User Story 2（5 種模板）
5. **停止並驗證**: 確認 Skill 可載入、工作流程完整、模板語法正確
6. 此時 Skill 已具備核心價值，可先交付

### 增量交付

1. 設定 + 基礎設施 → 骨架就位
2. 新增 US1 + US2 → 核心可用（MVP）
3. 新增 US3 → 工具整合指引
4. 新增 US4 → 品質保證流程
5. 每步新增皆不影響已完成的部分

---

## 備註

- [P] 任務 = 不同區段、無相依性
- [Story] 標籤對應 spec.md 中的 User Story
- 所有任務都在同一個檔案（`.opencode/skills/flow-builder/SKILL.md`）中進行
- 所有內容以繁體中文撰寫
- 每完成一個檢查點即可驗證
