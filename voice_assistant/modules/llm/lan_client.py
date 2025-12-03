import json
import aiohttp
import asyncio
from typing import Iterator
from .base import LLMBase

class LanLLM(LLMBase):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    async def generate_async(self, prompt: str) -> Iterator[str]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            pass

    def generate(self, prompt: str) -> Iterator[str]:
        # Bridge async to sync iterator if needed, or better yet, make base async
        # For now, we'll assume the pipeline handles async generators
        raise NotImplementedError("Use generate_async instead")
