from abc import ABC, abstractmethod
from typing import Iterator

class LLMBase(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> Iterator[str]:
        """
        Generates a response from the LLM as a stream of text chunks.
        """
        pass
