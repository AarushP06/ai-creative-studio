"""Shared test helpers. Tests are offline and deterministic: they never call Gemini."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.service import CardService

ROOT = Path(__file__).resolve().parent.parent
SIMULATED = ROOT / "data" / "simulated_responses"
MOCK_CARDS = ROOT / "data" / "mock_cards"

VALID_CARD = {
    "title": "Quiet tables for deep work",
    "summary": "Find a calm seat, good coffee and fast Wi-Fi for your next long study session.",
    "cta_text": "Plan your visit",
    "image": "community",
    "tone": "friendly",
    "cta_action": "visit",
}


def card(**changes) -> dict:
    """A valid card with some fields changed — handy for negative tests."""
    return {**VALID_CARD, **changes}


def make_settings(**changes) -> Settings:
    base = dict(
        gemini_api_key="test-key-not-real",
        gemini_model="gemini-test-model",
        ai_mode="auto",
        timeout_seconds=1,
        cooldown_seconds=0,
        max_live_per_session=100,
    )
    base.update(changes)
    return Settings(**base)


class FakeGenerator:
    """Stands in for Gemini. Returns whatever raw text a test gives it."""

    name = "live"

    def __init__(self, raw_outputs=None, error=None):
        self.raw_outputs = list(raw_outputs or [])
        self.error = error
        self.calls = 0

    def generate(self, brief_text: str) -> str:
        self.calls += 1
        if self.error:
            raise self.error
        return self.raw_outputs.pop(0)


@pytest.fixture
def make_client():
    def _make(settings=None, live=None):
        settings = settings or make_settings()
        service = CardService(settings, live_generator=live)
        return TestClient(create_app(settings=settings, service=service))

    return _make


def raw(obj) -> str:
    return json.dumps(obj)
