# Contract: LLMClient

**Date**: 2025-12-23
**Module**: `src/voice_assistant/llm/client.py`

## Overview

封裝 OpenAI API 呼叫的客戶端類別，支援 Function Calling。

---

## Interface

```python
class LLMClient:
    """OpenAI LLM 客戶端"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
    ) -> None:
        """
        初始化 LLM 客戶端。

        Args:
            api_key: OpenAI API Key
            model: 使用的模型名稱
            timeout: API 呼叫逾時秒數
        """
        ...

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> ChatMessage:
        """
        發送對話請求。

        Args:
            messages: 對話歷史
            tools: OpenAI Function Calling 工具定義
            system_prompt: 系統提示詞（會插入到 messages 開頭）

        Returns:
            LLM 回應的 ChatMessage

        Raises:
            LLMError: API 呼叫失敗時
        """
        ...
```

---

## Error Handling

```python
class LLMError(Exception):
    """LLM 相關錯誤基底類別"""
    pass

class LLMConnectionError(LLMError):
    """連線錯誤"""
    pass

class LLMAuthenticationError(LLMError):
    """認證錯誤（API Key 無效）"""
    pass

class LLMRateLimitError(LLMError):
    """速率限制錯誤"""
    pass
```

---

## Usage Example

```python
from voice_assistant.llm.client import LLMClient
from voice_assistant.llm.schemas import ChatMessage

# 初始化
client = LLMClient(api_key="sk-xxx")

# 簡單對話
messages = [ChatMessage(role="user", content="你好")]
response = await client.chat(messages)
print(response.content)  # "你好！有什麼我可以幫助你的嗎？"

# 帶 Function Calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查詢天氣",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        }
    }
]
response = await client.chat(messages, tools=tools)
if response.tool_calls:
    print(response.tool_calls[0].function)  # {"name": "get_weather", "arguments": '{"city": "台北"}'}
```

---

## Behavior Specifications

### B-001: System Prompt 處理

當 `system_prompt` 參數有值時，客戶端 MUST 將其作為 `role="system"` 的訊息插入到 `messages` 列表開頭。

### B-002: 空 tools 處理

當 `tools=None` 或 `tools=[]` 時，客戶端 MUST NOT 在 API 請求中包含 `tools` 參數。

### B-003: 錯誤轉換

客戶端 MUST 將 OpenAI SDK 的錯誤轉換為自定義 `LLMError` 子類別：
- `openai.AuthenticationError` → `LLMAuthenticationError`
- `openai.RateLimitError` → `LLMRateLimitError`
- `openai.APIConnectionError` → `LLMConnectionError`

### B-004: 回應轉換

客戶端 MUST 將 OpenAI API 回應轉換為 `ChatMessage` 結構，包含：
- `role`: 固定為 "assistant"
- `content`: 回應文字（可能為 None）
- `tool_calls`: 工具呼叫列表（可能為 None）
