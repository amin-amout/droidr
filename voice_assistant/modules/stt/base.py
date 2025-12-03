from abc import ABC, abstractmethod
from typing import Iterator

class STTBase(ABC):
    @abstractmethod
    def stream_transcribe(self, audio_stream: Iterator[bytes]) -> Iterator[str]:
        """
        Takes an iterator of audio bytes and yields transcribed text chunks.
        """
        pass
