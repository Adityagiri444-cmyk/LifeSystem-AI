from pydantic import BaseModel
from typing import Optional
from app.schemas.quest import QuestResponse

class NextActionResponse(BaseModel):
    quest: Optional[QuestResponse] = None
    domain_name: Optional[str] = None
    reason: Optional[str] = None
    xp_remaining_today: int
    message: Optional[str] = None