import json
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.models import UserProfile
from app.services.recovery import get_latest_check_in, get_recovery_status

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "content_catalog.json"

with open(CATALOG_PATH, "r") as f:
    CATALOG = json.load(f)

CATEGORIES = ("movement", "breathing", "music", "video", "entertainment", "journaling", "social")

# Energy we assume (1 = drained, 5 = great) when the user gave no energy rating.
DEFAULT_ENERGY_BY_STATE = {"tired": 2, "low_energy": 2, "overwhelmed": 2, "stressed": 3, "okay": 5}

SAFETY_NOTE = (
    "These are light suggestions, not medical or mental-health advice. "
    "If you're struggling, please talk to someone you trust or a qualified professional."
)


def energy_cap(state: Optional[str], energy: Optional[int]) -> int:
    """Pure logic: the highest energy_required we will suggest."""
    if energy is not None:
        return max(1, min(5, energy))
    return DEFAULT_ENERGY_BY_STATE.get(state, 5)


def preferred_categories(preferences: Optional[dict]) -> list:
    """Pure logic: read content_categories from profile preferences, ignoring anything unknown."""
    if not isinstance(preferences, dict):
        return []
    raw = preferences.get("content_categories")
    if not isinstance(raw, list):
        return []
    return [c for c in raw if c in CATEGORIES]


def score_item(item: dict, state: Optional[str], preferred: list, recovery: bool) -> tuple:
    """Pure logic: (score, reasons). Higher is better."""
    score, reasons = 0.0, []
    effective_state = state or "okay"

    if effective_state in item["suited_states"]:
        score += 3
        if state:
            reasons.append(f"suits how you're feeling ({state.replace('_', ' ')})")
    if item["category"] in preferred:
        score += 2
        reasons.append(f"matches your preference for {item['category']}")
    if recovery and item["duration_minutes"] <= 10:
        score += 1
        reasons.append("short enough to start right now")
    if item["energy_required"] == 1:
        score += 0.5
    return score, reasons


def recommend_content(
    catalog: list,
    state: Optional[str],
    energy: Optional[int],
    max_minutes: Optional[int],
    preferred: list,
    recovery: bool,
    category: Optional[str] = None,
    limit: int = 3,
) -> list:
    """
    Pure logic: filter by context, rank, then pick the best item per category first
    so the list has variety. Returns [{"item": ..., "score": ..., "reasons": [...]}].
    """
    cap = energy_cap(state, energy)
    ranked = []
    for item in catalog:
        if category and item["category"] != category:
            continue
        if item["energy_required"] > cap:
            continue
        if max_minutes is not None and item["duration_minutes"] > max_minutes:
            continue
        score, reasons = score_item(item, state, preferred, recovery)
        if score <= 0:
            continue  # nothing makes this item a fit right now
        ranked.append({"item": item, "score": score, "reasons": reasons})

    ranked.sort(key=lambda r: (-r["score"], r["item"]["duration_minutes"], r["item"]["id"]))

    picked, seen_categories = [], set()
    for r in ranked:  # pass 1: one per category
        if r["item"]["category"] not in seen_categories:
            picked.append(r)
            seen_categories.add(r["item"]["category"])
    for r in ranked:  # pass 2: fill remaining slots
        if r not in picked:
            picked.append(r)

    return picked[:limit]


def get_content_recommendations(
    db: Session,
    user_id: int,
    max_minutes: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 3,
) -> dict:
    recovery = get_recovery_status(db, user_id)
    active = recovery["recovery_active"]
    state = recovery["state"] if active else None

    latest_energy = None
    if active:
        latest = get_latest_check_in(db, user_id)
        latest_energy = latest.energy if latest else None

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    preferred = preferred_categories(profile.preferences if profile else None)

    results = recommend_content(CATALOG, state, latest_energy, max_minutes, preferred, active, category, limit)
    return {
        "mode": "recovery" if active else "general",
        "state": state,
        "recommendations": [
            {**r["item"], "reasons": r["reasons"] or ["a good general option"]} for r in results
        ],
        "message": None if results else "Nothing in the catalog fits those filters. Try a longer time limit.",
        "safety_note": SAFETY_NOTE,
    }