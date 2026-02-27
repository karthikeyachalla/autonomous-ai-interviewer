"""
backend/round2/interview_ai.py — Gemini-powered conversational AI interviewer.

The AI interviewer:
- Reads the candidate's actual resume text and JD
- Asks deeply contextual questions (not generic templates)
- Reacts to each answer: probes deeper, pushes back if answer is weak, asks follow-ups
- Sounds like a real senior interviewer (Google/Microsoft style)
- Evaluates each answer honestly using Gemini's reasoning
"""
import json
import re
from backend.core.config import settings


# ─── Gemini call ─────────────────────────────────────────────────────────────
def call_gemini(prompt: str, temperature: float = 0.7) -> str | None:
    key = settings.GEMINI_API_KEY
    if not key:
        return None
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 512},
    }
    try:
        import requests
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        r.raise_for_status()
        resp = r.json()
        if "candidates" in resp and resp["candidates"]:
            return resp["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"[Gemini error] {e}")
    # If Gemini fails (e.g. invalid API key), fall back to Groq which is also excellent at reasoning
    from backend.round1.ats_evaluator import call_grok
    print("[Fallback] Gemini failed or key invalid, using Groq for logic/reasoning.")
    return call_grok(prompt)


# ─── Generate next question ───────────────────────────────────────────────────
def generate_question(
    job_role: str,
    jd_text: str,
    resume_text: str,
    conversation: list[dict],
    question_num: int,
) -> str:
    """
    Generate the next interview question. The AI behaves like a real senior
    interviewer — it reads the transcript so far and decides what to ask next,
    whether to probe the last answer deeper, or pivot to a new topic.
    """
    history_lines = []
    for i, turn in enumerate(conversation):
        history_lines.append(f"Q{i+1}: {turn['question']}")
        history_lines.append(f"A{i+1}: {turn['answer']}")
        if turn.get("feedback"):
            history_lines.append(f"[Score: {turn.get('score',0)}/20 — {turn['feedback']}]")
    history = "\n".join(history_lines) if history_lines else "No questions asked yet."

    if question_num == 1:
        phase = "Start with a friendly, ultra-short welcome. Ask them to briefly introduce themselves."
    elif question_num <= 3:
        phase = (
            "Dive deeper technically based on their resume or last answer. "
            "If their last answer was strong, ask a quick follow-up. "
            "If weak, push back politely. Keep it to one concise question."
        )
    elif question_num <= 6:
        phase = (
            "Problem-solving or scenario. Pose a quick, specific challenge relevant to the role. "
            "Don't give too many details, let them figure it out."
        )
    else:
        phase = "Wrap up. Ask a short final question about their approach or excitement for the role."

    prompt = (
        "You are an AI Voice Interviewer for a top tech company. You are having a real-time VOICE conversation over the phone. "
        "CRITICAL RULE: People are listening to you over audio. You MUST speak in extremely short, crisp, natural sentences. "
        "Like Siri or Gemini Live. Maximum 1-2 sentences. NO long paragraphs. NO bullet points. NO complex jargon that is hard to hear. "
        "Sound relaxed, engaging, and highly conversational. React naturally to what the candidate just said.\n\n"
        f"Role: {job_role}\n"
        f"Job Description context: {jd_text[:800]}\n"
        f"Candidate Resume context: {resume_text[:800]}\n\n"
        f"Voice transcript so far:\n{history}\n\n"
        f"This is turn {question_num}. Your goal right now: {phase}\n\n"
        "Write exactly what you are going to SAY next. Keep it under 25 words if possible."
    )
    result = call_gemini(prompt, temperature=0.75)
    if result:
        # Clean up any AI preambles
        q = result.strip()
        for prefix in ["Question:", "Q:", "Interviewer:", "Sure!", "Great!"]:
            if q.startswith(prefix):
                q = q[len(prefix):].strip()
        return q

    # Fallbacks only if Gemini fails entirely
    fallbacks = [
        "Walk me through your background and your most relevant project for this role.",
        "Tell me about a specific technical challenge you solved — what was your exact approach?",
        "How would you design a scalable system for the core product in this role?",
        "Describe a time something broke in production. How did you diagnose and fix it?",
        f"What excites you most about this {job_role} role, and how would you approach your first 30 days?",
    ]
    return fallbacks[min(question_num - 1, len(fallbacks) - 1)]


# ─── Evaluate single answer ───────────────────────────────────────────────────
def evaluate_answer(question: str, answer: str, job_role: str) -> dict:
    """
    Score a single answer (0-20) using Gemini. The model is told to be
    honest and strict — shallow answers get low scores.
    """
    if not answer or len(answer.strip()) < 8:
        return {"score": 0, "feedback": "Answer not received or too short."}

    prompt = (
        f"You are a supportive but fair technical interviewer evaluating a spoken answer for a {job_role} role.\n\n"
        f"Question asked: {question}\n"
        f"Candidate's raw speech transcript: {answer}\n\n"
        "Score the answer from 0 to 20. Keep in mind this is a literal transcription of spoken speech, so grammar and structure will be messy. "
        "Judge primarily on the presence of correct concepts, relevant experience, and logical thought process.\n\n"
        "  0-6   = completely irrelevant or blank\n"
        "  7-12  = on the right track but very brief or missing key concepts\n"
        " 13-16  = solid, conversational answer that hits the core points\n"
        " 17-20  = excellent, hits specific technical details or gives great context\n\n"
        "Do not punish the user for speech-to-text grammar errors. Be generous if they hit the right keywords.\n\n"
        "Return ONLY valid JSON — no markdown, no extra text:\n"
        '{"score": <integer 0-20>, "feedback": "<one short, friendly sentence validating what they said>"}'
    )
    result = call_gemini(prompt, temperature=0.3)
    if result:
        js = re.search(r"\{[^{}]+\}", result)
        if js:
            try:
                data = json.loads(js.group(0))
                return {
                    "score": min(20, max(0, int(data.get("score", 10)))),
                    "feedback": str(data.get("feedback", "")).strip(),
                }
            except Exception:
                pass
    # fallback: length heuristic
    words = len(answer.split())
    score = min(15, max(4, words // 8))
    return {"score": score, "feedback": "Answer recorded — could not auto-score."}


# ─── Final verdict ────────────────────────────────────────────────────────────
def generate_final_verdict(job_role: str, conversation: list[dict], total_score: int) -> str:
    passed = total_score >= 50
    transcript = "\n".join(
        f"Q{i+1}: {m['question']}\n"
        f"Answer: {m['answer'][:300]}\n"
        f"Score: {m.get('score', 0)}/20 — {m.get('feedback','')}"
        for i, m in enumerate(conversation)
    )
    prompt = (
        f"You are a senior hiring manager. You just finished interviewing a candidate for a {job_role} role.\n"
        f"Total interview score: {total_score}/100 (minimum to pass: 50).\n"
        f"{'The candidate PASSED.' if passed else 'The candidate did NOT pass.'}\n\n"
        f"Interview transcript:\n{transcript}\n\n"
        "Write a 3-4 sentence professional and honest verdict. "
        "Mention specific strengths, what they could improve, and the hiring decision. "
        "Sound like a real hiring manager, not a bot."
    )
    result = call_gemini(prompt, temperature=0.5)
    if result:
        return result.strip()
    if passed:
        return f"Candidate scored {total_score}/100 — strong performance across technical and behavioral questions. Selected to advance."
    return f"Candidate scored {total_score}/100 — below the required threshold of 50. We recommend strengthening technical depth and specificity."
