"""One visitor question: live agent when possible, mock agent otherwise.

Same resilience rule as the service cards: no key, quota limit, timeout or
outage → the visitor still gets an answer, and the trace says why.
"""
from __future__ import annotations

import datetime as dt

from app.agent.agent import run_agent
from app.agent.models import GeminiAgentModel, MockAgentModel
from app.brief import read_brief_text
from app.generators import GenerationError
from app.limits import SessionLimiter

MAX_QUESTION_CHARS = 300


class VisitAssistant:
    def __init__(self, settings, live_model=None, today: str | None = None):
        self.settings = settings
        self.limiter = SessionLimiter(settings.cooldown_seconds, settings.max_live_per_session)
        self._live = live_model
        self._today = today

    @property
    def today(self) -> str:
        return self._today or dt.date.today().strftime("%A").lower()

    @property
    def live(self):
        if self._live is None and self.settings.live_enabled:
            self._live = GeminiAgentModel(self.settings)
        return self._live

    def ask(self, session_id: str, question: str) -> dict:
        question = question.strip()[:MAX_QUESTION_CHARS]
        brief = read_brief_text()
        mock = MockAgentModel(brief, today=self.today)

        if self.settings.ai_mode == "mock":
            reason = "mock_mode"
        elif not self.settings.gemini_api_key:
            reason = "no_key"
        else:
            reason = self.limiter.check(session_id)

        if not reason:
            try:
                return {"source": "live", **run_agent(question, self.live, brief, self.today)}
            except GenerationError as err:
                print(f"[agent] live call failed: {err.kind} → mock agent")
                reason = err.kind

        result = run_agent(question, mock, brief, self.today)
        result["trace"].insert(1, {"kind": "fallback", "step": "Using the mock agent", "detail": reason, "ok": True})
        return {"source": "mock", "reason": reason, **result}
