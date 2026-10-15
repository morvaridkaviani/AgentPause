from __future__ import annotations

from collections.abc import Iterator

import pytest
from api_helpers import make_client
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    with make_client() as c:
        yield c


@pytest.fixture
def secured() -> Iterator[TestClient]:
    with make_client(admin_token="s3cret") as c:
        yield c
