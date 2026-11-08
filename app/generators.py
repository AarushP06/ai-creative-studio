"""Where the raw model output comes from.

GeminiCardGenerator — the real LLM API call (run-time AI).
MockCardGenerator   — cached cards, used when there is no key or the API fails.

Both return RAW TEXT. Nothing here trusts the output; app/pipeline.py validates it.
"""
from __future__ import annotations

import itertools
import time
from pathlib import Path

from app.config import MOCK_CARDS_DIR, Settings
from app.models import gemini_response_schema
from app.prompts import build_input, build_instructions


class GenerationError(Exception):
    """A live call failed. `kind` tells the app (and the student) why."""

    def __init__(self, kind: str, detail: str = ""):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind  # rate_limit | timeout | bad_key | network | server | empty | error
        self.detail = detail


def classify_error(err: Exception) -> str:
    """Map any SDK/HTTP exception to a small set of kinds students can reason about."""
    name = type(err).__name__.lower()
    status = getattr(err, "status_code", None) or getattr(err, "code", None)
    if "timeout" in name:
        return "timeout"
    if status == 429:
        return "rate_limit"
    if status in (400, 401, 403):
        return "bad_key"
    if isinstance(status, int) and status >= 500:
        return "server"
    if "connection" in name:
        return "network"
    return "error"


class GeminiCardGenerator:
    """SDK → auth → model → payload: the same four parts in every LLM API call."""

    name = "live"

    def __init__(self, settings: Settings, http_client=None):
        from google import genai  # imported here so tests never need the network
        from google.genai import types

        self.settings = settings
        # The SDK retries failed calls by itself (several times, with back-off), which can
        # freeze a click for many seconds. We switch that off and do ONE visible retry below.
        # http_client lets tests plug in a fake transport: real SDK code, no network.
        options = types.HttpOptions(
            retryOptions=types.HttpRetryOptions(attempts=1),
            httpxClient=http_client,
        )
        self.client = genai.Client(api_key=settings.gemini_api_key, http_options=options)

    def _call(self, brief_text: str) -> str:
        interaction = self.client.interactions.create(
            model=self.settings.gemini_model,
            system_instruction=build_instructions(),
            input=build_input(brief_text),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": gemini_response_schema(),
            },
            store=False,  # do not keep this request on Google's side for later retrieval
            timeout=self.settings.timeout_seconds,
        )
        text = getattr(interaction, "output_text", None)
        if not text:
            raise GenerationError("empty", "the model returned no text")
        return text

    def generate(self, brief_text: str) -> str:
        try:
            return self._call(brief_text)
        except GenerationError:
            raise
        except Exception as first:  # noqa: BLE001 — we classify every failure
            kind = classify_error(first)
            if kind != "rate_limit":
                raise GenerationError(kind, type(first).__name__) from first
        # HTTP 429: wait once, retry once, then give up (the app falls back to mock).
        time.sleep(1.5)
        try:
            return self._call(brief_text)
        except Exception as second:  # noqa: BLE001
            raise GenerationError(classify_error(second), type(second).__name__) from second


class MockCardGenerator:
    """Returns cached, pre-approved cards in rotation. Never calls the network."""

    name = "mock"

    def __init__(self, folder: Path = MOCK_CARDS_DIR):
        files = sorted(folder.glob("*.json"))
        if not files:
            raise RuntimeError(f"No mock cards found in {folder}")
        self._cycle = itertools.cycle([f.read_text(encoding="utf-8") for f in files])

    def generate(self, brief_text: str) -> str:
        return next(self._cycle)
