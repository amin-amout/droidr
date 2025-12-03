import yaml
import os
import numpy as np
import asyncio
from dotenv import load_dotenv

from .audio import AudioManager
from ..modules.wakeword.porcupine import PorcupineWakeWord
from ..modules.wakeword.openwakeword import OpenWakeWord
from ..modules.stt.vosk_stt import VoskSTT
from ..modules.llm.lan_client import LanLLM
from ..modules.llm.groq_client import GroqLLM
from ..modules.llm.gemini_client import GeminiLLM
from ..modules.tts.piper_tts import PiperTTS

class PipelineManager:
    def __init__(self, config_path: str):
        load_dotenv()
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize Audio
        self.audio = AudioManager(
            sample_rate=self.config['audio']['sample_rate'],
            channels=self.config['audio']['channels']
        )

        # Initialize Wake Word
        ww_engine = self.config['system']['wake_word_engine']
        if ww_engine == 'porcupine':
            self.wakeword = PorcupineWakeWord(
                access_key=os.getenv('PORCUPINE_ACCESS_KEY'),
                keywords=self.config['wakeword']['porcupine']['keywords']
            )
        elif ww_engine == 'openwakeword':
            self.wakeword = OpenWakeWord(
                model_paths=self.config['wakeword']['openwakeword']['model_paths']
            )
        
        # Initialize STT
        self.stt = VoskSTT(
            model_path=self.config['stt']['vosk']['model_path']
        )

        # Initialize TTS
        self.tts = PiperTTS(
            model_path=self.config['tts']['piper']['model_path']
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
        print("Starting Voice Assistant...")
        self.audio.start_input_stream()
        
        print("Listening for wake word...")
        while True:
            # 1. Wake Word Detection
            chunk_bytes = self.audio.read_chunk()
            # Convert to numpy for wake word engine
            pcm = np.frombuffer(chunk_bytes, dtype=np.int16)
            
            keyword_index = self.wakeword.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected!")
                await self.handle_interaction()

    async def handle_interaction(self):
        # 2. STT (Listen until silence)
        print("Listening for command...")
        # We need a generator that yields audio chunks from the audio manager
        # until some condition (silence) is met.
        # For MVP, let's just record for 5 seconds fixed, or use a simple VAD loop.
        
        # Quick hack: Record 3 seconds of audio for STT
        # In production, use webrtcvad to detect end of speech.
        audio_buffer = []
        for _ in range(0, int(16000 / 512 * 3)): # 3 seconds
            audio_buffer.append(self.audio.read_chunk())
            
        # Transcribe
        text_stream = self.stt.stream_transcribe(iter(audio_buffer))
        user_text = ""
        for text in text_stream:
            user_text += text + " "
        
        user_text = user_text.strip()
        print(f"User said: {user_text}")
        
        if not user_text:
            return

        # 3. LLM
        print("Generating response...")
        # We need to bridge the sync/async gap depending on the LLM provider
        # Our LLM classes have generate_async
        
        response_stream = self.llm.generate_async(user_text)
        
        # 4. TTS & Playback
        # We need to feed the response stream to TTS.
        # TTS.synthesize takes an iterator of strings.
        # We can create an async generator adapter if needed, 
        # but PiperTTS implementation above was sync.
        # Let's collect the response for the MVP to avoid complex async/sync bridging in this step
        # OR better, iterate async and feed to TTS chunk by chunk.
        
        full_response = ""
        async for chunk in response_stream:
            full_response += chunk
            # Optimization: We could feed 'chunk' to TTS here if it formed a complete sentence.
        
        print(f"AI: {full_response}")
        
        # Synthesize
        audio_stream = self.tts.synthesize(iter([full_response]))
        
        # Play
        for audio_chunk in audio_stream:
            self.audio.play_audio(audio_chunk)

    def stop(self):
        self.audio.stop()
