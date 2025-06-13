from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str
    session_id: str 
