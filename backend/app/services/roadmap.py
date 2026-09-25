# Simple template-based milestone generation, keyed by domain.
# This is intentionally rule-based (not AI) per the roadmap's Week 14/15 principle:
# deterministic logic first, AI wording/personalization comes later (Week 24).

DOMAIN_TEMPLATES = {
    1: [  # Physical
        ("Build a consistent baseline", "consistency"),
        ("Increase duration/intensity gradually", "progressive-overload"),
        ("Reach your target milestone", "goal-completion"),
    ],
    2: [  # Educational
        ("Learn the fundamentals", "foundations"),
        ("Practice with real exercises", "applied-practice"),
        ("Test your understanding", "assessment"),
    ],
    3: [  # Mental Wellness
        ("Establish a small daily habit", "habit-formation"),
        ("Build consistency over 2+ weeks", "consistency"),
        ("Reflect on what's working", "reflection"),
    ],
    4: [  # Emotional
        ("Identify a regular outlet", "self-awareness"),
        ("Practice it consistently", "consistency"),
        ("Check in on how it's helping", "reflection"),
    ],
    5: [  # Career
        ("Clarify the specific target", "clarity"),
        ("Build the needed skill or asset", "skill-building"),
        ("Take the concrete next step", "action"),
    ],
}

GENERIC_TEMPLATE = [
    ("Get started", "initiation"),
    ("Build momentum", "consistency"),
    ("Reach the goal", "goal-completion"),
]


def generate_milestones_for_goal(goal) -> list[dict]:
    template = DOMAIN_TEMPLATES.get(goal.domain_id, GENERIC_TEMPLATE)
    milestones = []
    for i, (title, skill_tag) in enumerate(template):
        milestones.append({
            "title": f"{title}: {goal.title}",
            "order_index": i,
            "skill_tag": skill_tag,
            "status": "active" if i == 0 else "locked",
        })
    return milestones