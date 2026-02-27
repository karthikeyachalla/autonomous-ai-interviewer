from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from typing import List
from backend.round2 import service as r2service
from backend.round2.aptitude_engine import get_aptitude_questions, evaluate_answer
from backend.round2.dsa_engine import sample_dsa_questions
from backend.round2.scoring import aggregate_round2

router = APIRouter(prefix="/round2", tags=["round2"])


# ── existing routes (kept for compatibility) ──────────────────────────────────
@router.get("/start/{application_id}")
def start_round(application_id: int):
    try:
        return r2service.start_round2(application_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="application not found")


@router.post("/run-code")
def run_code(language: str = Form(...), code: str = Form(...), application_id: int | None = Form(None)):
    from backend.round2.code_runner import run_code as runner
    rc, out, err = runner(language, code, timeout=10)
    if application_id:
        scr = 100 if rc == 0 else 20
        try:
            r2service.persist_round2_subresult(application_id, "technical", scr, artifacts={"rc": rc, "out": out, "err": err})
        except Exception:
            pass
    return {"returncode": rc, "stdout": out, "stderr": err}


@router.post("/final-score")
def final_score(scores: dict, hints_used: int = 0, application_id: int | None = None):
    agg = r2service.finalize_round2(application_id if application_id else 0, scores, hints_used)
    return agg


# ── NEW: AI Video Interview Routes ────────────────────────────────────────────

class QuestionRequest(BaseModel):
    application_id: int
    job_role: str
    jd_text: str
    resume_text: str
    question_num: int           # 1-5
    conversation: List[dict]    # [{question, answer, score}, ...]


class AnswerRequest(BaseModel):
    application_id: int
    job_role: str
    question: str
    answer: str
    question_num: int


class FinalizeRequest(BaseModel):
    application_id: int
    job_role: str
    conversation: List[dict]
    total_score: int


@router.post("/interview/question")
def get_next_question(req: QuestionRequest):
    """Generate the next AI interview question."""
    from backend.round2.interview_ai import generate_question
    question = generate_question(
        job_role=req.job_role,
        jd_text=req.jd_text,
        resume_text=req.resume_text,
        conversation=req.conversation,
        question_num=req.question_num,
    )
    return {"question": question, "question_num": req.question_num}


@router.post("/interview/evaluate-answer")
def evaluate_interview_answer(req: AnswerRequest):
    """Score a single interview answer (0-20)."""
    from backend.round2.interview_ai import evaluate_answer as ai_eval
    result = ai_eval(req.question, req.answer, req.job_role)
    return result


@router.post("/interview/finalize")
def finalize_interview(req: FinalizeRequest):
    """Generate final verdict and persist Round 2 result."""
    from backend.round2.interview_ai import generate_final_verdict
    from backend.database.db import get_session
    from backend.database.models import RoundResult
    from backend.core.config import settings

    verdict = generate_final_verdict(req.job_role, req.conversation, req.total_score)
    passed = 1 if req.total_score >= 50 else 0

    if req.application_id:
        try:
            session = get_session()
            rr = RoundResult(
                application_id=req.application_id,
                round_name="round2",
                score=req.total_score,
                passed=passed,
                artifacts={"conversation": req.conversation, "verdict": verdict},
            )
            session.add(rr)
            session.commit()
            session.close()
        except Exception as e:
            print(f"[finalize_interview] DB error: {e}")

    return {
        "total_score": req.total_score,
        "passed": bool(passed),
        "verdict": verdict,
    }
