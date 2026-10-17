from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class CheckInCreate(BaseModel):
    state: Literal["tired", "stressed", "overwhelmed", "low_energy", "okay"]
    energy: Optional[int] = Field(default=None, ge=1, le=5)  # 1 = drained, 5 = great


class CheckInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    state: str
    energy: Optional[int] = None
    created_at: datetime


class RecoveryStatusResponse(BaseModel):
    recovery_active: bool
    state: Optional[str] = None
    since: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    message: str
    xp_target_today: Optional[int] = None
    max_quest_minutes: Optional[int] = None
    safety_note: str