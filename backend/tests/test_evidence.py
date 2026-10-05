import pytest
from fastapi import HTTPException
from app.services.evidence import validate_evidence


def test_checkbox_requires_confirmation():
    with pytest.raises(HTTPException):
        validate_evidence("checkbox", {})


def test_checkbox_confirmed_gives_full_xp():
    assert validate_evidence("checkbox", {"confirmed": True}) == 100


def test_text_too_short_rejected():
    with pytest.raises(HTTPException):
        validate_evidence("text", {"text": "short"})


def test_text_moderate_length_partial_xp():
    assert validate_evidence("text", {"text": "a" * 15}) == 70


def test_text_long_full_xp():
    assert validate_evidence("text", {"text": "a" * 50}) == 100


def test_duration_meets_target_full_xp():
    assert validate_evidence("duration", {"minutes": 30}, expected_minutes=30) == 100


def test_duration_half_target_partial_xp():
    assert validate_evidence("duration", {"minutes": 16}, expected_minutes=30) == 70


def test_duration_far_below_target_low_xp():
    assert validate_evidence("duration", {"minutes": 5}, expected_minutes=30) == 40


def test_duration_missing_minutes_rejected():
    with pytest.raises(HTTPException):
        validate_evidence("duration", {})


def test_none_type_always_full_xp():
    assert validate_evidence("none", {}) == 100