from app.services.explain import build_explanation, confidence_label


def make_quest(**overrides):
    base = {"title": "Read 10 pages", "difficulty": "easy", "xp_reward": 10}
    base.update(overrides)
    return base


def make_domain(**overrides):
    base = {
        "domain_name": "Educational",
        "assessment_score": 4.0,
        "has_active_goal": False,
        "priority_score": 1.0,
        "bottleneck_score": 0.0,
        "bottleneck_severity": None,
        "bottleneck_reasons": [],
        "combined_score": 1.0,
    }
    base.update(overrides)
    return base


def explain(quest=None, domain=None, rank_position=3, total_domains=5,
            user_difficulty="easy", xp_remaining=100, completed_today=False):
    return build_explanation(
        quest or make_quest(), domain or make_domain(),
        rank_position, total_domains, user_difficulty, xp_remaining, completed_today,
    )


def by_name(result):
    return {f["name"]: f for f in result["factors"]}


def test_strong_case_is_high_confidence():
    domain = make_domain(
        assessment_score=2.0, has_active_goal=True, bottleneck_score=5.0,
        bottleneck_severity="high", bottleneck_reasons=["stalled goal"],
    )
    result = explain(domain=domain, rank_position=1)
    assert result["confidence"] == 0.95  # 0.4 + 5 * 0.1 + 0.1 = 1.0, clamped
    assert result["confidence_label"] == "high"
    assert result["recommended_now"] is True


def test_weak_case_is_low_confidence_and_not_recommended():
    result = explain(quest=make_quest(difficulty="hard"), completed_today=True)
    assert result["confidence"] == 0.2  # 0.4 - 2 * 0.15 + 0.1
    assert result["confidence_label"] == "low"
    assert result["recommended_now"] is False


def test_unassessed_domain_is_neutral_and_gets_no_data_bonus():
    result = explain(domain=make_domain(assessment_score=None))
    factor = by_name(result)["Assessment score"]
    assert factor["impact"] == "neutral"
    assert "haven't been assessed" in factor["detail"]
    assert result["confidence"] == 0.5  # 0.4 + 0.1 (difficulty fit), no data bonus
    assert result["confidence_label"] == "medium"


def test_low_assessment_score_supports():
    result = explain(domain=make_domain(assessment_score=2.0))
    assert by_name(result)["Assessment score"]["impact"] == "supports"


def test_high_assessment_score_is_neutral():
    result = explain(domain=make_domain(assessment_score=4.0))
    assert by_name(result)["Assessment score"]["impact"] == "neutral"


def test_difficulty_mismatch_counts_against():
    result = explain(quest=make_quest(difficulty="hard"), user_difficulty="easy")
    factor = by_name(result)["Difficulty fit"]
    assert factor["impact"] == "against"
    assert "hard" in factor["detail"] and "easy" in factor["detail"]


def test_xp_cap_reached_blocks_recommendation():
    result = explain(xp_remaining=0)
    assert by_name(result)["Daily XP"]["impact"] == "against"
    assert result["recommended_now"] is False


def test_partial_xp_warns_but_still_recommended():
    result = explain(quest=make_quest(xp_reward=10), xp_remaining=5)
    factor = by_name(result)["Daily XP"]
    assert factor["impact"] == "against"
    assert "5" in factor["detail"]
    assert result["recommended_now"] is True


def test_bottleneck_reasons_appear_in_detail():
    domain = make_domain(
        bottleneck_score=3.0, bottleneck_severity="medium",
        bottleneck_reasons=["stalled goal", "low score"],
    )
    factor = by_name(explain(domain=domain))["Bottleneck"]
    assert factor["impact"] == "supports"
    assert "stalled goal" in factor["detail"]
    assert "medium" in factor["detail"]


def test_confidence_is_clamped_at_the_floor():
    result = explain(
        domain=make_domain(assessment_score=None), rank_position=5,
        quest=make_quest(difficulty="hard"), xp_remaining=0, completed_today=True,
    )
    assert result["confidence"] == 0.05  # 0.4 - 3 * 0.15 = -0.05, clamped
    assert result["confidence_label"] == "low"


def test_confidence_label_thresholds():
    assert confidence_label(0.95) == "high"
    assert confidence_label(0.75) == "high"
    assert confidence_label(0.74) == "medium"
    assert confidence_label(0.5) == "medium"
    assert confidence_label(0.49) == "low"


def test_difficulty_mismatch_caps_confidence_and_blocks_recommendation():
    domain = make_domain(
        assessment_score=2.0, has_active_goal=True, bottleneck_score=2.0,
        bottleneck_severity="medium", bottleneck_reasons=["low score"],
    )
    result = explain(
        quest=make_quest(difficulty="hard"), domain=domain,
        rank_position=1, user_difficulty="easy",
    )
    assert result["confidence"] == 0.6  # would be 0.75 without the cap
    assert result["confidence_label"] == "medium"
    assert result["recommended_now"] is False
    assert "current easy level" in result["summary"]    