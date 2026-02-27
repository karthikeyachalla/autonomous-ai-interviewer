import streamlit as st
import io
from backend.round1.service import handle_application
from backend.round2.service import start_round2, select_questions_for_round2, finalize_round2
from backend.round2.code_runner import run_code
from backend.round2.aptitude_engine import evaluate_answer
from backend.database.db import init_db
from backend.core.config import settings

# Initialize the SQLite database defined in db.py
init_db()

st.set_page_config(page_title="AuraCloud AI Recruitment", page_icon="🤖", layout="wide")

# --- Session State Management ---
# We use this to track the candidate's progress through the rounds
if "current_round" not in st.session_state:
    st.session_state.current_round = 1
if "app_id" not in st.session_state:
    st.session_state.app_id = None
if "r2_questions" not in st.session_state:
    st.session_state.r2_questions = None
if "scores" not in st.session_state:
    st.session_state.scores = {"aptitude": 0, "dsa": 0, "technical": 0}
if "round1_results" not in st.session_state:
    st.session_state.round1_results = None

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ System Control")
    st.info(f"Phase: Round {st.session_state.current_round}")
    
    # [cite_start]Check for Grok API Key status from config.py [cite: 1]
    if settings.GROK_API_KEY:
        st.success("Grok AI: Active")
    else:
        st.warning("Grok AI: Fallback Mode (No Key)")

    if st.button("Reset Workflow"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- ROUND 1: ATS SCREENING ---
if st.session_state.current_round == 1:
    st.title("🚀 Round 1: AI ATS Screening")
    st.markdown("Automated Resume alignment and semantic scoring.")

    col1, col2 = st.columns(2)
    with col1:
        job_role = st.text_input("Target Job Role", value="AI Engineer")
        jd_text = st.text_area("Job Description", height=250, placeholder="Paste JD here...")
    with col2:
        c_name = st.text_input("Candidate Name")
        c_email = st.text_input("Candidate Email")
        uploaded_file = st.file_uploader("Resume (PDF)", type=["pdf"])

    if st.button("Run Evaluation", type="primary"):
        if not jd_text or not uploaded_file:
            st.error("Please provide both the Job Description and a Resume file.")
        else:
            with st.spinner("Grok is analyzing text and calculating similarity..."):
                # Read file into BytesIO for service.py compatibility
                file_bytes = io.BytesIO(uploaded_file.read())
                
                # Execute Round 1 Service Logic
                res = handle_application(
                    file_bytes, 
                    job_role, 
                    jd_text, 
                    {"name": c_name, "email": c_email}
                )
                
                # Store results in session state to persist after rerun
                st.session_state.app_id = res["application_id"]
                st.session_state.round1_results = res
                st.rerun()

    # Display results if they exist in state
    if st.session_state.round1_results:
        res = st.session_state.round1_results
        st.divider()
        
        if res["passed"]:
            st.balloons()
            st.success(f"Candidate Passed Round 1! Score: {res['score']}%")
            
            # Display breakdown from artifacts
            details = res.get("details", {})
            tab1, tab2 = st.tabs(["Matched Keywords", "AI Feedback"])
            with tab1:
                st.write(details.get("matched", details.get("matches", [])))
            with tab2:
                for reason in details.get("reasons", []):
                    st.write(f"- {reason}")
            
            # Button is outside the 'Run Evaluation' click logic to prevent disappearing
            if st.button("Proceed to Technical Round", type="secondary"):
                st.session_state.current_round = 2
                st.rerun()
        else:
            st.error(f"Rejected. Score: {res['score']}%")
            st.write(res["details"].get("reasons", "Does not meet role requirements."))

# --- ROUND 2: TECHNICAL & APTITUDE ---
elif st.session_state.current_round == 2:
    st.title("🧠 Round 2: Technical Assessment")
    
    # Generate dynamic questions using Grok if available
    if st.session_state.r2_questions is None:
        with st.spinner("Generating role-specific questions..."):
            st.session_state.r2_questions = select_questions_for_round2(st.session_state.app_id)

    qs = st.session_state.r2_questions

    # Part 1: Aptitude
    st.header("1. Aptitude & Logic")
    for i, q in enumerate(qs.get("aptitude", [])):
        st.write(f"**Q{i+1}:** {q.get('question')}")
        user_ans = st.text_input("Answer", key=f"apt_ans_{i}")
        
        if st.button(f"Verify Q{i+1}", key=f"apt_btn_{i}"):
            eval_res = evaluate_answer(q.get("id"), user_ans)
            if eval_res["score"] > 0:
                st.success("Correct!")
                st.session_state.scores["aptitude"] += eval_res["score"]
            else:
                st.error(f"Incorrect. Expected: {eval_res['correct']}")

    # Part 2: DSA / Coding
    st.header("2. Data Structures & Algorithms")
    for dsa in qs.get("dsa", []):
        st.subheader(dsa.get("title", "Coding Challenge"))
        st.info(dsa.get("prompt", "Write a function to solve the problem."))
        
        code_input = st.text_area("Python Editor", value="def solve():\n    # your code\n    pass", height=250)
        
        if st.button("Run Code"):
            with st.spinner("Running code..."):
                rc, out, err = run_code("python", code_input)
                if rc == 0:
                    st.code(out, language="text")
                    st.success("Execution Successful!")
                    st.session_state.scores["dsa"] = 100
                else:
                    st.error(f"Runtime Error: {err}")

    st.divider()
    if st.button("Finish Round 2", type="primary"):
        # Aggregates scores and applies penalties
        finalize_round2(st.session_state.app_id, st.session_state.scores, hints_used=0)
        st.session_state.current_round = 3
        st.rerun()

# --- ROUND 3: FINAL SUMMARY ---
elif st.session_state.current_round == 3:
    st.title("📊 Candidate Final Report")
    st.success("All assessment data has been successfully stored.")
    
    st.subheader("Performance Summary")
    st.json(st.session_state.scores)
    
    st.info(f"Data persisted for Application ID: {st.session_state.app_id}")
    if st.button("Start New Evaluation"):
        st.session_state.current_round = 1
        st.session_state.round1_results = None
        st.rerun()