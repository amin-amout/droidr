"""
Speaker Recognition Integration Example

This script demonstrates how to integrate speaker identification
into the voice assistant pipeline.
"""

import asyncio
import numpy as np
from core.speaker_id import SpeakerIdentifier
from core.audio import AudioManager


# Example 1: Enrollment Script
# -----------------------------
# Use this to enroll family members

def enroll_family_members():
    """
    Enroll family members using recorded audio samples.
    """
    speaker_id = SpeakerIdentifier(similarity_threshold=0.75)
    
    # Enroll yourself
    print("Enrolling: You")
    print("Please speak for 3-5 seconds when prompted...")
    # In practice, record audio here
    # audio_data = record_audio(duration=5)
    # speaker_id.enroll_user("You", audio_data=audio_data, sample_rate=16000)
    
    # For testing with audio files:
    speaker_id.enroll_user("Dad", audio_file="recordings/dad_sample.wav")
    speaker_id.enroll_user("Mom", audio_file="recordings/mom_sample.wav")
    speaker_id.enroll_user("Child", audio_file="recordings/child_sample.wav")
    
    # List enrolled users
    users = speaker_id.list_users()
    print(f"\nEnrolled users: {users}")


# Example 2: Integration with Main Assistant Loop
# ------------------------------------------------

async def assistant_loop_with_speaker_id():
    """
    Modified assistant loop with speaker identification.
    """
    # Initialize components
    speaker_id = SpeakerIdentifier(similarity_threshold=0.75)
    audio_manager = AudioManager(sample_rate=16000, channels=1)
    
    print("Voice Assistant with Speaker Recognition")
    print(f"Enrolled speakers: {', '.join(speaker_id.list_users())}")
    
    while True:
        # 1. Wait for wake word
        print("\nListening for wake word...")
        # wake_word_detected = await detect_wake_word()
        
        # 2. Record audio snippet for speaker identification (2-3 seconds)
        print("Wake word detected! Identifying speaker...")
        speaker_audio = audio_manager.record(duration=3.5)
        
        # 3. Identify speaker
        speaker_name = speaker_id.identify_speaker(speaker_audio, sample_rate=16000)
        
        print(f"Identified speaker: {speaker_name}")
        
        # 4. Greet the speaker
        if speaker_name != "unknown":
            greeting = get_personalized_greeting(speaker_name)
            print(f"Assistant: {greeting}")
            # await tts.speak(greeting)
        else:
            print("Assistant: Hello! I don't recognize your voice.")
        
        # 5. Continue with normal STT and command processing
        # user_text = await stt.transcribe()
        # response = await process_command(user_text, speaker=speaker_name)
        # await tts.speak(response)
        
        break  # Remove in production


# Example 3: Personalized Responses
# ----------------------------------

def get_personalized_greeting(speaker: str) -> str:
    """
    Generate personalized greeting based on speaker identity.
    """
    greetings = {
        "Dad": "Hello! Welcome back. What can I help you with?",
        "Mom": "Hi there! How can I assist you today?",
        "Child": "Hey kiddo! What would you like to know?",
    }
    
    return greetings.get(speaker, "Hello! How can I help you?")


def get_speaker_context(speaker: str) -> dict:
    """
    Load speaker-specific context and preferences.
    """
    contexts = {
        "Dad": {
            "preferences": {"temperature_unit": "celsius", "news_topics": ["tech", "business"]},
            "calendar": "dad_calendar",
            "music_playlist": "dad_favorites"
        },
        "Mom": {
            "preferences": {"temperature_unit": "celsius", "news_topics": ["health", "local"]},
            "calendar": "mom_calendar",
            "music_playlist": "mom_favorites"
        },
        "Child": {
            "preferences": {"temperature_unit": "celsius", "news_topics": ["kids"]},
            "calendar": "child_schedule",
            "music_playlist": "kids_songs"
        },
    }
    
    return contexts.get(speaker, {})


# Example 4: Pipeline Integration Pattern
# ----------------------------------------

