from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/quests", tags=["quests"])

@router.get("/")
def get_quests(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT id, title, domain_id, difficulty, xp_reward FROM quests"))
    rows = result.fetchall()
    return [
        {"id": r.id, "title": r.title, "domain_id": r.domain_id, "difficulty": r.difficulty, "xp_reward": r.xp_reward}
        for r in rows
    ]