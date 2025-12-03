import json
import vosk
from typing import Iterator
from .base import STTBase

class VoskSTT(STTBase):
    def __init__(self, model_path: str, sample_rate: int = 16000):
        vosk.SetLogLevel(-1) # Silence Vosk logs
        self.model = vosk.Model(model_path)
        self.sample_rate = sample_rate

    def stream_transcribe(self, audio_stream: Iterator[bytes]) -> Iterator[str]:
        rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
        
        for data in audio_stream:
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get("text"):
                    yield result["text"]
            else:
                # Partial results can be useful for lower latency UI feedback
                # partial = json.loads(rec.PartialResult())
                pass
        
        # Final result
        final = json.loads(rec.FinalResult())
        if final.get("text"):
            yield final["text"]
