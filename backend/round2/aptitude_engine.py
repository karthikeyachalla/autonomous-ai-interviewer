import random


SAMPLE_QUESTIONS = [
    {"id": 1, "question": "What is the output of 2+2*2?", "answer": "6", "points": 10},
    {"id": 2, "question": "If a train travels 60km in 1.5 hours, what's its speed?", "answer": "40", "points": 10},
]


def get_aptitude_questions(role: str, n: int = 3):
    return random.sample(SAMPLE_QUESTIONS, min(n, len(SAMPLE_QUESTIONS)))


def evaluate_answer(question_id: int, response: str) -> dict:
    for q in SAMPLE_QUESTIONS:
        if q["id"] == question_id:
            correct = q["answer"].strip().lower()
            score = q["points"] if response.strip().lower() == correct else 0
            return {"score": score, "correct": correct}
    return {"score": 0, "correct": None}
