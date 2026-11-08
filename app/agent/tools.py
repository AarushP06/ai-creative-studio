"""Python functions the runtime agent may ask to call.

The model never runs code itself. It only ASKS: "call check_availability(day='thursday')".
agent.py checks permissions.py, then runs the function and sends the result back.
"""
from __future__ import annotations

import json

from app.config import ROOT

AVAILABILITY_PATH = ROOT / "data" / "availability.json"
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Break-it exercise: set this to True, restart the server and ask "Book me Thursday at 14:00".
# The model will now ASK for book_visit — and permissions.py will block it.
OFFER_BOOKING_TOOL = False


def check_availability(day: str) -> dict:
    """Read-only: the free visit times for one weekday, from data/availability.json."""
    day = (day or "").strip().lower()
    if day not in WEEKDAYS:
        return {"error": f"unknown day '{day}'. Use a weekday name, e.g. 'thursday'."}
    slots = json.loads(AVAILABILITY_PATH.read_text(encoding="utf-8"))
    free = slots.get(day, [])
    if not free:
        return {"day": day, "free_times": [], "note": "no free times on this day"}
    return {"day": day, "free_times": free}


def book_visit(day: str, time: str) -> dict:
    """A WRITE action. Not allowed in Level 1 (see permissions.py)."""
    return {"error": "booking needs a database and human approval: that is Level 2"}


# What the model is told about each tool (name, purpose, parameters).
DECLARATIONS = {
    "check_availability": {
        "type": "function",
        "name": "check_availability",
        "description": "Get the free visit times for one weekday. Use it for any question about when to come.",
        "parameters": {
            "type": "object",
            "properties": {"day": {"type": "string", "enum": WEEKDAYS, "description": "Weekday in lower case"}},
            "required": ["day"],
        },
    },
    "book_visit": {
        "type": "function",
        "name": "book_visit",
        "description": "Book a visit for the visitor at a given day and time.",
        "parameters": {
            "type": "object",
            "properties": {"day": {"type": "string", "enum": WEEKDAYS}, "time": {"type": "string"}},
            "required": ["day", "time"],
        },
    },
}

FUNCTIONS = {"check_availability": check_availability, "book_visit": book_visit}


def offered_tools() -> list[dict]:
    """The tool descriptions sent to the model."""
    names = ["check_availability"] + (["book_visit"] if OFFER_BOOKING_TOOL else [])
    return [DECLARATIONS[n] for n in names]


def run_tool(name: str, arguments: dict) -> dict:
    try:
        return FUNCTIONS[name](**(arguments or {}))
    except (KeyError, TypeError) as err:
        return {"error": f"bad tool call: {err}"}
