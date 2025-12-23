# AI Voice Assistant Constitution

## Core Principles

### I. Tool-First Architecture（工具優先架構）

- 所有外部資料查詢必須透過獨立、可測試的 Tool 模組實現
- 每個 Tool 繼承統一的 `BaseTool` 基底類別
- 禁止在 Tool 以外的地方直接呼叫外部 API
- 透過 `ToolRegistry` 自動化註冊機制管理工具

### II. LLM Auto-Routing（LLM 自動路由）

- 語音輸入統一透過 FastRTC Stream 入口處理
- 意圖識別完全由 LLM Function Calling 決定
- 前端/語音層不做意圖判斷邏輯
- Tool 選擇由 OpenAI `tools` 參數自動決定

### III. Human-Friendly Response（人性化回覆）

- 所有輸出必須經過 LLM 轉換為自然語言
- 使用口語化繁體中文，適合語音輸出
- 禁止直接回傳原始 JSON 或技術性資料
- 數字表達需考慮聽覺友善性

### IV. Safe Boundary（安全邊界）

- 明確定義處理範圍：天氣查詢、匯率換算、股價查詢
- 範圍外問題必須禮貌拒絕，不得編造答案
- 禁止虛構數據，所有資料必須來自工具取得
- 工具呼叫失敗時需誠實告知使用者

### V. Extensible Design（可擴展設計）

- LLM Provider 抽象化，支援未來更換
- Tool 註冊機制自動化，新增工具無需修改核心邏輯
- 配置與程式碼分離，透過環境變數管理

---

## Technical Stack（技術規範）

> **此為專案唯一技術標準，所有文件與實作必須遵循**

### Runtime & Package Management

| 項目 | 技術 | 版本 | 說明 |
|------|------|------|------|
| **Python** | Python | 3.14 | 專案指定版本 |
| **套件管理** | uv | >=0.5.x | 取代 pip/poetry |
| **虛擬環境** | uv venv | - | 內建於 uv |

### Core Framework

| 項目 | 技術 | 版本 | 說明 |
|------|------|------|------|
| **語音框架** | FastRTC | >=0.0.33 | WebRTC 實時通訊 |
| **ASR** | Moonshine | FastRTC 內建 | 本地 CPU 語音轉文字 |
| **TTS** | Kokoro | FastRTC 內建 | 本地 CPU 文字轉語音 |
| **UI** | Gradio | >=5.x | FastRTC 內建 WebRTC 介面 |

### LLM & AI

| 項目 | 技術 | 版本 | 說明 |
|------|------|------|------|
| **LLM SDK** | openai | >=1.58.x | OpenAI Python SDK |
| **LLM Model** | GPT-4o-mini | - | 支援 Function Calling |

### External APIs

| 功能 | API | 條件 |
|------|-----|------|
| **天氣** | Open-Meteo | 免費，無需 API Key |
| **匯率** | Frankfurter | 免費，無需 API Key |
| **股價** | yfinance | 免費 Python 套件 |

### Development Tools

| 項目 | 技術 | 版本 | 說明 |
|------|------|------|------|
| **Linting** | Ruff | >=0.8.x | 程式碼檢查與格式化 |
| **Type Check** | Pyright | latest | 靜態型別檢查 |
| **Testing** | pytest | >=8.x | 單元測試框架 |
| **Validation** | Pydantic | >=2.10.x | 資料驗證 |

### Deployment

| 項目 | 技術 | 說明 |
|------|------|------|
| **Container** | Docker | 容器化部署 |
| **Orchestration** | Docker Compose v2 | 服務編排 |

---

## Quality Gates（品質門檻）

### 測試要求

- 每個 Tool 必須有單元測試
- API 整合需有 mock 測試
- 端對端語音對話測試

### 效能要求

- 語音回應延遲 < 5 秒
- API 呼叫需有逾時處理
- 實作優雅降級機制

### 程式碼品質

- 所有程式碼必須通過 Ruff 檢查
- 關鍵模組需有型別標註
- pre-commit hooks 強制執行

---

## Governance（治理）

- 本憲章為專案最高指導原則
- 所有 Spec、Plan、實作必須符合憲章規範
- 技術棧變更必須先更新憲章
- PR 合併前需確認符合憲章要求
- 修改憲章需明確記錄變更原因與版本更新

---

**Version**: 1.0.0 | **Ratified**: 2025-12-23 | **Last Amended**: 2025-12-23
