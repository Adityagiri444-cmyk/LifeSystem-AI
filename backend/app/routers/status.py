from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserStatus, AssessmentResult
from app.schemas.status import StatusResponse
from app.services.status import compute_rank, compute_balance_score
from app.services.auth import get_current_user

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/", response_model=StatusResponse)
def get_my_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    status_row = db.query(UserStatus).filter(UserStatus.user_id == current_user.id).first()
    if not status_row:
        status_row = UserStatus(user_id=current_user.id, xp=0, level=1)
        db.add(status_row)
        db.commit()
        db.refresh(status_row)

    assessment = db.query(AssessmentResult).filter(AssessmentResult.user_id == current_user.id).first()
    domain_scores = assessment.domain_scores if assessment else None

    return StatusResponse(
        xp=status_row.xp,
        level=status_row.level,
        rank=compute_rank(status_row.level),
        domain_scores=domain_scores,
        balance_score=compute_balance_score(domain_scores),
        trend="Not enough history yet — trends will appear after multiple check-ins over time.",
    )