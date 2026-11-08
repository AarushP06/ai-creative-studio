"""Per-browser-session limits for live Gemini calls.

Each student runs their own server with their own key, so these limits
protect that student's free-tier quota from accidental button-spamming.
They never block other students: there is no global lock.
"""
from __future__ import annotations

import threading
import time


class SessionLimiter:
    def __init__(self, cooldown_seconds: float, max_calls: int, clock=time.monotonic):
        self.cooldown_seconds = cooldown_seconds
        self.max_calls = max_calls
        self._clock = clock
        self._sessions: dict[str, tuple[float, int]] = {}
        self._lock = threading.Lock()

    def check(self, session_id: str) -> str | None:
        """Return None if a live call is allowed (and record it), else a reason."""
        now = self._clock()
        with self._lock:
            last, count = self._sessions.get(session_id, (float("-inf"), 0))
            if count >= self.max_calls:
                return "session_limit"
            if now - last < self.cooldown_seconds:
                return "cooldown"
            self._sessions[session_id] = (now, count + 1)
            return None
