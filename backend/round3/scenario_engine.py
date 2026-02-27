"""
backend/round3/scenario_engine.py — LLM-powered scenario generation and evaluation.
"""
from typing import List, Dict


def call_gemini_simple(prompt: str) -> str | None:
    try:
        from backend.core.config import settings
        import requests, json
        key = settings.GEMINI_API_KEY
        if not key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.6, "maxOutputTokens": 600},
        }
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        r.raise_for_status()
        resp = r.json()
        if "candidates" in resp and resp["candidates"]:
            return resp["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"[Gemini R3 error] {e}")
    # Fallback to Groq if Gemini key fails
    from backend.round1.ats_evaluator import call_grok
    print("[Fallback] Gemini failed in R3, using Groq.")
    return call_grok(prompt)


def generate_scenarios(jd_text: str, resume_text: str = "", n: int = 3) -> List[Dict]:
    """Generate n realistic, behavioral and psychological scenarios using Gemini."""
    prompt = (
        f"You are an expert organizational psychologist and senior hiring manager.\n"
        f"Job Description: {jd_text[:1000]}\n"
        f"Candidate Resume Summary: {resume_text[:800] if resume_text else 'Not available'}\n\n"
        f"Create exactly {n} distinct scenario-based psychological and behavioral questions.\n"
        f"Each scenario should place the candidate in a difficult, realistic workplace dilemma (e.g., an ethical conflict, a failing project with a difficult teammate, or a strong disagreement with management).\n"
        f"The goal is to test the candidate's personality, empathy, logical reasoning, ownership, integrity, and resilience.\n"
        f"Return ONLY a valid JSON array of {n} objects:\n"
        '[{"id": 1, "prompt": "...", "points": 30}, {"id": 2, ...}, ...]'
    )
    result = call_gemini_simple(prompt)
    if result:
        # cleanup markdown wrapping if present
        cleaned = result.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        import json, re
        arr = re.search(r"\[.*\]", cleaned, re.S)
        if arr:
            try:
                items = json.loads(arr.group(0))
                if isinstance(items, list) and items:
                    return [{"id": i.get("id", idx+1), "prompt": i.get("prompt",""), "points": i.get("points", 30)} for idx, i in enumerate(items[:n])]
            except Exception:
                pass

    # fallback behavioral scenarios
    return [
        {"id": 1, "prompt": f"You discover that a senior team member has been cutting corners on a critical project, potentially compromising security. Confronting them directly could damage your team dynamic, but ignoring it puts the company at risk. How do you handle this psychologically and practically?", "points": 30},
        {"id": 2, "prompt": f"You are 2 days away from a major launch, and you realize a fundamental flaw in your own design that will cause it to fail. Admitting the mistake now will delay the launch by weeks and anger management. What is your immediate course of action and how do you manage the psychological impact on yourself and the team?", "points": 30},
        {"id": 3, "prompt": f"A key stakeholder constantly changes project requirements at the last minute and blames you for missed deadlines. You feel burnt out and unfairly targeted. How do you navigate this conflict constructively without losing your composure or damaging the relationship?", "points": 30},
    ]


def evaluate_response(response_text: str, scenario_prompt: str = "", job_role: str = "") -> Dict:
    """Evaluate a scenario response using Gemini or fallback heuristic."""
    if not response_text or len(response_text.strip()) < 20:
        return {"score": 0, "notes": "Response too short or empty."}

    prompt = (
        f"You are an expert organizational psychologist evaluating a candidate's response to a behavioral/psychological dilemma.\n\n"
        f"Scenario: {scenario_prompt[:500] if scenario_prompt else 'Workplace dilemma'}\n"
        f"Candidate Response: {response_text[:1000]}\n\n"
        "Score from 0-30 based on:\n"
        "- Empathy and Emotional Intelligence (0-10)\n"
        "- Integrity and Ownership (0-10)\n"
        "- Logical problem solving and Resilience (0-10)\n\n"
        "Be extremely honest. Surface-level generic answers should score low (5-12). Detailed, self-aware responses score higher (20-30).\n"
        'Return ONLY valid JSON: {"score": <0-30>, "notes": "<2-3 sentence psychological analysis identifying strengths and red flags>"}'
    )
    result = call_gemini_simple(prompt)
    if result:
        # cleanup markdown wrapping if present
        cleaned = result.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        import json, re
        js = re.search(r"\{[^{}]+\}", cleaned)
        if js:
            try:
                data = json.loads(js.group(0))
                return {
                    "score": min(30, max(0, int(data.get("score", 15)))),
                    "notes": str(data.get("notes", "")).strip(),
                }
            except Exception:
                pass

    # fallback heuristic
    words = len(response_text.split())
    score = 0
    if words > 100:
        score += 15
    elif words > 50:
        score += 10
    action_words = ["design", "deploy", "scale", "monitor", "debug", "test", "refactor", "optimize", "analyse", "prioritize"]
    hits = sum(1 for w in action_words if w in response_text.lower())
    score += min(15, hits * 3)
    return {"score": score, "notes": f"Response recorded. Word count: {words}. Action indicators: {hits}."}
