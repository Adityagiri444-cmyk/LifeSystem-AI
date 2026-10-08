from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models import (
    Domain, Goal, AssessmentResult, QuestCompletion, Quest, Evidence, DifficultyState,
)
from app.services.recommender import DOMAIN_KEY_MAP

STALL_DAYS = 7
LOW_SCORE_THRESHOLD = 3.0
WEAK_EVIDENCE_THRESHOLD = 70


def score_bottleneck(domain_name: str, signals: dict) -> tuple[float, list[str]]:
    """
    Pure scoring logic: takes pre-gathered signals for one domain and returns
    (bottleneck_score, list of human-readable reasons). No database access here.
    """
    score = 0.0
    reasons = []

    assessment_score = signals.get("assessment_score")
    if assessment_score is not None and assessment_score < LOW_SCORE_THRESHOLD:
        score += 2
        reasons.append(
            f"your {domain_name} assessment score ({assessment_score}) is below {LOW_SCORE_THRESHOLD}"
        )

    completions = signals.get("completions_in_window", 0)
    has_goal = signals.get("has_active_goal", False)
    if completions == 0:
        if has_goal:
            score += 3
            reasons.append(
                f"you have an active goal in {domain_name} but no quests completed in the last {STALL_DAYS} days"
            )
        else:
            score += 1
            reasons.append(f"no {domain_name} activity in the last {STALL_DAYS} days")

    avg_multiplier = signals.get("avg_xp_multiplier")
    if avg_multiplier is not None and avg_multiplier < WEAK_EVIDENCE_THRESHOLD:
        score += 1.5
        reasons.append(
            f"recent {domain_name} completions had low evidence quality (average {round(avg_multiplier)}%)"
        )

    streak = signals.get("difficulty_streak")
    if streak is not None and streak < 0:
        score += 1
        reasons.append(f"your {domain_name} performance streak is negative ({streak})")

    return score, reasons


def classify_severity(score: float) -> str:
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def detect_bottlenecks(db: Session, user_id: int) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=STALL_DAYS)

    assessment = db.query(AssessmentResult).filter(AssessmentResult.user_id == user_id).first()
    domain_scores = assessment.domain_scores if assessment and assessment.domain_scores else {}

    active_goal_domains = {
        g.domain_id
        for g in db.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    }

    results = []
    for domain in db.query(Domain).all():
        completions = (
            db.query(QuestCompletion)
            .join(Quest, Quest.id == QuestCompletion.quest_id)
            .filter(
                QuestCompletion.user_id == user_id,
                Quest.domain_id == domain.id,
                QuestCompletion.completed_at >= since,
            )
            .all()
        )

        avg_multiplier = None
        if completions:
            rows = (
                db.query(Evidence.xp_multiplier)
                .filter(Evidence.quest_completion_id.in_([c.id for c in completions]))
                .all()
            )
            values = [r[0] for r in rows if r[0] is not None]
            if values:
                avg_multiplier = sum(values) / len(values)

        diff_state = (
            db.query(DifficultyState)
            .filter(DifficultyState.user_id == user_id, DifficultyState.domain_id == domain.id)
            .first()
        )

        score_key = DOMAIN_KEY_MAP.get(domain.id)
        signals = {
            "assessment_score": domain_scores.get(score_key) if score_key else None,
            "has_active_goal": domain.id in active_goal_domains,
            "completions_in_window": len(completions),
            "avg_xp_multiplier": avg_multiplier,
            "difficulty_streak": diff_state.streak if diff_state else None,
        }

        bottleneck_score, reasons = score_bottleneck(domain.name, signals)
        if bottleneck_score > 0:
            results.append({
                "domain_id": domain.id,
                "domain_name": domain.name,
                "severity": classify_severity(bottleneck_score),
                "bottleneck_score": round(bottleneck_score, 2),
                "reasons": reasons,
            })

    results.sort(key=lambda r: r["bottleneck_score"], reverse=True)
    return results