class SpeakerAwarePipeline:
    """
    Voice assistant pipeline with speaker recognition.
    """
    
    def __init__(self):
        self.speaker_id = SpeakerIdentifier(similarity_threshold=0.75)
        self.current_speaker = "unknown"
    
    async def handle_interaction(self):
        """
        Handle a single voice interaction with speaker identification.
        """
        # Step 1: Detect wake word
        await self.wait_for_wake_word()
        
        # Step 2: Identify speaker from short audio sample
        speaker_audio = await self.record_for_identification(duration=2.0)
        self.current_speaker = self.speaker_id.identify_speaker(
            speaker_audio, sample_rate=16000
        )
        
        print(f"🎤 Speaker: {self.current_speaker}")
        
        # Step 3: Personalized greeting
        if self.current_speaker != "unknown":
            await self.speak(get_personalized_greeting(self.current_speaker))
        
        # Step 4: Listen to full command
        user_text = await self.listen_and_transcribe()
        
        # Step 5: Process with speaker context
        context = get_speaker_context(self.current_speaker)
        response = await self.process_command(user_text, context)
        
        # Step 6: Speak response
        await self.speak(response)
    
    async def wait_for_wake_word(self):
        """Wait for wake word detection."""
        pass  # Implement with your wake word detector
    
    async def record_for_identification(self, duration: float) -> np.ndarray:
        """Record audio for speaker identification."""
        pass  # Implement with AudioManager
    
    async def listen_and_transcribe(self) -> str:
        """Listen and transcribe user speech."""
        pass  # Implement with STT
    
    async def process_command(self, text: str, context: dict) -> str:
        """Process command with speaker context."""
        pass  # Implement with LLM
    
    async def speak(self, text: str):
        """Speak response via TTS."""
        pass  # Implement with TTS


# Example 5: Command-line Enrollment Tool
# ----------------------------------------

def interactive_enrollment():
    """
    Interactive enrollment tool for adding new speakers.
    """
    from core.audio import AudioManager
    
    speaker_id = SpeakerIdentifier()
    audio_manager = AudioManager(sample_rate=16000, channels=1)
    
    print("=== Speaker Enrollment Tool ===\n")
    
    name = input("Enter speaker name: ").strip()
    
    if not name:
        print("Invalid name!")
        return
    
    # Check if already enrolled
    if name in speaker_id.list_users():
        response = input(f"{name} is already enrolled. Re-enroll? (y/n): ")
        if response.lower() != 'y':
            return
    
    print(f"\n🎤 Recording {name}'s voice samples...")
    print("Please read the following long sample (3-5 seconds) aloud, 2-3 times:")
    print("  'Hey Jarvis, this is <your name>. I am enrolling my voice so you can recognise me."
          " Please remember this voice and respond to me by name.'")
    print("\nWe'll record 3 samples. Try to speak naturally and clearly in a quiet room.")

    samples_to_record = 4
    recorded_any = False
    for i in range(samples_to_record):
        input(f"Press Enter to record sample {i+1}/{samples_to_record} (or Ctrl-C to cancel)...")
        print("Recording in 3... 2... 1...")
        audio_data = audio_manager.record(duration=8.0)
        print("✓ Recording complete!")
        recorded_any = True

        # Enroll (averaging handled by enroll_user if user already exists)
        success = speaker_id.enroll_user(name, audio_data=audio_data, sample_rate=16000)
        if not success:
            print(f"Failed to enroll sample {i+1}")
        else:
            print(f"Enrolled sample {i+1}/{samples_to_record}")

    if not recorded_any:
        print("No samples recorded. Enrollment aborted.")
        return
    
    if success:
        print(f"✓ Successfully enrolled {name}!")
        print(f"\nTotal enrolled speakers: {speaker_id.get_speaker_count()}")
        print(f"Users: {', '.join(speaker_id.list_users())}")
    else:
        print(f"✗ Failed to enroll {name}")


# Main entry point for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "enroll":
        interactive_enrollment()
    else:
        print("""
Speaker Recognition Integration Examples

Available commands:
  python examples/speaker_integration.py enroll    - Enroll new speaker
  
For integration into your pipeline:
  1. Import: from core.speaker_id import SpeakerIdentifier
  2. Initialize: speaker_id = SpeakerIdentifier()
  3. Identify: speaker = speaker_id.identify_speaker(audio_data)
  
See SpeakerAwarePipeline class for full integration pattern.
        """)
