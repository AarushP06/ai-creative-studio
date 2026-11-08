"""The runtime agent (Architecture C), tested OFFLINE.

A scripted fake model plays Gemini. permissions.py and tools.py run for real,
so these tests prove what CODE allows — whatever the model asks for.
"""
import json

import httpx
from fastapi.testclient import TestClient

from app.agent import permissions, tools
from app.agent.agent import SAFE_ANSWER, build_system_prompt, run_agent
from app.agent.models import GeminiAgentModel, MockAgentModel
from app.agent.service import VisitAssistant
from app.generators import GenerationError
from app.main import create_app
from tests.conftest import ROOT, make_settings

BRIEF = "Name: Test Bike Lab\nOffer: Tune-ups and flat-tyre fixes.\n"


def call(name, **args):
    return {"type": "function_call", "id": f"c-{name}", "name": name, "arguments": args}


def say(text):
    return {"type": "model_output", "content": [{"type": "text", "text": text}]}


class ScriptedModel:
    """Returns the next scripted list of steps on each call and records what it was sent."""

    name = "live"

    def __init__(self, *turns, error=None):
        self.turns = list(turns)
        self.error = error
        self.seen = []

    def respond(self, system, history, tools_offered):
        self.seen.append({"system": system, "history": list(history), "tools": tools_offered})
        if self.error:
            raise self.error
        return self.turns.pop(0) if self.turns else [call("check_availability", day="monday")]


def test_model_decides_to_call_the_tool_and_answers_from_its_result():
    model = ScriptedModel([call("check_availability", day="thursday")], [say("Yes! Thursday at 14:00 or 16:30.")])
    result = run_agent("Are you free on Thursday?", model, BRIEF, today="monday")
    assert result["status"] == "answered" and result["tool_calls"] == 1
    sent_back = model.seen[1]["history"][-1]
    assert sent_back["type"] == "function_result" and sent_back["call_id"] == "c-check_availability"
    assert "14:00" in sent_back["result"][0]["text"]          # the real data reached the model


def test_no_tool_call_when_the_model_does_not_need_one():
    result = run_agent("Hi!", ScriptedModel([say("Hi! How can I help?")]), BRIEF)
    assert result["tool_calls"] == 0 and result["answer"] == "Hi! How can I help?"


def test_permissions_block_a_tool_the_model_asks_for():
    """Instructions ask; code enforces. book_visit is never run, even if the model wants it."""
    model = ScriptedModel([call("book_visit", day="thursday", time="14:00")], [say("Please call us to book.")])
    result = run_agent("Book me Thursday at 14:00", model, BRIEF)
    assert result["tool_calls"] == 0
    assert any(s["kind"] == "permission" and not s["ok"] for s in result["trace"])
    assert "not in ALLOWED_TOOLS" in model.seen[1]["history"][-1]["result"][0]["text"]


def test_tool_and_model_call_limits_stop_a_runaway_loop():
    model = ScriptedModel()  # asks for a tool forever
    result = run_agent("Free times?", model, BRIEF)
    assert result["tool_calls"] == permissions.MAX_TOOL_CALLS
    assert len(model.seen) == permissions.MAX_MODEL_CALLS
    assert result["status"] == "rejected" and result["answer"] == SAFE_ANSWER


def test_answer_with_a_price_is_replaced_by_a_safe_answer():
    result = run_agent("How much?", ScriptedModel([say("A tune-up is only $19!")]), BRIEF)
    assert result["status"] == "rejected" and result["answer"] == SAFE_ANSWER
    assert "price" in result["trace"][-1]["detail"]


def test_level_1_agent_may_only_use_read_only_tools():
    assert permissions.ALLOWED_TOOLS == {"check_availability"}
    assert "book_visit" not in [t["name"] for t in tools.offered_tools()]  # unless OFFER_BOOKING_TOOL


def test_check_availability_reads_the_data_file():
    data = json.loads((ROOT / "data" / "availability.json").read_text(encoding="utf-8"))
    assert tools.check_availability("Thursday")["free_times"] == data["thursday"]
    assert "error" in tools.check_availability("someday")


def test_instructions_are_loaded_from_instructions_md_not_agents_md():
    prompt = build_system_prompt(BRIEF, "monday")
    assert (ROOT / "app" / "agent" / "instructions.md").read_text(encoding="utf-8") in prompt
    assert "Never edit or commit on `main`" not in prompt          # AGENTS.md is for coding agents
    assert "<business_brief>" in prompt and "Today is Monday" in prompt


def test_mock_agent_uses_the_real_tool():
    result = run_agent("Are you free on Thursday?", MockAgentModel(BRIEF, "monday"), BRIEF, "monday")
    assert result["tool_calls"] == 1 and "14:00" in result["answer"]


def test_live_error_falls_back_to_the_mock_agent():
    assistant = VisitAssistant(make_settings(), live_model=ScriptedModel(error=GenerationError("rate_limit")), today="monday")
    result = assistant.ask("s1", "Are you free on Thursday?")
    assert result["source"] == "mock" and result["reason"] == "rate_limit" and "14:00" in result["answer"]


def test_ask_endpoint_in_mock_mode():
    settings = make_settings(gemini_api_key="")
    client = TestClient(create_app(settings=settings, assistant=VisitAssistant(settings, today="monday")))
    data = client.post("/api/ask", json={"question": "Are you free on Thursday?"}).json()
    assert data["source"] == "mock" and data["status"] == "answered"
    assert [s["kind"] for s in data["trace"]][:4] == ["question", "fallback", "instructions", "model"]
    assert client.post("/api/ask", json={"question": ""}).status_code == 422


def test_gemini_function_calling_round_trip_offline():
    """Real SDK code, fake transport: tool declared → function_call → function_result sent back."""
    seen = []
    replies = [
        {"id": "i1", "status": "requires_action",
         "steps": [{"type": "function_call", "id": "call_1", "name": "check_availability", "arguments": {"day": "thursday"}}]},
        {"id": "i2", "status": "completed", "steps": [say("Thursday at 14:00 or 16:30 works.")]},
    ]

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=replies[len(seen) - 1])

    model = GeminiAgentModel(make_settings(), http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = run_agent("Free on Thursday?", model, BRIEF, today="monday")
    assert result["answer"] == "Thursday at 14:00 or 16:30 works." and result["tool_calls"] == 1
    assert seen[0]["tools"][0]["name"] == "check_availability" and seen[0]["store"] is False
    assert seen[1]["input"][-1]["type"] == "function_result" and seen[1]["input"][-1]["call_id"] == "call_1"
    assert "test-key-not-real" not in json.dumps(seen)
