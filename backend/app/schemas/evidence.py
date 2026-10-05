from pydantic import BaseModel
from typing import Dict, Any

class EvidenceSubmission(BaseModel):
    content: Dict[str, Any] = {}