def compute_rank(level: int) -> str:
    if level < 3:
        return "Novice"
    elif level < 6:
        return "Apprentice"
    elif level < 10:
        return "Adept"
    else:
        return "Master"


def compute_balance_score(domain_scores: dict | None) -> float | None:
    if not domain_scores:
        return None
    values = [v for v in domain_scores.values() if v is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 2)