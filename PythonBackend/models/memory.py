from typing import Optional
from pydantic import BaseModel

class MemoryData(BaseModel):
    title: str
    bodyText: str
    url: str
    links: list[str] = []
    type: str = "webpage"
    metadata: Optional[dict] = {}
    timestamp: int

class PDFProcessingResult(BaseModel):
    status: str
    message: str
    chunks_created: int
    tokens_processed: int
    document_id: str