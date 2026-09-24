from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Quest, QuestCompletion, UserStatus
from app.schemas.quest import QuestCreate, QuestUpdate, QuestResponse
from app.schemas.quest_completion import QuestCompletionResponse
from app.schemas.recommendation import RecommendationResponse
from app.services.auth import get_current_user
from app.services.leveling import compute_level, xp_earned_today, already_completed_today, DAILY_XP_CAP
from app.services.recommender import generate_recommendations

router = APIRouter(prefix="/quests", tags=["quests"])


@router.get("/", response_model=List[QuestResponse])
def get_quests(db: Session = Depends(get_db)):
    return db.query(Quest).all()


@router.get("/recommended", response_model=List[RecommendationResponse])
def get_recommended_quests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return generate_recommendations(db, current_user.id)


@router.get("/{quest_id}", response_model=QuestResponse)
def get_quest(quest_id: int, db: Session = Depends(get_db)):
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    return quest


@router.post("/", response_model=QuestResponse)
def create_quest(
    quest_data: QuestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_quest = Quest(**quest_data.model_dump())
    db.add(new_quest)
    db.commit()
    db.refresh(new_quest)
    return new_quest


@router.put("/{quest_id}", response_model=QuestResponse)
def update_quest(
    quest_id: int,
    quest_data: QuestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    updates = quest_data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(quest, field, value)

    db.commit()
    db.refresh(quest)
    return quest


@router.delete("/{quest_id}")
def delete_quest(
    quest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    db.delete(quest)
    db.commit()
    return {"detail": "Quest deleted"}


@router.post("/{quest_id}/complete", response_model=QuestCompletionResponse)
def complete_quest(
    quest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    if already_completed_today(db, current_user.id, quest_id):
        raise HTTPException(status_code=400, detail="Quest already completed in the last 24 hours")

    unmet = [p for p in (quest.prerequisites or []) if not already_completed_today(db, current_user.id, p)]
    # Note: this prerequisite check only looks at the last 24h; a proper "ever completed"
    # check will come once we track full completion history in a later week.

    xp_today = xp_earned_today(db, current_user.id)
    xp_to_award = quest.xp_reward

    if xp_today + xp_to_award > DAILY_XP_CAP:
        xp_to_award = max(0, DAILY_XP_CAP - xp_today)
        if xp_to_award == 0:
            raise HTTPException(status_code=400, detail="Daily XP cap reached. Try again tomorrow.")

    completion = QuestCompletion(user_id=current_user.id, quest_id=quest_id)
    db.add(completion)

    status_row = db.query(UserStatus).filter(UserStatus.user_id == current_user.id).first()
    if not status_row:
        status_row = UserStatus(user_id=current_user.id, xp=0, level=1)
        db.add(status_row)
        db.flush()

    old_level = status_row.level
    status_row.xp += xp_to_award
    level_info = compute_level(status_row.xp)
    status_row.level = level_info["level"]

    db.commit()

    return QuestCompletionResponse(
        xp_awarded=xp_to_award,
        total_xp=status_row.xp,
        level=level_info["level"],
        xp_into_level=level_info["xp_into_level"],
        xp_to_next_level=level_info["xp_to_next_level"],
        leveled_up=level_info["level"] > old_level,
    )