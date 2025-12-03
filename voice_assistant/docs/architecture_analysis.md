# Voice Assistant Architecture Analysis for Orange Pi 3 LTS

## 1. Executive Summary

Your proposed architecture is **viable but not optimal** for the Orange Pi 3 LTS (2GB RAM, Cortex-A53). While the components you selected are high-quality, some (specifically Whisper.cpp and standard Python loops) may introduce unacceptable latency or resource contention on this specific hardware.

**Key Findings:**
- **STT:** `whisper.cpp` (even tiny) will likely have 1.5s+ latency on Cortex-A53, which feels sluggish for voice commands. **Vosk** is objectively faster for this specific hardware.
- **TTS:** `Piper` is the correct choice; it is highly optimized and will run faster than real-time.
- **Wake Word:** `Porcupine` is the most efficient (~4% CPU) but requires an access key. `OpenWakeWord` is free but heavy (~70% of one core).
- **Networking:** REST is "okay" but WebSockets are significantly better for latency and streaming.

---

## 2. Architecture Evaluation

| Component | Your Proposal | Evaluation | Verdict |
| :--- | :--- | :--- | :--- |
| **STT** | Whisper.cpp (Tiny) | **Too Slow.** Expect ~1.5-2s processing time per phrase. Good accuracy, but poor interactive experience. | ⚠️ Replace |
| **TTS** | Piper | **Excellent.** Fast, low resource usage, good quality. | ✅ Keep |
| **Wake Word** | Porcupine / Snowboy | **Porcupine** is highly efficient but has non-free limits. **Snowboy** is unmaintained. | ⚠️ Review |
| **Logic** | Python Client | Good, but needs careful audio handling to avoid blocking. | ✅ Keep |
| **LLM** | Remote LAN | **Perfect.** Offloading is the only viable path for 2GB RAM. | ✅ Keep |

---

## 3. Proposed "Objectively Better" Solution

This proposal prioritizes **latency** and **resource efficiency** while maintaining the "fully free" constraint.

### Optimized Stack
- **Wake Word:** **Porcupine** (if free tier acceptable) OR **Precise-Lite** (fully free, lighter than OpenWakeWord).
- **STT:** **Vosk** (Small model). It is significantly faster (hundreds of ms vs seconds) on Cortex-A53 and supports streaming, meaning it transcribes *as you speak* rather than waiting for you to finish.
- **TTS:** **Piper** (Low quality voice for speed, or Medium if CPU allows).
- **Audio Backend:** **PipeWire**. Lower latency and better resource management than PulseAudio on modern Linux.
- **Networking:** **WebSockets** (Socket.IO or raw WS). Maintains a persistent connection to the LLM server, saving handshake time and allowing full-duplex streaming.

---

## 4. Component-by-Component Breakdown

### A. Speech-to-Text (STT)
**Recommendation:** **Vosk** (with `vosk-model-small-en-us-0.15`)
- **Why:** Whisper.cpp is a "batch" processor (records audio -> processes). Vosk is a "streaming" processor. On a Cortex-A53, Whisper.cpp `tiny` might take 2 seconds to process a 3-second command. Vosk will finish processing milliseconds after you stop speaking.
- **Trade-off:** Whisper has better accuracy for dictation. Vosk is better for commands and short queries.

### B. Text-to-Speech (TTS)
**Recommendation:** **Piper**
- **Why:** It runs faster than real-time on Raspberry Pi 3 class hardware. Coqui TTS is too heavy (often based on VITS/GlowTTS which can be slow without AVX/Neon optimization).
- **Optimization:** Use the `.onnx` models with the `piper-phonemize` library directly in Python to avoid spawning subprocesses.

### C. Wake Word
**Recommendation:** **Porcupine** (Free Tier) or **OpenWakeWord** (if CPU budget allows)
- **Porcupine:** Uses ~4% CPU. Extremely reliable. Free tier allows 3 devices.
- **OpenWakeWord:** Fully free. Uses ~60-70% of *one* core on Cortex-A53. This is acceptable since you have 4 cores, but you must ensure your main loop doesn't block this core.
- **Snowboy:** Avoid. Deprecated and difficult to build on modern systems.

### D. Networking (Client <-> LAN LLM)
**Recommendation:** **WebSockets**
- **Why:** A REST API requires a new TCP handshake and HTTP overhead for every turn. WebSockets keep a pipe open.
- **Latency:** Saves ~50-100ms per turn.
- **Streaming:** Allows the LLM to stream tokens *back* to the Pi. The Pi can start TTS generation *before* the LLM finishes the sentence (advanced optimization).

---

## 5. Concrete Actionable Suggestions

### 1. Implement "VAD-based Interrupt"
Use `webrtcvad` to detect when the user stops speaking. Do not rely on a fixed silence timeout. This makes the assistant feel "snappy."

### 2. The "Streaming" Pipeline
Instead of `Record -> STT -> Send -> Wait -> TTS`, build a pipeline:
1.  **Wake Word** triggers.
2.  **Vosk** starts streaming audio immediately.
3.  **VAD** detects silence -> Finalize STT text.
4.  Send text to LAN LLM via **WebSocket**.
5.  LLM streams text back.
6.  **Piper** receives sentence chunks (e.g., split by `.`, `?`, `!`) and generates audio *while* the LLM is still thinking about the next sentence.
7.  **ALSA/PipeWire** plays audio chunks immediately.

### 3. System Optimization
- **ZRAM:** Enable ZRAM (compressed RAM swap). With only 2GB RAM, this is critical to prevent locking up if you load a slightly larger model or buffer.
- **CPU Isolation (Optional):** If using OpenWakeWord, use `taskset` to pin it to CPU Core 3, leaving Cores 0-2 free for the OS and Python logic.

### 4. Offline Capability (Hybrid Mode)
You can make the Pi "smart" even without the LAN LLM:
- Implement a simple **intent matcher** (like `fuzzyset` or regex) *before* sending to the LLM.
- **Example:** If text contains "turn on lights", execute locally. If no match, send to LLM.
- This reduces latency to near-zero for home automation commands.

## Summary of Recommended Stack

| Layer | Software | Note |
| :--- | :--- | :--- |
| **OS** | Ubuntu Jammy (Server) | Headless, no desktop environment. |
| **Audio** | PipeWire | Low latency audio server. |
| **Wake Word** | Porcupine (Free) | Fallback: OpenWakeWord (pinned to core 3). |
| **STT** | Vosk | Small model for speed. |
| **Logic** | Python 3.10+ | Asyncio based (essential for streaming). |
| **Comms** | Socket.IO / Websockets | Persistent connection to LAN. |
| **TTS** | Piper | Streamed output. |
