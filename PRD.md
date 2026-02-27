# Product Requirements Document (PRD)

**Project:** AuraCloud AI Interview Agent  
**Initiative:** Automated Multi-Round AI Technical Recruiter  

## 1. Executive Summary
Hiring technical engineers currently requires thousands of hours of manual labor from senior engineering staff to parse resumes, conduct initial cultural fit screens, and run technical baseline interviews.

**AuraCloud AI Interview Agent** is an end-to-end autonomous recruiting system that allows a candidate to upload their PDF resume and seamlessly walk through three automated rounds:
1. **ATS Screening**: Validates their resume against the specific Job Description.
2. **Live Voice Technical Interview**: A real-time, hands-free conversational AI that tests technical depth.
3. **Behavioral Assessment**: Psychological scenario testing.

## 2. Target Audience
*   **Candidates:** Software Engineers, AI Engineers, Backend Developers applying for technical roles.
*   **Recruiters / Hiring Managers:** Saving hundreds of hours by only receiving final, vetted candidate reports that have survived all three rounds of AI scrutiny.

## 3. Product Features & Requirements

### 3.1 Feature: Intelligent ATS Document Parsing (Round 1)
- **Requirement:** The system must accept a raw `.pdf` resume file and a raw Job Description text block.
- **Requirement:** It must use an LLM (not simple keyword regex) to detect semantics, project scope, and experience timeline.
- **Requirement:** It must generate a concrete score (0-100), with a strict boundary (>50 required to proceed).

### 3.2 Feature: Siri-Like Hands-Free Voice Agent (Round 2)
- **Requirement:** The AI must generate questions specific to the candidate's exact resume and JD. Generic questions are strictly prohibited.
- **Requirement:** The agent should converse entirely via voice.
- **Requirement:** The interface must use Voice Activity Detection (VAD) to automatically listen when the AI stops talking, and automatically submit when the user stops talking (delay: 2500ms). No manual "submit" buttons.
- **Requirement:** The AI's responses must be heavily constrained to 1 or 2 fast, conversational sentences to emulate a phone call.
- **Requirement:** The AI must evaluate the messy, transcribed speech and map it to a 0-20 score per question seamlessly.

### 3.3 Feature: Psychological Deep Dive (Round 3)
- **Requirement:** The AI must drop the candidate into custom, JD-specific workplace dilemmas.
- **Requirement:** Questions must strictly target emotional intelligence, ownership, conflict resolution, and integrity.
- **Requirement:** Evaluator logic must punish surface-level corporate generic answers and reward deep self-awareness.

### 3.4 Feature: Performance & UI
- **Requirement:** The UI must adhere to a strict premium "Cyber-Luxury" aesthetic (Deep Space Dark `#080B14`, Neon Violets, Cyans).
- **Requirement:** Fast performance, minimal loading screens. 

## 4. Success Metrics
- **Automated Rejection Rate:** System should successfully reject >60% of unqualified candidates in Round 1 before costing Voice AI runtime.
- **Latency:** Round 2 conversational turn-around must remain under 3000ms.
- **Completion Rate:** >80% of candidates who pass Round 1 should be able to finish Round 3 without encountering tech/media pipeline errors.

## 5. Future Roadmap
- Integration with external coding execution environments (e.g. WebContainers bounds).
- OAuth logins for Hiring Managers to dashboard all applicant states.
- Calendar integration (auto-booking Round 4 human interviews if overall score > 85/100).
