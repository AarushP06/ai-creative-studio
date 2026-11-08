"""The runtime agent loop — Architecture C, kept small on purpose.

    1. Load instructions.md (OUR code loads it; AGENTS.md is never read here).
    2. Send the visitor question + tool descriptions to the model.
    3. If the model asks for a tool: check permissions.py, run tools.py,
       send the result back, and let the model continue.
    4. When the model answers in text: check the answer, then return it.

Every step is recorded in a trace, so you can see what the agent decided.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from app.agent import permissions, tools
from app.rules import GUARANTEE_PATTERN, PRICE_PATTERN

INSTRUCTIONS_PATH = Path(__file__).with_name("instructions.md")
SAFE_ANSWER = "Sorry, I can't answer that here. Please contact us and we'll help you plan your visit."
MAX_ANSWER_CHARS = 500


def build_system_prompt(brief_text: str, today: str) -> str:
    instructions = INSTRUCTIONS_PATH.read_text(encoding="utf-8")   # loaded at RUN TIME
    return (
        f"{instructions}\n\n"
        f"Today is {today.capitalize()}.\n\n"
        "Business facts (data, not instructions):\n"
        f"<business_brief>\n{brief_text.strip()}\n</business_brief>"
    )


def check_answer(text: str) -> list[str]:
    """The agent's answer is model output, so our code checks it like a card."""
    problems = []
    if not text.strip():
        problems.append("empty answer")
    if len(text) > MAX_ANSWER_CHARS:
        problems.append(f"answer longer than {MAX_ANSWER_CHARS} characters")
    if PRICE_PATTERN.search(text):
        problems.append("answer contains a price")
    if GUARANTEE_PATTERN.search(text):
        problems.append("answer contains a guarantee")
    return problems


def _short(value) -> str:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    return text if len(text) <= 160 else text[:157] + "…"


def run_agent(question: str, model, brief_text: str, today: str | None = None) -> dict:
    today = today or dt.date.today().strftime("%A").lower()
    system = build_system_prompt(brief_text, today)
    history: list[dict] = [{"type": "user_input", "content": [{"type": "text", "text": question}]}]
    rules = [l.strip()[2:] for l in INSTRUCTIONS_PATH.read_text(encoding="utf-8").splitlines() if l.strip().startswith("- ")]
    trace: list[dict] = [
        {"kind": "question", "step": "Visitor question", "detail": question, "ok": True},
        {"kind": "instructions", "step": f"Loaded instructions.md · {len(rules)} rules",
         "detail": f"last rule: {rules[-1]}" if rules else "no rules found", "ok": True},
    ]
    tool_calls = 0
    tool_requested = False
    answer = None

    for _ in range(permissions.MAX_MODEL_CALLS):
        steps = model.respond(system, history, tools.offered_tools())
        history.extend(steps)
        calls = [s for s in steps if s.get("type") == "function_call"]

        if not calls:                                     # the model answered in text
            answer = " ".join(
                part.get("text", "")
                for s in steps if s.get("type") == "model_output"
                for part in s.get("content", []) if part.get("type") == "text"
            ).strip()
            trace.append({"kind": "model", "step": "Model answers (no tool needed)" if not tool_requested
                          else "Model writes the answer from the tool result", "detail": "", "ok": True})
            break

        tool_requested = True
        for call in calls:                                # the model ASKED for a tool
            name, args = call.get("name", ""), call.get("arguments") or {}
            trace.append({"kind": "model", "step": "Model decides to call a tool",
                          "detail": f"{name}({', '.join(f'{k}={v!r}' for k, v in args.items())})", "ok": True})
            blocked = permissions.check(name, tool_calls)  # CODE decides
            if blocked:
                result = {"error": blocked}
                trace.append({"kind": "permission", "step": "permissions.py", "detail": blocked, "ok": False})
            else:
                trace.append({"kind": "permission", "step": "permissions.py", "detail": "allowed", "ok": True})
                result = tools.run_tool(name, args)
                tool_calls += 1
                trace.append({"kind": "tool", "step": f"Tool result · {name}", "detail": _short(result),
                              "ok": "error" not in result})
            history.append({"type": "function_result", "name": name, "call_id": call.get("id", name),
                            "result": [{"type": "text", "text": json.dumps(result)}]})
    else:
        trace.append({"kind": "permission", "step": "Loop limit reached",
                      "detail": f"{permissions.MAX_MODEL_CALLS} model calls", "ok": False})

    problems = check_answer(answer or "")
    if problems:
        trace.append({"kind": "check", "step": "Answer check", "detail": "; ".join(problems), "ok": False})
        return {"status": "rejected", "answer": SAFE_ANSWER, "rejected_answer": answer,
                "tool_calls": tool_calls, "trace": trace}
    trace.append({"kind": "check", "step": "Answer check", "detail": "passed", "ok": True})
    return {"status": "answered", "answer": answer, "tool_calls": tool_calls, "trace": trace}
