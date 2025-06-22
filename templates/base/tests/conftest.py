from datetime import timedelta
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from server import create_app
from server.config import settings as s
from server.db import get_session
from server.db.user.dao import UserDAO
from server.db.user.schema import User
from server.db.user.schema import UserRole
from server.exceptions import register_exceptions
from server.models import AccessTokenResponse
from server.models import LoginRequest
from server.models import RefreshTokenData
from server.models import RefreshTokenResponse
from server.models import UserCreateRequest
from server.models import UserResponse
from server.models import UserUpdateRequest
from server.services.auth import AuthService
from server.services.auth import get_auth_service
from server.services.auth.dependencies import get_current_active_user
from server.services.email import EmailService
from server.services.email import get_email_service
from server.services.user import UserService
from server.services.user import get_user_service
from server.utils import nowutc
from server.utils.security.devices import DeviceManager
from server.utils.security.password import PasswordManager
from server.utils.security.tokens import TokenManager
from sqlalchemy.ext.asyncio.session import AsyncSession


@pytest.fixture
def app():
    """Fixture to create and return the FastAPI application instance."""
    app = create_app()
    register_exceptions(app)
    return app


mock_session = AsyncMock(spec=AsyncSession)


def get_mock_session():
    yield mock_session


@pytest.fixture
def test_client(app):
    return TestClient(app)


@pytest.fixture
def mock_user_dao():
    return AsyncMock(spec=UserDAO)


@pytest.fixture
def mock_email_service():
    return AsyncMock(spec=EmailService)


@pytest.fixture
def mock_user_service():
    return AsyncMock(spec=UserService)


@pytest.fixture
def mock_password_manager():
    return MagicMock(spec=PasswordManager)


@pytest.fixture
def mock_token_manager():
    return AsyncMock(spec=TokenManager)


@pytest.fixture
def mock_device_manager():
    return MagicMock(spec=DeviceManager)


@pytest.fixture
def mock_auth_service(
    mock_user_dao,
    mock_password_manager,
    mock_token_manager,
    mock_device_manager,
    mock_email_service,
):
    return AuthService(
        mock_user_dao,
        mock_password_manager,
        mock_token_manager,
        mock_device_manager,
        mock_email_service,
    )


@pytest.fixture
def mock_request():
    return MagicMock()


@pytest.fixture
def mock_response():
    return MagicMock()


@pytest.fixture
def mock_background_tasks():
    from fastapi.background import BackgroundTasks

    return BackgroundTasks()


@pytest.fixture
def mock_current_user():
    def _create_mock_user(email="user@example.com", role=UserRole.USER):
        return UserResponse(
            first_name="Mock",
            last_name="User",
            email=email,
            role=role,
            verified=nowutc(),
        )

    return _create_mock_user


@pytest.fixture
def mock_current_user_with_id():
    def _create_mock_user(user_id="123", email="user@example.com", role=UserRole.USER):
        mock_user = User(
            id=user_id,
            first_name="Mock",
            last_name="User",
            email=email,
            password="hashed_password",
            role=role,
            verified=nowutc(),
            created_at=nowutc(),
            updated_at=nowutc(),
        )
        return mock_user

    return _create_mock_user


@pytest.fixture(autouse=True)
def override_dependencies(
    app, mock_user_service, mock_auth_service, mock_email_service
):
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_email_service] = lambda: mock_email_service
    app.dependency_overrides[get_session] = get_mock_session
    app.dependency_overrides[get_current_active_user] = lambda: mock_current_user

    yield

    # Cleanup after tests
    app.dependency_overrides = {}


@pytest.fixture
def sample_new_user_response():
    return UserResponse(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        role="user",
    )


@pytest.fixture
def sample_user():
    mock_user = MagicMock()
    mock_user.id = "123"
    mock_user.email = "john.doe@example.com"
    mock_user.password = "hashed_password"
    mock_user.verified = nowutc()
    mock_user.role = UserRole.USER
    mock_user.model_dump.return_value = {
        "id": "123",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "role": UserRole.USER,
        "verified": mock_user.verified.isoformat(),
    }
    return mock_user


@pytest.fixture
def unverified_user(sample_user):
    # Copy the sample_user and set `verified` to None
    sample_user.verified = None
    sample_user.model_dump.return_value["verified"] = None
    return sample_user


