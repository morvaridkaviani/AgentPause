"""FastAPI application factory.

Run locally::

    uvicorn app.main:app --reload --app-dir backend

OpenAPI docs: http://localhost:8000/docs (Swagger) and /redoc.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import agentpause

from .config import Settings
from .db import Database
from .routers import evaluate, meta, research, sessions, study

DESCRIPTION = """
**AgentPause**: research infrastructure for studying *when* an AI agent should continue,
clarify, ask, defer, or stop.

* Every agent action in this API's scenarios is **simulated**. Nothing sends email, spends
  money, or deletes files.
* Results produced by `/experiments` and `/compare` are **simulated** and not evaluated with
  human participants.
* Send action *metadata* only. Never send passwords, tokens, or private message content.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    database = Database(settings)
    database.create_all()

    app = FastAPI(
        title="AgentPause API",
        version=agentpause.__version__,
        description=DESCRIPTION,
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        license_info={"name": "MIT"},
    )
    app.state.settings = settings
    app.state.database = database
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for module in (meta, evaluate, sessions, research, study):
        app.include_router(module.router, prefix="/api/v1")
    return app


_app: FastAPI | None = None


def __getattr__(name: str) -> FastAPI:
    """Create the default app lazily, so importing this module has no side effects
    (``uvicorn app.main:app`` still works)."""
    global _app
    if name == "app":
        if _app is None:
            _app = create_app()
        return _app
    raise AttributeError(name)
