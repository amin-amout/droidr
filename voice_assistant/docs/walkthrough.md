# Voice Assistant Walkthrough

## Prerequisites
- **Hardware:** Orange Pi 3 LTS (or similar ARM SBC)
- **OS:** Ubuntu Jammy (Headless)
- **Audio:** USB Microphone and Speaker (or 3.5mm jack)
- **Python:** 3.10+

## 1. Installation

### System Dependencies
Install system libraries required for audio and building python packages:
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv portaudio19-dev libasound2-dev
```

### Python Environment
Create a virtual environment and install dependencies:
```bash
cd ~/projects/droidr/voice_assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Model Setup
You need to download the models manually as they are large files.

### Create Directory
```bash
mkdir -p resources/models
```

### Download Vosk Model (STT)
Download the small English model (approx 40MB):
```bash
cd resources/models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip
```

### Download Piper TTS Binary and Voice Model
Download the Piper binary for your system architecture and the "Lessac" voice (medium quality):

```bash
# Check your architecture
uname -m  # x86_64 = amd64, aarch64 = arm64

# For x86_64 systems (Intel/AMD)
mkdir -p ../../bin
cd ../../bin
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz
tar -xzf piper_amd64.tar.gz
rm piper_amd64.tar.gz

# For ARM64 systems (like Orange Pi, Raspberry Pi)
# wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
# tar -xzf piper_arm64.tar.gz
# rm piper_arm64.tar.gz

# Test Piper installation
cd ~/projects/droidr/voice_assistant
echo "Hello, this is a test." | ./bin/piper/piper --model resources/models/en_US-lessac-medium.onnx --output-raw | aplay -r 22050 -f S16_LE -c 1

# Download voice model
cd resources/models
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### Download OpenWakeWord Models
If using OpenWakeWord instead of Porcupine, download the wake word model and required preprocessing models:

```bash
# Download wake word model
wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/hey_jarvis_v0.1.tflite

# Download required preprocessing models (needed by openwakeword library)
mkdir -p ../../venv/lib/python3.10/site-packages/openwakeword/resources/models
cd ../../venv/lib/python3.10/site-packages/openwakeword/resources/models
wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.tflite
wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.tflite
cd ~/projects/droidr/voice_assistant/resources/models
```

## 3. Configuration
Edit `config.yaml` to select your preferred engines and keys.

### API Keys
Edit `.env` and add your keys:
```bash
nano .env
```
- **Porcupine:** Get a free key from [Picovoice Console](https://console.picovoice.ai/).
- **Groq/Gemini:** Add keys if using cloud LLMs.

## 4. Running the Assistant
Start the application:
```bash
python3.10 main.py
```

## Troubleshooting
- **Audio Device Error:** If `sounddevice` fails, check `aplay -l` and `arecord -l` to see if your devices are detected. You may need to specify device indices in `config.yaml`.
- **Latency:** If STT is slow, ensure you are using the `small` Vosk model.
