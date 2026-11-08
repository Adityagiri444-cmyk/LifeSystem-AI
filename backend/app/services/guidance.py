import json
import re
import time
from typing import Callable, Optional
from sqlalchemy.orm import Session
from app.services.content import get_content_recommendations
from app.services.llm import LLMError, call_llm, llm_configured
from app.services.next_action import get_next_best_action
from app.services.recovery import get_recovery_status
from app.services.safety import find_output_violations

MAX_MESSAGE_CHARS = 280
ALLOWED_TONES = ("gentle", "encouraging", "neutral")
CACHE_TTL_SECONDS = 600

_cache: dict = {}

SYSTEM_PROMPT = (
    "You write one short, warm message for a personal-progress app. "
    "You are given a few facts. Use ONLY those facts. Do not invent activities, numbers or advice. "
    "Never diagnose, never mention medical conditions, medication or treatment, never promise outcomes. "
    "Do not include links. Keep it under 40 words, plain text, no emojis. "
    'Reply with JSON only: {"message": "<text>", "tone": "gentle" | "encouraging" | "neutral"}.'
)


# ---------- pure logic ----------

def build_facts(mode: str, state: Optional[str], quest_title: Optional[str], content_title: Optional[str]) -> dict:
    """Pure logic: the ONLY information that ever reaches the LLM. No names, emails, notes or history."""
    return {
        "mode": mode,                       # "recovery" or "growth"
        "feeling": state.replace("_", " ") if state else None,
        "quest": quest_title,
        "activity": content_title,
    }


def build_prompt(facts: dict) -> str:
    return "Facts:\n" + json.dumps(facts, ensure_ascii=False)


def template_message(facts: dict) -> str:
    """Pure logic: the deterministic fallback. Always safe, always available."""
    quest, activity = facts.get("quest"), facts.get("activity")
    if facts["mode"] == "recovery":
        parts = ["Today can be a light one."]
        if quest:
            parts.append(f"If you feel like it, try: {quest}.")
        elif activity:
            parts.append(f"A small option: {activity}.")
        parts.append("Resting is fine too.")
        return " ".join(parts)
    parts = ["Ready when you are."]
    if quest:
        parts.append(f"Your next step: {quest}.")
    if activity:
        parts.append(f"For a break: {activity}.")
    return " ".join(parts)


def extract_json(raw: str) -> dict:
    """Pure logic: parse a JSON object even if wrapped in a code fence or extra text."""
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no json object")
    data = json.loads(text[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("not an object")
    return data


def validate_llm_output(raw: str) -> dict:
    """
    Pure logic: strict schema + safety gate. Returns {"message", "tone"} or raises ValueError(reason).
    The backend, not the model, decides what is allowed to be shown.
    """
    data = extract_json(raw)
    message, tone = data.get("message"), data.get("tone")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("invalid_output")
    message = message.strip()
    if len(message) > MAX_MESSAGE_CHARS or "\n" in message:
        raise ValueError("invalid_output")
    if tone not in ALLOWED_TONES:
        raise ValueError("invalid_output")
    if re.search(r"https?://|www\.|\.com\b", message.lower()):
        raise ValueError("invalid_output")
    if find_output_violations(message):
        raise ValueError("blocked_by_safety")
    return {"message": message, "tone": tone}


def generate_message(facts: dict, llm_call: Optional[Callable[[str, str], str]]) -> dict:
    """
    Orchestrate: try the LLM, validate, otherwise fall back. Never raises.
    Returns {"message", "source", "fallback_reason"}.
    """
    fallback = template_message(facts)
    if llm_call is None:
        return {"message": fallback, "source": "template", "fallback_reason": "llm_not_configured"}
    try:
        raw = llm_call(SYSTEM_PROMPT, build_prompt(facts))
        result = validate_llm_output(raw)
        return {"message": result["message"], "source": "llm", "fallback_reason": None}
    except LLMError as e:
        return {"message": fallback, "source": "template", "fallback_reason": f"llm_error:{e}"}
    except ValueError as e:
        reason = str(e) if str(e) in ("invalid_output", "blocked_by_safety") else "invalid_output"
        return {"message": fallback, "source": "template", "fallback_reason": reason}
    except Exception:
        return {"message": fallback, "source": "template", "fallback_reason": "llm_error:unexpected"}


def cache_get(key: tuple, now: Optional[float] = None) -> Optional[dict]:
    entry = _cache.get(key)
    if not entry:
        return None
    if (now if now is not None else time.time()) - entry["at"] > CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return entry["value"]


def cache_put(key: tuple, value: dict, now: Optional[float] = None) -> None:
    _cache[key] = {"at": now if now is not None else time.time(), "value": value}


# ---------- DB layer ----------

def get_guidance(db: Session, user_id: int) -> dict:
    recovery = get_recovery_status(db, user_id)
    mode = "recovery" if recovery["recovery_active"] else "growth"

    action = get_next_best_action(db, user_id)
    quest = action["quest"]
    content = get_content_recommendations(db, user_id, limit=1)["recommendations"]
    content_item = content[0] if content else None

    facts = build_facts(
        mode,
        recovery["state"] if recovery["recovery_active"] else None,
        quest.title if quest else None,
        content_item["title"] if content_item else None,
    )

    key = (user_id, json.dumps(facts, sort_keys=True))
    cached = cache_get(key)
    if cached is None:
        cached = generate_message(facts, call_llm if llm_configured() else None)
        cache_put(key, cached)

    return {
        "mode": mode,
        "message": cached["message"],
        "source": cached["source"],
        "fallback_reason": cached["fallback_reason"],
        "quest": quest,
        "content": content_item,
        "support_prompt": recovery["support_prompt"],
        "safety_note": recovery["safety_note"],
    }