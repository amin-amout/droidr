import openwakeword
from openwakeword.model import Model
import numpy as np
from .base import WakeWordBase

class OpenWakeWord(WakeWordBase):
    def __init__(self, model_paths: list[str], inference_framework: str = "tflite"):
        # Load models. If paths are empty, it might load defaults or fail.
        # OpenWakeWord usually expects paths to .tflite or .onnx models
        self.model = Model(wakeword_models=model_paths, inference_framework=inference_framework)
        self.chunk_size = 1280 # OpenWakeWord typically works well with 80ms chunks (1280 samples at 16kHz)

    def process(self, pcm: np.ndarray) -> int:
        # OpenWakeWord expects int16 numpy array
        prediction = self.model.predict(pcm)
        
        # Check if any model crossed the threshold (default 0.5)
        for i, model_name in enumerate(self.model.models.keys()):
            if prediction[model_name] >= 0.5:
                self.model.reset() # Reset buffer after detection
                return i
        return -1

    @property
    def frame_length(self) -> int:
        return self.chunk_size
