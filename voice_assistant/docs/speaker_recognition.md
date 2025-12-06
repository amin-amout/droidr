# Speaker Recognition System

## Overview

The speaker recognition system allows your voice assistant to identify who is speaking and provide personalized responses based on the speaker's identity.

## Features

- **Offline speaker identification** using voice embeddings
- **SQLite database** for storing speaker profiles
- **Enrolls multiple users** (you, spouse, child, etc.)
- **Cosine similarity matching** with configurable threshold
- **Easy integration** with existing pipeline

## Installation

Install required dependencies:

```bash
pip install resemblyzer soundfile librosa
```

## Quick Start

### 1. Enroll Family Members

```python
from core.speaker_id import SpeakerIdentifier

# Initialize
speaker_id = SpeakerIdentifier(similarity_threshold=0.75)

# Enroll from audio file
speaker_id.enroll_user("Dad", audio_file="recordings/dad_voice.wav")
speaker_id.enroll_user("Mom", audio_file="recordings/mom_voice.wav")
speaker_id.enroll_user("Child", audio_file="recordings/child_voice.wav")

# Or enroll from numpy audio data
import numpy as np
audio_data = np.random.randn(16000 * 3)  # 3 seconds at 16kHz
speaker_id.enroll_user("Dad", audio_data=audio_data, sample_rate=16000)
```

If you see "No module named 'core'" when running the example, run the example module from the project root using:

```bash
PYTHONPATH=. python -m examples.speaker_integration enroll
```

This ensures Python can import the `core` package from the repository.

When integrated, Jarvis will greet recognized speakers by name after the wake word (for example: "Hello Amine, how can I help you?").

### 2. Identify Speaker

```python
# During interaction
audio_chunk = record_audio(duration=2.0)  # 2 seconds of speech
speaker = speaker_id.identify_speaker(audio_chunk, sample_rate=16000)

print(f"Identified: {speaker}")  # "Dad", "Mom", "Child", or "unknown"
```

### 3. Integration with Pipeline

```python
from core.speaker_id import SpeakerIdentifier

class PipelineManager:
    def __init__(self, config_path: str):
        # ... existing initialization ...
        
        # Add speaker identifier
        self.speaker_id = SpeakerIdentifier(
            db_path="data/speakers.db",
            similarity_threshold=0.75
        )
        self.current_speaker = "unknown"
    
    async def handle_interaction(self):
        # After wake word detection
        print("Wake word detected!")
        
        # Record short audio for identification (2 seconds)
        speaker_audio = self.audio.record(duration=2.0)
        
        # Identify speaker
        self.current_speaker = self.speaker_id.identify_speaker(
            speaker_audio, 
            sample_rate=16000
        )
        
        # Personalized greeting
        if self.current_speaker != "unknown":
            greeting = f"Hello {self.current_speaker}!"
            await self.speak(greeting)
        
        # Continue with normal STT/LLM flow...
        # Add speaker context to LLM prompt if needed
```

## Command-Line Tools

### Command-Line Tools

Use these commands from the project root. If you see import errors, run with `PYTHONPATH=.` as shown.

```bash
# Interactive enrollment (recommended)
PYTHONPATH=. python -m examples.speaker_integration enroll

# Enroll from an audio file
python -m core.speaker_id --enroll "Dad" --audio recordings/dad.wav

# List enrolled users
python -m core.speaker_id --list

# Delete a user
python -m core.speaker_id --delete "Dad"

# Identify a test audio file and print score
python -m core.speaker_id --identify test_audio.wav

# Dump embeddings to a pickle file for inspection
python -m core.speaker_id --dump-embeddings embeddings.pkl

# Recompute averaged embeddings from stored enrollment samples
python -m core.speaker_id --reprocess
```

## Recording Audio Samples for Enrollment

For best results when enrolling:

