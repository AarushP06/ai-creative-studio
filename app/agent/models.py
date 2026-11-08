"""Where the agent's 'thinking' comes from.

GeminiAgentModel — the real model, through Gemini function calling (Interactions API).
MockAgentModel   — a scripted stand-in for mock mode. Only the MODEL is fake:
                   permissions.py and tools.py still run for real.

Both take the conversation so far and return the model's next steps as plain dicts:
  {"type": "function_call", "id": ..., "name": ..., "arguments": {...}}
  {"type": "model_output", "content": [{"type": "text", "text": ...}]}
"""
from __future__ import annotations

import json
import re

from app.brief import parse_brief
from app.generators import GenerationError, classify_error

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class GeminiAgentModel:
    name = "live"

    def __init__(self, settings, http_client=None):
        from google import genai  # imported here so tests never need the network
        from google.genai import types

        self.settings = settings
        options = types.HttpOptions(retryOptions=types.HttpRetryOptions(attempts=1), httpxClient=http_client)
        self.client = genai.Client(api_key=settings.gemini_api_key, http_options=options)

    def respond(self, system: str, history: list[dict], tools: list[dict]) -> list[dict]:
        try:
            interaction = self.client.interactions.create(
                model=self.settings.gemini_model,
                system_instruction=system,
                input=history,      # stateless: we send the whole conversation every time
                tools=tools,        # tool descriptions are re-sent on every call
                store=False,
                timeout=self.settings.timeout_seconds,
            )
        except Exception as err:  # noqa: BLE001 — every failure becomes a GenerationError
            raise GenerationError(classify_error(err), type(err).__name__) from err
        # Keep every step (including the model's hidden 'thought' steps) for the next call.
        return [step.model_dump(mode="json", exclude_none=True) for step in interaction.steps or []]


def _text(text: str) -> list[dict]:
    return [{"type": "model_output", "content": [{"type": "text", "text": text}]}]


class MockAgentModel:
    """Scripted decisions, so the agent works with no key, no quota and no internet."""

    name = "mock"
    TIME_WORDS = ("free", "available", "availability", "open", "come", "time", "slot", "visit", "when")

    def __init__(self, brief_text: str = "", today: str = "monday"):
        self.facts = parse_brief(brief_text)
        self.today = today

    def _day(self, question: str) -> str | None:
        for day in WEEKDAYS:
            if day in question:
                return day
        if "tomorrow" in question:
            return WEEKDAYS[(WEEKDAYS.index(self.today) + 1) % 7]
        if "today" in question:
            return self.today
        return None

    def respond(self, system: str, history: list[dict], tools: list[dict]) -> list[dict]:
        last = history[-1]
        if last.get("type") == "function_result":
            return _text(self._answer_from(json.loads(last["result"][0]["text"])))

        question = last["content"][0]["text"].lower()
        offered = {t["name"] for t in tools}
        day = self._day(question)
        if re.search(r"\b(book|reserve)\b", question) and "book_visit" in offered:
            time = (re.search(r"\b\d{1,2}[:h]\d{2}\b", question) or [""])[0] or "10:00"
            return [{"type": "function_call", "id": "mock-1", "name": "book_visit",
                     "arguments": {"day": day or self.today, "time": time}}]
        if re.search(r"\b(book|reserve)\b", question):
            return _text("I can't book visits here. Please call us or drop by and we'll find a time.")
        if re.search(r"\b(hi|hello|hey|bonjour)\b", question) and len(question) < 25:
            return _text("Hi! Ask me when you can visit, or what we offer.")
        if any(w in question for w in ("hour", "close", "opening")) and self.facts.get("opening_hours") and not day:
            return _text(f"Our opening hours: {self.facts['opening_hours']}")
        if day or any(w in question for w in self.TIME_WORDS):
            return [{"type": "function_call", "id": "mock-1", "name": "check_availability",
                     "arguments": {"day": day or self.today}}]
        if any(w in question for w in ("repair", "fix", "offer", "service", "what can")) and self.facts.get("offer"):
            return _text(f"Here is what we offer: {self.facts['offer']}")
        return _text("I'm not sure. Please contact us.")

    @staticmethod
    def _answer_from(result: dict) -> str:
        if "error" in result:
            return "Sorry, I can't do that here. Please call us or drop by."
        day = result["day"].capitalize()
        if not result["free_times"]:
            return f"Sorry, there are no free times on {day}. Would another day work for you?"
        times = result["free_times"]
        listed = times[0] if len(times) == 1 else ", ".join(times[:-1]) + " or " + times[-1]
        return f"Yes! On {day} you can come at {listed}. See you soon!"
