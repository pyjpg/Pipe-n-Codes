from langchain_cohere import CohereEmbeddings
from app.config import get_settings
from functools import lru_cache

settings = get_settings()

@lru_cache()
def get_embeddings():
    """Get cached embeddings instance"""
    return CohereEmbeddings(
        model=settings.embedding_model,
        cohere_api_key=settings.cohere_api_key
    )