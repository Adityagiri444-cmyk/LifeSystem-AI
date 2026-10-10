from sqlalchemy.orm import Session
from app.models import Quest
from app.services.bottleneck import detect_bottlenecks
from app.services.difficulty import get_or_create_difficulty_state
from app.services.leveling import xp_earned_today, already_completed_today, DAILY_XP_CAP
from app.services.recommender import get_domain_priorities


def rank_domains(priorities: list[dict], bottlenecks: dict[int, dict]) -> list[dict]:
    """
    Pure logic: merge recommender priorities with bottleneck results into one
    ranking. combined_score = priority_score + bottleneck_score.
    """
    ranked = []
    for p in priorities:
        b = bottlenecks.get(p["domain_id"])
        bottleneck_score = b["bottleneck_score"] if b else 0.0
        ranked.append({
            "domain_id": p["domain_id"],
            "domain_name": p["domain_name"],
            "assessment_score": p["score"],
            "has_active_goal": p["has_active_goal"],
            "priority_score": p["priority_score"],
            "bottleneck_score": bottleneck_score,
            "bottleneck_severity": b["severity"] if b else None,
            "bottleneck_reasons": b["reasons"] if b else [],
            "combined_score": round(p["priority_score"] + bottleneck_score, 2),
        })
    ranked.sort(key=lambda d: d["combined_score"], reverse=True)
    return ranked


def build_reason(domain: dict, difficulty: str, matched_level: bool, quest_xp: int, xp_remaining: int) -> str:
    """Pure logic: turn the ranking signals into a plain-language explanation."""
    name = domain["domain_name"]

    if domain["bottleneck_reasons"]:
        why = "; ".join(domain["bottleneck_reasons"])
    else:
        bits = []
        if domain["assessment_score"] is not None:
            bits.append(f"your {name} assessment score is {domain['assessment_score']}")
        else:
            bits.append(f"you haven't been assessed in {name} yet")
        if domain["has_active_goal"]:
            bits.append(f"you have an active goal in {name}")
        why = " and ".join(bits)

    sentences = [f"Suggested because {why}."]

    if matched_level:
        sentences.append(f"It matches your current {difficulty} level in {name}.")
    else:
        sentences.append(f"No unfinished {difficulty} quest was available in {name}, so this is the closest match.")

    if quest_xp > xp_remaining:
        sentences.append(
            f"Only {xp_remaining} XP is left under today's cap, so you'll earn less than the full {quest_xp} XP."
        )
    else:
        sentences.append(f"You have {xp_remaining} XP left to earn today.")

    return " ".join(sentences)


def get_next_best_action(db: Session, user_id: int) -> dict:
    xp_remaining = max(0, DAILY_XP_CAP - xp_earned_today(db, user_id))
    if xp_remaining == 0:
        return {
            "quest": None,
            "domain_name": None,
            "reason": None,
            "xp_remaining_today": 0,
            "message": "You've reached today's XP cap. Rest up, new XP unlocks tomorrow.",
        }

    bottlenecks = {b["domain_id"]: b for b in detect_bottlenecks(db, user_id)}
    ranked = rank_domains(get_domain_priorities(db, user_id), bottlenecks)
    states = {d["domain_id"]: get_or_create_difficulty_state(db, user_id, d["domain_id"]) for d in ranked}

    # Pass 1: only quests at the user's current difficulty. Pass 2: anything unfinished.
    for require_match in (True, False):
        for domain in ranked:
            level = states[domain["domain_id"]].current_difficulty
            query = db.query(Quest).filter(Quest.domain_id == domain["domain_id"])
            if require_match:
                query = query.filter(Quest.difficulty == level)

            for quest in query.order_by(Quest.id).all():
                if not already_completed_today(db, user_id, quest.id):
                    return {
                        "quest": quest,
                        "domain_name": domain["domain_name"],
                        "reason": build_reason(domain, level, require_match, quest.xp_reward, xp_remaining),
                        "xp_remaining_today": xp_remaining,
                        "message": None,
                    }

    return {
        "quest": None,
        "domain_name": None,
        "reason": None,
        "xp_remaining_today": xp_remaining,
        "message": "You've completed every available quest today. Check back tomorrow.",
    }