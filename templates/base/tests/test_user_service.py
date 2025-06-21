import pytest
from unittest.mock import MagicMock

from server.services.user.service import UserService
from server.exceptions.user import UserNotFoundException, UserRoleNotAllowedException, UserWithEmailAlreadyExistsException


@pytest.mark.asyncio
async def test_get_user_success(mock_user_dao, sample_user):
    # Create an instance of UserService with the mocked DAO
    user_service = UserService(user_dao=mock_user_dao)

    # Mock the DAO's `get_user_by_id` method
    mock_user_dao.get_user_by_id.return_value = sample_user

    # Mock `_check_user_permission` to prevent any side effects
    user_service._check_user_permission = MagicMock()

    # Call the service method
    result = await user_service.get_user(user_id="123", current_user=sample_user)

    # Assert the result
    assert result == sample_user
    mock_user_dao.get_user_by_id.assert_called_once_with("123")
    user_service._check_user_permission.assert_called_once_with("123", sample_user)

@pytest.mark.asyncio
async def test_get_users_success(mock_user_dao, admin_user, sample_user):
    # Create an instance of UserService with the mocked DAO
    user_service = UserService(user_dao=mock_user_dao)

    # Mock the DAO's `get_users` method
    mock_user_dao.get_users.return_value = [sample_user]

    # Mock `_check_user_permission` to prevent any side effects
    user_service._require_admin = MagicMock()
    
    # Call the service method with an admin user
    result = await user_service.get_users(current_user=admin_user)

    # Assert the result
    assert result == [sample_user]
    mock_user_dao.get_users.assert_called_once()
    user_service._require_admin.assert_called_once_with(admin_user)

@pytest.mark.asyncio
async def test_get_users_non_admin_raises_exception(mock_user_dao, sample_user):
    # Create an instance of UserService with the mocked DAO
    user_service = UserService(user_dao=mock_user_dao)

    # Call the service method with a non-admin user and expect an exception
    with pytest.raises(UserRoleNotAllowedException):
        await user_service.get_users(current_user=sample_user)

@pytest.mark.asyncio
async def test_create_user_success(mock_user_dao, sample_user_create_request, sample_user):
    # Create an instance of UserService with the mocked DAO
    user_service = UserService(user_dao=mock_user_dao)

    # Mock the DAO's `get_user_by_email` method to simulate email not found
    mock_user_dao.get_user_by_email.side_effect = UserNotFoundException()

    # Mock the DAO's `insert_user` method
    mock_user_dao.insert_user.return_value = sample_user

    # Call the service method
    result = await user_service.create_user(user_data=sample_user_create_request)

    # Assert the result
    assert result == sample_user
    mock_user_dao.get_user_by_email.assert_called_once_with(sample_user_create_request.email)
    mock_user_dao.insert_user.assert_called_once_with(sample_user_create_request)


@pytest.mark.asyncio
async def test_create_user_email_already_exists(mock_user_dao, sample_user_create_request, sample_user):
    # Create an instance of UserService with the mocked DAO
    user_service = UserService(user_dao=mock_user_dao)

    # Mock the DAO's `get_user_by_email` method to simulate email already exists
    mock_user_dao.get_user_by_email.return_value = sample_user

    # Call the service method and expect an exception
    with pytest.raises(UserWithEmailAlreadyExistsException):
        await user_service.create_user(user_data=sample_user_create_request)



@pytest.mark.asyncio
async def test_update_user_success(mock_user_dao, sample_user_update_request, sample_user):
    # Create an instance of UserService with the mocked DAO
    user_service = UserService(user_dao=mock_user_dao)

    # Mock the DAO's `update_user` method
    mock_user_dao.update_user.return_value = sample_user

    # Call the service method
    result = await user_service.update_user(user_id="123", user_data=sample_user_update_request, current_user=sample_user)

    # Assert the result
    assert result == sample_user
    mock_user_dao.update_user.assert_called_once_with("123", sample_user_update_request)


@pytest.mark.asyncio
async def test_update_user_no_permission_raises_exception(mock_user_dao, sample_user_update_request):
    # Create an instance of UserService with the mocked DAO
    user_service = UserService(user_dao=mock_user_dao)

    # Simulate a different user
    other_user = MagicMock(id="456", role="user")

    # Call the service method and expect an exception
    with pytest.raises(UserRoleNotAllowedException):
        await user_service.update_user(user_id="123", user_data=sample_user_update_request, current_user=other_user)



@pytest.mark.asyncio
async def test_delete_user_success(mock_user_dao, sample_user):
    # Create an instance of UserService with the mocked DAO
    user_service = UserService(user_dao=mock_user_dao)

    # Call the service method
    await user_service.delete_user(user_id="123", current_user=sample_user)

    # Assert the DAO's `delete_user` method was called
    mock_user_dao.delete_user.assert_called_once_with("123")


@pytest.mark.asyncio
async def test_delete_user_no_permission_raises_exception(mock_user_dao):
    # Create an instance of UserService with the mocked DAO
    user_service = UserService(user_dao=mock_user_dao)

    # Simulate a different user
    other_user = MagicMock(id="456", role="user")

    # Call the service method and expect an exception
    with pytest.raises(UserRoleNotAllowedException):
        await user_service.delete_user(user_id="123", current_user=other_user)