1. **Duration**: Record longer samples — 6-10 seconds each (8s recommended)
2. **Content**: Have the person say something like:
2. **Content**: Read a longer, natural phrase that includes the wake word so the model learns the way you say it. Example recommended enrollment phrase:
    - "Hey Jarvis, this is <your name>. I'm enrolling my voice so you can recognise me. Please remember this voice and respond to me by name."
    - Say this longer sentence 3-4 times during enrollment, at natural speaking volume and pacing.
    - For best results, record 4 samples of ~8 seconds each in a quiet room.
3. **Quality**: Use the same microphone as the assistant
4. **Environment**: Record in a quiet environment
5. **Multiple samples**: For better accuracy, enroll with 2-3 samples

## Configuration

```python
speaker_id = SpeakerIdentifier(
    db_path="speakers.db",           # SQLite database path
    similarity_threshold=0.75        # 0.0-1.0, higher = stricter
)
```

### Similarity Threshold Guidelines

- **0.70-0.75**: Balanced (recommended for families)
- **0.75-0.80**: Stricter (fewer false positives)
- **0.65-0.70**: More permissive (better for noisy environments)

## Database Schema

```sql
CREATE TABLE speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    embedding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## API Reference

### SpeakerIdentifier

```python
class SpeakerIdentifier:
    def __init__(self, model_path=None, db_path="speakers.db", 
                 similarity_threshold=0.75)
    
    def enroll_user(self, name: str, audio_file: str = None, 
                    audio_data: np.ndarray = None, sample_rate: int = 16000) -> bool
    
    def identify_speaker(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str
    
    def list_users(self) -> List[str]
    
    def delete_user(self, name: str) -> bool
    
    def get_speaker_count(self) -> int
```

## Personalized Features

### Example: Speaker-Specific Greetings

```python
def get_personalized_greeting(speaker: str) -> str:
    greetings = {
        "Dad": "Welcome back! What can I help you with?",
        "Mom": "Hi! How can I assist you today?",
        "Child": "Hey there kiddo! What would you like to know?",
    }
    return greetings.get(speaker, "Hello! How can I help you?")
```

### Example: Speaker-Specific Context

```python
def get_speaker_preferences(speaker: str) -> dict:
    preferences = {
        "Dad": {
            "temperature_unit": "celsius",
            "news_topics": ["tech", "business"],
            "music_style": "rock"
        },
        "Mom": {
            "temperature_unit": "celsius",
            "news_topics": ["health", "local"],
            "music_style": "classical"
        },
        "Child": {
            "temperature_unit": "celsius",
            "news_topics": ["kids"],
            "music_style": "pop"
        }
    }
    return preferences.get(speaker, {})
```

## Technical Details

### Embedding Model

The system uses **Resemblyzer** by default:
- Pretrained on VoxCeleb dataset
- Produces 256-dimensional embeddings
- Works offline (no API calls)
- Fast inference (~50ms per audio)

### Fallback: MFCC-based Embeddings

If Resemblyzer is unavailable, the system falls back to MFCC features:
- 40 MFCCs + statistics + deltas = 120-dimensional vector
- Less accurate but still functional
- Requires `librosa`

## Troubleshooting

### Low Recognition Accuracy

1. **Re-enroll with more samples**: Enroll each person 2-3 times
2. **Lower threshold**: Try `similarity_threshold=0.70`
3. **Better audio quality**: Use a quieter environment
4. **Longer samples**: Record 5+ seconds instead of 2-3

### False Positives

1. **Increase threshold**: Try `similarity_threshold=0.80`
2. **Ensure distinct voices**: System works best with clearly different voices
3. **Check audio quality**: Poor quality can cause mismatches

### "Unknown" Speaker Always

1. **Check enrollment**: Verify users are enrolled with `list_users()`
2. **Audio format**: Ensure audio is mono, 16kHz
3. **Database path**: Make sure `db_path` is consistent
4. **Threshold too high**: Lower the threshold

## Future Enhancements

- Real-time continuous identification
- Voice activity detection before identification
- Speaker-specific conversation memories
- Multi-speaker conversations
- Voice authentication for sensitive commands

## Examples

See `examples/speaker_integration.py` for complete integration examples.
