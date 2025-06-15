from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

class MemoryData(BaseModel):
    """Model for storing memory/document data"""
    title: str = Field(..., description="Title of the document or webpage")
    bodyText: str = Field(..., description="Main text content to be stored")
    url: str = Field(..., description="Source URL of the content")
    links: List[str] = Field(default_factory=list, description="List of links found in the content")
    type: str = Field(default="webpage", description="Type of content (webpage, pdf, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    timestamp: int = Field(..., description="Unix timestamp when the memory was created")
    
    @validator('timestamp', pre=True)
    def validate_timestamp(cls, v):
        """Ensure timestamp is valid and convert from milliseconds if needed"""
        if v is None:
            # If no timestamp provided, use current time
            return int(datetime.now().timestamp())
            
        # Convert to int if string
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {v}")
        
        if v < 0:
            raise ValueError("Timestamp must be positive")
        
        # Current time in seconds
        current_time = int(datetime.now().timestamp())
        
        # Check if timestamp is in milliseconds (typical JavaScript timestamp)
        # If timestamp is larger than year 2100 in seconds, it's likely in milliseconds
        if v > 4102444800:  # Jan 1, 2100 in seconds
            # Convert from milliseconds to seconds
            v = v // 1000
        
        # After conversion, check if it's still in the future
        # Allow up to 1 hour in the future for clock skew
        if v > current_time + 3600:  # 1 hour in future
            # If it's too far in future, just use current time
            return current_time
        
        # Check if timestamp is not too old (optional - e.g., not before year 2000)
        min_timestamp = int(datetime(2000, 1, 1).timestamp())
        if v < min_timestamp:
            raise ValueError(f"Timestamp seems too old (before year 2000): {v}")
        
        return v
    
    @validator('bodyText')
    def validate_body_text(cls, v):
        """Ensure body text is not empty"""
        if not v or not v.strip():
            raise ValueError("Body text cannot be empty")
        return v.strip()
    
    @validator('url')
    def validate_url(cls, v):
        """Basic URL validation"""
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        # Basic check for URL format
        if not (v.startswith('http://') or v.startswith('https://') or v.startswith('file://')):
            raise ValueError("URL must start with http://, https://, or file://")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Building Regulations 2010",
                "bodyText": "The Building Regulations 2010 set out the standards for the design and construction of buildings...",
                "url": "https://www.gov.uk/building-regulations",
                "links": ["https://www.gov.uk/related-link1", "https://www.gov.uk/related-link2"],
                "type": "webpage",
                "metadata": {"category": "regulations", "year": 2010},
                "timestamp": 1634567890  # Unix timestamp in seconds
            }
        }


class MemorySearchResult(BaseModel):
    """Model for memory search results"""
    content: str = Field(..., description="Relevant content excerpt")
    title: str = Field(..., description="Title of the source document")
    url: str = Field(..., description="Source URL")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: int = Field(..., description="When this memory was created")
    
    @validator('relevance_score')
    def validate_relevance_score(cls, v):
        """Ensure relevance score is between 0 and 1"""
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Relevance score must be between 0 and 1")
        return v


class MemoryStats(BaseModel):
    """Model for memory storage statistics"""
    total_documents: int = Field(..., description="Total number of documents stored")
    total_chunks: int = Field(..., description="Total number of chunks in vectorstore")
    storage_size_mb: Optional[float] = Field(None, description="Approximate storage size in MB")
    oldest_document: Optional[datetime] = Field(None, description="Timestamp of oldest document")
    newest_document: Optional[datetime] = Field(None, description="Timestamp of newest document")
    document_types: Dict[str, int] = Field(default_factory=dict, description="Count by document type")