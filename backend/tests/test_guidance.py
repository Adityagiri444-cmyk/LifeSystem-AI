import json

import pytest

from app.services import guidance
from app.services.guidance import (
    MAX_MESSAGE_CHARS,
    SYSTEM_PROMPT,
    build_facts,
    build_prompt,
    cache_get,
    cache_put,
    extract_json,
    generate_message,
    template_message,
    validate_llm_output,
)
from app.services.llm import LLMError
from app.services.safety import find_output_violations

FACTS = build_facts("recovery", "overwhelmed", "Read 10 pages", "Three lines about today")
GOOD = json.dumps({"message": "Today can be gentle. Maybe read a few pages if you feel like it.", "tone": "gentle"})


def fake(reply):
    return lambda system, user: reply


def boom(exc):
    def _call(system, user):
        raise exc
    return _call


def test_facts_contain_only_allowed_keys_and_no_identity():
    assert set(FACTS) == {"mode", "feeling", "quest", "activity"}
    prompt = build_prompt(FACTS)
    assert "overwhelmed" in prompt and "Read 10 pages" in prompt
    assert "@" not in prompt and "password" not in prompt.lower()


def test_valid_llm_output_is_used():
    result = generate_message(FACTS, fake(GOOD))
    assert result["source"] == "llm"
    assert result["fallback_reason"] is None
    assert "gentle" in result["message"].lower()


def test_code_fenced_json_is_accepted():
    raw = "```json\n" + GOOD + "\n```"
    assert generate_message(FACTS, fake(raw))["source"] == "llm"
    assert extract_json("Sure! " + GOOD + " Hope that helps")["tone"] == "gentle"


@pytest.mark.parametrize("reply", [
    "not json at all",
    "{}",
    json.dumps({"message": "", "tone": "gentle"}),
    json.dumps({"message": "Hi", "tone": "sarcastic"}),
    json.dumps({"message": "Hi"}),
    json.dumps({"message": "x" * (MAX_MESSAGE_CHARS + 1), "tone": "gentle"}),
    json.dumps({"message": "Line one\nLine two", "tone": "gentle"}),
    json.dumps({"message": "Check https://example.com now", "tone": "gentle"}),
    json.dumps(["list", "not", "object"]),
    json.dumps({"message": 123, "tone": "gentle"}),
])
def test_invalid_output_falls_back_to_template(reply):
    result = generate_message(FACTS, fake(reply))
    assert result["source"] == "template"
    assert result["fallback_reason"] == "invalid_output"
    assert result["message"] == template_message(FACTS)


@pytest.mark.parametrize("message", [
    "You have depression, so try reading.",
    "This will cure your anxiety.",
    "Stop taking your medication and read.",
    "You don't need a therapist.",
])
def test_unsafe_llm_text_is_blocked(message):
    reply = json.dumps({"message": message, "tone": "gentle"})
    result = generate_message(FACTS, fake(reply))
    assert result["source"] == "template"
    assert result["fallback_reason"] == "blocked_by_safety"
    assert not find_output_violations(result["message"])


def test_llm_failures_fall_back_without_raising():
    assert generate_message(FACTS, boom(LLMError("http_429")))["fallback_reason"] == "llm_error:http_429"
    assert generate_message(FACTS, boom(LLMError("request_failed")))["source"] == "template"
    assert generate_message(FACTS, boom(RuntimeError("anything")))["fallback_reason"] == "llm_error:unexpected"


def test_no_llm_configured_uses_template():
    result = generate_message(FACTS, None)
    assert result == {"message": template_message(FACTS), "source": "template", "fallback_reason": "llm_not_configured"}


def test_templates_are_safe_and_mode_aware():
    recovery = template_message(build_facts("recovery", "tired", "Read 10 pages", None))
    growth = template_message(build_facts("growth", None, "Read 10 pages", "A short walk"))
    assert "Resting is fine" in recovery
    assert "next step" in growth and "A short walk" in growth
    for text in (recovery, growth, template_message(build_facts("growth", None, None, None))):
        assert text and not find_output_violations(text)


def test_validate_returns_clean_dict():
    assert validate_llm_output(GOOD)["tone"] == "gentle"
    with pytest.raises(ValueError):
        validate_llm_output("nope")


def test_system_prompt_forbids_clinical_content():
    lowered = SYSTEM_PROMPT.lower()
    assert "never diagnose" in lowered and "only those facts" in lowered


def test_cache_hit_and_expiry():
    guidance._cache.clear()
    key = (1, "k")
    assert cache_get(key, now=0) is None
    cache_put(key, {"message": "m"}, now=100)
    assert cache_get(key, now=200) == {"message": "m"}
    assert cache_get(key, now=100 + guidance.CACHE_TTL_SECONDS + 1) is None