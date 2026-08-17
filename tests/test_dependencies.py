import asyncio
import uuid

from fastapi import HTTPException
import pytest

from app.dependencies import get_current_user_id


def test_get_current_user_id_returns_uuid():
    user_id = uuid.uuid4()

    result = asyncio.run(get_current_user_id(str(user_id)))

    assert result == user_id


def test_get_current_user_id_requires_header():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user_id(None))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "X-User-Id header is required"


def test_get_current_user_id_rejects_invalid_uuid():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user_id("not-a-uuid"))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "X-User-Id must be a valid UUID"
