import json
import re
from pathlib import Path
from typing import Optional

POLICY_PATH = Path(__file__).resolve().parent.parent / "data" / "safety_policy.json"

with open(POLICY_PATH, "r", encoding="utf-8") as f:
    POLICY = json.load(f)


def _compile(key: str) -> list:
    return [re.compile(p) for p in POLICY[key]]


CRISIS = _compile("crisis_patterns")
TREATMENT = _compile("treatment_patterns")
DIAGNOSIS = _compile("diagnosis_patterns")
BANNED_OUTPUT = _compile("banned_output_patterns")
RESOURCES = POLICY["resources"]
MESSAGES = POLICY["messages"]

# Order matters: the most serious category wins.
INPUT_RULES = (
    ("crisis", "escalate", CRISIS),
    ("treatment", "redirect", TREATMENT),
    ("diagnosis", "redirect", DIAGNOSIS),
)

SUPPORT_PROMPT = (
    "You've checked in as struggling a few times recently. It might help to talk to someone "
    "you trust, or a qualified professional. LifeSystem can't replace that."
)
SUPPORT_PROMPT_MIN_CHECKINS = 3


def normalize(text: str) -> str:
    """Pure logic: lowercase, straighten apostrophes, collapse whitespace."""
    text = (text or "").lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip()


def assess_text(text: str) -> dict:
    """
    Pure logic: classify user-written text. Never stores or logs the text.
    level: "none" | "redirect" | "escalate"
    """
    clean = normalize(text)
    for category, level, patterns in INPUT_RULES:
        if any(p.search(clean) for p in patterns):
            return {
                "level": level,
                "category": category,
                "message": MESSAGES["escalate" if category == "crisis" else category],
                "resources": RESOURCES if category == "crisis" else [],
            }
    return {"level": "none", "category": None, "message": MESSAGES["none"], "resources": []}


def find_output_violations(text: str) -> list:
    """Pure logic: which banned patterns (diagnosis / treatment claims) appear in generated text."""
    clean = normalize(text)
    return [p.pattern for p in BANNED_OUTPUT if p.search(clean)]


def safe_output(text: str, fallback: Optional[str] = None) -> dict:
    """
    Pure logic: gate for anything the system shows that was generated (Week 24 LLM).
    Returns the text if clean, otherwise the fallback. The backend stays the authority.
    """
    violations = find_output_violations(text)
    if violations:
        return {"text": fallback or MESSAGES["output_fallback"], "blocked": True, "violations": violations}
    return {"text": text, "blocked": False, "violations": []}


def needs_support_prompt(strain_checkins_last_72h: int) -> bool:
    """Pure logic: repeated strain check-ins trigger a gentle 'talk to someone' prompt."""
    return strain_checkins_last_72h >= SUPPORT_PROMPT_MIN_CHECKINS