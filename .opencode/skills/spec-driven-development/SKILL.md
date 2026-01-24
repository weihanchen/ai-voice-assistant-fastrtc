---
name: spec-driven-development
description: 專案遵循 Spec-Driven Development 開發流程，確保所有功能都按照統一規範實作
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: spec-driven
  language: python
  framework: voice-assistant
---

## Spec-Driven Development Skill

### 專案概述
AI 語音助理專案採用 Spec-Driven Development 方法，所有功能開發必須遵循統一流程和架構原則。

### 核心開發流程

#### 1. Spec-Kit 標準流程
每個新功能必須依序執行：
```
/speckit.specify  →  撰寫 spec.md (定義 What & Why)
        ↓
/speckit.plan     →  撰寫 plan.md (定義 How)
        ↓
/speckit.tasks    →  撰寫 tasks.md (拆解可執行任務)
        ↓
/speckit.implement →  逐一實作任務
```

#### 2. 禁止直接建立功能分支
- 不可直接使用 `git checkout -b NNN-feature`
- 必須透過 `/speckit.specify` 建立規格目錄
- 每個 spec 目錄包含：spec.md, plan.md, tasks.md, checklists/

### 技術架構原則

#### 1. 核心技術棧
- **Python 3.13**：使用型別標註，現代語法特性
- **uv + venv**：套件管理和虛擬環境
- **OpenAI SDK + Pydantic**：LLM 整合和資料驗證
- **FastRTC**：實時語音通訊框架
- **LangGraph**：流程編排（006+）
- **Ruff**：程式碼檢查與格式化

#### 2. 架構設計原則
- **KISS & YAGNI**：追求極致簡潔，拒絕過度設計
- **SOLID 原則**：嚴格遵守，尤其是 SRP 和 ISP
- **Clean Code & DRY**：消除重複邏輯，注重自解釋性
- **防禦性程式設計**：Null Check, Exception Handling
- **效能敏感**：關注系統開銷、資源佔用、演算法複雜度

#### 3. 專案結構模式
```
src/voice_assistant/
├── main.py              # 入口點
├── config.py            # 環境變數配置
├── llm/                 # LLM 客戶端模組
├── tools/               # 查詢工具模組
├── flows/               # LangGraph 流程模組 (006+)
├── agents/              # 多代理模組 (007+)
├── roles/               # 角色系統模組 (008+)
└── voice/               # 語音管線模組
```

### 程式碼品質標準

#### 1. 命名規範
- **Boolean**: `is_*` / `has_*` / `can_*`
- **函式**: 動詞開頭 `get_*` / `create_*` / `handle_*`
- **類別**: PascalCase，繼承自適當的基底類別
- **常數**: UPPER_SNAKE_CASE

#### 2. 型別標註
- 所有函式參數和回傳值必須有型別標註
- 使用 `from __future__ import annotations`
- 複雜型別使用 `typing` 模組
- Pydantic 模型用於資料驗證

#### 3. 錯誤處理
- 外部 API 呼叫需處理異常（httpx 請求等）
- 內部邏輯讓異常自然冒泡，由上層統一處理
- 使用 Pydantic 驗證外部輸入資料
- 非同步函式使用 `async/await`

#### 4. 文檔和註解
- **繁體中文優先**：所有文件、註解、commit message
- Docstring 使用 Google 風格
- 類別和重要函式必須有 Docstring
- 避免過度註解，程式碼應自解釋

### 開發工作流程

#### 1. 開發前準備
```bash
# 啟動虛擬環境
.venv\Scripts\activate  # Windows

# 安裝依賴
uv sync
```

#### 2. 實作階段
- 遵循現有 OOP 架構（BaseTool/BaseAgent 繼承模式）
- 重用現有工具和模組，避免重複造輪
- 先寫測試，再實作功能（TDD）
- 即時執行 lint 和 format 檢查

#### 3. 測試和品質檢查
```bash
# 執行測試
uv run pytest

# Lint 檢查和修正
uv run ruff check --fix .
uv run ruff format .
```

#### 4. Commit 前流程
1. **Code Review** - AI 審查邏輯、安全性、最佳實踐
2. **修正問題** - 根據審查建議調整程式碼
3. **Lint + Format** - 執行程式碼檢查和格式化
4. **Commit** - 提交變更

#### 5. Commit Message 格式
```
<type>: <簡述>

type: feat | fix | refactor | docs | test | chore
```

### 特殊模組開發指南

#### 1. Tools 開發
- 繼承 `BaseTool` 抽象類別
- 實作 `name`, `description`, `parameters`, `execute` 方法
- 使用 `ToolResult` 包裝回傳結果
- 支援 OpenAI Function Calling 格式

#### 2. Agents 開發 (007+)
- 繼承 `BaseAgent` 抽象類別
- 實作 `agent_type` 和 `execute` 方法
- 使用 `AgentTask` 和 `AgentResult`
- 重用現有 Tool，不重複實作

#### 3. Roles 開發 (008+)
- 繼承 `BaseRole` 抽象類別
- 實作動態系統提示詞切換
- 最小侵入性設計原則
- 支援語音指令自動切換

#### 4. Flows 開發 (006+)
- 使用 LangGraph StateGraph
- 實作流程節點和路由邏輯
- 支援流程視覺化輸出
- 保留現有 Tool 功能

### 安全性和最佳實踐

#### 1. 安全性
- 禁止硬編碼密鑰或敏感資訊
- 檢查注入風險（SQL、Command Injection）
- 外部輸入必須驗證和清理
- 使用環境變數管理配置

#### 2. 效能最佳實踐
- 非同步操作優先（async/await）
- 避免阻塞 I/O 操作
- 合理使用快機制
- 監控資源使用情況

#### 3. 可維護性
- 單一職責原則
- 依賴注入模式
- 介面隔離原則
- 模組化設計

### 測試策略

#### 1. 測試結構
```
tests/
├── unit/                 # 單元測試
├── integration/          # 整合測試
├── smoke/               # 煙霧測試
└── fixtures/            # 測試資料
```

#### 2. 測試原則
- 每個功能模組都對應測試檔案
- 使用 pytest 和 pytest-asyncio
- Mock 外部 API 呼叫
- 測試覆蓋率目標：>80%

### 範例實作模式

#### 1. 新 Tool 範例
```python
class NewTool(BaseTool):
    @property
    def name(self) -> str:
        return "new_tool"
    
    @property
    def description(self) -> str:
        return "新工具描述"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
            },
            "required": ["param1"],
        }
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        # 實作邏輯
        return ToolResult.success(data=result)
```

#### 2. 新 Agent 範例
```python
class NewAgent(BaseAgent):
    @property
    def agent_type(self) -> AgentType:
        return AgentType.NEW
    
    async def execute(self, task: AgentTask) -> AgentResult:
        # 實作邏輯
        return AgentResult.success(response=response)
```

### 使用時機

當你需要：
- 開發新功能（009, 010...）
- 重構現有程式碼
- 實作新的 Tool/Agent/Role
- 進行程式碼審查
- 撰寫測試
- 優化效能

### 注意事項

- 必須遵循專案的 Constitution 參考文件
- 不可修改 Protected Files（CLAUDE.md, AGENTS.md）
- 使用 `uv run` 執行所有 Python 指令
- 優先考慮重用現有模組和工具
- 保持程式碼簡潔和可讀性

---

這個 Skill 確保所有開發都遵循專案的統一標準和最佳實踐。