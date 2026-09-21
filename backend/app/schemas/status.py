from pydantic import BaseModel
from typing import Dict, Optional

class StatusResponse(BaseModel):
    xp: int
    level: int
    rank: str
    domain_scores: Optional[Dict[str, float]] = None
    balance_score: Optional[float] = None
    trend: str