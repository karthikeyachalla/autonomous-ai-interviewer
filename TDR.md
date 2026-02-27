# Technical Design Record (TDR)

**Project:** AuraCloud AI Interview Agent  
**Date:** February 2026  
**Status:** Implemented  

## 1. Context & Objective
The traditional technical hiring process is slow, expensive, and scales poorly. The objective is to build an autonomous, multi-round AI interview system capable of simulating a high-quality human interviewer, executing deep-resume screening, maintaining dynamic voice conversations, and evaluating psychological depth. 

## 2. System Architecture
The platform is structured into a unified FastAPI backend with distinct sub-modules per evaluation round, driven by an uncoupled static SPA (Single Page Application) frontend.

### 2.1 Backend Design
- **Web Framework:** FastAPI for highly concurrent asynchronous handling of AI I/O requests.
- **Database:** SQLite via SQLAlchemy. Tracks Candidates, Applications, and RoundResults per round increment.
- **`round1` (ATS Engine):** Uses `PyMuPDF` to extract raw binary text from PDFs. Feeds text alongside JD to Groq (Llama-3.3-70b-versatile) for deterministic JSON evaluations. Evaluates strengths, weaknesses, and a rigid 0-100 score threshold.
- **`round2` (Live Voice Agent):** Utilizes Google `gemini-1.5-flash` natively to maintain an array of conversation JSON dicts. Prompts are aggressively tuned to produce Siri-like sub-25-word responses.
  - Implements a resilient Fallback pipeline: `Gemini -> native Groq inference` to guard against `400 Bad Request` or API key rotations.
- **`round3` (Behavioral Scenarios):** Dynamically injects candidate resume details into Gemini prompts to generate bespoke organizational psychology dilemmas.
- **Evaluator Design:** All scoring prompts instruct the LLM to output pure JSON strings bypassing markdown wrappers, executing structural parsing via Regex (`\{[^{}]+\}`) natively in Python.

### 2.2 Frontend Architecture
- **Tech Stack:** Vanilla JavaScript, HTML5, CSS3. Zero-build dependency (No React, Webpack).
- **Voice Interactivity (VAD):** 
  - Uses `SpeechSynthesisUtterance` for TTS with a tuned speech `rate=0.9` for optimal UX comprehension.
  - Uses `SpeechRecognition` (Web Speech API) for continuous client-side STT transcription.
  - Employs a debounce timer (`SILENCE_MS = 2500ms`) on voice activity. When the candidate pauses for 2.5s, the WebRTC pipeline automatically submits the transcript payload to `/round2/interview/evaluate-answer`.
- **UI System:** Advanced CSS variables enforcing a deep-space dark theme, animated SVGs, and responsive grid layouts.

## 3. Data Flow
1. User uploads PDF + Role + JD `->` POST `/round1/apply`.
2. Python parses PDF, contacts Groq, stores to DB. Returns `Application_ID`.
3. JS auto-routes to Round 2 if score >= 50.
4. JS hits GET `/round2/interview/question` `->` LLM reads transcript + Resume + JD `->` LLM says "Hello".
5. Web Speech API speaks.
6. STT listens. Silence 2.5s -> JS captures text -> POST `/round2/evaluate` `->` API maps to 0-20 score + dynamic pushback.
7. Loop finishes at Q8 `->` POST `/round2/finalize`.
8. JS routes to Round 3 scenarios `->` LLM creates 3 dilemmas `->` POST `/round3/submit`.
9. Final rendering.

## 4. Security & Privacy
- Zero persistent storage of API Keys (enforced via `.env` `.gitignore`).
- No raw code execution (sandbox not required as evaluating logic is purely conceptual via LLM).
- SQL Injection mitigation native via SQLAlchemy ORM parameters.
