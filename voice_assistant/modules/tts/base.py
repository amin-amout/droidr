from abc import ABC, abstractmethod
from typing import Iterator

class TTSBase(ABC):
    @abstractmethod
    def synthesize(self, text_stream: Iterator[str]) -> Iterator[bytes]:
        """
        Takes a stream of text and yields audio bytes (PCM).
        """
        pass
