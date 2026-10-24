from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class SafetyCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class SafetyResource(BaseModel):
    region: str
    name: str
    contact: str
    note: str


class SafetyCheckResponse(BaseModel):
    level: Literal["none", "redirect", "escalate"]
    category: Optional[str] = None
    message: str
    resources: List[SafetyResource] = []