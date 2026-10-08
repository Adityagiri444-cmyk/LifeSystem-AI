from pydantic import BaseModel
from typing import List

class BottleneckResponse(BaseModel):
    domain_id: int
    domain_name: str
    severity: str
    bottleneck_score: float
    reasons: List[str]