@pytest.fixture
def admin_user():
    mock_admin = MagicMock()
    mock_admin.id = "admin"
    mock_admin.email = "admin@example.com"
    mock_admin.password = "hashed_password"
    mock_admin.verified = nowutc()
    mock_admin.role = UserRole.ADMIN
    mock_admin.model_dump.return_value = {
        "id": "admin",
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.com",
        "role": UserRole.ADMIN,
        "verified": mock_admin.verified.isoformat(),
    }


@pytest.fixture
def sample_user_create_request():
    return UserCreateRequest(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        password="secure_password",
    )


@pytest.fixture
def sample_user_update_request():
    return UserUpdateRequest(
        first_name="Jane",
        last_name="Doe Updated",
        email="jane.doe@example.com",
    )


@pytest.fixture
def sample_login_request():
    return LoginRequest(email="john.doe@example.com", password="password123")


@pytest.fixture
def sample_access_token_response():
    return AccessTokenResponse(token="access_token", token_type="Bearer")


@pytest.fixture
def sample_refresh_token_login_response():
    return RefreshTokenResponse(
        token="refresh_token", expires_at=nowutc() + timedelta(days=30)
    )


# NOTE: Refresh token fixtures:


@pytest.fixture
def sample_refresh_token_data():
    return {
        "jti": "refresh_token",
        "user_id": "123",
        "device_id": "456",
        "exp": nowutc() + timedelta(days=30),
    }


@pytest.fixture
def sample_refresh_token_wrong_jti_data():
    return {
        "jti": "wrong_jti",
        "user_id": "123",
        "device_id": "456",
        "exp": nowutc() + timedelta(days=30),
    }


@pytest.fixture
def sample_refresh_token_no_jti_data():
    return {
        "jti": None,
        "user_id": "123",
        "device_id": "456",
        "exp": nowutc() + timedelta(days=30),
    }


@pytest.fixture
def sample_expired_refresh_token_data(sample_refresh_token_data):
    sample_refresh_token_data["expires_at"] = nowutc() - timedelta(days=1)
    return sample_refresh_token_data


@pytest.fixture
def mock_access_token():
    def _mock_access_token(
        user_id="234", email="admin@example.com", role=UserRole.ADMIN
    ):
        payload = {"sub": user_id, "role": role}
        token = jwt.encode(payload, s.AUTH_SECRET, algorithm=s.ALGORITHM)
        return token

    return _mock_access_token


# NOTE: Encoded refresh token fixtures:


@pytest.fixture
def sample_refresh_token(sample_refresh_token_data):
    encoded_jwt = jwt.encode(
        sample_refresh_token_data, s.AUTH_SECRET, algorithm=s.ALGORITHM
    )
    return encoded_jwt


@pytest.fixture
def sample_expired_refresh_token(sample_expired_refresh_token_data):
    encoded_jwt = jwt.encode(
        sample_expired_refresh_token_data, s.AUTH_SECRET, algorithm=s.ALGORITHM
    )
    return encoded_jwt


@pytest.fixture
def sample_wrong_jti_refresh_token(sample_refresh_token_wrong_jti_data):
    encoded_jwt = jwt.encode(
        sample_refresh_token_wrong_jti_data, s.AUTH_SECRET, algorithm=s.ALGORITHM
    )
    return encoded_jwt


@pytest.fixture
def sample_refresh_token_no_jti(sample_refresh_token_no_jti_data):
    encoded_jwt = jwt.encode(
        sample_refresh_token_no_jti_data, s.AUTH_SECRET, algorithm=s.ALGORITHM
    )
    return encoded_jwt


@pytest.fixture
def sample_refresh_token_response(sample_refresh_token_data):
    return RefreshTokenData(
        jti=sample_refresh_token_data["jti"],
        user_id=sample_refresh_token_data["user_id"],
        device_id=sample_refresh_token_data["device_id"],
        expires_at=sample_refresh_token_data["exp"],
    )


@pytest.fixture
def sample_refresh_token_mock():
    mock_token = MagicMock()
    mock_token.jti = "refresh_token"
    mock_token.user_id = "123"
    mock_token.device_id = "456"
    return mock_token


# NOTE: Device fixtures:


@pytest.fixture
def sample_device_data():
    return {
        "user_id": "123",
        "browser": "Chrome",
        "browser_version": "100.0.4896.127",
        "os": "Windows 10",
        "device_type": "desktop",
        "is_mobile": False,
        "is_tablet": False,
        "is_desktop": True,
        "raw_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        "ip_address": "127.0.0.1",
        "last_seen": nowutc(),
    }
