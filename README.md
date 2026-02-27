# AuraCloud AI Recruitment Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)

> **Origin:** This project was developed and performed during an exclusive code-a-thon at **Microsoft Office, Hyderabad**, organized by **Forged Alumni**. 

A multi-round, AI-powered autonomous interviewing platform that simulates a comprehensive real-world technical hiring process. Built using FastAPI, Google Gemini's reasoning engine, and a glass-morphism web interface.

![AI Interview Agent](docs/assets/banner.png) *(Placeholder if you want to add an image later)*

## Overview
The AI Interview Agent automates the traditional initial screening and technical interviewing phases. It consists of three primary rounds:

1. **Round 1: ATS Resume Screening & Analysis**
   - Candidates upload their resume (PDF) and provide a Job Description (JD).
   - Powered by LLM (Groq / Llama 3) for deep semantic matching, moving beyond keyword matching.
   - Outputs a detailed JSON struct with scores, strengths, weaknesses, and a strict pass/fail threshold (50/100).
   - Candidates that pass automatically advance to the live interview.

2. **Round 2: Live AI Voice Interview**
   - A fully autonomous, dynamic voice-to-voice interview simulating a Google/Microsoft-tier technical bar.
   - **Continuous Interaction**: Similar to Siri/Alexa. The AI speaks, the microphone auto-activates locally, listens to the candidate, and auto-submits upon conversational pauses using Web Speech APIs and Voice Activity Detection (VAD).
   - **Dynamic Reasoning (Powered by Gemini)**: The AI reads the candidate's resume and JD, generates specific technical/architectural questions, and actively pushes back or probes deeper based on the candidate's realtime verbal output.
   - Real-time scoring using strict evaluating heuristics.

3. **Round 3: Behavioral & Psychological Assessment**
   - The AI uses Gemini to generate deep, realistic workplace dilemmas directly relevant to the JD and Candidate's experience.
   - Tests candidates on empathy, ownership, psychological resilience, and ethical problem-solving.

## Architecture & Tech Stack

**Backend**
*   **FastAPI / Python**: Handles async routing, database interactions, and integrations with LLMs.
*   **SQLAlchemy / SQLite**: Tracks Candidate profiles, Applications, and per-round Results (`RoundResult`).
*   **LLMs:**
    *   **Google Gemini (1.5 Flash)**: Primary engine for Round 2 conversational logic, scoring, and Round 3 dilemma generation.
    *   **Groq (Llama 3)**: Super-fast inference engine for Round 1 ATS parsing and as a fallback reasoning engine if the Gemini API fails.

**Frontend**
*   **Vanilla JS / HTML / CSS**: No heavy frameworks. A highly optimized, single-page application.
*   **Web Speech API & WebRTC**: For Text-to-Speech (TTS) and Speech-to-Text (STT) continuous audio loop.
*   **Cyber-Luxury UI**: Deep space dark theme with glass-morphism cards, animated SVGs, and responsive grids. 

## Run Locally

### 1. Requirements
- Python 3.10+
- Valid API keys for Groq and/or Google Gemini.

### 2. Setup
Clone the repository and install dependencies:
```bash
git clone https://github.com/karthikeyachalla/autonomous-ai-interviewer.git
cd autonomous-ai-interviewer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
GROK_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
# Optional DB URL override
# DATABASE_URL=sqlite:///./backend/data.db
```

### 4. Start the Application
Run the FastAPI Uvicorn server:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open up your browser to: `http://127.0.0.1:8000/ui/index.html`

## Directory Structure
- `/backend`
  - `/core` - Configuration and environment bindings.
  - `/database` - SQLAlchemy models and DB session logic.
  - `/round1` - Resume parsing (`PyMuPDF`) and ATS evaluating service via Groq.
  - `/round2` - Live AI conversational flow via Gemini.
  - `/round3` - Psychological scenario generation service.
  - `main.py` - FastAPI entrypoint and static mount.
- `/frontend`
  - `index.html` - The unified single page application.

---
*Developed by Karthikeya Challa.*
