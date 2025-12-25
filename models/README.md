# Models Directory

This directory is used as the HuggingFace cache directory for TTS models.

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

After downloading, you can run offline:

```bash
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
- See `.env.example` for model path configuration
