from backend.round3.scenario_engine import generate_scenarios, evaluate_response
from backend.database.db import get_session
from backend.database.models import RoundResult, Application


def start_scenarios(application_id: int, n: int = 3):
    session = get_session()
    app = session.query(Application).filter(Application.id == application_id).first()
    if not app:
        session.close()
        raise ValueError("application not found")
    # Pass resume_text so Gemini can generate resume-specific scenarios
    scenarios = generate_scenarios(
        jd_text=app.jd_text or "",
        resume_text=app.resume_text or "",
        n=n,
    )
    session.close()
    return scenarios


def submit_response(
    application_id: int,
    scenario_id: int,
    response_text: str,
    scenario_prompt: str = "",
):
    # Retrieve job_role for richer evaluation
    session = get_session()
    try:
        app = session.query(Application).filter(Application.id == application_id).first()
        job_role = app.job_role if app else ""
    finally:
        session.close()

    result = evaluate_response(response_text, scenario_prompt=scenario_prompt, job_role=job_role)
    session = get_session()
    rr = RoundResult(
        application_id=application_id,
        round_name="round3",
        score=result.get("score"),
        passed=(1 if result.get("score", 0) >= 20 else 0),
        artifacts={"scenario_id": scenario_id, "eval": result},
    )
    session.add(rr)
    session.commit()
    session.close()
    return {
        "score": result.get("score"),
        "passed": (1 if result.get("score", 0) >= 20 else 0),
        "eval": result,
    }
