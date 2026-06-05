"""Provides tests for simple CRUD operations and errors handling in the MessageRepository."""
import pytest


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
    mock_collection.insert_one.assert_called_once_with({"token": "fake_token"})


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
        with pytest.raises(Exception) as e:
            await mock_repo.save_doc(mock_data)

    # Assert
    assert "Failed to save message with token=fake_token" in caplog.text
    mock_collection.insert_one.assert_called_once_with({"token": "fake_token"})


@pytest.mark.asyncio
async def test_delete_doc_success(
        mock_collection,
        mock_repo,
        mock_data
):
    """Tests that deleting a document succeeds from the database collection."""
    # Act
    await mock_repo.delete_doc(mock_data.token)

    # Assert
    mock_collection.delete_one.assert_called_once_with({"token": "fake_token"})


@pytest.mark.asyncio
async def test_delete_doc_fail(
        mock_collection,
        mock_repo,
        mock_data,
        caplog
):
    """Tests that deleting a document fails and raises error."""
    # Arrange
    mock_collection.delete_one.side_effect = Exception()

    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception) as e:
            await mock_repo.delete_doc(mock_data.token)

    # Assert
    assert "Failed to delete message with token=fake_token" in caplog.text
    mock_collection.delete_one.assert_called_once_with({"token": "fake_token"})


@pytest.mark.asyncio
async def test_increase_attempts_success(
        mock_collection,
        mock_repo,
        mock_data
):
    """Tests that increasing message sending attempts succeeds."""
    # Act
    await mock_repo.increase_attempts(mock_data.token)

    # Assert
    mock_collection.update_one.assert_called_once_with({"token": "fake_token"}, {"$inc": {"attempts": 1}})


@pytest.mark.asyncio
async def test_increase_attempts_fail(
        mock_collection,
        mock_repo,
        mock_data,
        caplog
):
    """Tests that increasing message sending attempts fails and raises error."""
    # Arrange
    mock_collection.update_one.side_effect = Exception()

    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception) as e:
            await mock_repo.increase_attempts(mock_data.token)

    # Assert
    assert "Failed to increase message attempts with token=fake_token" in caplog.text
    mock_collection.update_one.assert_called_once_with({"token": "fake_token"}, {"$inc": {"attempts": 1}})


@pytest.mark.asyncio
async def test_get_doc_success(
        mock_collection,
        mock_repo,
        mock_data
):
    """Tests that getting a document from the database collection succeeds."""
    # Act
    await mock_repo.get_doc(mock_data.token)

    # Assert
    mock_collection.find_one.assert_called_once_with({"token": "fake_token"})


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
        with pytest.raises(Exception) as e:
            await mock_repo.get_doc(mock_data.token)

    # Assert
    assert "Failed to find message with token=fake_token" in caplog.text
    mock_collection.find_one.assert_called_once_with({"token": "fake_token"})


@pytest.mark.asyncio
async def test_update_status_doc_success(
        mock_collection,
        mock_repo,
        mock_data
):
    """Tests that updating message status succeeds."""
    # Act
    await mock_repo.update_status_doc(mock_data.token, mock_data.status)

    # Assert
    mock_collection.find_one_and_update.assert_called_once_with({"token": "fake_token"}, {"$set": {"status": "fake_status"}})


@pytest.mark.asyncio
async def test_update_status_doc_fail(
        mock_collection,
        mock_repo,
        mock_data,
        caplog
):
    """Tests that updating message status fails and raises error."""
    # Arrange
    mock_collection.find_one_and_update.side_effect = Exception()

    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception) as e:
            await mock_repo.update_status_doc(mock_data.token, mock_data.status)

    # Assert
    assert "Failed to update message status with token=fake_token" in caplog.text
    mock_collection.find_one_and_update.assert_called_once_with({"token": "fake_token"}, {"$set": {"status": "fake_status"}})