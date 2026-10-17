from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.recovery import CheckInCreate, CheckInResponse, RecoveryStatusResponse
from app.services.auth import get_current_user
from app.services.recovery import record_check_in, get_recovery_status

router = APIRouter(prefix="/recovery", tags=["recovery"])


@router.post("/check-in", response_model=CheckInResponse, status_code=201)
def create_check_in(
    payload: CheckInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return record_check_in(db, current_user.id, payload.state, payload.energy)


@router.get("/status", response_model=RecoveryStatusResponse)
def recovery_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_recovery_status(db, current_user.id)