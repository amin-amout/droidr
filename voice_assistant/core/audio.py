import sounddevice as sd
import numpy as np
import queue
from typing import Iterator

class AudioManager:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 512):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.stream = None

    def start_input_stream(self):
        """Starts the audio input stream."""
        def callback(indata, frames, time, status):
            if status:
                print(status)
            self.input_queue.put(bytes(indata))

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16',
            callback=callback,
            blocksize=self.chunk_size
        )
        self.stream.start()

    def read_chunk(self) -> bytes:
        """Blocking read of the next audio chunk."""
        return self.input_queue.get()

    def play_audio(self, audio_data: bytes, sample_rate: int = None):
        """Plays raw audio data."""
        # Simple blocking playback for now. 
        # For a real async pipeline, we'd want a separate output stream/thread.
        # But sd.play is blocking-ish or fires and forgets depending on usage.
        # Better to use an OutputStream.
        
        # Convert bytes back to numpy for sounddevice
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        # Use provided sample rate or default to instance sample rate
        playback_rate = sample_rate if sample_rate else self.sample_rate
        sd.play(audio_np, playback_rate, blocking=True)
        sd.wait()  # Ensure audio finishes playing

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
