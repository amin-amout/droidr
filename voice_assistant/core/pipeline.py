import yaml
import os
import re
import numpy as np
import asyncio
import logging
from dotenv import load_dotenv

from .audio import AudioManager
from .session import ConversationSession
from .intents import detect_local_intent, handle_local_intent
from .speaker_id import SpeakerIdentifier
from modules.wakeword.porcupine import PorcupineWakeWord
from modules.wakeword.openwakeword import OpenWakeWord
from modules.stt.vosk_stt import VoskSTT
from modules.tts.piper_tts import PiperTTS
from modules.llm.lan_client import LanLLM
from modules.llm.groq_client import GroqLLM
from modules.llm.gemini_client import GeminiLLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineManager:
    def __init__(self, config_path: str):
        load_dotenv()
        
        with open(config_path, 'r') as f:
            config_content = f.read()
            # Replace ${VAR} with environment variable values
            config_content = re.sub(
                r'\$\{([^}]+)\}',
                lambda m: os.getenv(m.group(1), ''),
                config_content
            )
            self.config = yaml.safe_load(config_content)

        # Initialize Session Manager
        exit_phrases = self.config.get('session', {}).get('exit_phrases', [
            "stop listening", "go to sleep", "exit", "goodbye", "bye", "stop"
        ])
        self.session = ConversationSession(
            max_memory_size=self.config.get('session', {}).get('max_memory_turns', 10),
            exit_phrases=exit_phrases
        )

        # Initialize Audio
        self.audio = AudioManager(
            sample_rate=self.config['audio']['sample_rate'],
            channels=self.config['audio']['channels'],
            noise_gate_threshold=self.config['audio'].get('noise_gate_threshold', 500)
        )

        # Initialize Speaker Identification (optional)
        speaker_cfg = self.config.get('speaker', {})
        self.speaker_id = SpeakerIdentifier(
            model_path=speaker_cfg.get('model_path'),
            db_path=speaker_cfg.get('db_path', 'speakers.db'),
            similarity_threshold=speaker_cfg.get('similarity_threshold', 0.75)
        )

        # Initialize Wake Word
        ww_engine = self.config['system']['wake_word_engine']
        if ww_engine == 'porcupine':
            self.wakeword = PorcupineWakeWord(
                access_key=os.getenv('PORCUPINE_ACCESS_KEY'),
                keywords=self.config['wakeword']['porcupine']['keywords']
            )
        elif ww_engine == 'openwakeword':
            self.wakeword = OpenWakeWord(  # Changed from OpenWakeWord (it was already wrong on line 40)
                model_paths=self.config['wakeword']['openwakeword']['model_paths']
            )
        
        # Initialize STT
        self.stt = VoskSTT(
            model_path=self.config['stt']['vosk']['model_path']
        )

        # Initialize TTS
        self.tts = PiperTTS(
            model_path=self.config['tts']['piper']['model_path'],
            piper_binary=self.config['tts']['piper'].get('piper_binary', 'piper')
        )

        # Initialize LLM
        llm_provider = self.config['system']['llm_provider']
        if llm_provider == 'lan':
            self.llm = LanLLM(
                base_url=self.config['llm']['lan']['base_url'],
                model=self.config['llm']['lan']['model']
            )
        elif llm_provider == 'groq':
            self.llm = GroqLLM(
                api_key=os.getenv('GROQ_API_KEY'),
                model=self.config['llm']['groq']['model']
            )
        elif llm_provider == 'gemini':
            self.llm = GeminiLLM(
                api_key=os.getenv('GEMINI_API_KEY'),
                model=self.config['llm']['gemini']['model']
            )

    async def run(self):
        """
        Main event loop with session-aware logic.
        - Wait for wake word when session is inactive
        - Listen continuously when session is active
        - Exit session on exit phrases
        """
        logger.info("Starting Voice Assistant...")
        self.audio.start_input_stream()
        
        while True:
            if not self.session.active:
                # Dormant mode: wait for wake word
                logger.info("Listening for wake word...")
                await self.wait_for_wake_word()
                self.session.activate()
                logger.info("Session activated! Listening continuously...")
                # After wake word, try to identify speaker (short sample)
                    try:
                        # Record a snippet for identification. Duration configurable via config.yaml
                        identify_duration = float(self.config.get('speaker', {}).get('identify_duration', 8.0))
                        sample = self.audio.record(duration=identify_duration)
                        name, score = self.speaker_id.identify_with_score(sample, sample_rate=self.audio.sample_rate)
                        
                        # If score is confidently above threshold
                        if score >= self.speaker_id.similarity_threshold:
                            speaker_name = name
                        # If score is near threshold, ask for confirmation
                        elif score > 0 and self.speaker_id.accept_near_threshold and score + self.speaker_id.near_margin >= self.speaker_id.similarity_threshold:
                            # Ask confirmation
                            await self.speak(f"I think you are {name}. Is that correct?")
                            # Record short yes/no response
                            confirm_audio = self.audio.record(duration=2.0)
                            confirm_text = await self.stt.transcribe_from_audio(confirm_audio)
                            if confirm_text and any(w in confirm_text.lower() for w in ["yes", "yep", "correct", "right", "oui"]):
                                speaker_name = name
                            else:
                                speaker_name = "unknown"
                        else:
                            speaker_name = "unknown"
                    except Exception:
                        speaker_name = "unknown"

                    # Personalized greeting
                    if speaker_name and speaker_name != "unknown":
                        await self.speak(f"Hello {speaker_name}, how can I help you?")
                    else:
                        await self.speak("Yes? How can I help you?")
            else:
                # Active session: listen for user input
                await self.handle_interaction()

    async def wait_for_wake_word(self) -> None:
        """
        Listen for wake word detection.
        Blocks until wake word is detected.
        """
        # Clear any buffered audio from previous session
        self.clear_audio_buffer()
        
        while True:
            chunk_bytes = self.audio.read_chunk()
            pcm = np.frombuffer(chunk_bytes, dtype=np.int16)
            
            keyword_index = self.wakeword.process(pcm)
            if keyword_index >= 0:
                logger.info("Wake word detected!")
                return
    
    def clear_audio_buffer(self) -> None:
        """
        Clear buffered audio from the input queue.
        Useful when transitioning back to wake word detection.
        """
        try:
            # Drain the queue without blocking
            while not self.audio.input_queue.empty():
                self.audio.input_queue.get_nowait()
            logger.debug("Audio buffer cleared")
        except Exception as e:
            logger.debug(f"Error clearing audio buffer: {e}")

    async def handle_interaction(self):
        """
        Handle a single user interaction within an active session.
        - Listen and transcribe
        - Check for exit phrases
        - Get LLM response with memory context
        - Speak response
        - Update memory
        """
        # Listen and transcribe
        user_text = await self.listen_and_transcribe()
        
        if not user_text:
            logger.warning("No speech detected, continuing...")
            return
        
        logger.info(f"User said: {user_text}")
        
        # Check for local intents first (time, weather, etc.)
        local_intent = detect_local_intent(user_text)
        if local_intent:
            logger.info(f"Local intent detected: {local_intent['intent']}")
            response = handle_local_intent(local_intent)
            logger.info(f"AI (local): {response}")
            
            # Add to memory for context continuity
            self.session.add_to_memory("user", user_text)
            self.session.add_to_memory("assistant", response)
            
            # Speak response directly without calling LLM
            await self.speak(response)
            await asyncio.sleep(1.5)
            return
        
        # Check for exit phrases
        if self.session.should_exit(user_text):
            logger.info("Exit phrase detected, ending session...")
            await self.speak("Goodbye! Let me know if you need anything.")
            self.session.deactivate()
            return
        
        # Add user message to memory
        self.session.add_to_memory("user", user_text)
        
        # Get LLM response with conversation history
        logger.info("Generating response...")
        response = await self.call_llm_with_memory(user_text)
        
        if not response:
            logger.error("No response from LLM")
            return
        
        logger.info(f"AI: {response}")
        
        # Add assistant response to memory
        self.session.add_to_memory("assistant", response)
        
        # Speak response
        await self.speak(response)
        
        # Longer pause after speaking to ensure:
        # 1. Audio playback is fully complete
        # 2. User has time to think
        # 3. No audio feedback/echo
        await asyncio.sleep(1.5)

    async def listen_and_transcribe(self) -> str:
        """
        Listen for user speech and transcribe it.
        Records for a configurable duration (default 5 seconds).
        
        TODO: Implement proper VAD (Voice Activity Detection) using webrtcvad
        to detect end of speech dynamically.
        
        Returns:
            Transcribed text
        """
        logger.info("Listening for command...")
        
        # Record audio for configurable duration (default 5 seconds)
        # In production, use VAD to detect speech end
        audio_buffer = []
        duration_seconds = self.config.get('audio', {}).get('listen_duration', 5)
        chunks_needed = int(self.config['audio']['sample_rate'] / 512 * duration_seconds)
        
        # Collect all audio first
        for _ in range(chunks_needed):
            audio_buffer.append(self.audio.read_chunk())
        
        # Play a friendly beep to indicate listening has stopped
        if self.config.get('audio', {}).get('beep_on_listen_end', True):
            self.audio.play_beep()
        
        # Add silence padding at the end to help Vosk finalize properly
        silence_chunks = 10  # ~200ms of silence
        silence = bytes(1024)  # 512 samples * 2 bytes = 1024 bytes of silence
        for _ in range(silence_chunks):
            audio_buffer.append(silence)
        
        # Transcribe all at once
        text_stream = self.stt.stream_transcribe(iter(audio_buffer))
        user_text = ""
        for text in text_stream:
            user_text += text + " "
        
        return user_text.strip()

    async def call_llm_with_memory(self, user_input: str) -> str:
        """
        Call LLM with conversation history and current input.
        
        Args:
            user_input: Latest user message
            
        Returns:
            LLM response text
        """
        # Build prompt with system message and conversation history
        system_prompt = """You are Jarvis, a helpful voice assistant. You provide concise, friendly, and direct answers. 
When asked how you are or about your feelings, simply respond positively and move on (e.g., "I'm doing well, thanks for asking!").
Keep responses brief and to the point since they will be spoken aloud. Avoid mentioning that you're an AI or language model unless specifically asked about your nature.
You can remember context from earlier in the conversation."""
        
        # Get conversation history
        history = self.session.get_memory_for_llm()
        
        # Build full prompt
        if history:
            # Include conversation context
            context = self.session.get_memory_context()
            full_prompt = f"{system_prompt}\n\nPrevious conversation:\n{context}\n\nUser: {user_input}\nAssistant:"
        else:
            # First message in session
            full_prompt = f"{system_prompt}\n\nUser: {user_input}\nAssistant:"
        
        # Call LLM
        response_stream = self.llm.generate_async(full_prompt)
        
        # Collect full response
        full_response = ""
        async for chunk in response_stream:
            full_response += chunk
        
        return full_response.strip()

    async def speak(self, text: str) -> None:
        """
        Synthesize and play speech.
        
        Args:
            text: Text to speak
        """
        if not text:
            return
        
        logger.info("Synthesizing speech...")
        
        # Synthesize
        audio_stream = self.tts.synthesize(iter([text]))
        
        # Collect all audio chunks
        all_audio = bytearray()
        for audio_chunk in audio_stream:
            all_audio.extend(audio_chunk)
        
        # Play
        self.audio.play_audio(bytes(all_audio), sample_rate=22050)

    def stop(self):
        self.audio.stop()
