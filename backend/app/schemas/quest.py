from pydantic import BaseModel
from typing import Optional, List

class QuestCreate(BaseModel):
    title: str
    objective: Optional[str] = None
    domain_id: int
    difficulty: str
    duration_minutes: Optional[int] = None
    prerequisites: Optional[List[int]] = []
    evidence_type: Optional[str] = "none"
    xp_reward: int

class QuestUpdate(BaseModel):
    title: Optional[str] = None
    objective: Optional[str] = None
    domain_id: Optional[int] = None
    difficulty: Optional[str] = None
    duration_minutes: Optional[int] = None
    prerequisites: Optional[List[int]] = None
    evidence_type: Optional[str] = None
    xp_reward: Optional[int] = None

class QuestResponse(BaseModel):
    id: int
    title: str
    objective: Optional[str]
    domain_id: int
    difficulty: str
    duration_minutes: Optional[int]
    prerequisites: List[int]
    evidence_type: str
    xp_reward: int

    class Config:
        from_attributes = True