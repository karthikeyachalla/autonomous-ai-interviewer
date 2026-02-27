from backend.database.db import get_session
from backend.database.models import RoundResult, Application
from backend.core.config import settings
from backend.round1.ats_evaluator import call_grok
from backend.round2.aptitude_engine import get_aptitude_questions
from backend.round2.dsa_engine import sample_dsa_questions


def start_round2(application_id: int) -> dict:
    session = get_session()
    try:
        app = session.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError("application not found")
        # return minimal state for the frontend to start round2
        return {"application_id": app.id, "job_role": app.job_role, "resume_preview": (app.resume_text or "")[:1000]}
    finally:
        session.close()


def select_questions_for_round2(application_id: int, n_apt: int = 3, n_dsa: int = 1):
    """Try to select role-specific questions using Grok (JD + resume). Fallback to sample providers."""
    session = get_session()
    try:
        app = session.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError("application not found")
        jd = app.jd_text or ""
        resume = (app.resume_text or "")[:5000]
    finally:
        session.close()

    # Try Grok
    prompt = (
        "Given the job description and a candidate resume, produce JSON with fields: {\n"
        "  'aptitude': [{'id':1,'question':...}, ...],\n"
        "  'dsa':[{'id':1,'title':..., 'prompt':...}],\n"
        "  'technical':[{'id':1,'prompt':...}]\n"
        "}\nRespond only JSON.\n\nJD:\n" + jd + "\n\nResume:\n" + resume
    )
    grok_resp = call_grok(prompt)
    if grok_resp:
        import re, json

        js = re.search(r"\{.*\}", grok_resp, re.S)
        if js:
            try:
                parsed = json.loads(js.group(0))
                return parsed
            except Exception:
                pass

    # Fallback
    return {"aptitude": get_aptitude_questions(app.job_role, n_apt), "dsa": sample_dsa_questions(app.job_role, n_dsa), "technical": [{"id": 1, "prompt": "Describe a major project you worked on from the resume and how you designed it."}]}



def persist_round2_subresult(application_id: int, subround: str, score: int, artifacts: dict | None = None) -> dict:
    """Persist a sub-result for round2 (aptitude, dsa, technical).

    subround: one of 'aptitude','dsa','technical'
    """
    session = get_session()
    try:
        rr = RoundResult(application_id=application_id, round_name=f"round2_{subround}", score=score, passed=(1 if score>=0 else 0), artifacts=artifacts or {})
        session.add(rr)
        session.commit()
        return {"id": rr.id, "score": score}
    finally:
        session.close()


def finalize_round2(application_id: int, scores: dict, hints_used: int = 0) -> dict:
    """Aggregate provided scores, apply hint penalty and persist final round2 result."""
    from backend.round2.scoring import aggregate_round2

    agg = aggregate_round2(scores, hints_used)
    session = get_session()
    try:
        rr = RoundResult(application_id=application_id, round_name="round2", score=agg.get("final"), passed=(1 if agg.get("final",0) >= settings.ATS_THRESHOLD else 0), artifacts={"details": agg})
        session.add(rr)
        session.commit()
        return {"final": agg}
    finally:
        session.close()
