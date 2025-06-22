from datetime import datetime
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr
from server.db.user.schema import UserRole

# NOTE: User pydantic models for type safety:


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserCreateRequest(UserBase):
    password: str
    role: Optional[UserRole] = None


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    verified: Optional[datetime] = None


class PasswordResetRequest(BaseModel):
    password: str
    confirm_password: str


class EmailRequest(BaseModel):
    email: EmailStr


class UserResponse(UserBase):
    role: str
    verified: Optional[datetime] = None


class UserCreateResponse(BaseModel):
    message: str = (
        "Account successfully created! Please check your email to verify your account."
    )
    user: UserResponse


# NOTE: Token related pydantic models:


class TokenBase(BaseModel):
    expires_at: datetime


class AccessTokenData(TokenBase):
    id: str


class RefreshTokenData(TokenBase):
    jti: str
    user_id: str
    device_id: str
    valid: bool = True


class ValidationTokenData(BaseModel):
    user_id: str
    token: str
    expires_at: datetime
    token_type: str


class RefreshTokenResponse(TokenBase):
    token: str


class AccessTokenResponse(BaseModel):
    token: str
    token_type: str


# NOTE: Auth related pydantic models:
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponseBase(BaseModel):
    access_token: AccessTokenResponse
    user: UserResponse


class LoginResponse(AuthResponseBase):
    message: str = "User successfully logged in"


class RefreshResponse(AuthResponseBase):
    message: str = "User access token has been refreshed."


class AuthResponse(AuthResponseBase):
    refresh_token: RefreshTokenResponse


# NOTE: Device pydantic models:


class DeviceData(BaseModel):
    user_id: str
    browser: str
    browser_version: str
    os: str
    device_type: str
    is_mobile: bool
    is_tablet: bool
    is_desktop: bool
    raw_user_agent: str
    ip_address: str
    last_seen: datetime


class UserDevicesData(BaseModel):
    devices: List[DeviceData]


class UpdateDeviceData(BaseModel):
    user_id: Optional[str] = None
    raw_user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    is_mobile: Optional[bool] = None
    is_tablet: Optional[bool] = None
    is_desktop: Optional[bool] = None
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    os: Optional[str] = None
    device_type: Optional[str] = None
    last_seen: Optional[datetime] = None
