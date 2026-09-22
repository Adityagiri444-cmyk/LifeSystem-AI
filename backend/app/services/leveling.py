DAILY_XP_CAP = 150

def xp_required_for_level(level: int) -> int:
    """XP needed to go from `level` to `level + 1`. Increases by 50 each level."""
    return 100 + (level - 1) * 50


def compute_level(total_xp: int) -> dict:
    """
    Given a user's total lifetime XP, work out their current level,
    how much XP they have into the current level, and how much
    more they need to reach the next one.
    """
    level = 1
    xp_remaining = total_xp

    while xp_remaining >= xp_required_for_level(level):
        xp_remaining -= xp_required_for_level(level)
        level += 1

    return {
        "level": level,
        "xp_into_level": xp_remaining,
        "xp_to_next_level": xp_required_for_level(level) - xp_remaining,
    }

from datetime import datetime, timezone, timedelta


def xp_earned_today(db, user_id: int) -> int:
    """Sum XP from quest completions in the last 24 hours."""
    from app.models import QuestCompletion, Quest

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    completions = (
        db.query(QuestCompletion)
        .filter(QuestCompletion.user_id == user_id, QuestCompletion.completed_at >= since)
        .all()
    )
    total = 0
    for c in completions:
        quest = db.query(Quest).filter(Quest.id == c.quest_id).first()
        if quest:
            total += quest.xp_reward
    return total


def already_completed_today(db, user_id: int, quest_id: int) -> bool:
    """Prevent completing the exact same quest more than once per 24h."""
    from app.models import QuestCompletion

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    existing = (
        db.query(QuestCompletion)
        .filter(
            QuestCompletion.user_id == user_id,
            QuestCompletion.quest_id == quest_id,
            QuestCompletion.completed_at >= since,
        )
        .first()
    )
    return existing is not None