"""Gemini LLM provider implementation"""

import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME, TEMPERATURE, MAX_TOKENS
from app.services.llm.base import BaseLLM
from langchain_core.runnables import Runnable

class GeminiLLM(BaseLLM, Runnable):
    """Google Gemini LLM implementation"""
    
    def __init__(self):
        """Initialize the Gemini model"""
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            generation_config={
                "temperature": TEMPERATURE,
                "max_output_tokens": MAX_TOKENS,
            }
        )
    
    def generate_content(self, prompt):
        """
        Generate content using Gemini
        
        Args:
            prompt (str): The input prompt
            
        Returns:
            Response object with text attribute
        """
        return self.model.generate_content(prompt)
    
    def stream_content(self, prompt):
        return self.model.generate_content(prompt, stream=True)
    

    # runnable interface 
    def invoke(self, input, config=None):
        """
        GeminiLLM compatible with LangChain's Runnable interface.
        To use with the agent
        """
        if isinstance(input, dict):
            prompt = input.get("input", "")
        else:
            prompt = str(input)

        response = self.model.generate_content(prompt)
        return response.text