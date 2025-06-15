from typing import List, Dict
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.models.memory import MemoryData
from app.core.vectorstore import vector_store_manager
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class MemoryService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    
    async def save_memory(self, data: MemoryData) -> Dict:
        """Save memory data to vectorstore"""
        try:
            # Create document from memory data
            full_text = f"Title: {data.title}\nURL: {data.url}\n\n{data.bodyText}"
            doc = Document(
                page_content=full_text, 
                metadata={
                    "source": data.url,
                    "title": data.title,
                    "type": data.type,
                    "timestamp": data.timestamp
                }
            )
            
            # Split into chunks
            docs_split = self.text_splitter.split_documents([doc])
            
            # Get vectorstore and add documents
            vectorstore = vector_store_manager.get_main_store()
            vectorstore.add_documents(docs_split)
            vectorstore.persist()
            
            logger.info(f"Saved {len(docs_split)} chunks from {data.title}")
            
            return {
                "chunks_created": len(docs_split),
                "source": data.url
            }
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            raise
    
    def search_memories(self, query: str, limit: int = 5) -> List[Dict]:
        """Search through saved memories"""
        try:
            vectorstore = vector_store_manager.get_main_store()
            retriever = vectorstore.as_retriever(search_kwargs={"k": limit})
            docs = retriever.get_relevant_documents(query)
            
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content[:500],  # First 500 chars
                    "metadata": doc.metadata,
                    "relevance_score": getattr(doc, "score", None)
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise

# Singleton instance
memory_service = MemoryService()