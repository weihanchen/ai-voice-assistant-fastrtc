# 資料模型：Flow Builder Agent Skill

**功能**: 010-flow-builder-skill  
**日期**: 2026-02-10

## 概述

此功能的產出是 OpenCode Agent Skill 檔案（SKILL.md），不涉及新的 Python 資料模型。以下記錄 Skill 檔案本身的結構模型，以及 Skill 模板中引用的現有資料模型。

## Skill 檔案結構

### SKILL.md 結構

```
YAML Frontmatter
├── name: string              # Skill 名稱（flow-builder）
├── description: string       # 觸發條件描述
├── allowed-tools: string     # 允許使用的工具清單
└── compatibility: string     # 相容性（opencode）

Markdown Body
├── 觸發條件                   # 關鍵字清單
├── 工作流程                   # 10 步驟
│   ├── Step 1: 需求解析
│   ├── Step 2: 現有工具盤點
│   ├── Step 3: 整合策略判斷
│   ├── Step 4: 設計 FlowState
│   ├── Step 5: 設計節點
│   ├── Step 6: 設計 StateGraph
│   ├── Step 7: 產生 FlowState 程式碼
│   ├── Step 8: 產生節點程式碼
│   ├── Step 9: 產生 Graph + Executor 程式碼
│   └── Step 10: 產生測試 + 驗證
├── 程式碼模板                 # 5 種模板（fenced code blocks）
│   ├── FlowState TypedDict
│   ├── Node 工廠函式（3 種類型）
│   ├── StateGraph 定義
│   ├── BaseFlowExecutor 子類別
│   └── pytest 測試
├── 品質規則
├── 常見錯誤檢查清單
└── 完成後回報格式
```

## 模板引用的現有資料模型

以下是 Skill 模板中需要引用的現有架構元件（來自 009 重構）：

### BaseFlowExecutor（ABC）

| 成員 | 型別 | 說明 |
|------|------|------|
| `flow_name` | `@property -> str` | 流程唯一識別名稱 |
| `execute(user_input, on_node_change)` | `async -> str` | 執行流程 |
| `get_visualization()` | `-> str \| None` | 取得 Mermaid 圖 |

### FlowState（TypedDict, total=False）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `user_input` | `str` | 使用者輸入 |
| `intent` | `IntentType` | 意圖分類 |
| `tool_name` | `str \| None` | 工具名稱 |
| `tool_args` | `dict \| None` | 工具參數 |
| `tool_result` | `dict \| None` | 工具結果 |
| `travel_state` | `TravelPlanState \| None` | 子流程狀態 |
| `response` | `str` | 最終回應 |
| `error` | `str \| None` | 錯誤訊息 |

### NodeChangeCallback

```python
NodeChangeCallback = Callable[[str, NodeStatus], None]
```

### FlowRegistry

| 方法 | 簽名 | 說明 |
|------|------|------|
| `register(executor)` | `BaseFlowExecutor -> None` | 註冊執行器 |
| `get(name)` | `str -> BaseFlowExecutor` | 取得執行器 |
| `list_flows()` | `-> list[str]` | 列出已註冊流程 |
| `has(name)` | `str -> bool` | 檢查是否已註冊 |

## 狀態轉換

此功能無狀態轉換（Skill 是靜態 Markdown 檔案）。
