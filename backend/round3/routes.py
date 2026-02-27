from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.round3.service import start_scenarios, submit_response

router = APIRouter(prefix="/round3", tags=["round3"])


@router.get("/scenarios/{application_id}")
def scenarios(application_id: int, n: int = 3):
    try:
        return start_scenarios(application_id, n=n)
    except ValueError:
        raise HTTPException(status_code=404, detail="application not found")


class SubmitScenarioRequest(BaseModel):
    application_id: int
    scenario_id: int
    response_text: str
    scenario_prompt: str = ""


@router.post("/submit")
def submit(req: SubmitScenarioRequest):
    return submit_response(
        application_id=req.application_id,
        scenario_id=req.scenario_id,
        response_text=req.response_text,
        scenario_prompt=req.scenario_prompt,
    )
