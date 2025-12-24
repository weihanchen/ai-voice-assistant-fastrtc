# Research: AI Voice Assistant 核心架構

**Date**: 2025-12-23
**Spec**: [spec.md](./spec.md)

## 技術決策

### 1. OpenAI SDK 使用方式

**Decision**: 使用 `openai` 官方 SDK 的 `AsyncOpenAI` 客戶端

**Rationale**:
- 官方支援，維護穩定
- 內建 Function Calling 支援
- 支援 async/await，適合後續 FastRTC 整合
- 型別標註完整

**Alternatives Considered**:
- `httpx` 直接呼叫 API：需自行處理認證與錯誤，維護成本高
- `litellm`：抽象層過多，此階段不需要多 Provider 支援

### 2. 資料驗證框架

**Decision**: 使用 Pydantic v2

**Rationale**:
- Constitution 指定使用 Pydantic
- 內建 JSON Schema 生成，適合 Function Calling parameters
- `pydantic-settings` 提供環境變數管理
- 與 OpenAI SDK 相容性佳

**Alternatives Considered**:
- `dataclasses`：缺乏驗證功能
- `attrs`：社群較小，文件較少

### 3. 非同步設計

**Decision**: 核心類別使用 `async/await`

**Rationale**:
- FastRTC 是非同步框架
- OpenAI API 呼叫為 I/O bound
- 為後續語音串流整合做準備

**Alternatives Considered**:
- 同步設計：會阻塞語音串流處理

### 4. 專案結構

**Decision**: 使用 `src/` layout

**Rationale**:
- Python 社群推薦做法
- 避免 import 路徑問題
- 與 Constitution 目錄結構規範一致

**Alternatives Considered**:
- Flat layout：小專案可行，但不利於擴展

### 5. Tool 註冊機制

**Decision**: 手動註冊（顯式呼叫 `registry.register(tool)`）

**Rationale**:
- 此階段簡單明確
- 避免過早引入裝飾器或自動發現機制
- 符合 YAGNI 原則

**Alternatives Considered**:
- 裝飾器自動註冊：增加複雜度，此階段不需要
- 掃描模組自動發現：過於隱式，不利調試

---

## 技術細節

### OpenAI Function Calling 格式

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查詢指定城市的天氣",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名稱"
                    }
                },
                "required": ["city"]
            }
        }
    }
]
```

### OpenAI API 回應結構

當 LLM 決定呼叫工具時：

```python
response.choices[0].message.tool_calls = [
    {
        "id": "call_abc123",
        "type": "function",
        "function": {
            "name": "get_weather",
            "arguments": '{"city": "台北"}'
        }
    }
]
```

### Tool 執行結果回傳格式

```python
# 將 Tool 結果回傳給 LLM
messages.append({
    "role": "tool",
    "tool_call_id": "call_abc123",
    "content": '{"temperature": 25, "condition": "晴天"}'
})
```

---

## 待確認項目

| 項目 | 狀態 | 備註 |
|------|------|------|
| OpenAI SDK 版本 | ✅ 已確認 | >=1.58.x |
| Pydantic 版本 | ✅ 已確認 | >=2.10.x |
| pytest-asyncio 設定 | ✅ 已確認 | asyncio_mode = "auto" |

---

## 參考資源

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [Python Packaging User Guide - src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
