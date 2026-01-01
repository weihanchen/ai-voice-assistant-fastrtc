# UI Components Contract

**Feature**: 005-realtime-conversation-ui
**Date**: 2025-12-31

## 概述

定義 Gradio Blocks UI 元件的介面契約，確保 UI 層與資料層的正確整合。

---

## Component 1: create_conversation_ui

建立對話 UI 的 Gradio Blocks 實例。

### 函式簽名

```python
def create_conversation_ui() -> gr.Blocks:
    """建立對話 UI

    Returns:
        Gradio Blocks 實例，包含：
        - 狀態顯示區
        - 對話歷史區（Chatbot）
        - WebRTC 音訊元件

    Components:
        - status_display: gr.Textbox (readonly)
        - chatbot: gr.Chatbot
        - audio: WebRTC
    """
```

### 元件佈局

```
gr.Blocks():
    gr.Markdown("# AI 語音助理")
    status_display = gr.Textbox(label="狀態", interactive=False)
    chatbot = gr.Chatbot(type="messages")
    audio = WebRTC(mode="send-receive", modality="audio")
```

### 回傳結構

```python
@dataclass
class UIComponents:
    blocks: gr.Blocks          # Gradio Blocks 實例
    status_display: gr.Textbox # 狀態顯示元件
    chatbot: gr.Chatbot        # 對話歷史元件
    audio: WebRTC              # 音訊元件
```

---

## Component 2: setup_stream_with_ui

整合 FastRTC Stream 與自定義 UI。

### 函式簽名

```python
def setup_stream_with_ui(
    stream: Stream,
    pipeline: VoicePipeline,
) -> gr.Blocks:
    """設定 Stream 使用自定義 UI

    Args:
        stream: FastRTC Stream 實例
        pipeline: 語音管線實例（提供對話狀態）

    Returns:
        配置好的 Gradio Blocks 實例

    Side Effects:
        - 設定 stream.ui 為自定義 Blocks
        - 註冊 on_additional_outputs 事件處理器
    """
```

### 事件綁定

```python
# 音訊串流事件
audio.stream(
    fn=ReplyOnPause(pipeline.process_audio_with_outputs),
    inputs=[audio],
    outputs=[audio],
)

# 額外輸出事件（更新 UI）
audio.on_additional_outputs(
    fn=update_ui,
    outputs=[chatbot, status_display],
    queue=False,
)
```

---

## Component 3: update_ui callback

處理 AdditionalOutputs 的 UI 更新回呼。

### 函式簽名

```python
def update_ui(
    history: list[dict],
    status: str,
) -> tuple[list[dict], str]:
    """更新 UI 元件

    Args:
        history: Gradio Chatbot 格式的對話歷史
                 [{"role": "user", "content": "..."},
                  {"role": "assistant", "content": "..."}]
        status: 狀態顯示文字（如 "🟢 待命"）

    Returns:
        (history, status) 直接傳遞給 Gradio 元件
    """
```

---

## Pipeline Extension: process_audio_with_outputs

擴展 VoicePipeline 以支援 AdditionalOutputs。

### 函式簽名

```python
def process_audio_with_outputs(
    self,
    audio: tuple[int, NDArray[np.float32]],
) -> Iterator[tuple[int, NDArray[np.float32]] | AdditionalOutputs]:
    """處理音訊並回傳額外輸出

    Args:
        audio: (sample_rate, audio_array) 使用者語音

    Yields:
        - AdditionalOutputs(history, status): 每次狀態變更時
        - (sample_rate, audio_chunk): TTS 音訊片段
    """
```

### Yield 時機

| 時機 | Yield 內容 |
|------|-----------|
| STT 完成後 | `AdditionalOutputs(history, "⏳ 處理中...")` |
| LLM 回應後 | `AdditionalOutputs(history, "🔊 回應中...")` |
| TTS 播放中 | `(sample_rate, audio_chunk)` |
| 回應完成後 | `AdditionalOutputs(history, "🟢 待命")` |

---

## Error Handling

### UI 更新失敗

```python
def update_ui(history, status):
    try:
        return (history, status)
    except Exception as e:
        logger.error(f"UI 更新失敗: {e}")
        return ([], "❌ UI 錯誤")
```

### 空對話處理

```python
# Chatbot 接受空列表
if not history:
    return ([], status)
```

---

## 測試契約

### 單元測試需求

| 測試案例 | 驗證項目 |
|----------|----------|
| `test_create_conversation_ui` | UI 元件正確建立 |
| `test_update_ui_with_history` | 對話記錄正確更新 |
| `test_update_ui_status_change` | 狀態正確顯示 |
| `test_empty_history_handling` | 空對話正確處理 |

### Mock 需求

```python
# 測試時 mock WebRTC 元件
@pytest.fixture
def mock_webrtc():
    with patch("gradio_webrtc.WebRTC") as mock:
        yield mock
```
