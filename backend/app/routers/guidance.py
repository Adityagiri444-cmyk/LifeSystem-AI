from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.guidance import GuidanceResponse
from app.services.auth import get_current_user
from app.services.guidance import get_guidance

router = APIRouter(prefix="/guidance", tags=["guidance"])


@router.get("/today", response_model=GuidanceResponse)
def guidance_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_guidance(db, current_user.id)