from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Quest
from app.services.bottleneck import detect_bottlenecks, LOW_SCORE_THRESHOLD
from app.services.difficulty import get_or_create_difficulty_state
from app.services.leveling import xp_earned_today, already_completed_today, DAILY_XP_CAP
from app.services.next_action import rank_domains
from app.services.recommender import get_domain_priorities


def confidence_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"


def _factor(name: str, impact: str, value: str, detail: str) -> dict:
    return {"name": name, "impact": impact, "value": value, "detail": detail}


def build_explanation(
    quest: dict,
    domain: dict,
    rank_position: int,
    total_domains: int,
    user_difficulty: str,
    xp_remaining: int,
    completed_today: bool,
) -> dict:
    """
    Pure logic: turn the signals behind a recommendation into traceable factors,
    a confidence score and a plain-language summary. No database access here.
    """
    name = domain["domain_name"]
    factors = []

    # 1. Domain priority
    factors.append(_factor(
        "Domain priority",
        "supports" if rank_position <= 2 else "neutral",
        f"#{rank_position} of {total_domains}",
        f"Ranked #{rank_position} of {total_domains} domains by combined priority and bottleneck score ({domain['combined_score']}).",
    ))

    # 2. Assessment score
    score = domain["assessment_score"]
    if score is None:
        factors.append(_factor("Assessment score", "neutral", "not assessed",
                               f"You haven't been assessed in {name} yet, so there's less data behind this pick."))
    elif score < LOW_SCORE_THRESHOLD:
        factors.append(_factor("Assessment score", "supports", str(score),
                               f"Your {name} score ({score}) is below {LOW_SCORE_THRESHOLD}, so this domain gets extra priority."))
    else:
        factors.append(_factor("Assessment score", "neutral", str(score),
                               f"Your {name} score ({score}) is at or above {LOW_SCORE_THRESHOLD}, so it's less urgent."))

    # 3. Active goal
    if domain["has_active_goal"]:
        factors.append(_factor("Active goal", "supports", "yes", f"You have an active goal in {name}."))
    else:
        factors.append(_factor("Active goal", "neutral", "no", f"You have no active goal in {name}."))

    # 4. Bottleneck
    if domain["bottleneck_score"] > 0:
        factors.append(_factor(
            "Bottleneck", "supports",
            f"{domain['bottleneck_severity']} ({domain['bottleneck_score']})",
            f"Flagged as a {domain['bottleneck_severity']} bottleneck: " + "; ".join(domain["bottleneck_reasons"]) + ".",
        ))
    else:
        factors.append(_factor("Bottleneck", "neutral", "none", f"No bottleneck flagged in {name}."))

    # 5. Difficulty fit
    if quest["difficulty"] == user_difficulty:
        factors.append(_factor("Difficulty fit", "supports", f"{quest['difficulty']} vs {user_difficulty}",
                               f"This quest is {quest['difficulty']} and your current level in {name} is {user_difficulty}."))
    else:
        factors.append(_factor("Difficulty fit", "against", f"{quest['difficulty']} vs {user_difficulty}",
                               f"This quest is {quest['difficulty']} but your current level in {name} is {user_difficulty}."))

    # 6. Daily XP
    if xp_remaining == 0:
        factors.append(_factor("Daily XP", "against", "0 XP left", "You've reached today's XP cap."))
    elif quest["xp_reward"] > xp_remaining:
        factors.append(_factor("Daily XP", "against", f"{xp_remaining} XP left",
                               f"Only {xp_remaining} XP is left under today's cap, so you'd earn less than the full {quest['xp_reward']} XP."))
    else:
        factors.append(_factor("Daily XP", "neutral", f"{xp_remaining} XP left", f"{xp_remaining} XP left to earn today."))

    # 7. Cooldown
    if completed_today:
        factors.append(_factor("Cooldown", "against", "done today", "You already completed this quest in the last 24 hours."))
    else:
        factors.append(_factor("Cooldown", "neutral", "available", "You haven't done this quest in the last 24 hours."))

    supports = sum(1 for f in factors if f["impact"] == "supports")
    against = sum(1 for f in factors if f["impact"] == "against")

    difficulty_mismatch = quest["difficulty"] != user_difficulty

    confidence = 0.4 + 0.1 * supports - 0.15 * against + (0.1 if score is not None else 0)
    if difficulty_mismatch:
        confidence = min(confidence, 0.6)  # a level mismatch can never be a high-confidence pick
    confidence = round(max(0.05, min(0.95, confidence)), 2)
    label = confidence_label(confidence)

    available = (not completed_today) and xp_remaining > 0
    recommended_now = available and not difficulty_mismatch
    summary = f"{quest['title']} is a {label}-confidence pick for {name}: {supports} factor(s) support it and {against} count against it."
    if not available:
        summary += " It isn't available right now."
    elif difficulty_mismatch:
        summary += f" It doesn't match your current {user_difficulty} level, so it won't be suggested yet."

    return {
        "domain_name": name,
        "confidence": confidence,
        "confidence_label": label,
        "summary": summary,
        "factors": factors,
        "recommended_now": recommended_now,
    }


def explain_quest(db: Session, user_id: int, quest_id: int) -> dict:
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    bottlenecks = {b["domain_id"]: b for b in detect_bottlenecks(db, user_id)}
    ranked = rank_domains(get_domain_priorities(db, user_id), bottlenecks)

    position = next((i + 1 for i, d in enumerate(ranked) if d["domain_id"] == quest.domain_id), None)
    if position is None:
        raise HTTPException(status_code=404, detail="Quest's domain not found")

    state = get_or_create_difficulty_state(db, user_id, quest.domain_id)
    xp_remaining = max(0, DAILY_XP_CAP - xp_earned_today(db, user_id))

    result = build_explanation(
        {"title": quest.title, "difficulty": quest.difficulty, "xp_reward": quest.xp_reward},
        ranked[position - 1],
        position,
        len(ranked),
        state.current_difficulty,
        xp_remaining,
        already_completed_today(db, user_id, quest.id),
    )
    result["quest"] = quest
    return result