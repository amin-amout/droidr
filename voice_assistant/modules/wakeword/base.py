from abc import ABC, abstractmethod
import numpy as np

class WakeWordBase(ABC):
    @abstractmethod
    def process(self, pcm: np.ndarray) -> int:
        """
        Process a chunk of audio and return the index of the detected keyword, or -1 if none.
        """
        pass

    @property
    @abstractmethod
    def frame_length(self) -> int:
        """
        Required frame length (number of samples) for processing.
        """
        pass
