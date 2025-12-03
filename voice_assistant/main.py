import asyncio
import os
from core.pipeline import PipelineManager

async def main():
    # Ensure resources directory exists or warn user
    if not os.path.exists("resources/models"):
        print("WARNING: 'resources/models' directory not found.")
        print("Please download the required models (Vosk, Piper, etc.) and place them there.")
    
    pipeline = PipelineManager("config.yaml")
    try:
        await pipeline.run()
    except KeyboardInterrupt:
        print("\nStopping...")
        pipeline.stop()

if __name__ == "__main__":
    asyncio.run(main())
