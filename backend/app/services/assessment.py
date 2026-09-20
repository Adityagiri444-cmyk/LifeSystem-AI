import json
from pathlib import Path
from fastapi import HTTPException

QUESTIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "assessment_questions.json"

with open(QUESTIONS_PATH, "r") as f:
    QUESTION_BANK = json.load(f)


def score_assessment(answers: dict) -> dict:
    domain_scores = {}

    for domain, questions in QUESTION_BANK.items():
        scored_values = []

        for question in questions:
            qid = question["id"]
            qtype = question["type"]

            if qid not in answers:
                continue  # skip unanswered questions rather than failing the whole submission

            answer = answers[qid]

            if qtype == "scale":
                try:
                    value = float(answer)
                except (TypeError, ValueError):
                    raise HTTPException(status_code=400, detail=f"Invalid scale answer for {qid}")
                if not (question["min"] <= value <= question["max"]):
                    raise HTTPException(status_code=400, detail=f"Answer for {qid} out of range")
                scored_values.append(value)

            elif qtype == "multiple_choice":
                matched = next(
                    (opt["score"] for opt in question["options"] if opt["label"] == answer),
                    None,
                )
                if matched is None:
                    raise HTTPException(status_code=400, detail=f"Invalid option for {qid}")
                scored_values.append(matched)

            # yes_no and open_text are intentionally not scored

        if scored_values:
            domain_scores[domain] = round(sum(scored_values) / len(scored_values), 2)
        else:
            domain_scores[domain] = None  # no scored questions answered for this domain

    return domain_scores