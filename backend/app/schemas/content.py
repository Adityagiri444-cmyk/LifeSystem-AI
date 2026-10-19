from typing import List, Optional
from pydantic import BaseModel


class ContentItem(BaseModel):
    id: str
    category: str
    title: str
    description: str
    duration_minutes: int
    energy_required: int
    format: str
    tags: List[str] = []
    search_hint: Optional[str] = None


class ContentRecommendation(ContentItem):
    reasons: List[str]


class ContentRecommendationResponse(BaseModel):
    mode: str                       # "recovery" or "general"
    state: Optional[str] = None
    recommendations: List[ContentRecommendation]
    message: Optional[str] = None
    safety_note: str