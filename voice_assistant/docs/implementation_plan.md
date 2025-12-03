# Implementation Plan: Open Source Voice Assistant

# Goal Description
Build a lightweight, modular, and fully open-source voice assistant optimized for the Orange Pi 3 LTS (Cortex-A53, 2GB RAM). The system will feature interchangeable LLM backends (LAN, Groq, Gemini) and prioritize low latency using an asynchronous pipeline.

## User Review Required
> [!IMPORTANT]
> **API Keys:** For Groq and Gemini usage, you will need to provide API keys in a `.env` file.
> **Porcupine Access Key:** If choosing Porcupine for wake word, a free Access Key from the Picovoice console is required.
> **Hardware Access:** This plan assumes access to audio devices (microphone/speaker). On a headless server, ensure `user` has `audio` group privileges.

## Proposed Changes

### Project Structure
We will create a Python project with the following structure:
```
voice_assistant/
├── main.py                 # Entry point, orchestrates the async loop
├── config.yaml             # Configuration (backends, models, timeouts)
├── .env                    # Secrets (API keys)
├── core/
│   ├── audio.py            # Audio capture and playback (PyAudio/SoundDevice)
│   ├── pipeline.py         # Manages the flow: Wake -> STT -> LLM -> TTS
│   └── utils.py            # Helper functions
└── modules/
    ├── wakeword/
    │   ├── base.py         # Abstract Base Class
    │   ├── porcupine.py    # Porcupine implementation
    │   └── openwakeword.py # OpenWakeWord implementation
    ├── stt/
    │   ├── base.py
    │   └── vosk_stt.py     # Vosk implementation
    ├── tts/
    │   ├── base.py
    │   └── piper_tts.py    # Piper implementation
    └── llm/
        ├── base.py
        ├── lan_client.py   # Connects to local LLM (Ollama/Llama.cpp)
        ├── groq_client.py  # Connects to Groq API
        └── gemini_client.py# Connects to Google Gemini API
```

### [Core]
#### [NEW] [main.py](file:///home/droidlulz/projects/droidr/voice_assistant/main.py)
- Initializes configuration and modules.
- Starts the `PipelineManager`.
- Handles graceful shutdown.

#### [NEW] [core/pipeline.py](file:///home/droidlulz/projects/droidr/voice_assistant/core/pipeline.py)
- Implements the main event loop:
    1.  **Wait for Wake Word** (Blocking/Async wait)
    2.  **Listen & Transcribe** (Stream audio to Vosk until silence)
    3.  **Dispatch to LLM** (Send text to selected provider)
    4.  **Synthesize & Play** (Stream text chunks to Piper -> Audio Output)

### [Modules]
#### [NEW] [modules/wakeword](file:///home/droidlulz/projects/droidr/voice_assistant/modules/wakeword)
- `PorcupineWakeWord`: Wraps `pvporcupine`. Efficient, requires key.
- `OpenWakeWord`: Wraps `openwakeword`. Free, heavier.

#### [NEW] [modules/stt](file:///home/droidlulz/projects/droidr/voice_assistant/modules/stt)
- `VoskSTT`: Uses `vosk-api`. Handles audio stream and returns text. Implements silence detection (VAD) logic implicitly or via `webrtcvad`.

#### [NEW] [modules/llm](file:///home/droidlulz/projects/droidr/voice_assistant/modules/llm)
- `LLMBase`: Interface with `generate(text) -> Iterator[str]`.
- `LanLLM`: Connects via WebSocket or HTTP to local server.
- `GroqLLM`: Uses `groq` python library.
- `GeminiLLM`: Uses `google-generativeai` library.

#### [NEW] [modules/tts](file:///home/droidlulz/projects/droidr/voice_assistant/modules/tts)
- `PiperTTS`: Wraps `piper` binary or python bindings. Accepts text stream, generates raw audio bytes.

## Verification Plan

### Automated Tests
- **Unit Tests:** Test individual modules (e.g., LLM client returns expected stream format, Config loader parses correctly).
- **Mock Audio:** Simulate audio input using pre-recorded `.wav` files to test the pipeline without a physical microphone.

### Manual Verification
- **Latency Check:** Measure time from "Stop Speaking" to "First Audio Response".
- **Resource Monitor:** Use `htop` to verify CPU/RAM usage during idle and active states on the Orange Pi.
