from fastapi import APIRouter, HTTPException
from app.services.session_service import session_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/session", tags=["Session"])

@router.get("/")
async def list_sessions():
    """List all active session IDs"""
    try:
        sessions = session_service.list_active_sessions()
        return {
            "active_sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = session_service.get_session_history(session_id)
        return {
            "session_id": session_id,
            "history": [
                {"type": msg.type, "content": msg.content} 
                for msg in history
            ],
            "message_count": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session"""
    try:
        session_service.clear_session(session_id)
        return {
            "status": "success", 
            "message": f"Session {session_id} cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/export")
async def export_session(session_id: str):
    """Export session history"""
    try:
        export_data = session_service.export_session(session_id)
        return {
            "status": "success",
            "session_id": session_id,
            "data": export_data
        }
    except Exception as e:
        logger.error(f"Error exporting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))