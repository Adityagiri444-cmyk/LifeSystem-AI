from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Goal, Milestone
from app.schemas.milestone import MilestoneResponse
from app.services.auth import get_current_user
from app.services.roadmap import generate_milestones_for_goal

router = APIRouter(prefix="/goals", tags=["roadmap"])


@router.post("/{goal_id}/roadmap", response_model=List[MilestoneResponse])
def generate_roadmap(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    existing = db.query(Milestone).filter(Milestone.goal_id == goal_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Roadmap already exists for this goal")

    milestone_data = generate_milestones_for_goal(goal)
    milestones = [Milestone(goal_id=goal_id, **m) for m in milestone_data]
    db.add_all(milestones)
    db.commit()

    return db.query(Milestone).filter(Milestone.goal_id == goal_id).order_by(Milestone.order_index).all()


@router.get("/{goal_id}/roadmap", response_model=List[MilestoneResponse])
def get_roadmap(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    return db.query(Milestone).filter(Milestone.goal_id == goal_id).order_by(Milestone.order_index).all()