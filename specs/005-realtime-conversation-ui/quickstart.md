# Quickstart: Realtime Conversation UI

**Feature**: 005-realtime-conversation-ui
**Date**: 2025-12-31

## 概述

本指南說明如何在現有語音助理中啟用即時對話顯示功能。

---

## 前置需求

- 已完成 001-fastrtc-voice-pipeline 設定
- Python 3.13+ 環境
- FastRTC >=0.0.33

---

## 快速整合

### 1. 更新 schemas.py

新增對話訊息和歷史模型：

```python
# src/voice_assistant/voice/schemas.py

class ConversationMessage(BaseModel):
    """單一對話訊息"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationHistory(BaseModel):
    """對話歷史"""
    messages: list[ConversationMessage] = Field(default_factory=list)
    max_messages: int = 40

    def add_user_message(self, content: str) -> None:
        self._add_message("user", content)

    def add_assistant_message(self, content: str) -> None:
        self._add_message("assistant", content)

    def _add_message(self, role: str, content: str) -> None:
        self.messages.append(ConversationMessage(role=role, content=content))
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def to_gradio_format(self) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.messages]
```

### 2. 建立 UI 模組

```python
# src/voice_assistant/voice/ui/blocks.py

import gradio as gr
from gradio_webrtc import WebRTC

def create_conversation_ui() -> tuple[gr.Blocks, gr.Textbox, gr.Chatbot, WebRTC]:
    """建立對話 UI"""
    with gr.Blocks(title="AI 語音助理") as blocks:
        gr.Markdown("# 🎤 AI 語音助理")

        status = gr.Textbox(
            label="狀態",
            value="🟢 待命",
            interactive=False,
        )

        chatbot = gr.Chatbot(
            label="對話記錄",
            type="messages",
            height=400,
        )

        audio = WebRTC(
            mode="send-receive",
            modality="audio",
            label="語音輸入/輸出",
        )

    return blocks, status, chatbot, audio
```

### 3. 修改 pipeline.py

在 `process_audio` 中 yield AdditionalOutputs：

```python
from fastrtc import AdditionalOutputs

def process_audio_with_outputs(self, audio):
    # ... STT 處理 ...
    user_text = self.stt.stt(audio)
    self.state.history.add_user_message(user_text)

    # 發送 UI 更新
    yield AdditionalOutputs(
        self.state.history.to_gradio_format(),
        "⏳ 處理中..."
    )

    # ... LLM 處理 ...
    response = self._call_llm(user_text)
    self.state.history.add_assistant_message(response)

    yield AdditionalOutputs(
        self.state.history.to_gradio_format(),
        "🔊 回應中..."
    )

    # ... TTS 串流 ...
    for chunk in self.tts.stream(response):
        yield chunk

    yield AdditionalOutputs(
        self.state.history.to_gradio_format(),
        "🟢 待命"
    )
```

### 4. 整合 Stream 與 UI

```python
# src/voice_assistant/voice/handlers/reply_on_pause.py

from voice_assistant.voice.ui.blocks import create_conversation_ui

def create_voice_stream_with_ui(settings: Settings) -> Stream:
    # ... 現有設定 ...

    # 建立自定義 UI
    blocks, status, chatbot, audio = create_conversation_ui()

    # 設定串流事件
    audio.stream(
        fn=ReplyOnPause(pipeline.process_audio_with_outputs, ...),
        inputs=[audio],
        outputs=[audio],
    )

    # 設定額外輸出更新
    audio.on_additional_outputs(
        fn=lambda history, status_text: (history, status_text),
        outputs=[chatbot, status],
        queue=False,
    )

    # 建立 Stream 並設定 UI
    stream = Stream(handler=..., modality="audio", mode="send-receive")
    stream.ui = blocks

    return stream
```

---

## 使用方式

1. 啟動應用程式：
   ```bash
   uv run python -m voice_assistant.main
   ```

2. 開啟瀏覽器訪問 `http://localhost:7860`

3. 對話功能：
   - 點擊麥克風開始錄音
   - 說話後停頓 0.5 秒觸發處理
   - 觀察狀態從「待命」→「聆聽」→「處理」→「回應」
   - 對話記錄即時顯示於聊天區

---

## 驗證

### 功能檢查清單

- [ ] 狀態指示器正確顯示當前狀態
- [ ] 使用者語音辨識結果即時顯示
- [ ] AI 回應文字同步顯示
- [ ] 對話歷史可捲動瀏覽
- [ ] 多輪對話正確保留

### 效能檢查

- [ ] ASR 文字顯示延遲 < 1 秒
- [ ] 狀態更新延遲 < 0.3 秒
- [ ] 語音播放流暢無卡頓

---

## 疑難排解

### 問題：對話記錄不更新

**原因**：`on_additional_outputs` 未正確綁定

**解決**：確認 `queue=False` 設定正確

### 問題：狀態卡在「處理中」

**原因**：LLM 或 TTS 處理異常

**解決**：檢查後台 log 確認錯誤訊息

### 問題：音訊正常但無文字

**原因**：`AdditionalOutputs` 未正確 yield

**解決**：確認 `process_audio_with_outputs` 正確實作
