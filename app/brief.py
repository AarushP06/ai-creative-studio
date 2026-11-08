"""Reads business/brief.md — the fictional business each student invents.

The brief is UNTRUSTED INPUT. It goes to the model as data, never as
instructions, and nothing in it can switch off the validator.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.config import BRIEF_PATH

FIELD_PATTERN = re.compile(r"^(?P<key>[A-Za-z ]{2,20}):\s*(?P<value>.+)$")
MAX_BRIEF_CHARS = 2000

DISPLAY_FIELDS = ("name", "type", "tagline", "city")


def read_brief_text(path: Path = BRIEF_PATH) -> str:
    text = path.read_text(encoding="utf-8")
    return text[:MAX_BRIEF_CHARS]


def parse_brief(text: str) -> dict[str, str]:
    """Collect 'Key: value' lines, e.g. 'Name: Maple Lane Café'."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD_PATTERN.match(line.strip().lstrip("-* "))
        if match:
            key = match.group("key").strip().lower().replace(" ", "_")
            fields.setdefault(key, match.group("value").strip())
    return fields


def public_brief(text: str) -> dict[str, str]:
    """Only the fields the web page needs for its header."""
    fields = parse_brief(text)
    return {
        "name": fields.get("name", "Your Business"),
        "type": fields.get("type", "Local business"),
        "tagline": fields.get("tagline", "Edit business/brief.md to make this site yours."),
        "city": fields.get("city", ""),
    }
