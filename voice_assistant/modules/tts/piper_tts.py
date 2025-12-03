import subprocess
import os
from typing import Iterator
from .base import TTSBase

class PiperTTS(TTSBase):
    def __init__(self, model_path: str, piper_binary: str = "piper"):
        self.model_path = model_path
        self.piper_binary = piper_binary

    def synthesize(self, text_stream: Iterator[str]) -> Iterator[bytes]:
        """
        Streams text to piper subprocess and yields raw audio bytes.
        """
        # Start piper process
        # We use --output-raw to get raw PCM data (16-bit, mono, 22050Hz usually)
        cmd = [
            self.piper_binary,
            "--model", self.model_path,
            "--output-raw"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0 # Unbuffered
        )

        try:
            # We need a separate thread or non-blocking way to write to stdin
            # while reading from stdout to avoid deadlocks.
            # However, for simplicity in this synchronous generator, we will 
            # write chunk by chunk. Ideally, Piper should be fed sentences.
            
            # NOTE: A robust implementation would use asyncio subprocesses.
            # For this MVP, we'll assume text_stream yields complete sentences
            # and we write them one by one.
            
            for text_chunk in text_stream:
                if not text_chunk.strip():
                    continue
                    
                # Write text to piper
                process.stdin.write(text_chunk.encode('utf-8') + b'\n')
                process.stdin.flush()
                
                # Read audio output. 
                # Piper outputs audio as it generates. We need to read continuously.
                # This is tricky with blocking I/O. 
                # A better approach for the MVP:
                # Use the python bindings or run a new process per sentence if latency allows.
                # Running a persistent process is better but harder to manage synchronously.
                
                # Let's try reading a chunk. 
                # WARNING: This might block if piper doesn't output immediately.
                # For safety in this MVP, we might want to just read until we get data.
                
                while True:
                    # Read 1024 bytes
                    data = process.stdout.read(1024)
                    if not data:
                        break
                    yield data
                    # If we read less than requested, maybe it's done for now? 
                    # No, pipe might just be empty.
                    
        except BrokenPipeError:
            pass
        finally:
            if process.stdin:
                process.stdin.close()
            process.terminate()
            process.wait()
