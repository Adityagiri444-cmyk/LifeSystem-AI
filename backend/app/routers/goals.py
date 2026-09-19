from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Goal
from app.schemas.goal import GoalCreate, GoalResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/goals", tags=["goals"])

@router.post("/", response_model=GoalResponse)
def create_goal(
    goal_data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_goal = Goal(
        user_id=current_user.id,
        domain_id=goal_data.domain_id,
        title=goal_data.title,
        description=goal_data.description,
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


@router.get("/", response_model=List[GoalResponse])
def get_my_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Goal).filter(Goal.user_id == current_user.id).all()