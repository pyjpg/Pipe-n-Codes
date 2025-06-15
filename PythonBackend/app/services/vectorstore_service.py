from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain.schema import Document
from app.core.vectorstore import vector_store_manager
from app.core.embeddings import get_embeddings
from app.config import get_settings
import time
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class VectorStoreService:
    def __init__(self):
        self.embeddings = get_embeddings()
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    
    def check_vectorstore_exists(self) -> bool:
        """Check if vectorstore exists and has documents"""
        return vector_store_manager.check_store_exists("main")
    
    def load_documents(self) -> List[Document]:
        """Load documents from data directory"""
        logger.info(f"📂 Loading documents from {settings.data_dir}")
        all_docs = []
        
        if not settings.data_dir.exists():
            logger.error(f"Data directory not found: {settings.data_dir}")
            return []
        
        # Load PDF documents
        try:
            pdf_loader = DirectoryLoader(
                str(settings.data_dir),
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
            )
            pdf_docs = pdf_loader.load()
            all_docs.extend(pdf_docs)
            logger.info(f"✅ Loaded {len(pdf_docs)} PDF documents")
        except Exception as e:
            logger.warning(f"Could not load PDF documents: {e}")
        
        # Load text documents
        try:
            txt_loader = DirectoryLoader(
                str(settings.data_dir),
                glob="**/*.txt",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8", "errors": "ignore"}
            )
            txt_docs = txt_loader.load()
            all_docs.extend(txt_docs)
            logger.info(f"✅ Loaded {len(txt_docs)} text documents")
        except Exception as e:
            logger.warning(f"Could not load text documents: {e}")
        
        logger.info(f"📊 Total documents loaded: {len(all_docs)}")
        return all_docs
    
    def embed_documents_safely(self, docs: List[Document], batch_size: int = 10) -> bool:
        """Embed documents in batches with error handling"""
        logger.info(f"🚀 Embedding {len(docs)} document chunks")
        
        try:
            vectorstore = vector_store_manager.get_main_store()
            
            # Check current count
            try:
                current_count = vectorstore._collection.count()
                logger.info(f"📊 Current vectorstore contains {current_count} documents")
            except:
                current_count = 0
            
            # Add documents in batches
            total_batches = (len(docs) + batch_size - 1) // batch_size
            
            for i in range(0, len(docs), batch_size):
                batch = docs[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"⏳ Processing batch {batch_num}/{total_batches}")
                
                try:
                    vectorstore.add_documents(batch)
                    logger.info(f"✅ Added batch {batch_num}/{total_batches}")
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error adding batch {batch_num}: {e}")
                    time.sleep(10)
                    # Retry once
                    try:
                        vectorstore.add_documents(batch)
                        logger.info(f"✅ Added batch {batch_num} on retry")
                    except Exception as retry_error:
                        logger.error(f"Failed to add batch {batch_num} even on retry: {retry_error}")
                        continue
            
            # Persist changes
            vectorstore.persist()
            return True
            
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            return False
    
    def setup_vectorstore(self) -> bool:
        """Setup vectorstore from documents in data directory"""
        logger.info("🚀 Setting up vectorstore...")
        
        # Load documents
        docs = self.load_documents()
        if not docs:
            logger.error("No documents found!")
            return False
        
        # Split documents
        logger.info("✂️ Splitting documents into chunks...")
        docs_split = self.text_splitter.split_documents(docs)
        logger.info(f"📄 Split into {len(docs_split)} chunks")
        
        # Embed documents
        success = self.embed_documents_safely(docs_split)
        
        if success:
            logger.info("✅ Vectorstore setup completed successfully!")
            return True
        else:
            logger.error("❌ Failed to setup vectorstore")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vectorstore statistics"""
        stats = {
            "main_store": {"exists": False, "count": 0},
            "chat_store": {"exists": False, "count": 0},
            "pdf_store": {"exists": False, "count": 0}
        }
        
        try:
            # Main store
            main_store = vector_store_manager.get_main_store()
            stats["main_store"]["exists"] = True
            stats["main_store"]["count"] = main_store._collection.count()
        except Exception as e:
            logger.error(f"Error getting main store stats: {e}")
        
        try:
            # Chat store
            chat_store = vector_store_manager.get_chat_store()
            stats["chat_store"]["exists"] = True
            stats["chat_store"]["count"] = chat_store._collection.count()
        except Exception as e:
            logger.error(f"Error getting chat store stats: {e}")
        
        try:
            # PDF store
            pdf_store = vector_store_manager.get_pdf_store()
            stats["pdf_store"]["exists"] = True
            stats["pdf_store"]["count"] = pdf_store._collection.count()
        except Exception as e:
            logger.error(f"Error getting PDF store stats: {e}")
        
        stats["total_documents"] = sum(store["count"] for store in stats.values())
        return stats

# Singleton instance
vectorstore_service = VectorStoreService()