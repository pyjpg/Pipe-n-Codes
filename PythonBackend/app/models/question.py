from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import uuid

class QuestionRequest(BaseModel):
    """Model for RAG question requests"""
    question: str = Field(..., description="The user's question")
    session_id: str = Field(..., description="Session ID for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the question")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in response")
    temperature: Optional[float] = Field(None, description="LLM temperature setting")
    
    @validator('question')
    def validate_question(cls, v):
        """Ensure question is not empty"""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        # Limit question length
        if len(v) > 1000:
            raise ValueError("Question must be less than 1000 characters")
        return v.strip()
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session ID format"""
        if not v or not v.strip():
            # Generate a default session ID if not provided
            return str(uuid.uuid4())
        return v.strip()
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Ensure temperature is in valid range"""
        if v is not None and (v < 0 or v > 2):
            raise ValueError("Temperature must be between 0 and 2")
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        """Ensure max_tokens is reasonable"""
        if v is not None:
            if v < 1:
                raise ValueError("max_tokens must be at least 1")
            if v > 4000:
                raise ValueError("max_tokens cannot exceed 4000")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the fire safety requirements for residential buildings?",
                "session_id": "user-session-123",
                "context": {"building_type": "residential", "floors": 5},
                "max_tokens": 500,
                "temperature": 0.7
            }
        }


class QuestionResponse(BaseModel):
    """Model for RAG question responses"""
    answer: str = Field(..., description="The generated answer")
    simplified_answer: str = Field(..., description="Simplified version for UI display")
    source: str = Field(..., description="Source of answer (rag, fallback, error)")
    hallucinated: bool = Field(..., description="Whether hallucination was detected")
    session_id: str = Field(..., description="Session ID used")
    retrieved_docs_count: int = Field(default=0, description="Number of documents retrieved")
    confidence_score: Optional[float] = Field(None, description="Confidence in the answer (0-1)")
    processing_time: Optional[float] = Field(None, description="Time taken to process in seconds")
    
    @validator('source')
    def validate_source(cls, v):
        """Ensure source is valid"""
        valid_sources = ['rag', 'fallback', 'error', 'cache']
        if v not in valid_sources:
            raise ValueError(f"Source must be one of: {', '.join(valid_sources)}")
        return v
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        """Ensure confidence score is between 0 and 1"""
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Confidence score must be between 0 and 1")
        return v


class ConversationTurn(BaseModel):
    """Model for a single conversation turn"""
    role: str = Field(..., description="Role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="When message was sent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('role')
    def validate_role(cls, v):
        """Ensure role is valid"""
        if v not in ['user', 'assistant', 'system']:
            raise ValueError("Role must be 'user', 'assistant', or 'system'")
        return v


class SessionHistory(BaseModel):
    """Model for session history"""
    session_id: str = Field(..., description="Session identifier")
    conversation: List[ConversationTurn] = Field(default_factory=list, description="Conversation turns")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    last_activity: datetime = Field(default_factory=datetime.now, description="Last activity time")
    message_count: int = Field(default=0, description="Total message count")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")