from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import User, Quest, QuestCompletion, UserStatus
from app.schemas.quest_completion import QuestCompletionResponse
from app.services.auth import get_current_user
from app.services.leveling import compute_level, xp_earned_today, already_completed_today, DAILY_XP_CAP

router = APIRouter(prefix="/quests", tags=["quests"])

@router.get("/")
def get_quests(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT id, title, domain_id, difficulty, xp_reward FROM quests"))
    rows = result.fetchall()
    return [
        {"id": r.id, "title": r.title, "domain_id": r.domain_id, "difficulty": r.difficulty, "xp_reward": r.xp_reward}
        for r in rows
    ]


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