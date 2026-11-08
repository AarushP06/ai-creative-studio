"""Orchestrates one "Generate service card" click.

    browser → FastAPI → [limits] → Gemini or mock → pipeline → JSON for the UI

A rejected live response is never shown as a card. The visitor gets a
validated mock card instead, and the rejection is shown in the Validator panel.
"""
from __future__ import annotations

from app.brief import read_brief_text
from app.config import BRIEF_PATH, ROOT, SIMULATED_DIR, Settings
from app.generators import GeminiCardGenerator, GenerationError, MockCardGenerator
from app.limits import SessionLimiter
from app.pipeline import validate_raw_output

FALLBACK_MESSAGES = {
    "no_key": "No GEMINI_API_KEY in .env — using a cached mock card.",
    "mock_mode": "AI_MODE=mock — using a cached mock card.",
    "cooldown": "Slow down: live calls are limited to one every few seconds.",
    "session_limit": "Live-call limit for this session reached — using mock cards.",
    "rate_limit": "Gemini returned HTTP 429 (rate limit) twice — using a mock card.",
    "timeout": "Gemini did not answer in time — using a mock card.",
    "bad_key": "Gemini rejected the API key (HTTP 400/401/403) — check .env.",
    "network": "Could not reach Gemini — check your internet connection.",
    "server": "Gemini had a server error (HTTP 5xx) — using a mock card.",
    "empty": "Gemini returned an empty response — using a mock card.",
    "error": "Unexpected error calling Gemini — using a mock card.",
    "rejected": "The live response failed validation — showing a mock card instead.",
}


# "main" is the student's own brief; "injected" is the untrusted-input test brief.
BRIEFS = {
    "main": BRIEF_PATH,
    "injected": ROOT / "business" / "injected-brief-example.md",
}


def list_simulations() -> list[str]:
    return sorted(p.stem for p in SIMULATED_DIR.glob("*.json"))


class CardService:
    def __init__(self, settings: Settings, live_generator=None, mock_generator=None):
        self.settings = settings
        self.limiter = SessionLimiter(settings.cooldown_seconds, settings.max_live_per_session)
        self.mock = mock_generator or MockCardGenerator()
        self._live = live_generator

    @property
    def live(self):
        if self._live is None and self.settings.live_enabled:
            self._live = GeminiCardGenerator(self.settings)
        return self._live

    def _mock_card(self, brief_text: str, reason: str) -> dict:
        result = validate_raw_output(self.mock.generate(brief_text))
        return {
            "source": "mock",
            "card": result.card.model_dump() if result.card else None,
            "reason": reason,
            "message": FALLBACK_MESSAGES.get(reason, reason),
        }

    def simulate(self, name: str) -> dict:
        """Feed a deliberately bad 'model response' through the SAME pipeline."""
        path = SIMULATED_DIR / f"{name}.json"
        if name not in list_simulations():
            raise KeyError(name)
        raw = path.read_text(encoding="utf-8")
        result = validate_raw_output(raw)
        return self._response("simulated", raw, result, reason=f"simulation:{name}")

    def create_card(self, session_id: str, brief: str = "main") -> dict:
        if brief not in BRIEFS:
            raise KeyError(brief)
        brief_text = read_brief_text(BRIEFS[brief])

        if self.settings.ai_mode == "mock":
            reason = "mock_mode"
        elif not self.settings.gemini_api_key:
            reason = "no_key"
        else:
            reason = self.limiter.check(session_id)

        if reason:
            mock = self._mock_card(brief_text, reason)
            return {"status": "accepted", **mock, "violations": [], "raw": None,
                    "trace": [{"step": "live call skipped", "ok": False, "detail": reason}]}

        try:
            raw = self.live.generate(brief_text)
        except GenerationError as err:
            print(f"[studio] live call failed: {err.kind} → mock card")
            mock = self._mock_card(brief_text, err.kind)
            return {"status": "accepted", **mock, "violations": [], "raw": None,
                    "trace": [{"step": "Gemini API", "ok": False, "detail": err.kind}]}

        result = validate_raw_output(raw)
        response = self._response("live", raw, result, reason="live")
        if not result.accepted:
            print(f"[studio] live response REJECTED: {result.violations}")
            response["fallback"] = self._mock_card(brief_text, "rejected")
        return response

    @staticmethod
    def _response(source: str, raw: str, result, reason: str) -> dict:
        trace = [{"step": "model output", "ok": True, "detail": source}] + result.trace
        if result.accepted:
            trace.append({"step": "show on website", "ok": True, "detail": ""})
        return {
            "status": "accepted" if result.accepted else "rejected",
            "source": source,
            "card": result.card.model_dump() if result.card else None,
            "violations": result.violations,
            "raw": raw,
            "reason": reason,
            "trace": trace,
        }
