from sqlalchemy.orm import Session
from app.models import Quest, Domain, Goal, AssessmentResult
from app.services.leveling import already_completed_today

DOMAIN_KEY_MAP = {
    1: "physical",
    2: "educational",
    3: "mental_wellness",
    4: "emotional",
    5: "career",
}


def get_domain_priorities(db: Session, user_id: int) -> list[dict]:
    """
    Rank all domains by how much attention they need.
    Lower assessment score -> higher priority.
    Having an active goal in that domain adds a priority boost.
    """
    assessment = db.query(AssessmentResult).filter(AssessmentResult.user_id == user_id).first()
    domain_scores = assessment.domain_scores if assessment else {}

    active_goal_domains = {
        g.domain_id for g in db.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    }

    domains = db.query(Domain).all()
    priorities = []

    for domain in domains:
        score_key = DOMAIN_KEY_MAP.get(domain.id)
        score = domain_scores.get(score_key) if score_key else None

        # No assessment data yet for this domain -> treat as neutral (score 3)
        base_priority = (5 - score) if score is not None else 2.0
        goal_boost = 1.5 if domain.id in active_goal_domains else 0
        priority_score = round(base_priority + goal_boost, 2)

        priorities.append({
            "domain_id": domain.id,
            "domain_name": domain.name,
            "score": score,
            "has_active_goal": domain.id in active_goal_domains,
            "priority_score": priority_score,
        })

    priorities.sort(key=lambda d: d["priority_score"], reverse=True)
    return priorities


def generate_recommendations(db: Session, user_id: int, limit: int = 5) -> list[dict]:
    priorities = get_domain_priorities(db, user_id)
    recommendations = []

    for domain_info in priorities:
        if len(recommendations) >= limit:
            break

        candidate_quests = (
            db.query(Quest)
            .filter(Quest.domain_id == domain_info["domain_id"])
            .order_by(Quest.difficulty)
            .all()
        )

        for quest in candidate_quests:
            if not already_completed_today(db, user_id, quest.id):
                reason_parts = []
                if domain_info["score"] is not None:
                    reason_parts.append(f"your {domain_info['domain_name']} score ({domain_info['score']}) is lower than other domains")
                else:
                    reason_parts.append(f"you haven't been assessed in {domain_info['domain_name']} yet")
                if domain_info["has_active_goal"]:
                    reason_parts.append(f"you have an active goal in {domain_info['domain_name']}")

                reason = "Suggested because " + " and ".join(reason_parts) + "."

                recommendations.append({
                    "quest": quest,
                    "reason": reason,
                    "domain_priority_score": domain_info["priority_score"],
                })
                break  # one quest per domain, move to next domain

    return recommendations