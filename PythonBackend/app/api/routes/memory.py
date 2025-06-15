from fastapi import APIRouter, HTTPException
from app.models.memory import MemoryData
from app.services.memory_service import memory_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory", tags=["Memory"])

@router.post("/save")
async def save_memory(data: MemoryData):
    """Save and embed memory data"""
    try:
        result = await memory_service.save_memory(data)
        return {
            "status": "success", 
            "message": "Memory saved and embedded.",
            "chunks_created": result.get("chunks_created", 0)
        }
    except Exception as e:
        logger.error(f"Error saving memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_memory(query: str, limit: int = 5):
    """Search through saved memories"""
    try:
        results = memory_service.search_memories(query, limit)
        return {
            "status": "success",
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))