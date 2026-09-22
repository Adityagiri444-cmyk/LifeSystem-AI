from pydantic import BaseModel

class QuestCompletionResponse(BaseModel):
    xp_awarded: int
    total_xp: int
    level: int
    xp_into_level: int
    xp_to_next_level: int
    leveled_up: bool