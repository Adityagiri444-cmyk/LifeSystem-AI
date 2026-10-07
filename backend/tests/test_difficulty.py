from app.services.difficulty import DIFFICULTY_ORDER, STREAK_UP_THRESHOLD, STREAK_DOWN_THRESHOLD


class FakeDifficultyState:
    """A minimal stand-in for the DifficultyState model, for testing the
    pure progression logic without needing a real database session."""
    def __init__(self, current_difficulty="easy", streak=0):
        self.current_difficulty = current_difficulty
        self.streak = streak


def apply_completion(state: FakeDifficultyState, xp_multiplier: int) -> FakeDifficultyState:
    """Mirrors the core logic inside update_difficulty_after_completion,
    operating on a fake state object instead of a DB-backed one."""
    if xp_multiplier >= 90:
        state.streak += 1
    elif xp_multiplier < 60:
        state.streak -= 1

    current_index = DIFFICULTY_ORDER.index(state.current_difficulty)

    if state.streak >= STREAK_UP_THRESHOLD and current_index < len(DIFFICULTY_ORDER) - 1:
        state.current_difficulty = DIFFICULTY_ORDER[current_index + 1]
        state.streak = 0
    elif state.streak <= STREAK_DOWN_THRESHOLD and current_index > 0:
        state.current_difficulty = DIFFICULTY_ORDER[current_index - 1]
        state.streak = 0

    return state


def test_streak_increments_on_strong_success():
    state = FakeDifficultyState()
    apply_completion(state, 100)
    assert state.streak == 1
    assert state.current_difficulty == "easy"


def test_streak_neutral_on_moderate_xp():
    state = FakeDifficultyState(streak=1)
    apply_completion(state, 75)  # between 60 and 90, neutral
    assert state.streak == 1


def test_streak_decrements_on_weak_effort():
    state = FakeDifficultyState(streak=0)
    apply_completion(state, 40)
    assert state.streak == -1


def test_difficulty_increases_after_three_strong_completions():
    state = FakeDifficultyState()
    apply_completion(state, 100)
    apply_completion(state, 100)
    apply_completion(state, 100)
    assert state.current_difficulty == "medium"
    assert state.streak == 0


def test_difficulty_does_not_exceed_hard():
    state = FakeDifficultyState(current_difficulty="hard", streak=2)
    apply_completion(state, 100)  # would push streak to 3, but already at max
    assert state.current_difficulty == "hard"
    assert state.streak == 3  # streak keeps climbing, just no further difficulty to move to


def test_difficulty_decreases_after_two_weak_completions():
    state = FakeDifficultyState(current_difficulty="medium", streak=0)
    apply_completion(state, 40)
    apply_completion(state, 40)
    assert state.current_difficulty == "easy"
    assert state.streak == 0


def test_difficulty_does_not_go_below_easy():
    state = FakeDifficultyState(current_difficulty="easy", streak=-1)
    apply_completion(state, 40)  # would push streak to -2, but already at minimum
    assert state.current_difficulty == "easy"
    assert state.streak == -2


def test_medium_to_hard_progression():
    state = FakeDifficultyState(current_difficulty="medium", streak=2)
    apply_completion(state, 95)
    assert state.current_difficulty == "hard"
    assert state.streak == 0