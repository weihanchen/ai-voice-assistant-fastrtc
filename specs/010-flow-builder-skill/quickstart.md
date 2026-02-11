# 快速入門：Flow Builder Agent Skill

**功能**: 010-flow-builder-skill  
**日期**: 2026-02-10

## 前置條件

- OpenCode CLI 已安裝並可運行
- 專案已完成 009 架構重構（BaseFlowExecutor、FlowRegistry 可用）
- `.opencode/skills/` 目錄存在

## 快速使用

### 1. 確認 Skill 已就位

```
.opencode/skills/flow-builder/SKILL.md
```

### 2. 在 OpenCode 中觸發

使用以下任一關鍵字觸發 Skill：
- 「建立流程」
- 「新增 flow」
- 「設計一個工作流」

### 3. 描述你的流程

```
建立一個美食推薦流程：
1. 確認使用者所在城市
2. 查詢該城市天氣
3. 根據天氣推薦室內或戶外餐廳
4. 顯示餐廳資訊
```

### 4. 預期產出

Skill 會指引 OpenCode agent 產生以下檔案：

```
src/voice_assistant/flows/
├── state.py                              # 新增子流程 State（修改既有檔案）
├── nodes/<domain>/
│   ├── __init__.py
│   ├── <node_1>.py                       # 節點工廠函式
│   ├── <node_2>.py
│   └── ...
├── graphs/<domain>.py                    # StateGraph 定義
└── <domain>_executor.py                  # BaseFlowExecutor 子類別（可選）

tests/unit/flows/
└── test_<domain>.py                      # pytest 測試
```

### 5. 驗證

產生程式碼後，執行：

```bash
uv run ruff check src/voice_assistant/flows/
uv run ruff format src/voice_assistant/flows/
uv run pytest tests/unit/flows/test_<domain>.py -v
```

## 開發指引

### 新增節點到現有流程

如果你要擴展現有流程（如 travel_planner），只需：
1. 在 `flows/nodes/<domain>/` 新增節點檔案
2. 在對應的 `flows/graphs/<domain>.py` 新增節點和邊

### 建立全新獨立流程

如果你要建立與現有意圖完全無關的流程：
1. 建立新的 FlowState 子狀態
2. 建立節點和 graph
3. 建立 BaseFlowExecutor 子類別
4. 在 composition root 中 `flow_registry.register()` 註冊
