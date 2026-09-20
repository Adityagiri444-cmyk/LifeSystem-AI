from pydantic import BaseModel
from typing import Dict, Any

class AssessmentSubmission(BaseModel):
    answers: Dict[str, Any]   # question_id -> answer value

class AssessmentResultResponse(BaseModel):
    id: int
    user_id: int
    domain_scores: Dict[str, float]

    class Config:
        from_attributes = True