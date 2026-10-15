from __future__ import annotations

import pytest

from agentpause import SessionState


@pytest.fixture
def state() -> SessionState:
    return SessionState()
