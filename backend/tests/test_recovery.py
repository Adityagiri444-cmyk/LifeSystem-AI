from datetime import datetime, timedelta, timezone

from app.services.recovery import (
    RECOVERY_MAX_MINUTES,
    VALID_STATES,
    build_recovery_reason,
    is_recovery_active,
    is_recovery_friendly,
    recovery_message,
)

NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)


def test_recent_strain_checkin_activates_recovery():
    assert is_recovery_active("tired", NOW - timedelta(hours=2), NOW) is True


def test_okay_checkin_ends_recovery():
    assert is_recovery_active("okay", NOW - timedelta(minutes=5), NOW) is False


def test_old_strain_checkin_expires_after_24h():
    assert is_recovery_active("overwhelmed", NOW - timedelta(hours=25), NOW) is False
    assert is_recovery_active("overwhelmed", NOW - timedelta(hours=23), NOW) is True


def test_no_checkin_means_no_recovery():
    assert is_recovery_active(None, None, NOW) is False


def test_naive_datetime_is_treated_as_utc():
    naive = datetime(2026, 10, 15, 10, 0)
    assert is_recovery_active("stressed", naive, NOW) is True


def test_recovery_friendly_requires_easy_and_short():
    assert is_recovery_friendly("easy", 10) is True
    assert is_recovery_friendly("easy", RECOVERY_MAX_MINUTES) is True
    assert is_recovery_friendly("easy", RECOVERY_MAX_MINUTES + 1) is False
    assert is_recovery_friendly("medium", 5) is False
    assert is_recovery_friendly("easy", None) is True


def test_every_state_has_a_message():
    for state in VALID_STATES:
        assert recovery_message(state)


def test_messages_stay_non_clinical():
    banned = ["diagnos", "depress", "anxiety", "disorder", "therapy", "medicat", "burnout"]
    for state in VALID_STATES:
        text = recovery_message(state).lower()
        assert not any(word in text for word in banned)


def test_recovery_reason_mentions_state_and_duration():
    reason = build_recovery_reason("low_energy", "Read 10 pages", 10, 50)
    assert "low energy" in reason
    assert "10 minutes" in reason
    assert "50 XP" in reason