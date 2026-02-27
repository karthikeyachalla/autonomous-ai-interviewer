from backend.core.config import settings


def apply_help_penalty(base_score: int, hints_used: int) -> int:
    penalty = hints_used * settings.HELP_PENALTY_PER_HINT
    final = max(0, base_score - penalty)
    return final


def aggregate_round2(scores: dict, hints_used: int) -> dict:
    # scores: {"aptitude": int, "dsa": int, "technical": int}
    total = sum(scores.values())
    adjusted = apply_help_penalty(total, hints_used)
    return {"raw": total, "hints_used": hints_used, "final": adjusted}
