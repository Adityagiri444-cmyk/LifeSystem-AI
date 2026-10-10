from app.services.next_action import rank_domains, build_reason


def make_priorities():
    return [
        {"domain_id": 1, "domain_name": "Physical", "score": 3.67, "has_active_goal": True, "priority_score": 2.83},
        {"domain_id": 2, "domain_name": "Educational", "score": 4.0, "has_active_goal": False, "priority_score": 1.0},
    ]


def make_domain(**overrides):
    base = {
        "domain_name": "Educational",
        "assessment_score": 2.5,
        "has_active_goal": False,
        "bottleneck_severity": None,
        "bottleneck_reasons": [],
    }
    base.update(overrides)
    return base


def test_rank_without_bottlenecks_keeps_priority_order():
    ranked = rank_domains(make_priorities(), {})
    assert [d["domain_id"] for d in ranked] == [1, 2]
    assert ranked[0]["combined_score"] == 2.83


def test_bottleneck_can_reorder_domains():
    bottlenecks = {2: {"severity": "medium", "bottleneck_score": 3, "reasons": ["stalled goal"]}}
    ranked = rank_domains(make_priorities(), bottlenecks)
    assert ranked[0]["domain_id"] == 2
    assert ranked[0]["combined_score"] == 4.0


def test_missing_bottleneck_defaults_to_zero():
    ranked = rank_domains(make_priorities(), {})
    assert ranked[1]["bottleneck_score"] == 0.0
    assert ranked[1]["bottleneck_reasons"] == []


def test_reason_uses_bottleneck_reasons_when_present():
    domain = make_domain(bottleneck_reasons=["you have an active goal in Educational but no quests completed"])
    reason = build_reason(domain, "easy", True, 10, 100)
    assert "no quests completed" in reason
    assert "current easy level" in reason


def test_reason_falls_back_to_assessment_score():
    reason = build_reason(make_domain(), "easy", True, 10, 100)
    assert "assessment score is 2.5" in reason


def test_reason_for_unassessed_domain():
    reason = build_reason(make_domain(assessment_score=None), "easy", True, 10, 100)
    assert "haven't been assessed" in reason


def test_reason_mentions_active_goal():
    reason = build_reason(make_domain(has_active_goal=True), "easy", True, 10, 100)
    assert "active goal" in reason


def test_reason_warns_when_cap_will_truncate_xp():
    reason = build_reason(make_domain(), "easy", True, 20, 5)
    assert "Only 5 XP is left" in reason


def test_reason_explains_closest_match_fallback():
    reason = build_reason(make_domain(), "medium", False, 10, 100)
    assert "closest match" in reason