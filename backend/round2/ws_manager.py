from threading import Lock
import time


class WSManager:
    def __init__(self):
        self.sessions = {}  # application_id -> state
        self.lock = Lock()

    def start_session(self, application_id: int):
        with self.lock:
            state = {
                "application_id": application_id,
                "hints_used": 0,
                "start_time": time.time(),
                "current_question": None,
                "submissions": 0,
            }
            self.sessions[application_id] = state
            return state

    def get(self, application_id: int):
        return self.sessions.get(application_id)

    def increment_hints(self, application_id: int):
        with self.lock:
            s = self.sessions.get(application_id)
            if not s:
                return 0
            s["hints_used"] += 1
            return s["hints_used"]

    def end_session(self, application_id: int):
        with self.lock:
            return self.sessions.pop(application_id, None)


manager = WSManager()
