from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.round2.interviewer import SimpleInterviewer
from backend.round2.ws_manager import manager
from backend.round2.service import select_questions_for_round2
from backend.round2.service import persist_round2_subresult
from backend.database.db import get_session

router = APIRouter()


@router.websocket("/ws/{application_id}")
async def websocket_endpoint(websocket: WebSocket, application_id: int):
    await websocket.accept()
    interviewer = SimpleInterviewer()
    # start session
    state = manager.start_session(application_id)
    try:
        await websocket.send_text("Connected to AI interviewer. Send 'start' to begin the Round 2 flow.")
        while True:
            data = await websocket.receive_text()
            txt = data.strip()
            # detect hint keywords
            if txt.lower() in ("hint", "help", "suggestion", "suggest"):
                hints = manager.increment_hints(application_id)
                hint = interviewer.give_hint(0)
                await websocket.send_text(f"HINT #{hints}: {hint}")
                continue

            if txt.lower() == "start":
                # select questions and send them
                try:
                    qs = select_questions_for_round2(application_id)
                except Exception as e:
                    await websocket.send_text(f"Error selecting questions: {e}")
                    continue
                # store selection as RoundResult artifact
                try:
                    persist_round2_subresult(application_id, "question_selection", 0, artifacts={"questions": qs})
                except Exception:
                    pass
                await websocket.send_text("Selected questions for Round2:\nAptitude:\n")
                for q in qs.get("aptitude", []):
                    await websocket.send_text(f"- {q.get('question') if isinstance(q,dict) else q}\n")
                await websocket.send_text("DSA:\n")
                for q in qs.get("dsa", []):
                    await websocket.send_text(f"- {q.get('title', q.get('prompt'))}\n")
                await websocket.send_text("Technical prompt:\n" + str(qs.get("technical", [])))
                continue

            # For any other user message, provide short feedback
            if txt.lower().startswith("answer:"):
                # treat as a submission; increment submissions
                s = manager.get(application_id)
                if s is not None:
                    s["submissions"] += 1
                await websocket.send_text(interviewer.short_feedback(True))
            else:
                await websocket.send_text(interviewer.short_feedback(True))
    except WebSocketDisconnect:
        manager.end_session(application_id)
        return
