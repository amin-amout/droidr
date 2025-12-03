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

### Download Piper Voice (TTS)
Download the "Lessac" voice (medium quality):
```bash
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### Download OpenWakeWord Model (Optional)
If using OpenWakeWord instead of Porcupine:
```bash
wget https://github.com/dscripka/openWakeWord/raw/main/openwakeword/resources/models/alexa_v0.1.tflite
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
python3 main.py
```

## Troubleshooting
- **Audio Device Error:** If `sounddevice` fails, check `aplay -l` and `arecord -l` to see if your devices are detected. You may need to specify device indices in `config.yaml`.
- **Latency:** If STT is slow, ensure you are using the `small` Vosk model.
