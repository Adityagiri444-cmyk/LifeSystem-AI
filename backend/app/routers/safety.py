from typing import List
from fastapi import APIRouter, Depends
from app.models import User
from app.schemas.safety import SafetyCheckRequest, SafetyCheckResponse, SafetyResource
from app.services.auth import get_current_user
from app.services.safety import RESOURCES, assess_text

router = APIRouter(prefix="/safety", tags=["safety"])


@router.post("/check", response_model=SafetyCheckResponse)
def check_text(
    payload: SafetyCheckRequest,
    current_user: User = Depends(get_current_user),
):
    # The text is classified in memory and never stored or logged.
    return assess_text(payload.text)


@router.get("/resources", response_model=List[SafetyResource])
def get_resources(current_user: User = Depends(get_current_user)):
    return RESOURCES