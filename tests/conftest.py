"""
Provides reusable pytest fixtures for MongoDB, repository, message data
and mock connections used across tests.
"""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from db.config import MongoDB
from db.mongo_services import MessageRepository


@pytest.fixture
def mock_mongo_db():
    """Creates a MongoDB instance."""
    return MongoDB("test_url")


@pytest.fixture
def mock_collection():
    """Creates a mock asynchronous MongoDB collection."""
    return AsyncMock()


@pytest.fixture
def mock_repo(mock_collection):
    """Creates a MessageRepository instance bounded to the mocked collection."""
    return MessageRepository(mock_collection)


@pytest.fixture
def mock_data():
    """Creates a mock message like object with token, status and attempts."""
    obj = MagicMock()
    obj.model_dump.return_value = {"_id": "fake_id"}
    obj._id = "fake_id"
    obj.id = "fake_id"
    obj.token = "fake_token"
    obj.status = "fake_status"
    return obj


@pytest.fixture
def mock_incoming_data():
    """Creates serialized incoming message data."""
    return json.dumps({
        "subject": "reset password",
        "body": "click the link",
        "email": "user@example.com",
        "token": "fake_token",
        "datetime": "2026-06-04T10:00:00"
    })

@pytest.fixture
def mock_connection():
    """Creates a mock asynchronous connection object."""
    connection = AsyncMock()
    return connection


@pytest.fixture
def mock_mongo():
    """Creates a mock client."""
    mongo = AsyncMock()
    return mongo