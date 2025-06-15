from fastapi import APIRouter
from app.services.health_service import health_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "RAG API",
        "version": "1.0.0"
    }

@router.get("/vectorstore")
async def check_vectorstore_health():
    """Check if vectorstore is working properly"""
    try:
        health_status = health_service.check_vectorstore_health()
        return health_status
    except Exception as e:
        logger.error(f"Error checking vectorstore health: {str(e)}")
        return {
            "status": "error",
            "vectorstore_exists": False,
            "can_retrieve": False,
            "message": f"Error checking vectorstore: {str(e)}"
        }

@router.get("/database")
async def check_database_health():
    """Check if Cassandra is working properly"""
    try:
        health_status = health_service.check_database_health()
        return health_status
    except Exception as e:
        logger.error(f"Error checking database health: {str(e)}")
        return {
            "status": "error",
            "connected": False,
            "message": f"Error checking database: {str(e)}"
        }

@router.get("/llm")
async def check_llm_health():
    """Check if LLM is accessible"""
    try:
        health_status = await health_service.check_llm_health()
        return health_status
    except Exception as e:
        logger.error(f"Error checking LLM health: {str(e)}")
        return {
            "status": "error",
            "accessible": False,
            "message": f"Error checking LLM: {str(e)}"
        }

@router.get("/detailed")
async def detailed_health_check():
    """Comprehensive health check of all components"""
    try:
        detailed_status = await health_service.get_detailed_health()
        return detailed_status
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        return {
            "status": "error",
            "message": f"Error performing detailed health check: {str(e)}"
        }