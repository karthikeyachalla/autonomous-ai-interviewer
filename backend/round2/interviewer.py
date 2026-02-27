from typing import Dict


class SimpleInterviewer:
    """Stateful simple interviewer that can send hints and short feedback.

    NOTE: In production this would wrap LLM calls and maintain conversation state.
    """

    def __init__(self):
        self.hint_count = 0

    def prompt_for_dive(self, project_text: str) -> str:
        return "Please describe the primary challenges you faced in the project and how you solved them."

    def give_hint(self, question_id: int) -> str:
        self.hint_count += 1
        return "Try considering edge cases and complexity. Start by writing brute-force and then optimize."

    def short_feedback(self, correct: bool) -> str:
        return "Good direction" if correct else "Keep thinking about time complexity"
