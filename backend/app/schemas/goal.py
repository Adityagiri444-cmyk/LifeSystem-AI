from pydantic import BaseModel
from typing import Optional

class GoalCreate(BaseModel):
    domain_id: int
    title: str
    description: Optional[str] = None

class GoalResponse(BaseModel):
    id: int
    user_id: int
    domain_id: int
    title: str
    description: Optional[str]
    status: str

    class Config:
        from_attributes = True