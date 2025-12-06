import sounddevice as sd
import numpy as np
import queue
from typing import Iterator

class AudioManager:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 512, 
                 noise_gate_threshold: int = 500):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.noise_gate_threshold = noise_gate_threshold  # Amplitude threshold for noise gate
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.stream = None

    def apply_noise_gate(self, audio_data: bytes) -> bytes:
        """
        Apply a simple noise gate to reduce background noise.
        If the audio level is below threshold, replace with silence.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Processed audio bytes
        """
        # Convert to numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16).copy()
        
        # Calculate RMS (Root Mean Square) of the audio
        rms = np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))
        
        # If below threshold, replace with silence
        if rms < self.noise_gate_threshold:
            audio_np = np.zeros_like(audio_np)
        
        return audio_np.tobytes()

    def start_input_stream(self):
        """Starts the audio input stream."""
        def callback(indata, frames, time, status):
            if status:
                print(status)
            # Apply noise gate to reduce background noise
            audio_bytes = bytes(indata)
            filtered_audio = self.apply_noise_gate(audio_bytes)
            self.input_queue.put(filtered_audio)

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

    def play_beep(self, frequency: int = 800, duration: float = 0.15, volume: float = 0.3):
        """
        Play a simple beep tone.
        
        Args:
            frequency: Beep frequency in Hz (default 800Hz for friendly sound)
            duration: Duration in seconds
            volume: Volume level 0.0 to 1.0
        """
        # Pause input stream during beep
        was_streaming = self.stream and self.stream.active
        if was_streaming:
            self.stream.stop()
        
        # Generate sine wave
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        tone = np.sin(frequency * 2 * np.pi * t) * volume
        
        # Convert to int16
        audio_data = (tone * 32767).astype(np.int16)
        
        # Play
        sd.play(audio_data, self.sample_rate, blocking=False)
        sd.wait()
        
        # Resume input stream
        if was_streaming:
            import time
            time.sleep(0.1)
            self.stream.start()

    def play_audio(self, audio_data: bytes, sample_rate: int = None):
        """Plays raw audio data."""
        # Pause input stream while playing to avoid feedback
        was_streaming = self.stream and self.stream.active
        if was_streaming:
            self.stream.stop()
            # Clear any buffered input during playback
            while not self.input_queue.empty():
                try:
                    self.input_queue.get_nowait()
                except:
                    break
        
        # Convert bytes back to numpy for sounddevice
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        # Use provided sample rate or default to instance sample rate
        playback_rate = sample_rate if sample_rate else self.sample_rate
        
        # Play and wait for completion
        sd.play(audio_np, playback_rate, blocking=False)
        sd.wait()  # Wait for playback to finish
        
        # Add extra delay to ensure audio completes
        import time
        time.sleep(0.3)
        
        # Resume input stream
        if was_streaming:
            self.stream.start()
            # Give the stream a moment to stabilize
            time.sleep(0.2)

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def record(self, duration: float) -> np.ndarray:
        """
        Record audio for a fixed duration and return as a normalized mono numpy array.

        Args:
            duration: Recording duration in seconds

        Returns:
            Numpy array of float32 samples in range [-1.0, 1.0]
        """
        # Use sounddevice.rec for a simple blocking recording
        frames = int(self.sample_rate * float(duration))
        audio = sd.rec(frames, samplerate=self.sample_rate, channels=self.channels, dtype='int16')
        sd.wait()

        # Convert to mono if necessary
        if audio.ndim > 1 and audio.shape[1] > 1:
            audio = audio.mean(axis=1)

        # Ensure dtype and normalize to [-1, 1]
        audio = audio.astype(np.float32) / 32767.0

        return audio
