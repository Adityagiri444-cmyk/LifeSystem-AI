from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models import CheckIn

# States a user can report. "okay" means "I'm fine now" and ends recovery mode.
STRAIN_STATES = ("tired", "stressed", "overwhelmed", "low_energy")
VALID_STATES = STRAIN_STATES + ("okay",)

RECOVERY_WINDOW_HOURS = 24      # a strain check-in keeps recovery mode on for this long
RECOVERY_XP_CAP = 50            # gentler daily XP target while recovering (suggestions only)
RECOVERY_MAX_MINUTES = 20       # only short quests are suggested in recovery mode

SAFETY_NOTE = (
    "LifeSystem is a productivity tool, not a medical or mental-health service. "
    "If you're struggling, please talk to someone you trust or a qualified professional."
)

_MESSAGES = {
    "tired": "Rest counts as progress. Today we're keeping things short and easy.",
    "stressed": "Let's lower the pressure. Pick one small thing, or nothing at all.",
    "overwhelmed": "One small step is enough today. Everything else can wait.",
    "low_energy": "Low-energy days happen. A tiny win is plenty.",
    "okay": "Glad you're feeling okay. Normal mode is back.",
}


def _as_utc(dt: datetime) -> datetime:
    """Treat naive datetimes as UTC so comparisons never crash."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def is_recovery_active(latest_state: Optional[str], latest_at: Optional[datetime], now: datetime) -> bool:
    """Pure logic: recovery is on only if the latest check-in is a strain state and recent."""
    if latest_state not in STRAIN_STATES or latest_at is None:
        return False
    return _as_utc(now) - _as_utc(latest_at) < timedelta(hours=RECOVERY_WINDOW_HOURS)


def recovery_message(state: Optional[str]) -> str:
    """Pure logic: a supportive, non-clinical message for a state."""
    return _MESSAGES.get(state, _MESSAGES["okay"])


def is_recovery_friendly(difficulty: Optional[str], duration_minutes: Optional[int]) -> bool:
    """Pure logic: recovery mode only suggests easy quests that are short (unknown duration is allowed)."""
    if difficulty != "easy":
        return False
    return duration_minutes is None or duration_minutes <= RECOVERY_MAX_MINUTES


def build_recovery_reason(state: str, quest_title: str, duration_minutes: Optional[int], xp_remaining: int) -> str:
    """Pure logic: explain why this gentle quest was picked."""
    time_part = f" It takes about {duration_minutes} minutes." if duration_minutes else ""
    return (
        f"Recovery mode is on ({state.replace('_', ' ')}), so you're only seeing short, easy quests. "
        f"{quest_title} is a gentle option.{time_part} "
        f"You have {xp_remaining} XP left under today's recovery target."
    )


def record_check_in(db: Session, user_id: int, state: str, energy: Optional[int]) -> CheckIn:
    check_in = CheckIn(user_id=user_id, state=state, energy=energy)
    db.add(check_in)
    db.commit()
    db.refresh(check_in)
    return check_in


def get_latest_check_in(db: Session, user_id: int) -> Optional[CheckIn]:
    return (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id)
        .order_by(CheckIn.created_at.desc(), CheckIn.id.desc())
        .first()
    )


def get_recovery_status(db: Session, user_id: int) -> dict:
    latest = get_latest_check_in(db, user_id)
    now = datetime.now(timezone.utc)
    state = latest.state if latest else None
    active = is_recovery_active(state, latest.created_at if latest else None, now)
    return {
        "recovery_active": active,
        "state": state,
        "since": latest.created_at if latest else None,
        "expires_at": _as_utc(latest.created_at) + timedelta(hours=RECOVERY_WINDOW_HOURS) if active else None,
        "message": recovery_message(state) if latest else "No check-in yet. Tell us how you're feeling any time.",
        "xp_target_today": RECOVERY_XP_CAP if active else None,
        "max_quest_minutes": RECOVERY_MAX_MINUTES if active else None,
        "safety_note": SAFETY_NOTE,
    }