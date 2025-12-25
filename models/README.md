# Models Directory

This directory contains model files for ASR and TTS components.

## Required Model Files

### Kokoro TTS (Chinese)

Download from [kokoro-onnx releases](https://github.com/thewh1teagle/kokoro-onnx/releases):

**Linux/macOS (使用 curl):**

```bash
# Quantized model (~80MB)
curl -L -o kokoro-v1.0.int8.onnx \
    https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx

# Voice files
curl -L -o voices-v1.0.bin \
    https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

**Windows (PowerShell):**

```powershell
# Quantized model (~80MB)
Invoke-WebRequest -Uri "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx" -OutFile "kokoro-v1.0.int8.onnx"

# Voice files
Invoke-WebRequest -Uri "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin" -OutFile "voices-v1.0.bin"
```

### faster-whisper ASR

The `faster-whisper` library automatically downloads models on first use.
Models are cached in `~/.cache/huggingface/hub/`.

Default model: `tiny` (~39MB)

## Directory Structure

```text
models/
├── README.md
├── .gitkeep
├── kokoro-v1.0.int8.onnx    # TTS model (download required)
└── voices-v1.0.bin          # Voice embeddings (download required)
```

## Notes

- Model files are not committed to git (too large)
- Download models before running the voice assistant
- See `.env.example` for model path configuration
