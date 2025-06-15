from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.routes import memory, rag, session, health
from app.core.database import cassandra_conn
from app.services.vectorstore_service import vectorstore_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(memory.router)
app.include_router(rag.router)
app.include_router(session.router)
app.include_router(health.router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting up RAG application...")
    
    # Connect to Cassandra
    cassandra_conn.connect()
    
    # Check/setup vectorstore
    if vectorstore_service.check_vectorstore_exists():
        logger.info("✅ Vectorstore already exists and has documents")
    else:
        logger.info("🔄 Setting up vectorstore...")
        success = vectorstore_service.setup_vectorstore()
        if not success:
            logger.warning("⚠️ Failed to setup vectorstore!")
    
    logger.info("🎉 RAG application startup completed!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    cassandra_conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)