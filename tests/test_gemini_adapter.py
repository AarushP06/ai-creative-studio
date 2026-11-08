"""The real Gemini adapter, tested OFFLINE.

We plug a fake HTTP transport into the official google-genai SDK. The SDK code
runs for real — it builds the request and parses the response — but nothing
leaves your computer and no key is needed.
"""
import json

import httpx
import pytest

from app import generators
from app.generators import GeminiCardGenerator, GenerationError, classify_error
from tests.conftest import VALID_CARD, make_settings


def gemini_reply(text: str) -> dict:
    """The shape of a successful Interactions API response."""
    return {
        "id": "v1_test",
        "status": "completed",
        "steps": [{"type": "model_output", "content": [{"type": "text", "text": text}]}],
    }


def fake_gemini(status: int, body: dict, seen: list):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_successful_call_returns_raw_json_text():
    seen = []
    gen = GeminiCardGenerator(make_settings(), http_client=fake_gemini(200, gemini_reply(json.dumps(VALID_CARD)), seen))
    assert json.loads(gen.generate("Name: Test Café")) == VALID_CARD

    sent = json.loads(seen[0].content)
    assert sent["model"] == "gemini-test-model"
    assert sent["response_format"]["mime_type"] == "application/json"
    assert sent["store"] is False
    assert "<business_brief>" in sent["input"]          # brief is wrapped as data
    assert "test-key-not-real" not in sent["input"]     # the key never goes in the prompt


def test_rate_limit_retries_once_then_fails(monkeypatch):
    monkeypatch.setattr(generators.time, "sleep", lambda s: None)
    seen = []
    body = {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}}
    gen = GeminiCardGenerator(make_settings(), http_client=fake_gemini(429, body, seen))
    with pytest.raises(GenerationError) as err:
        gen.generate("Name: Test Café")
    assert err.value.kind == "rate_limit"
    assert len(seen) == 2


@pytest.mark.parametrize("status, kind", [(403, "bad_key"), (500, "server")])
def test_http_errors_are_classified(status, kind):
    body = {"error": {"code": status, "message": "x", "status": "X"}}
    gen = GeminiCardGenerator(make_settings(), http_client=fake_gemini(status, body, []))
    with pytest.raises(GenerationError) as err:
        gen.generate("Name: Test Café")
    assert err.value.kind == kind


def test_empty_model_output_is_an_error():
    gen = GeminiCardGenerator(make_settings(), http_client=fake_gemini(200, gemini_reply(""), []))
    with pytest.raises(GenerationError) as err:
        gen.generate("Name: Test Café")
    assert err.value.kind == "empty"


def test_classify_timeout_by_exception_name():
    class APITimeoutError(Exception):
        pass

    assert classify_error(APITimeoutError()) == "timeout"
