"""Qwen 2.5 LLM provider implementation"""

from config.settings import TEMPERATURE, MAX_TOKENS
from app.services.llm.base import BaseLLM
from openai import OpenAI

class QwenLLM(BaseLLM):
    """QWEN LLM implementation"""
    

    def __init__(self, base_url="http://localhost:8000/v1", model_name=""):
        self.client = OpenAI(base_url=base_url, api_key="yourkey")
        self.model_name = model_name

    def generate_content(self, prompt):
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )

    def stream_content(self, prompt):
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
