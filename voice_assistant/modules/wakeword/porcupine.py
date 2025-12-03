import pvporcupine
import numpy as np
from .base import WakeWordBase

class PorcupineWakeWord(WakeWordBase):
    def __init__(self, access_key: str, keywords: list[str] = None):
        if keywords is None:
            keywords = ["jarvis"]
        
        try:
            self.handle = pvporcupine.create(access_key=access_key, keywords=keywords)
        except pvporcupine.PorcupineError as e:
            # Fallback for invalid keys or network issues during init
            print(f"Error initializing Porcupine: {e}")
            raise

    def process(self, pcm: np.ndarray) -> int:
        return self.handle.process(pcm)

    @property
    def frame_length(self) -> int:
        return self.handle.frame_length

    def __del__(self):
        if hasattr(self, 'handle'):
            self.handle.delete()
