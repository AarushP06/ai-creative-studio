"""The running application: FastAPI routes, fallbacks and limits (Gemini is faked)."""
from app.generators import GenerationError
from tests.conftest import VALID_CARD, FakeGenerator, card, make_settings, raw


def test_status_reports_mode_but_never_the_key(make_client):
    client = make_client(make_settings(gemini_api_key="AIzaSECRET123"))
    body = client.get("/api/status").text
    assert '"mode":"live"' in body
    assert "AIzaSECRET123" not in body


def test_no_key_means_mock_mode(make_client):
    client = make_client(make_settings(gemini_api_key=""))
    assert client.get("/api/status").json()["mode"] == "mock"
    data = client.post("/api/service-card", json={}).json()
    assert data["status"] == "accepted" and data["source"] == "mock"
    assert data["reason"] == "no_key" and data["card"]


def test_valid_live_response_is_shown(make_client):
    fake = FakeGenerator([raw(VALID_CARD)])
    data = make_client(live=fake).post("/api/service-card", json={}).json()
    assert data["status"] == "accepted" and data["source"] == "live"
    assert data["card"]["title"] == VALID_CARD["title"]


def test_invalid_live_response_is_rejected_and_replaced_by_mock(make_client):
    fake = FakeGenerator([raw(card(title="Guaranteed best coffee in town"))])
    data = make_client(live=fake).post("/api/service-card", json={}).json()
    assert data["status"] == "rejected" and data["card"] is None
    assert data["fallback"]["source"] == "mock" and data["fallback"]["card"]


def test_api_failure_falls_back_to_mock(make_client):
    fake = FakeGenerator(error=GenerationError("rate_limit", "429"))
    data = make_client(live=fake).post("/api/service-card", json={}).json()
    assert data["status"] == "accepted" and data["source"] == "mock"
    assert data["reason"] == "rate_limit"


def test_cooldown_is_per_session_not_global(make_client):
    fake = FakeGenerator([raw(VALID_CARD)] * 3)
    client = make_client(make_settings(cooldown_seconds=60), live=fake)
    first = client.post("/api/service-card", json={}).json()
    second = client.post("/api/service-card", json={}).json()   # same browser cookie
    assert first["source"] == "live"
    assert second["source"] == "mock" and second["reason"] == "cooldown"
    client.cookies.clear()                                       # a different visitor
    third = client.post("/api/service-card", json={}).json()
    assert third["source"] == "live"


def test_simulation_goes_through_the_same_validator(make_client):
    data = make_client().post("/api/service-card", json={"simulate": "unknown-image"}).json()
    assert data["status"] == "rejected" and data["source"] == "simulated"


def test_unknown_simulation_or_brief_is_404(make_client):
    client = make_client()
    assert client.post("/api/service-card", json={"simulate": "nope"}).status_code == 404
    assert client.post("/api/service-card", json={"brief": "nope"}).status_code == 404


def test_website_and_static_files_are_served(make_client):
    client = make_client()
    assert "Generate a service card" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
