"""FastAPI dependencies: database session, settings, researcher authorization."""

from __future__ import annotations

import hmac
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from .config import Settings
from .db import Database


def get_database(request: Request) -> Database:
    database: Database = request.app.state.database
    return database


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_db(request: Request) -> Iterator[Session]:
    database: Database = request.app.state.database
    yield from database.session()


def require_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Guard researcher-only endpoints when ``AGENTPAUSE_ADMIN_TOKEN`` is configured.

    Without a token configured (local, single-researcher use), everything is open. Set a token
    before exposing the server to study participants.
    """
    if settings.admin_token is None:
        return
    expected = f"Bearer {settings.admin_token}"
    if authorization is None or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Researcher token required", headers={"WWW-Authenticate": "Bearer"})


DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]
Admin = Depends(require_admin)
