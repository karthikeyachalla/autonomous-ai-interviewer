from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from backend.round1.service import handle_application
from backend.database.db import get_session
from backend.database.models import Application
from backend.round1.ats_evaluator import call_grok

router = APIRouter(prefix="/round1", tags=["round1"])


@router.post("/apply")
async def apply_route(job_role: str = Form(...), jd_text: str = Form(...), resume: UploadFile = File(...)):
    """Endpoint to upload resume and JD text for ATS screening."""
    contents = await resume.read()
    # create an in-memory file-like
    from io import BytesIO

    f = BytesIO(contents)
    result = handle_application(f, job_role=job_role, jd_text=jd_text)
    return result



@router.post("/chat")
def chat(application_id: int = Form(...), message: str = Form(...)):
    """Simple chat endpoint that uses the stored application (resume + JD) and forwards the message to Grok.

    Returns Grok reply (or an error when Grok is unavailable).
    """
    session = get_session()
    try:
        app = session.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail="application not found")

        # Build prompt while instance is attached to session
        prompt = (
            "You are an assistant that explains ATS screening results.\n"
            f"Job Description:\n{app.jd_text}\n\nResume text:\n{app.resume_text}\n\n"
            f"Previous message from user:\n{message}\n\nRespond concisely and helpfully."
        )
    finally:
        session.close()

    text = call_grok(prompt)
    if not text:
        # fallback to a basic canned reply
        return {"reply": "AI assistant not available (Grok key not configured)."}
    return {"reply": text}
