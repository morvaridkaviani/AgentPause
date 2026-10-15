"""Settings, read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./data/agentpause.db"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3100"])
    admin_token: str | None = None
    """If set, researcher endpoints (exports, study configuration, deletion) require
    ``Authorization: Bearer <token>``. Leave unset for local, single-user use."""
    max_experiment_episodes: int = 20000
    max_compare_episodes: int = 3000
    instruments_local_dir: str | None = None
    """Folder with locally supplied questionnaire item text for instruments that cannot be
    redistributed (e.g. SUS). See docs/experiments.md."""
    environment: str = "development"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            database_url=os.environ.get("DATABASE_URL", cls.database_url),
            cors_origins=_list(os.environ.get("CORS_ORIGINS"), ["http://localhost:3100"]),
            admin_token=os.environ.get("AGENTPAUSE_ADMIN_TOKEN") or None,
            max_experiment_episodes=int(os.environ.get("MAX_EXPERIMENT_EPISODES", "20000")),
            max_compare_episodes=int(os.environ.get("MAX_COMPARE_EPISODES", "3000")),
            instruments_local_dir=os.environ.get("INSTRUMENTS_LOCAL_DIR") or None,
            environment=os.environ.get("AGENTPAUSE_ENV", "development"),
        )

    def ensure_sqlite_dir(self) -> None:
        if self.database_url.startswith("sqlite:///") and ":memory:" not in self.database_url:
            path = Path(self.database_url.removeprefix("sqlite:///"))
            path.parent.mkdir(parents=True, exist_ok=True)
