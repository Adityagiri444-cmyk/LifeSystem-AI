from app.services.bottleneck import score_bottleneck, classify_severity


def test_no_signals_means_no_bottleneck():
    score, reasons = score_bottleneck("Physical", {
        "assessment_score": 4.0,
        "has_active_goal": False,
        "completions_in_window": 3,
        "avg_xp_multiplier": 100,
        "difficulty_streak": 1,
    })
    assert score == 0
    assert reasons == []


def test_low_assessment_score_adds_points():
    score, reasons = score_bottleneck("Educational", {
        "assessment_score": 2.0,
        "completions_in_window": 2,
    })
    assert score == 2
    assert len(reasons) == 1


def test_assessment_score_exactly_at_threshold_is_not_low():
    score, _ = score_bottleneck("Career", {
        "assessment_score": 3.0,
        "completions_in_window": 1,
    })
    assert score == 0


def test_stalled_goal_is_strongest_signal():
    score, reasons = score_bottleneck("Physical", {
        "has_active_goal": True,
        "completions_in_window": 0,
    })
    assert score == 3
    assert "active goal" in reasons[0]


def test_inactivity_without_goal_is_minor():
    score, _ = score_bottleneck("Emotional", {
        "has_active_goal": False,
        "completions_in_window": 0,
    })
    assert score == 1


def test_weak_evidence_adds_points():
    score, _ = score_bottleneck("Mental Wellness", {
        "completions_in_window": 3,
        "avg_xp_multiplier": 50,
    })
    assert score == 1.5


def test_negative_streak_adds_points():
    score, _ = score_bottleneck("Physical", {
        "completions_in_window": 2,
        "difficulty_streak": -1,
    })
    assert score == 1


def test_signals_stack_up():
    # low score (2) + stalled goal (3) = 5
    score, reasons = score_bottleneck("Educational", {
        "assessment_score": 1.0,
        "has_active_goal": True,
        "completions_in_window": 0,
    })
    assert score == 5
    assert len(reasons) == 2


def test_missing_signals_are_handled_safely():
    score, reasons = score_bottleneck("Career", {})
    # no completions key defaults to 0, no goal -> minor inactivity only
    assert score == 1


def test_severity_thresholds():
    assert classify_severity(0) == "none"
    assert classify_severity(1) == "low"
    assert classify_severity(2) == "medium"
    assert classify_severity(3.9) == "medium"
    assert classify_severity(4) == "high"
    assert classify_severity(7) == "high"