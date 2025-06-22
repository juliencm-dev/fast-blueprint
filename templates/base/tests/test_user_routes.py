from datetime import datetime
from datetime import timezone
from unittest.mock import AsyncMock

import pytest
from server.config import settings as s
from server.db.user.schema import User
from server.db.user.schema import UserRole
from server.exceptions.user import UserRoleNotAllowedException
from server.models import UserResponse
from server.services.auth.dependencies import get_current_active_user
from server.services.user import get_user_service


@pytest.fixture
def admin_user_override(mock_current_user):
    return mock_current_user(email="admin@example.com", role=UserRole.ADMIN)


@pytest.mark.asyncio
async def test_get_users_as_admin(
    app, test_client, mock_user_service, admin_user_override, mock_access_token
):
    try:
        # Override the current user dependency
        app.dependency_overrides[get_current_active_user] = lambda: admin_user_override

        # Mock the UserService's `get_users` method
        users = [
            UserResponse(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                role=UserRole.USER,
            ),
            UserResponse(
                first_name="Jane",
                last_name="Doe",
                email="jane.doe@example.com",
                role=UserRole.USER,
            ),
            UserResponse(
                first_name="Bob",
                last_name="Doe",
                email="bob.doe@example.com",
                role=UserRole.USER,
            ),
        ]
        mock_user_service.get_users.return_value = [
            User(**user.model_dump()) for user in users
        ]

        # Call the endpoint with the mocked token
        headers = {"Authorization": f"Bearer {mock_access_token}"}
        response = test_client.get(f"{s.API_PREFIX}/users/", headers=headers)

        # Assert response
        assert response.status_code == 200
        assert response.json() == [user.model_dump() for user in users]
        mock_user_service.get_users.assert_called_once_with(admin_user_override)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_users(
    app, test_client, mock_user_service, mock_current_user, mock_access_token
):
    current_user_instance = mock_current_user(
        email="user@example.com", role=UserRole.USER
    )

    # Set up dependency overrides
    app.dependency_overrides[get_current_active_user] = lambda: current_user_instance
    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    # Mock an access token for the user
    mock_user_access_token = mock_access_token(role=current_user_instance.role)

    # Configure the mock service
    async def mock_get_users(current_user):
        raise UserRoleNotAllowedException()

    mock_user_service.get_users = AsyncMock(side_effect=mock_get_users)

    try:
        # Make the request
        headers = {"Authorization": f"Bearer {mock_user_access_token}"}
        response = test_client.get(f"{s.API_PREFIX}/users/", headers=headers)

        assert response.status_code == 403
        response_json = response.json()
        assert (
            response_json["message"] == "Only admins are allowed to access this route."
        )
        assert response_json["error_code"] == "user_role_not_allowed"

        mock_user_service.get_users.assert_called_once_with(current_user_instance)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user(app, test_client, mock_current_user, mock_access_token):
    try:
        # Create a mock user instance
        current_user_instance = mock_current_user(
            email="user@example.com", role=UserRole.USER
        )
        app.dependency_overrides[get_current_active_user] = (
            lambda: current_user_instance
        )

        # Call the endpoint
        headers = {"Authorization": f"Bearer {mock_access_token}"}
        response = test_client.get(f"{s.API_PREFIX}/users/me", headers=headers)

        dumped_user = current_user_instance.model_dump()
        dumped_user["verified"] = current_user_instance.verified.isoformat().replace(
            "+00:00", "Z"
        )

        # Assert response
        assert response.status_code == 200
        assert response.json() == dumped_user
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_user_by_id(
    app, test_client, mock_user_service, mock_current_user, mock_access_token
):
    try:
        # Create a mock current user
        current_user = mock_current_user(email="admin@example.com", role=UserRole.ADMIN)
        app.dependency_overrides[get_current_active_user] = lambda: current_user

        # Mock the UserService's `get_user` method
        user_response = UserResponse(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            role=UserRole.USER,
            verified=datetime.now(tz=timezone.utc),
        )
        mock_user_service.get_user.return_value = user_response

        # Call the endpoint
        headers = {"Authorization": f"Bearer {mock_access_token}"}
        response = test_client.get(f"{s.API_PREFIX}/users/123", headers=headers)

        # Convert model to JSON and normalize datetime
        expected_response = user_response.model_dump()
        if user_response.verified:
            expected_response["verified"] = user_response.verified.isoformat().replace(
                "+00:00", "Z"
            )

        # Assert response
        assert response.status_code == 200
        assert response.json() == expected_response
        mock_user_service.get_user.assert_called_once_with("123", current_user)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_user(
    app, test_client, mock_user_service, mock_current_user, mock_access_token
):
    try:
        # Create a mock current user
        current_user_instance = mock_current_user(
            email="admin@example.com", role=UserRole.ADMIN
        )
        app.dependency_overrides[get_current_active_user] = (
            lambda: current_user_instance
        )

        # Mock the UserService's `update_user` method
        updated_user = UserResponse(
            first_name="Updated",
            last_name="User",
            email="updated@example.com",
            role=UserRole.USER,
        )
        mock_user_service.update_user.return_value = updated_user

        # Call the endpoint
        headers = {"Authorization": f"Bearer {mock_access_token}"}
        payload = {"first_name": "Updated", "last_name": "User"}
        response = test_client.patch(
            f"{s.API_PREFIX}/users/123", headers=headers, json=payload
        )

        # Assert response
        assert response.status_code == 200
        assert response.json() == {**updated_user.model_dump()}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_user(
    app, test_client, mock_user_service, mock_current_user, mock_access_token
):
    try:
        # Create a mock current user
        current_user = mock_current_user(email="admin@example.com", role=UserRole.ADMIN)
        app.dependency_overrides[get_current_active_user] = lambda: current_user

        # Mock the UserService's `delete_user` method
        mock_user_service.delete_user.return_value = None

        # Call the endpoint
        headers = {"Authorization": f"Bearer {mock_access_token}"}
        response = test_client.delete(f"{s.API_PREFIX}/users/123", headers=headers)

        # Assert response
        assert response.status_code == 204
        mock_user_service.delete_user.assert_called_once_with("123", current_user)
    finally:
        app.dependency_overrides.clear()
