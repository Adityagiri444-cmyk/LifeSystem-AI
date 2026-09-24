from pydantic import BaseModel
from app.schemas.quest import QuestResponse

class RecommendationResponse(BaseModel):
    quest: QuestResponse
    reason: str
    domain_priority_score: float