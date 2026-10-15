from pydantic import BaseModel
from typing import List
from app.schemas.quest import QuestResponse

class ExplanationFactor(BaseModel):
    name: str
    impact: str
    value: str
    detail: str

class ExplanationResponse(BaseModel):
    quest: QuestResponse
    domain_name: str
    confidence: float
    confidence_label: str
    summary: str
    recommended_now: bool
    factors: List[ExplanationFactor]