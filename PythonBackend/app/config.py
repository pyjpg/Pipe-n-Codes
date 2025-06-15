import os
from pathlib import Path
from typing import Optional, Any
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = None
    cohere_api_key: str
    
    # LangSmith/LangChain settings (optional)
    langsmith_tracing_v2: Optional[str] = None
    langchain_endpoint: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    langchain_project: Optional[str] = None
    
    # Database
    cassandra_host: str = "127.0.0.1"
    cassandra_port: int = 9042
    cassandra_keyspace: str = "rag_chat"
    
    # Paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = project_root / "data"
    vectorstore_dir: Path = project_root / "chroma_db"
    chat_vectorstore_dir: Path = project_root / "chroma_chat_db"
    pdf_vectorstore_dir: Path = project_root / "chroma_pdf_db"
    
    # Model settings
    embedding_model: str = "embed-english-v3.0"
    llm_model: str = "command-r"
    llm_temperature: float = 0.0
    
    # Chunking settings
    chunk_size: int = 256
    chunk_overlap: int = 0
    
    # API settings
    api_title: str = "RAG API"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow extra fields from .env file
        extra = "allow"

@lru_cache()
def get_settings():
    return Settings()