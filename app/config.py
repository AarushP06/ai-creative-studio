"""Settings, read once from environment variables (.env is loaded by run.py / app.main).

The API key is read here and nowhere else. It is never returned by the API,
never logged, and never sent to the browser.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND_RULES_PATH = ROOT / "brand" / "brand-rules.json"
BRIEF_PATH = ROOT / "business" / "brief.md"
MOCK_CARDS_DIR = ROOT / "data" / "mock_cards"
SIMULATED_DIR = ROOT / "data" / "simulated_responses"
STATIC_DIR = ROOT / "static"


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    ai_mode: str  # "auto" = live when a key exists, "mock" = never call Gemini
    timeout_seconds: float
    cooldown_seconds: float
    max_live_per_session: int

    @property
    def live_enabled(self) -> bool:
        return self.ai_mode != "mock" and bool(self.gemini_api_key)


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def load_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip(),
        ai_mode=os.getenv("AI_MODE", "auto").strip().lower(),
        timeout_seconds=_float("GEMINI_TIMEOUT_SECONDS", 10),
        cooldown_seconds=_float("LIVE_COOLDOWN_SECONDS", 4),
        max_live_per_session=int(_float("LIVE_MAX_PER_SESSION", 30)),
    )


@lru_cache(maxsize=1)
def brand_rules() -> dict:
    return json.loads(BRAND_RULES_PATH.read_text(encoding="utf-8"))
