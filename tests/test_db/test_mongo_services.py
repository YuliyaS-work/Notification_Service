import pytest


@pytest.mark.asyncio
async def test_save_doc_success(
        mock_collection,
        mock_repo,
        mock_data
):
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
    # Arrange
    mock_collection.find_one_and_update.side_effect = Exception()

    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception) as e:
            await mock_repo.update_status_doc(mock_data.token, mock_data.status)

    # Assert
    assert "Failed to update message status with token=fake_token" in caplog.text
    mock_collection.find_one_and_update.assert_called_once_with({"token": "fake_token"}, {"$set": {"status": "fake_status"}})
