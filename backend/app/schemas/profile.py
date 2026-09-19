from pydantic import BaseModel
from typing import Optional, Dict, Any

class ProfileCreate(BaseModel):
    age_range: Optional[str] = None
    availability: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    age_range: Optional[str]
    availability: Optional[str]
    preferences: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True