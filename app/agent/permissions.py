"""What the runtime agent is ALLOWED to do — enforced by code, not by the prompt.

instructions.md *asks* the model to behave. This file *decides*.
Even if the model asks for a tool, agent.py runs it only when check() says yes.

Level 1 limits: read-only tools only, and a hard limit on tool calls per question.
Write actions (booking, changing data) need human approval — that is Level 2.
"""
from __future__ import annotations

ALLOWED_TOOLS = {"check_availability"}  # read-only. book_visit is deliberately NOT here.
MAX_TOOL_CALLS = 2                      # per visitor question
MAX_MODEL_CALLS = 3                     # per visitor question (stops endless loops)


def check(tool_name: str, tool_calls_so_far: int) -> str | None:
    """Return None if the call is allowed, otherwise the reason it is blocked."""
    if tool_name not in ALLOWED_TOOLS:
        return f"blocked: '{tool_name}' is not in ALLOWED_TOOLS"
    if tool_calls_so_far >= MAX_TOOL_CALLS:
        return f"blocked: more than {MAX_TOOL_CALLS} tool calls"
    return None
