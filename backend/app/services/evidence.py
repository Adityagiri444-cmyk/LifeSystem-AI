from fastapi import HTTPException


def validate_checkbox(content: dict) -> int:
    """Simple boolean confirmation. Always full XP if confirmed."""
    if not content.get("confirmed"):
        raise HTTPException(status_code=400, detail="Checkbox evidence requires 'confirmed': true")
    return 100


def validate_text(content: dict) -> int:
    """Open-text evidence. Reject empty/trivial responses; scale XP by effort (length), capped."""
    text = content.get("text", "").strip()
    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Text evidence must be at least 10 characters")
    if len(text) < 30:
        return 70
    return 100


def validate_duration(content: dict, expected_minutes: int | None) -> int:
    """Duration-based evidence (study session, exercise log). Scale XP by how close to target duration."""
    minutes = content.get("minutes")
    if minutes is None or not isinstance(minutes, (int, float)) or minutes <= 0:
        raise HTTPException(status_code=400, detail="Duration evidence requires a positive 'minutes' value")

    if not expected_minutes:
        return 100  # no target set on the quest, trust the submission fully

    ratio = minutes / expected_minutes
    if ratio >= 1:
        return 100
    elif ratio >= 0.5:
        return 70
    else:
        return 40


def validate_evidence(evidence_type: str, content: dict, expected_minutes: int | None = None) -> int:
    """
    Validates evidence content against the quest's required evidence_type.
    Returns an XP multiplier (percentage, 0-100).
    Raises HTTPException if evidence is invalid or missing when required.
    """
    if evidence_type == "none":
        return 100
    elif evidence_type == "checkbox":
        return validate_checkbox(content)
    elif evidence_type == "text":
        return validate_text(content)
    elif evidence_type == "duration":
        return validate_duration(content, expected_minutes)
    else:
        return 100  # unknown type, don't block completion