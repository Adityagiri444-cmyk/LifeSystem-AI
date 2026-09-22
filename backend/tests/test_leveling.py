from app.services.leveling import xp_required_for_level, compute_level


def test_xp_required_increases_each_level():
    assert xp_required_for_level(1) == 100
    assert xp_required_for_level(2) == 150
    assert xp_required_for_level(3) == 200


def test_compute_level_at_zero_xp():
    result = compute_level(0)
    assert result["level"] == 1
    assert result["xp_into_level"] == 0
    assert result["xp_to_next_level"] == 100


def test_compute_level_partial_progress():
    result = compute_level(60)
    assert result["level"] == 1
    assert result["xp_into_level"] == 60
    assert result["xp_to_next_level"] == 40


def test_compute_level_exact_threshold():
    # Exactly enough to hit level 2
    result = compute_level(100)
    assert result["level"] == 2
    assert result["xp_into_level"] == 0


def test_compute_level_multiple_level_ups():
    # 100 (lvl1->2) + 150 (lvl2->3) = 250 total to reach level 3
    result = compute_level(250)
    assert result["level"] == 3
    assert result["xp_into_level"] == 0


def test_compute_level_large_xp():
    result = compute_level(1000)
    assert result["level"] >= 3
    assert result["xp_into_level"] >= 0
    assert result["xp_to_next_level"] > 0