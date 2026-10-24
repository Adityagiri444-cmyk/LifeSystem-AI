import pytest

from app.services.content import CATALOG
from app.services.recovery import recovery_message, SAFETY_NOTE
from app.services.safety import (
    RESOURCES,
    assess_text,
    find_output_violations,
    needs_support_prompt,
    normalize,
    safe_output,
)


@pytest.mark.parametrize("text", [
    "I want to kill myself",
    "i dont want to live anymore",
    "I don’t want to be here anymore",
    "thinking about suicide",
    "I'm feeling suicidal",
    "I want to die",
    "there's no point in living",
    "everyone would be better off without me",
    "I keep wanting to hurt myself",
    "I've been self-harming",
    "I can't go on",
    "I want to end my life",
    "KILL   MYSELF",
])
def test_crisis_language_escalates(text):
    result = assess_text(text)
    assert result["level"] == "escalate"
    assert result["category"] == "crisis"
    assert result["resources"]
    assert "emergency" in result["message"].lower()


@pytest.mark.parametrize("text", [
    "I'm dying to try that new cafe",
    "I need to kill some time",
    "my phone is dead",
    "I want to learn to cook",
    "tired after a long day",
    "feeling a bit stressed about exams",
    "Read 10 pages",
    "I want to go for a walk",
])
def test_everyday_language_is_not_flagged(text):
    assert assess_text(text)["level"] == "none"


@pytest.mark.parametrize("text", [
    "Do I have depression?",
    "am I bipolar",
    "can you diagnose me",
    "what disorder do I have",
])
def test_diagnosis_requests_are_redirected(text):
    result = assess_text(text)
    assert result["level"] == "redirect"
    assert result["category"] == "diagnosis"
    assert "can't diagnose" in result["message"]


@pytest.mark.parametrize("text", [
    "Should I stop taking my medication?",
    "what medication should I take",
    "how can I cure my anxiety",
    "what dosage is safe",
])
def test_treatment_requests_are_redirected(text):
    result = assess_text(text)
    assert result["level"] == "redirect"
    assert result["category"] == "treatment"
    assert "can't give medical" in result["message"]


def test_crisis_beats_other_categories():
    result = assess_text("Do I have depression? I want to kill myself")
    assert result["level"] == "escalate"


def test_empty_and_odd_input_is_safe():
    assert assess_text("")["level"] == "none"
    assert assess_text("   ")["level"] == "none"
    assert assess_text(None)["level"] == "none"


def test_normalize_handles_curly_quotes_and_spacing():
    assert normalize("  I   DON’T  ") == "i don't"


def test_resources_have_required_fields_and_a_directory():
    assert len(RESOURCES) >= 4
    for r in RESOURCES:
        assert r["name"] and r["contact"] and r["region"]
    assert any("findahelpline" in r["contact"] for r in RESOURCES)


@pytest.mark.parametrize("text", [
    "You have depression, so try journaling.",
    "You are clinically depressed.",
    "This breathing exercise will cure your anxiety.",
    "Journaling can treat your symptoms.",
    "Stop taking your medication and walk instead.",
    "You don't need a therapist, just music.",
    "Take 50 mg before bed.",
    "This is clinically proven to help.",
    "I diagnose this as burnout.",
])
def test_output_filter_blocks_clinical_claims(text):
    assert find_output_violations(text)
    result = safe_output(text)
    assert result["blocked"] is True
    assert result["text"] != text


@pytest.mark.parametrize("text", [
    "Try a 5-minute walk. Many people enjoy it.",
    "Write three lines about your day.",
    "Take a short break and have some water.",
    "If you're struggling, please talk to someone you trust.",
    "LifeSystem is not a medical service.",
])
def test_output_filter_allows_safe_text(text):
    assert safe_output(text) == {"text": text, "blocked": False, "violations": []}


def test_output_fallback_can_be_customised():
    assert safe_output("You are depressed.", fallback="Try a short walk.")["text"] == "Try a short walk."


def test_all_catalog_content_passes_the_output_filter():
    for item in CATALOG:
        assert not find_output_violations(item["title"] + ". " + item["description"]), item["id"]


def test_recovery_messages_pass_the_output_filter():
    for state in ("tired", "stressed", "overwhelmed", "low_energy", "okay"):
        assert not find_output_violations(recovery_message(state))
    assert not find_output_violations(SAFETY_NOTE)


def test_support_prompt_threshold():
    assert needs_support_prompt(2) is False
    assert needs_support_prompt(3) is True