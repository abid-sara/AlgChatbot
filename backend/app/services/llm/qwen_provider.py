"""Qwen 2.5 LLM provider implementation"""

from config.settings import TEMPERATURE, MAX_TOKENS
from app.services.llm.base import BaseLLM

class QwenLLM(BaseLLM):
    """QWEN LLM implementation"""
    
    def __init__(self):
        pass
    
    def generate_content(self, prompt):
       pass