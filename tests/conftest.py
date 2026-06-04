import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from db.config import MongoDB
from db.mongo_services import MessageRepository


@pytest.fixture
def mock_mongo_db():
    return MongoDB("test_url")


@pytest.fixture
def mock_collection():
    return AsyncMock()


@pytest.fixture
def mock_repo(mock_collection):
    return MessageRepository(mock_collection)


@pytest.fixture
def mock_data():
    obj = MagicMock()
    obj.model_dump.return_value = {"token": "fake_token"}
    obj.token = "fake_token"
    obj.attempts = 0
    obj.status = "fake_status"
    return obj


@pytest.fixture
def mock_incoming_data():
    return json.dumps({
        "subject": "reset password",
        "body": "click the link",
        "email": "user@example.com",
        "token": "fake_token",
        "datetime": "2026-06-04T10:00:00"
    })

@pytest.fixture
def mock_connection():
    connection = AsyncMock()
    return connection

#
# class AsyncIteratorCM:
#     def __init__(self, items):
#         self.items = items
#
#     async def __aenter__(self):
#         return self
#
#     async def __aexit__(self, exc_type, exc, tb):
#         pass
#
#     def __aiter__(self):
#         return self._aiter()
#
#     async def _aiter(self):
#         for item in self.items:
#             yield item
#
#
# @pytest.fixture
# def mock_iterator():
#     def _mock_iterator(items):
#         return AsyncIteratorCM(items)
#     return _mock_iterator