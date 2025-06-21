from datetime import timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock

from server.db.auth.schema import ValidationToken, ValidationTokenType
from server.exceptions.auth import InvalidCredentialsException, EmailNotVerifiedException, InvalidRefreshTokenException, TokenNotFoundException
from server.exceptions.user import UserNotCreatedException, UserWithEmailAlreadyExistsException
from server.models import AccessTokenResponse, PasswordResetRequest, RefreshTokenResponse
from server.utils import nowutc

#NOTE: This test module is for testing the AuthService class methods.

#NOTE: Register function tests:

@pytest.mark.asyncio
async def test_register_success(mock_auth_service, mock_user_service, mock_email_service, mock_background_tasks , sample_user_create_request, sample_new_user_response):
    # Mock behavior
    mock_user_service.create_user.return_value = sample_new_user_response
    mock_email_service.send_validation_email.return_value = AsyncMock()

    # Call the method
    result = await mock_auth_service.register(
        sample_user_create_request, mock_user_service, mock_background_tasks
    )

    # Validate the result
    assert result == sample_new_user_response
    assert result.first_name == "John"
    assert result.email == "john.doe@example.com"
    assert len(mock_background_tasks.tasks) == 1

@pytest.mark.asyncio
async def test_register_email_already_exists(
    mock_auth_service, mock_user_service, mock_email_service, mock_background_tasks, sample_user_create_request
):
    # Mock behavior
    mock_user_service.create_user.side_effect = UserWithEmailAlreadyExistsException()
    mock_email_service.send_validation_email.return_value = AsyncMock()

    # Expect the exception
    with pytest.raises(UserWithEmailAlreadyExistsException):
        await mock_auth_service.register(
            sample_user_create_request, mock_user_service, mock_background_tasks
        )

@pytest.mark.asyncio
async def test_register_email_not_created(
    mock_auth_service, mock_user_service, mock_email_service, mock_background_tasks, sample_user_create_request
):
    # Mock behavior
    mock_user_service.create_user.return_value = None
    mock_email_service.send_validation_email.return_value = AsyncMock()

    # Expect the exception
    with pytest.raises(UserNotCreatedException):
        await mock_auth_service.register(
            sample_user_create_request, mock_user_service, mock_background_tasks
        )



#NOTE: Login function tests:


@pytest.mark.asyncio
async def test_login_success(
    mock_auth_service,
    sample_login_request,
    sample_user,
    mock_token_manager,
    mock_device_manager,
    sample_access_token_response,
    sample_refresh_token_login_response,
):
    # Mock the protected _authenticate_user method
    mock_auth_service._authenticate_user = AsyncMock(return_value=sample_user)

    # Mock TokenManager and DeviceManager behavior
    mock_token_manager.create_access_token.return_value = sample_access_token_response
    mock_token_manager.create_refresh_token.return_value = sample_refresh_token_login_response
    mock_device_manager.parse_user_device.return_value = "device_id"

    # Call the login method
    mock_request = MagicMock()
    result = await mock_auth_service.login(mock_request, sample_login_request)

    # Assert expected output
    assert result.access_token == sample_access_token_response
    assert result.refresh_token == sample_refresh_token_login_response
    assert result.user.email == "john.doe@example.com"


@pytest.mark.asyncio
async def test_login_invalid_credentials(mock_auth_service, sample_login_request):
    # Mock the protected _authenticate_user method to return None
    mock_auth_service._authenticate_user = AsyncMock(return_value=None)

    mock_request = MagicMock()

    # Expect an InvalidCredentialsException
    with pytest.raises(InvalidCredentialsException):
        await mock_auth_service.login(mock_request, sample_login_request)

@pytest.mark.asyncio
async def test_login_unverified_email(
    mock_auth_service, sample_login_request, unverified_user
):
    # Mock `_authenticate_user` to return the unverified user
    mock_auth_service._authenticate_user = AsyncMock(return_value=unverified_user)

    mock_request = MagicMock()

    # Expect an EmailNotVerifiedException
    with pytest.raises(EmailNotVerifiedException):
        await mock_auth_service.login(mock_request, sample_login_request)



#NOTE: Refresh access token function tests:



@pytest.mark.asyncio
async def test_refresh_access_token_success(
    mock_auth_service, mock_token_manager, sample_refresh_token_response, sample_user
):
    # Mock the TokenManager
    mock_token_manager.verify_refresh_token.return_value = sample_refresh_token_response
    mock_token_manager.create_access_token.return_value = AccessTokenResponse(
        token="new_access_token", token_type="Bearer"
    )
    mock_token_manager.create_refresh_token.return_value = RefreshTokenResponse(
        token="new_refresh_token", expires_at=nowutc() + timedelta(days=30)
    )
    mock_auth_service._user_dao.get_user_by_id.return_value = sample_user

    # Call the method
    result = await mock_auth_service.refresh_access_token("valid_refresh_token")

    # Assert expected behavior
    assert result.access_token.token == "new_access_token"
    assert result.refresh_token.token == "new_refresh_token"
    assert result.user.email == "john.doe@example.com"

