"""Provides tests for simple CRUD operations and errors handling in the MessageRepository."""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from pymongo import IndexModel, ASCENDING

fixed_time = datetime(2026, 6, 22, 18, 27, 43, tzinfo=timezone.utc)

@pytest.mark.asyncio
async def test_make_indexes_success(mock_collection, mock_repo, caplog):
    """Tests that indexes are created successfully."""
    # Act
    with caplog.at_level("INFO"):
        await mock_repo.make_indexes()

    # Assert
    expected_indexes = [
        IndexModel([("email", ASCENDING)], name="idx_email"),
        IndexModel([("published_at", ASCENDING)], name="idx_published_at"),
        IndexModel(
            [("sent_at", ASCENDING)],
            name="idx_sent_at_ttl",
            expireAfterSeconds=2592000,
        ),
    ]

    mock_collection.create_indexes.assert_called_once()
    created_indexes = mock_collection.create_indexes.call_args[0][0]
    assert len(created_indexes) == len(expected_indexes)
    for created, expected in zip(created_indexes, expected_indexes):
        assert created.document == expected.document

    assert "MongoDB indexes created successfully" in caplog.text


@pytest.mark.asyncio
async def test_make_indexes_fail(mock_collection, mock_repo, caplog):
    """Tests that index creation failure is logged and raised."""
    # Arrange
    mock_collection.create_indexes.side_effect = Exception()

    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception):
            await mock_repo.make_indexes()

    # Assert
    assert "Failed to create indexes" in caplog.text
    mock_collection.create_indexes.assert_called_once()


@pytest.mark.asyncio
async def test_save_doc_success(
        mock_collection,
        mock_repo,
        mock_data
):
    """Tests that saving a document succeeds into the database collection."""
    # Act
    await mock_repo.save_doc(mock_data)

    # Assert
    mock_collection.insert_one.assert_called_once_with({"_id": "fake_id"}, session=None)


@pytest.mark.asyncio
async def test_save_doc_fail(
        mock_collection,
        mock_repo,
        mock_data,
        caplog
):
    """Tests that saving a document fails and raises error."""
    # Arrange
    mock_collection.insert_one.side_effect = Exception()

    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception):
            await mock_repo.save_doc(mock_data)

    # Assert
    assert "Failed to save message with message_id=fake_id" in caplog.text
    mock_collection.insert_one.assert_called_once_with({"_id": "fake_id"}, session=None)


@pytest.mark.asyncio
async def test_get_doc_success(
        mock_collection,
        mock_repo,
        mock_data
):
    """Tests that getting a document from the database collection succeeds."""
    # Act
    await mock_repo.get_doc(mock_data._id, session=None)

    # Assert
    mock_collection.find_one.assert_called_once_with({"_id": "fake_id"}, session=None)


@pytest.mark.asyncio
async def test_get_doc_not_found(
        mock_collection,
        mock_repo,
        mock_data,
        caplog
):
    """Tests that getting a document from the database collection succeeds."""
    # Act
    mock_collection.find_one.return_value = None

    with caplog.at_level("WARNING"):
        await mock_repo.get_doc(mock_data._id, session=None)

        # Assert
    assert "Message not found with message_id=fake_id" in caplog.text
    mock_collection.find_one.assert_called_once_with({"_id": "fake_id"}, session=None)


@pytest.mark.asyncio
async def test_get_doc_fail(
        mock_collection,
        mock_repo,
        mock_data,
        caplog
):
    """Tests that getting a document from the database collection fails and raises error."""
    # Arrange
    mock_collection.find_one.side_effect = Exception()

    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception):
            await mock_repo.get_doc(mock_data._id, session=None)

    # Assert
    assert "Failed to find message with message_id=fake_id" in caplog.text
    mock_collection.find_one.assert_called_once_with({"_id": "fake_id"}, session=None)


@pytest.mark.asyncio
@patch("db.mongo_services.datetime")
async def test_update_status_doc_success(
        mock_datetime,
        mock_collection,
        mock_repo,
        mock_data
):
    """Tests that updating message status succeeds."""
    # Arrange
    mock_datetime.now.return_value = fixed_time
    mock_datetime.timezone = timezone

    # Act
    await mock_repo.update_status_doc(mock_data._id, mock_data.status, session=None)

    # Assert
    mock_collection.find_one_and_update.assert_called_once_with({"_id": "fake_id"}, {"$set": {"status": "fake_status", "sent_at": fixed_time}}, session=None)


@pytest.mark.asyncio
@patch("db.mongo_services.datetime")
async def test_update_status_doc_fail(
        mock_datetime,
        mock_collection,
        mock_repo,
        mock_data,
        caplog
):
    """Tests that updating message status fails and raises error."""
    # Arrange
    mock_datetime.now.return_value = fixed_time
    mock_datetime.timezone = timezone
    mock_collection.find_one_and_update.side_effect = Exception()

    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception):
            await mock_repo.update_status_doc(mock_data._id, mock_data.status)

    # Assert
    assert "Failed to update message status with message_id=fake_id" in caplog.text
    mock_collection.find_one_and_update.assert_called_once_with({"_id": "fake_id"}, {"$set": {"status": "fake_status", "sent_at": fixed_time}}, session=None)