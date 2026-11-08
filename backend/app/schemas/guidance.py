from typing import Optional
from pydantic import BaseModel
from app.schemas.content import ContentRecommendation
from app.schemas.quest import QuestResponse


class GuidanceResponse(BaseModel):
    mode: str                                   # "recovery" or "growth"
    message: str                                # LLM-drafted when valid, otherwise a template
    source: str                                 # "llm" or "template"
    fallback_reason: Optional[str] = None
    quest: Optional[QuestResponse] = None       # chosen by the backend, never by the LLM
    content: Optional[ContentRecommendation] = None
    support_prompt: Optional[str] = None
    safety_note: str