from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi import status
from server.db.user.schema import User
from server.exceptions.auth import TokenNotFoundException
from server.models import EmailRequest
from server.models import LoginRequest
from server.models import LoginResponse
from server.models import PasswordResetRequest
from server.models import RefreshResponse
from server.models import UserCreateRequest
from server.models import UserCreateResponse
from server.models import UserResponse
from server.services.auth import get_auth_service
from server.services.auth.dependencies import get_current_active_user
from server.services.auth.service import AuthService
from server.services.user import get_user_service
from server.services.user.service import UserService

router = APIRouter()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login a user and set the refresh_token cookie.

    Parameters:
        data (LoginRequest): The login request data.

    Returns:
        LoginResponse: The login response containing the access token, user and a confirmation message.

    """
    result = await auth_service.login(request=request, data=data)

    if result.refresh_token:
        auth_service.set_refresh_cookie(data=result, response=response)

    return result


@router.post(
    "/register", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    data: UserCreateRequest,
    bg_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    """
    Register a new user.

    Parameters:
        data (UserCreateRequest): The user create request data.

    Returns:
        UserCreateResponse: The user create response containing the created user and a confirmation message.
    """
    user: User = await auth_service.register(data, user_service, bg_tasks)
    return UserCreateResponse(user=UserResponse(**user.model_dump()))


@router.get(
    "/logout",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_active_user)],
)
async def logout(
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout the user. Deletes the refresh token cookie."""
    await auth_service.logout(response, request)
    return {"message": "You have been successfully logged out."}


# NOTE: Email verification and password reset routes:


@router.get("/account-activation/{token}", status_code=status.HTTP_200_OK)
async def account_activation(
    token: str, auth_service: AuthService = Depends(get_auth_service)
):
    """Activate the user's account. Returns a success message."""
    return await auth_service.activate_account(token)


@router.post("/reset-password-request", status_code=status.HTTP_200_OK)
async def reset_password_request(
    data: EmailRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """Request a password reset email. Returns a success message."""
    await auth_service.request_reset_password(data.email)
    return {
        "message": "An email has been sent to your address with a link to reset your password."
    }


@router.get("/reset-password/{token}", status_code=status.HTTP_200_OK)
async def reset_password(
    token: str,
    data: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Reset the user's password. Returns a success message."""
    return await auth_service.reset_password(token, data)


# NOTE: Refresh token and session tracking routes:


@router.get("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh the access token. Returns a login response containing the access and refresh tokens."""

    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise TokenNotFoundException()

    result = await auth_service.refresh_access_token(refresh_token)
    auth_service.set_refresh_cookie(data=result, response=response)
    return result
