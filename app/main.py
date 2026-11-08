"""FastAPI application — the RUN-TIME side of the project.

Routes
  GET  /                      the website (static/index.html)
  GET  /api/status            live or mock mode (never returns the key)
  GET  /api/brief             business name, type, tagline for the page header
  GET  /api/simulations       names of the deliberately invalid test responses
  POST /api/service-card      generate → validate → return one card      (Architecture B)
  POST /api/ask               visitor question → runtime agent → answer   (Architecture C)
"""
from __future__ import annotations

import secrets

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agent.service import VisitAssistant

from app.brief import public_brief, read_brief_text
from app.config import STATIC_DIR, load_settings
from app.service import CardService, list_simulations

SESSION_COOKIE = "studio_session"


class CardRequest(BaseModel):
    simulate: str | None = None  # name of a deliberately invalid response
    brief: str = "main"  # "main" or "injected" (untrusted-input test)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=300)


def _session(request: Request, response: Response) -> str:
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        session_id = secrets.token_urlsafe(12)
        response.set_cookie(SESSION_COOKIE, session_id, httponly=True, samesite="lax")
    return session_id


def create_app(settings=None, service: CardService | None = None,
               assistant: VisitAssistant | None = None) -> FastAPI:
    if settings is None:
        load_dotenv()  # reads .env into environment variables (the key stays server-side)
        settings = load_settings()
    app = FastAPI(title="AI Creative Studio", docs_url="/api/docs", redoc_url=None)
    app.state.settings = settings
    app.state.service = service or CardService(settings)
    app.state.assistant = assistant or VisitAssistant(settings)

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/status")
    def status():
        s = app.state.settings
        mode = "live" if s.live_enabled else "mock"
        return {
            "mode": mode,
            "model": s.gemini_model if mode == "live" else None,
            "key_present": bool(s.gemini_api_key),
            "cooldown_seconds": s.cooldown_seconds,
        }

    @app.get("/api/brief")
    def brief():
        return public_brief(read_brief_text())

    @app.get("/api/simulations")
    def simulations():
        return {"simulations": list_simulations()}

    @app.post("/api/service-card")
    def service_card(body: CardRequest, request: Request, response: Response):
        session_id = _session(request, response)
        if body.simulate:
            try:
                return app.state.service.simulate(body.simulate)
            except KeyError:
                raise HTTPException(404, f"Unknown simulation: {body.simulate}")
        try:
            return app.state.service.create_card(session_id, brief=body.brief)
        except KeyError:
            raise HTTPException(404, f"Unknown brief: {body.brief}")

    @app.post("/api/ask")
    def ask(body: AskRequest, request: Request, response: Response):
        if not body.question.strip():
            raise HTTPException(422, "Empty question")
        return app.state.assistant.ask(_session(request, response), body.question)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
