from pydantic import BaseModel

class WebSearch(BaseModel):
    """
    Use for general knowledge, real-world events, or questions 
    unrelated to Building Services
    """
    pass

class VectorStore(BaseModel):
    """
    Use for technical questions about Building Services, 
    construction works, and legislations
    """
    pass