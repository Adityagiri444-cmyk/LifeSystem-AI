from pydantic import BaseModel

class MilestoneResponse(BaseModel):
    id: int
    goal_id: int
    title: str
    order_index: int
    skill_tag: str | None
    status: str

    class Config:
        from_attributes = True