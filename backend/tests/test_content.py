from app.services.content import (
    CATALOG,
    CATEGORIES,
    energy_cap,
    preferred_categories,
    recommend_content,
    score_item,
)

BANNED = ["treat", "cure", "heal", "therap", "anxiety", "depress", "diagnos", "disorder",
          "medic", "symptom", "relieve", "reduce"]


def ids(results):
    return [r["item"]["id"] for r in results]


def test_catalog_is_well_formed():
    seen = set()
    for item in CATALOG:
        assert item["id"] not in seen
        seen.add(item["id"])
        assert item["category"] in CATEGORIES
        assert item["duration_minutes"] > 0
        assert 1 <= item["energy_required"] <= 5
        assert item["suited_states"]
    assert {i["category"] for i in CATALOG} == set(CATEGORIES)


def test_catalog_text_is_non_clinical():
    for item in CATALOG:
        text = (item["title"] + " " + item["description"]).lower()
        assert not any(word in text for word in BANNED), item["id"]


def test_energy_cap_prefers_explicit_energy():
    assert energy_cap("tired", 4) == 4
    assert energy_cap("tired", None) == 2
    assert energy_cap(None, None) == 5


def test_preferred_categories_ignores_junk():
    assert preferred_categories({"content_categories": ["music", "bogus"]}) == ["music"]
    assert preferred_categories({"content_categories": "music"}) == []
    assert preferred_categories(None) == []


def test_time_limit_is_respected():
    results = recommend_content(CATALOG, "okay", None, 5, [], False, limit=10)
    assert results and all(r["item"]["duration_minutes"] <= 5 for r in results)


def test_low_energy_never_gets_demanding_items():
    results = recommend_content(CATALOG, "overwhelmed", None, None, [], True, limit=10)
    assert all(r["item"]["energy_required"] <= 2 for r in results)
    assert "move-walk-30" not in ids(results)


def test_preference_boosts_category():
    results = recommend_content(CATALOG, "okay", None, None, ["music"], False, limit=1)
    assert results[0]["item"]["category"] == "music"


def test_results_have_variety():
    results = recommend_content(CATALOG, "tired", None, None, [], True, limit=3)
    cats = [r["item"]["category"] for r in results]
    assert len(set(cats)) == len(cats)


def test_category_filter():
    results = recommend_content(CATALOG, "okay", None, None, [], False, category="journaling", limit=10)
    assert results and all(r["item"]["category"] == "journaling" for r in results)


def test_impossible_filters_return_empty():
    assert recommend_content(CATALOG, "overwhelmed", 1, 1, [], True) == []


def test_reasons_mention_state_and_preference():
    item = next(i for i in CATALOG if i["id"] == "music-calm-10")
    score, reasons = score_item(item, "tired", ["music"], True)
    assert score >= 5
    assert any("tired" in r for r in reasons)
    assert any("music" in r for r in reasons)