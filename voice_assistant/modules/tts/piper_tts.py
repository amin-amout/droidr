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
        # Collect all text first
        full_text = ""
        for text_chunk in text_stream:
            if text_chunk.strip():
                full_text += text_chunk + " "
        
        if not full_text.strip():
            return
        
        # Run piper as a simple subprocess with input/output
        cmd = [
            self.piper_binary,
            "--model", self.model_path,
            "--output-raw"
        ]
        
        try:
            # Run piper with the full text as input
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            # Write text and close stdin to signal EOF
            process.stdin.write(full_text.encode('utf-8'))
            process.stdin.close()
            
            # Read all output
            while True:
                data = process.stdout.read(1024)
                if not data:
                    break
                yield data
            
            # Wait for process to finish
            process.wait()
            
        except Exception as e:
            print(f"Error in TTS: {e}")
            if process:
                process.terminate()
                process.wait()
