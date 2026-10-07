from pydantic import BaseModel

class DifficultyStateResponse(BaseModel):
    domain_id: int
    current_difficulty: str
    streak: int

    class Config:
        from_attributes = True