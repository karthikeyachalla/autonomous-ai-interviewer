from backend.utils.helpers import normalize_text, keywords_from_text
from backend.core.config import settings
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def heuristic_score(resume_text: str, jd_text: str) -> dict:
    r_text = normalize_text(resume_text)
    jd_text_n = normalize_text(jd_text)

    if not r_text or not jd_text_n:
        reasons = []
        if not r_text: reasons.append("Resume text appears empty or could not be parsed.")
        if not jd_text_n: reasons.append("Job description appears empty.")
        return {"score": 0, "matched": [], "missing": [], "reasons": reasons, "suggestions": []}

    vec = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, stop_words="english")
    docs = [jd_text_n, r_text]
    X = vec.fit_transform(docs)
    sim = float(cosine_similarity(X[0:1], X[1:2])[0][0])
    score = int(sim * 100)

    feature_names = np.array(vec.get_feature_names_out())
    jd_vec = X[0].toarray().ravel()
    resume_vec = X[1].toarray().ravel()
    shared = np.minimum(jd_vec, resume_vec)
    top_idx = shared.argsort()[::-1][:20]
    matched = [feature_names[i] for i in top_idx if shared[i] > 0]
    jd_top_idx = jd_vec.argsort()[::-1][:20]
    missing = [feature_names[i] for i in jd_top_idx if resume_vec[i] < 1e-3][:8]

    reasons = []
    suggestions = []
    threshold = settings.ATS_THRESHOLD  # 50

    if score < threshold:
        reasons.append(f"ATS score {score}/100 is below the minimum threshold of {threshold}.")
        if missing:
            reasons.append("Key skills missing from your resume: " + ", ".join(missing[:6]))
            suggestions.append("Add these skills/technologies to your resume: " + ", ".join(missing[:6]))
        else:
            reasons.append("Low semantic alignment between your resume and the job description.")
            suggestions.append("Include more role-specific language, project details, and measurable impact.")
    else:
        reasons.append(f"ATS score {score}/100 meets the minimum threshold of {threshold}.")

    if matched:
        suggestions.append("Strong matching areas: " + ", ".join(matched[:6]))

    if len(r_text.split()) < 80:
        reasons.append("Resume appears too short — missing sufficient detail about experience and projects.")
        suggestions.append("Expand your resume with project descriptions, technologies used, and outcomes.")
        score = min(score, 40)  # cap score for very thin resumes

    if not reasons:
        reasons.append("Resume appears to match the JD well. Polish formatting and add measurable impact.")

    return {"score": score, "matched": matched, "missing": missing, "reasons": reasons, "suggestions": suggestions}


def call_grok(prompt: str) -> str | None:
    """Call the Groq API (api.groq.com) using the OpenAI-compatible endpoint."""
    key = settings.GROK_API_KEY
    if not key:
        return None
    try:
        import requests
    except Exception:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 900,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        j = r.json()
        if "choices" in j and isinstance(j["choices"], list) and j["choices"]:
            c = j["choices"][0]
            if "message" in c and "content" in c["message"]:
                return c["message"]["content"]
            if "text" in c:
                return c["text"]
    except Exception as e:
        print(f"[Groq API error] {e}")
        return None
    return None


def llm_evaluate(resume_text: str, jd_text: str) -> dict:
    threshold = settings.ATS_THRESHOLD  # 50
    prompt = (
        "You are a strict but fair ATS system evaluating a resume against a job description.\n"
        "CRITICAL RULES:\n"
        f"- The minimum passing score is {threshold}/100. Be realistic — most resumes should NOT easily pass.\n"
        "- Award 70-100 ONLY if the candidate clearly demonstrates the required skills via concrete projects, measurable impact, and relevant experience.\n"
        "- Award 40-69 if there is partial match but key skills or experience depth are missing.\n"
        "- Award < 40 if the resume has poor alignment, missing critical skills, or lacks substance.\n"
        "- Ignore generic buzzwords, focus on REAL demonstrated experience.\n"
        "- Penalise vague resumes with no project details.\n\n"
        "Evaluate THOROUGHLY across these dimensions:\n"
        "1. Skills match (required technologies, tools, frameworks)\n"
        "2. Project relevance (projects directly relevant to this role)\n"
        "3. Experience depth (years, complexity of work done)\n"
        "4. Resume quality (clarity, specificity, measurable outcomes)\n"
        "5. Role-specific keywords alignment\n\n"
        "Return ONLY a valid JSON object (no markdown, no commentary):\n"
        "{\n"
        '  "score": <integer 0-100>,\n'
        '  "passed": <true or false>,\n'
        '  "strengths": [<up to 4 specific strengths found in the resume>],\n'
        '  "weaknesses": [<up to 4 specific gaps or weaknesses>],\n'
        '  "matched": [<top matched keywords/skills, max 12>],\n'
        '  "missing": [<important JD keywords not found in resume, max 8>],\n'
        '  "reasons": [<2-3 clear reasons for the score decision>],\n'
        '  "suggestions": [<2-3 concrete suggestions to improve the resume>],\n'
        '  "verdict": "<one sentence overall verdict>"\n'
        "}\n\n"
        f"Minimum passing score is {threshold}. Set passed=true only if score >= {threshold}.\n\n"
        f"Job Description:\n{jd_text}\n\nResume:\n{resume_text}\n"
    )
    grok_text = call_grok(prompt)
    if grok_text:
        import json, re
        js = re.search(r"\{.*\}", grok_text, re.S)
        if js:
            try:
                result = json.loads(js.group(0))
                # enforce minimum score rule server-side too
                score = int(result.get("score", 0))
                result["passed"] = score >= threshold
                return result
            except Exception:
                pass
    # fallback
    return heuristic_score(resume_text, jd_text)


def evaluate(resume_text: str, jd_text: str) -> dict:
    return llm_evaluate(resume_text, jd_text)


def decide_pass(result: dict) -> bool:
    score = int(result.get("score", 0))
    threshold = settings.ATS_THRESHOLD  # 50
    # LLM already sets passed field — trust it, but enforce min threshold
    if score >= threshold:
        return True
    return False
