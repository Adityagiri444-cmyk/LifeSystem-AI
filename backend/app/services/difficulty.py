from sqlalchemy.orm import Session
from app.models import DifficultyState

DIFFICULTY_ORDER = ["easy", "medium", "hard"]

STREAK_UP_THRESHOLD = 3     # 3 good completions in a row -> move up
STREAK_DOWN_THRESHOLD = -2  # 2 weak/failed signals in a row -> move down


def get_or_create_difficulty_state(db: Session, user_id: int, domain_id: int) -> DifficultyState:
    state = (
        db.query(DifficultyState)
        .filter(DifficultyState.user_id == user_id, DifficultyState.domain_id == domain_id)
        .first()
    )
    if not state:
        state = DifficultyState(user_id=user_id, domain_id=domain_id, current_difficulty="easy", streak=0)
        db.add(state)
        db.flush()
    return state


def update_difficulty_after_completion(db: Session, user_id: int, domain_id: int, xp_multiplier: int) -> DifficultyState:
    """
    Call this after a quest completion in a given domain.
    xp_multiplier >= 90 counts as a strong success (streak +1).
    xp_multiplier < 60 counts as weak effort (streak -1).
    Anything in between is neutral (streak unchanged).
    """
    state = get_or_create_difficulty_state(db, user_id, domain_id)

    if xp_multiplier >= 90:
        state.streak += 1
    elif xp_multiplier < 60:
        state.streak -= 1
    # else: neutral, streak unchanged

    current_index = DIFFICULTY_ORDER.index(state.current_difficulty)

    if state.streak >= STREAK_UP_THRESHOLD and current_index < len(DIFFICULTY_ORDER) - 1:
        state.current_difficulty = DIFFICULTY_ORDER[current_index + 1]
        state.streak = 0
    elif state.streak <= STREAK_DOWN_THRESHOLD and current_index > 0:
        state.current_difficulty = DIFFICULTY_ORDER[current_index - 1]
        state.streak = 0

    db.flush()
    return state