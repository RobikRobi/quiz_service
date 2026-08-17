import os
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault(
    "QUIZ_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/qrcard_quizzes",
)

from app.db import get_session
from app.main import app


async def override_get_session() -> AsyncIterator[object]:
    yield object()


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
