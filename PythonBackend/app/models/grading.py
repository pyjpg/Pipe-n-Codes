from typing import Literal
from pydantic import BaseModel, Field

class GradeDocuments(BaseModel):
    """Document relevance grading"""
    binary_score: Literal["yes", "no"] = Field(
        description="Answer must be 'yes' or 'no'."
    )

class HallucinationScore(BaseModel):
    """Binary score to assess if answer is grounded in documents"""
    binary_score: Literal["yes", "no"] = Field(
        description="Answer must be 'yes' or 'no'."
    )