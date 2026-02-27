from backend.round1.resume_parser import extract_text_from_file
from backend.round1.ats_evaluator import evaluate
from backend.database.db import get_session
from backend.database.models import Candidate, Application, RoundResult
from backend.core.config import settings


def handle_application(file, job_role: str, jd_text: str, candidate_info: dict | None = None):
    # extract text
    resume_text = extract_text_from_file(file)
    # print extracted text once for debugging (truncated to 2000 chars)
    try:
        print("[round1] Extracted resume text (preview):\n", resume_text[:2000])
    except Exception:
        pass
    # evaluate
    result = evaluate(resume_text, jd_text)
    # persist
    session = get_session()
    candidate = None
    try:
        if candidate_info:
            candidate = Candidate(name=candidate_info.get("name"), email=candidate_info.get("email"))
            session.add(candidate)
            session.flush()
        app = Application(candidate_id=(candidate.id if candidate else None), job_role=job_role, resume_text=resume_text, jd_text=jd_text)
        session.add(app)
        session.flush()

        # refresh to get DB-generated fields and expunge to safely detach for return/use later
        session.refresh(app)
        session.expunge(app)

        # decide pass/fail using evaluator helper
        try:
            from backend.round1.ats_evaluator import decide_pass
            passed_bool = decide_pass(result)
        except Exception:
            passed_bool = (result.get("score", 0) >= settings.ATS_THRESHOLD)
        passed_val = 1 if passed_bool else 0
        rr = RoundResult(application_id=app.id, round_name="round1", score=result.get("score"), passed=passed_val, artifacts={"details": result})
        session.add(rr)
        session.commit()
    finally:
        session.close()

    return {"application_id": app.id, "score": result.get("score"), "passed": passed_val, "details": result, "resume_preview": resume_text[:1000]}
