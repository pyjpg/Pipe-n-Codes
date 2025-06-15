from fastapi import APIRouter, HTTPException
from app.models.question import QuestionRequest
from app.services.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])

@router.post("/")
async def rag_answer(req: QuestionRequest):
    """Process a question using RAG"""
    try:
        result = rag_service.process_question(
            question=req.question,
            session_id=req.session_id
        )
        
        return {
            "answer": result["simplified_answer"],
            "raw_answer": result["answer"],
            "source": result["source"],
            "hallucinated": result["hallucination_score"] == "yes",
            "session_id": req.session_id
        }
    except Exception as e:
        logger.error(f"Error in RAG endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))