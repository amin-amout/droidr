import os
from groq import AsyncGroq
from typing import AsyncIterator
from .base import LLMBase

class GroqLLM(LLMBase):
    def __init__(self, api_key: str, model: str):
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def generate_async(self, prompt: str) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=self.model,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def generate(self, prompt: str):
        raise NotImplementedError("Use generate_async")
