from langchain_cohere import ChatCohere
from app.config import get_settings
from functools import lru_cache

settings = get_settings()

@lru_cache()
def get_llm(temperature: float = None):
    """Get cached LLM instance"""
    return ChatCohere(
        model=settings.llm_model,
        temperature=temperature or settings.llm_temperature,
        cohere_api_key=settings.cohere_api_key
    )