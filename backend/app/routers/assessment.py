from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, AssessmentResult
from app.schemas.assessment import AssessmentSubmission, AssessmentResultResponse
from app.services.assessment import score_assessment, QUESTION_BANK
from app.services.auth import get_current_user

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.get("/questions")
def get_questions():
    return QUESTION_BANK


@router.post("/submit", response_model=AssessmentResultResponse)
def submit_assessment(
    submission: AssessmentSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    domain_scores = score_assessment(submission.answers)

    result = db.query(AssessmentResult).filter(AssessmentResult.user_id == current_user.id).first()
    if result:
        result.domain_scores = domain_scores
        result.raw_answers = submission.answers
    else:
        result = AssessmentResult(
            user_id=current_user.id,
            domain_scores=domain_scores,
            raw_answers=submission.answers,
        )
        db.add(result)

    db.commit()
    db.refresh(result)
    return result


@router.get("/results", response_model=AssessmentResultResponse)
def get_my_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.query(AssessmentResult).filter(AssessmentResult.user_id == current_user.id).first()
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No assessment results found")
    return result