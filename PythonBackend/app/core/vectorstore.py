from langchain_community.vectorstores import Chroma
from app.config import get_settings
from app.core.embeddings import get_embeddings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class VectorStoreManager:
    def __init__(self):
        self.embeddings = get_embeddings()
        self._stores = {}
    
    def get_main_store(self):
        """Get main document vectorstore"""
        if "main" not in self._stores:
            self._stores["main"] = Chroma(
                persist_directory=str(settings.vectorstore_dir),
                embedding_function=self.embeddings
            )
        return self._stores["main"]
    
    def get_chat_store(self):
        """Get chat history vectorstore"""
        if "chat" not in self._stores:
            self._stores["chat"] = Chroma(
                persist_directory=str(settings.chat_vectorstore_dir),
                embedding_function=self.embeddings
            )
        return self._stores["chat"]
    
    def get_pdf_store(self):
        """Get PDF vectorstore"""
        if "pdf" not in self._stores:
            self._stores["pdf"] = Chroma(
                persist_directory=str(settings.pdf_vectorstore_dir),
                embedding_function=self.embeddings
            )
        return self._stores["pdf"]
    
    def check_store_exists(self, store_type: str = "main") -> bool:
        """Check if vectorstore exists and has documents"""
        try:
            store = self.get_main_store() if store_type == "main" else \
                    self.get_chat_store() if store_type == "chat" else \
                    self.get_pdf_store()
            count = store._collection.count()
            return count > 0
        except Exception as e:
            logger.error(f"Error checking {store_type} store: {e}")
            return False

# Singleton instance
vector_store_manager = VectorStoreManager()