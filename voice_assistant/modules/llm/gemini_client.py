import google.generativeai as genai
from typing import AsyncIterator
from .base import LLMBase

class GeminiLLM(LLMBase):
    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    async def generate_async(self, prompt: str) -> AsyncIterator[str]:
        response = await self.model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    def generate(self, prompt: str):
        raise NotImplementedError("Use generate_async")
