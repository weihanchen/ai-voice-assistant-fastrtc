# Models Directory

This directory contains all AI models for the voice assistant.

## Directory Structure

```text
models/
├── README.md
├── .gitkeep
├── hub/                          # HuggingFace cache
│   ├── models--hexgrad--Kokoro-82M-v1.1-zh/      # TTS
│   └── models--freddyaboulton--silero-vad/       # VAD
└── whisper/                      # ASR: faster-whisper models
    └── models--Systran--faster-whisper-small/
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_MODEL_PATH` | `models` | TTS 模型快取目錄（HF_HOME） |
| `WHISPER_MODEL_PATH` | `models/whisper` | ASR 模型快取目錄 |
| `WHISPER_MODEL_SIZE` | `small` | Whisper 模型大小 |

## Models

### TTS: Kokoro (Chinese)

- **Model**: [hexgrad/Kokoro-82M-v1.1-zh](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh)
- **Size**: ~327MB
- **Location**: `models/hub/`

### ASR: faster-whisper

- **Model**: Systran/faster-whisper-small (default)
- **Size**: ~244MB (small)
- **Location**: `models/whisper/`

Available sizes: `tiny` (~39MB), `base` (~74MB), `small` (~244MB), `medium` (~769MB), `large` (~1.5GB)

### VAD: Silero VAD

- **Model**: [freddyaboulton/silero-vad](https://huggingface.co/freddyaboulton/silero-vad)
- **Size**: ~2MB
- **Location**: `models/hub/`
- **Note**: Automatically downloaded by faster-whisper when `vad_filter=True`

## Pre-download Models

```bash
# Download all models before first run
uv run python scripts/download_models.py
```

## Offline Mode

After downloading, you can run offline:

```bash
# In .env file
HF_HUB_OFFLINE=1
```

## Notes

- Model files are not committed to git (too large)
- Models are automatically downloaded on first use if not present
- See `.env.example` for complete configuration options
