from fastapi import Request, Response, BackgroundTasks

from server.db.user.dao import UserDAO
from server.services.user import UserService
from server.services.email import EmailService
from server.db.user.schema import User
from server.utils.security.devices import DeviceManager
from server.utils.security.password import PasswordManager
from server.utils.security.tokens import TokenManager, ValidationTokenType
from server.exceptions.auth import (
    InvalidCredentialsException,
    InvalidVerificationTokenException,
    TokenNotFoundException,
    EmailNotVerifiedException,
)
from server.exceptions.user import UserNotCreatedException, UserNotFoundException
from server.models import (
    LoginRequest,
    AuthResponse,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
    PasswordResetRequest,
    LoginRequest,
)
from server.utils import nowutc
from server.config import settings as s


class AuthService:
    def __init__(
        self,
        user_dao: UserDAO,
        pwd_manager: PasswordManager,
        token_manager: TokenManager,
        device_manager: DeviceManager,
        email_service: EmailService,
    ):
        self._user_dao = user_dao
        self._email_service = email_service
        self._pwd_manager = pwd_manager
        self._token_manager = token_manager
        self._device_manager = device_manager

    # NOTE: Public class methods:

    async def register(
        self,
        user_data: UserCreateRequest,
        user_service: UserService,
        task_manager: BackgroundTasks,
    ) -> User:
        user = await user_service.create_user(user_data)
        if not user:
            raise UserNotCreatedException()

        send_email = await self._email_service.send_validation_email(
            user=user, validation_token_type=ValidationTokenType.VERIFICATION
        )
        task_manager.add_task(send_email)

        return user

    async def login(self, request: Request, data: LoginRequest) -> AuthResponse:
        """Login a user. Uses the email and password to authenticate the user and issue token pairs."""
        user = await self._authenticate_user(
            LoginRequest(email=data.email, password=data.password)
        )

        if not user:
            raise InvalidCredentialsException()

        if not user.verified:
            raise EmailNotVerifiedException()

        device_id = await self._device_manager.parse_user_device(request, user.id)
        access_token = self._token_manager.create_access_token(
            data={"sub": user.id, "role": user.role}
        )
        refresh_token = await self._token_manager.create_refresh_token(
            data={"sub": user.id, "device_id": device_id}
        )

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(**user.model_dump()),
        )

    async def refresh_access_token(self, token: str) -> AuthResponse:
        """Refresh the access token. Uses the refresh token to get the user and create a new access token."""
        refresh_token = await self._token_manager.verify_refresh_token(token)
        user = await self._user_dao.get_user_by_id(refresh_token.user_id)

        if not user:
            raise UserNotFoundException()

        new_access_token = self._token_manager.create_access_token(
            data={"sub": user.id, "role": user.role}
        )
        new_refresh_token = await self._token_manager.create_refresh_token(
            data={"sub": user.id, "device_id": refresh_token.device_id}
        )

        await self._token_manager.invalidate_refresh_token(refresh_token.jti)

        return AuthResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user=UserResponse(**user.model_dump()),
        )

    def set_refresh_cookie(self, data: AuthResponse, response: Response):
        """Helper function to set the refresh token cookie."""
        response.set_cookie(
            key="refresh_token",
            value=data.refresh_token.token,
            httponly=True,
            secure=True,
            samesite="lax",
            path=s.API_PREFIX + "/auth",
            expires=data.refresh_token.expires_at,
        )

    async def activate_account(self, validation_token: str):
        """Verify the email address. Uses the token to activate the user's account."""
        try:
            user, token = await self._token_manager.verify_validation_token(
                validation_token
            )

            if token.expires_at < nowutc():
                await self._email_service.send_validation_email(
                    user=user, validation_token_type=ValidationTokenType.VERIFICATION
                )
                return {
                    "message": "Verification link as expired. A new link has been sent to your email address."
                }

            updated_user = UserUpdateRequest(verified=nowutc())
            await self._user_dao.update_user(user.id, updated_user)
            await self._token_manager.invalidate_validation_token(token.token)
            return {
                "message": "Successfully verified email address. Your account is now activated."
            }

        except InvalidVerificationTokenException as e:
            raise e

    async def request_reset_password(self, user_email: str):
        """Request a password reset email. Uses the email address to create a new user."""
        user = await self._user_dao.get_user_by_email(user_email)

        if not user:
            raise UserNotFoundException()

        await self._email_service.send_validation_email(
            user=user, validation_token_type=ValidationTokenType.PASSWORD_RESET
        )

    async def reset_password(self, validation_token: str, data: PasswordResetRequest):
        """Reset the password. Uses the token to find the user's account and update the password."""
        try:
            user, token = await self._token_manager.verify_validation_token(
                validation_token
            )

            if token.expires_at < nowutc():
                return {
                    "message": "Verification link as expired. If you did not request a password reset, please ignore this warning. Otherwise, please request a new password reset link."
                }

            if data.password != data.confirm_password:
                return {"message": "New passwords do not match. Please try again."}

            hashed_password = self._pwd_manager.hash_password(data.password)

            updated_user = UserUpdateRequest(password=hashed_password)
            await self._user_dao.update_user(user.id, updated_user)
            await self._token_manager.invalidate_validation_token(token.token)
            return {
                "message": "Your password has been successfully reset. Your can now login using your new password."
            }

        except InvalidVerificationTokenException as e:
            raise e

    async def logout(self, response: Response, request: Request):
        """Logout the user. Deletes the refresh token cookie."""
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise TokenNotFoundException()

        refresh_token = await self._token_manager.verify_refresh_token(refresh_token)
        await self._token_manager.invalidate_refresh_token(refresh_token.jti)

        response.delete_cookie(
            key="refresh_token",
            secure=True,
            path=s.API_PREFIX + "/auth",
            httponly=True,
            samesite="lax",
        )

    # NOTE: Protected class methods:

    async def _authenticate_user(self, user_data: LoginRequest):
        """Authenticate a user. Uses a Pydantic model to validate the data."""
        user = await self._user_dao.get_user_by_email(user_data.email)

        if user:
            if self._pwd_manager.verify_password(user.password, user_data.password):
                return user
        return None
