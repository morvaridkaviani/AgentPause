"""Helpers shared by the backend API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(**overrides: object) -> TestClient:
    settings = Settings(database_url="sqlite:///:memory:", **overrides)  # type: ignore[arg-type]
    return TestClient(create_app(settings))


def drive(client: TestClient, session_id: str, *, respond: str = "approve", max_iter: int = 60) -> dict:
    """Play a demo session to the end, answering every card the same way."""
    for _ in range(max_iter):
        session = client.get(f"/api/v1/session/{session_id}").json()
        if session["status"] in ("completed", "cancelled"):
            return session
        if session["pending"]:
            allowed = session["pending"]["allowed_responses"]
            choice = respond if respond in allowed else ("answer" if "answer" in allowed else "takeover")
            r = client.post("/api/v1/intervention", json={"session_id": session_id, "response": choice})
            assert r.status_code == 200, r.text
        else:
            r = client.post(f"/api/v1/session/{session_id}/step", json={"until": "intervention"})
            assert r.status_code == 200, r.text
    raise AssertionError("session did not finish")
