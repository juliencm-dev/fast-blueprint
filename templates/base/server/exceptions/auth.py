from fastapi import status
from server.exceptions.base import ServerException


class InvalidCredentialsException(ServerException):
    """Raised when the credentials are invalid."""


class InvalidVerificationTokenException(ServerException):
    """Raised when the verification token is invalid."""


class InvalidPasswordResetTokenException(ServerException):
    """Raised when the password reset token is invalid."""


class InvalidRefreshTokenException(ServerException):
    """Raised when the refresh token is invalid."""


class TokenExpiredException(ServerException):
    """Raised when the token has expired."""


class EmailNotVerifiedException(ServerException):
    """Raised when the email is not verified."""


class TokenNotCreatedException(ServerException):
    """Raised when the token creation fails."""


class TokenNotFoundException(ServerException):
    """Raised when the token is not found."""


class DeviceNotFoundException(ServerException):
    """Raised when the device is not found."""


class DeviceNotCreatedException(ServerException):
    """Raised when the device creation fails."""


AUTH_EXCEPTIONS = {
    InvalidCredentialsException: {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "detail": {
            "message": "Provided credentials are invalid, please provide a valid access token",
            "error_code": "invalid_credentials",
        },
        "headers": {"WWW-Authenticate": "Bearer"},
    },
    InvalidVerificationTokenException: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": {
            "message": "Provided verification token is invalid",
            "error_code": "invalid_verification_token",
        },
    },
    InvalidPasswordResetTokenException: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": {
            "message": "Provided password reset token is invalid",
            "error_code": "invalid_password_reset_token",
        },
    },
    InvalidRefreshTokenException: {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "detail": {
            "message": "Provided refresh token is invalid",
            "error_code": "invalid_refresh_token",
        },
    },
    TokenExpiredException: {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "detail": {
            "message": "Provided token has expired",
            "error_code": "token_expired",
        },
    },
    EmailNotVerifiedException: {
        "status_code": status.HTTP_403_FORBIDDEN,
        "detail": {
            "message": "Please verify your email address to activate your account.",
            "error_code": "email_not_verified",
        },
    },
    TokenNotCreatedException: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": {
            "message": "Token could not be created",
            "error_code": "token_creation_failed",
        },
    },
    TokenNotFoundException: {
        "status_code": status.HTTP_404_NOT_FOUND,
        "detail": {
            "message": "Token could not be found",
            "error_code": "token_not_found",
        },
    },
    DeviceNotFoundException: {
        "status_code": status.HTTP_404_NOT_FOUND,
        "detail": {
            "message": "Device could not be found",
            "error_code": "device_not_found",
        },
    },
    DeviceNotCreatedException: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": {
            "message": "Device could not be created",
            "error_code": "device_creation_failed",
        },
    },
}
