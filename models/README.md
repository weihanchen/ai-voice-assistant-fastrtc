# Models Directory

This directory is used as the HuggingFace cache directory for TTS models.

## Configuration

There are two related environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `TTS_MODEL_PATH` | Application-level setting (used by voice_assistant) | `models` |
| `HF_HOME` | HuggingFace cache directory (set automatically by the app) | `models` |

The application reads `TTS_MODEL_PATH` from `.env` and sets `HF_HOME` internally.
You typically only need to set `TTS_MODEL_PATH`.

## Kokoro TTS (Chinese)

The project uses the native `kokoro` + `misaki[zh]` packages for Chinese TTS.
Models are automatically downloaded from HuggingFace on first use.

**Model**: [hexgrad/Kokoro-82M-v1.1-zh](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh) (~327MB)

### Pre-download Models

```bash
# Download models before first run
uv run python scripts/download_models.py
```

### Offline Mode

After downloading, you can run offline by setting:

```bash
# In .env file
HF_HUB_OFFLINE=1

# Or as environment variable
export HF_HUB_OFFLINE=1
```

## faster-whisper ASR

The `faster-whisper` library automatically downloads models on first use.
Models are cached in `~/.cache/huggingface/hub/`.

Default model: `tiny` (~39MB)

## Directory Structure

```text
models/
├── README.md
├── .gitkeep
└── hub/                # HuggingFace cache (auto-created)
    └── models--hexgrad--Kokoro-82M-v1.1-zh/
```

## Notes

- Model files are not committed to git (too large)
- Set `TTS_MODEL_PATH=models` in `.env` to use this directory
- See `.env.example` for complete configuration options
