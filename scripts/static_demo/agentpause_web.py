"""Run the AgentPause REST API inside the browser (Pyodide / WebAssembly).

Used by the online demo on GitHub Pages. The real FastAPI app from ``backend/app`` runs
unchanged in a Web Worker, with an in-memory SQLite database. Requests from the web app are
passed to it as ASGI calls instead of going over the network, so nothing leaves the browser.

Browsers cannot start threads, so the two places that would use one are adapted here:
FastAPI's thread pool for synchronous endpoints, and the background experiment runner
(see ``ExperimentService.create``, which runs inline on ``sys.platform == "emscripten"``).
"""

from __future__ import annotations

import json
from typing import Any

import anyio.to_thread


async def _run_sync_inline(
    func: Any, *args: Any, abandon_on_cancel: bool = False, cancellable: Any = None, limiter: Any = None
) -> Any:
    return func(*args)


anyio.to_thread.run_sync = _run_sync_inline  # type: ignore[assignment]

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

app = create_app(
    Settings(
        database_url="sqlite:///:memory:",
        environment="browser-demo",
        max_experiment_episodes=3000,
        max_compare_episodes=1200,
    )
)


async def handle(method: str, path: str, query: str, body: str | None) -> str:
    """Call the API like an HTTP client would and return ``{status, contentType, body}`` as JSON."""
    payload = (body or "").encode("utf-8")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": query.encode("utf-8"),
        "root_path": "",
        "headers": [
            (b"host", b"browser"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(payload)).encode()),
        ],
        "client": ("127.0.0.1", 0),
        "server": ("browser", 80),
    }
    delivered = False

    async def receive() -> dict[str, Any]:
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": payload, "more_body": False}
        return {"type": "http.disconnect"}

    status = 500
    content_type = "application/json"
    chunks: list[bytes] = []

    async def send(message: dict[str, Any]) -> None:
        nonlocal status, content_type
        if message["type"] == "http.response.start":
            status = int(message["status"])
            for key, value in message.get("headers", []):
                if key.lower() == b"content-type":
                    content_type = value.decode("latin-1")
        elif message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))

    await app(scope, receive, send)
    return json.dumps({"status": status, "contentType": content_type, "body": b"".join(chunks).decode("utf-8")})