@pytest.mark.asyncio
async def test_refresh_access_token_invalid_refresh_token(
    mock_auth_service, mock_token_manager, sample_refresh_token
):
    # Mock the TokenManager to raise an exception
    mock_token_manager.verify_refresh_token.side_effect = InvalidRefreshTokenException()

    # Call the method
    with pytest.raises(InvalidRefreshTokenException):
        await mock_auth_service.refresh_access_token(sample_refresh_token)

@pytest.mark.asyncio
async def test_refresh_access_token_refresh_token_not_found(
    mock_auth_service, mock_token_manager, sample_refresh_token
):
    # Mock the TokenManager to raise an exception
    mock_token_manager.verify_refresh_token.side_effect = TokenNotFoundException()

    # Call the method
    with pytest.raises(TokenNotFoundException):
        await mock_auth_service.refresh_access_token(sample_refresh_token)


#NOTE: Logout function tests:


@pytest.mark.asyncio
async def test_logout_success(
    mock_auth_service, mock_response, mock_request, sample_refresh_token_mock, mock_token_manager
):
    # Mock the TokenManager
    mock_token_manager.verify_refresh_token.return_value = sample_refresh_token_mock

    # Call the method
    await mock_auth_service.logout(mock_response, mock_request)

    # Assert the expected behavior
    assert mock_response.delete_cookie.call_count == 1


#NOTE: Activate account function tests:


@pytest.mark.asyncio
async def test_activate_account_success(
    mock_auth_service, mock_token_manager, sample_user
):
    # Mock the TokenManager
    mock_token_manager.verify_validation_token.return_value = (
        sample_user,
        MagicMock(token="valid_token", expires_at=nowutc() + timedelta(minutes=10)),
    )

    # Call the method
    result = await mock_auth_service.activate_account("valid_token")

    # Assert expected behavior
    assert result["message"] == "Successfully verified email address. Your account is now activated."

@pytest.mark.asyncio
async def test_activate_account_expired_token(
    mock_auth_service, mock_token_manager, sample_user
):
    # Mock the TokenManager
    mock_token_manager.verify_validation_token.return_value = (
        sample_user,
        MagicMock(token="valid_token", expires_at=nowutc() - timedelta(minutes=10)),
    )

    # Call the method
    result = await mock_auth_service.activate_account("valid_token")

    # Assert expected behavior
    assert result["message"] == "Verification link as expired. A new link has been sent to your email address."

#NOTE: Request password reset function tests:

@pytest.mark.asyncio
async def test_request_password_reset_success(mock_auth_service, sample_refresh_token, mock_email_service, mock_token_manager):
    # Mock the protected _token_manager.verify_refresh_token method
    mock_token_manager.verify_refresh_token.return_value = sample_refresh_token

    # Call the method
    await mock_auth_service.request_reset_password("email")

    # Assert expected output
    assert mock_email_service.send_validation_email.call_count == 1

#NOTE: Reset password function tests:



@pytest.mark.asyncio
async def test_reset_password_success(
    mock_auth_service, mock_token_manager, sample_user
):
    # Mock TokenManager
    mock_token_manager.verify_validation_token.return_value = (
        sample_user,
        MagicMock(token="valid_token", expires_at=nowutc() + timedelta(minutes=10)),
    )

    # Mock PasswordManager
    mock_auth_service._pwd_manager.hash_password.return_value = "hashed_new_password"

    # Call the method
    result = await mock_auth_service.reset_password(
        "valid_token", PasswordResetRequest(password="new_password", confirm_password="new_password")
    )

    # Assert expected behavior
    assert result["message"] == "Your password has been successfully reset. Your can now login using your new password."

@pytest.mark.asyncio
async def test_reset_password_password_mismatch(
    mock_auth_service, mock_token_manager, sample_user
):
    # Mock the TokenManager
    mock_token_manager.verify_validation_token.return_value = (
        sample_user,
        MagicMock(user_id="123", token="valid_token", expires_at=nowutc()+timedelta(minutes=10), token_type=ValidationTokenType.PASSWORD_RESET),
    )

    # Call the method
    result = await mock_auth_service.reset_password(
        "valid_token", PasswordResetRequest(password="new_password", confirm_password="new_psord")
    )

    # Assert expected behavior
    assert result["message"] == "New passwords do not match. Please try again."

@pytest.mark.asyncio
async def test_reset_password_expired_token(
    mock_auth_service, mock_token_manager, sample_user
):
    # Mock the TokenManager
    mock_token_manager.verify_validation_token.return_value = (
            sample_user,
        MagicMock(user_id="123", token="valid_token", expires_at=nowutc()-timedelta(minutes=10), token_type=ValidationTokenType.PASSWORD_RESET),
    )

    # Call the method
    result = await mock_auth_service.reset_password(
        "valid_token", PasswordResetRequest(password="new_password", confirm_password="new_password")
    )

    # Assert expected behavior
    assert result["message"] == "Verification link as expired. If you did not request a password reset, please ignore this warning. Otherwise, please request a new password reset link."
