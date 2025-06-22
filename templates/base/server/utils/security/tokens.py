from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Optional
from typing import Tuple

from jose import jwt
from server.config import settings as s
from server.db.auth.dao import AuthDAO
from server.db.auth.schema import ValidationToken
from server.db.auth.schema import ValidationTokenType
from server.db.user.dao import UserDAO
from server.db.user.schema import User
from server.exceptions.auth import InvalidCredentialsException
from server.exceptions.auth import InvalidRefreshTokenException
from server.exceptions.auth import InvalidVerificationTokenException
from server.exceptions.auth import TokenExpiredException
from server.exceptions.auth import TokenNotFoundException
from server.models import AccessTokenData
from server.models import AccessTokenResponse
from server.models import RefreshTokenData
from server.models import RefreshTokenResponse
from server.models import ValidationTokenData
from server.utils import cuid
from server.utils import nowutc


class TokenManager:
    def __init__(self, auth_dao: AuthDAO, user_dao: UserDAO):
        self._auth_dao = auth_dao
        self._user_dao = user_dao

    # NOTE: Acces token methods:

    def create_access_token(self, data: dict) -> AccessTokenResponse:
        """Create a JWT access token. Takes the data and the expiration time as arguments."""
        to_encode = data.copy()
        to_encode.update(
            {"exp": self._set_token_expiration(s.ACCESS_TOKEN_EXPIRE_MINUTES)}
        )

        encoded_jwt = jwt.encode(to_encode, s.AUTH_SECRET, algorithm=s.ALGORITHM)

        return AccessTokenResponse(token=encoded_jwt, token_type="bearer")

    def verify_access_token(self, token: str) -> AccessTokenData:
        """Verify the access token. Takes the token string as an argument."""
        payload = jwt.decode(token, s.AUTH_SECRET, algorithms=[s.ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        exp: Optional[int] = payload.get("exp")

        if exp is None:
            raise InvalidCredentialsException()

        datetime_exp = datetime.fromtimestamp(exp, tz=timezone.utc)

        if datetime_exp < nowutc():
            raise InvalidCredentialsException()

        if user_id is None:
            raise InvalidCredentialsException()

        return AccessTokenData(id=user_id, expires_at=datetime_exp)

    # NOTE: Refresh token methods:

    async def create_refresh_token(self, data: dict) -> RefreshTokenResponse:
        """Create a JWT refresh token. Takes the user's id as an argument."""
        to_encode = data.copy()
        to_encode.update(
            {"exp": self._set_token_expiration(s.REFRESH_TOKEN_EXPIRE_MINUTES)}
        )
        to_encode.update({"jti": cuid()})

        refresh_token = RefreshTokenData(
            jti=to_encode["jti"],
            user_id=to_encode["sub"],
            device_id=to_encode["device_id"],
            expires_at=to_encode["exp"],
        )
        await self._store_refresh_token(refresh_token)

        encoded_jwt = jwt.encode(to_encode, s.AUTH_SECRET, algorithm=s.ALGORITHM)

        return RefreshTokenResponse(token=encoded_jwt, expires_at=to_encode["exp"])

    async def verify_refresh_token(self, token: str) -> RefreshTokenData:
        """Verify the refresh token. Takes the token string as an argument."""
        payload = jwt.decode(token, s.AUTH_SECRET, algorithms=[s.ALGORITHM])
        jti: Optional[str] = payload.get("jti")

        if jti is None:
            raise InvalidRefreshTokenException()

        refresh_token = await self._auth_dao.get_refresh_token_by_jti(jti)

        if not refresh_token:
            raise TokenNotFoundException()

        if refresh_token.expires_at < nowutc():
            raise TokenExpiredException()

        return RefreshTokenData(**refresh_token.model_dump())

    async def invalidate_refresh_token(self, jti: str) -> None:
        """Invalidate a refresh token. Takes the token string as an argument."""
        await self._auth_dao.delete_refresh_token(jti)

    async def _store_refresh_token(self, token_data: RefreshTokenData) -> None:
        """Store the refresh token in the database. Takes the raw token data as arguments."""
        await self._auth_dao.insert_refresh_token(token_data)

    # NOTE: Validation tokens methods:

    async def create_validation_token(
        self, user_id: str, token_type: ValidationTokenType
    ) -> str:
        """Create a validation token. Takes the user's id and the token type as arguments."""

        existing_token = await self._auth_dao.get_validation_token_by_user_id_and_type(
            user_id, token_type
        )

        if existing_token:
            await self.invalidate_validation_token(existing_token.token)

        new_token = self._generate_validation_token(user_id, token_type)
        await self._auth_dao.insert_validation_token(new_token)
        return new_token.token

    async def verify_validation_token(
        self, token_str: str
    ) -> Tuple[User, ValidationToken]:
        """Validate a validation token. Takes the token string value as an argument."""
        token = await self._auth_dao.get_validation_token(token_str)

        if not token:
            raise InvalidVerificationTokenException()

        user = await self._user_dao.get_user_by_id(token.user_id)

        if not user:
            raise InvalidVerificationTokenException()

        return (user, token)

    async def invalidate_validation_token(self, token_str: str) -> None:
        """Delete a validation token. Takes the token string value as an argument."""
        await self._auth_dao.delete_validation_token(token_str)

    def _generate_validation_token(
        self, user_id: str, token_type: ValidationTokenType
    ) -> ValidationTokenData:
        """Generate either a verification or password reset token. Takes the user's id and the token type as arguments."""
        exp = (
            s.VERIFICATION_TOKEN_EXPIRE_MINUTES
            if token_type == ValidationTokenType.VERIFICATION
            else s.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        return ValidationTokenData(
            user_id=user_id,
            token=cuid(),
            expires_at=self._set_token_expiration(exp),
            token_type=token_type,
        )

    # NOTE: General token methods:

    def _set_token_expiration(self, exp: int) -> datetime:
        return nowutc() + timedelta(minutes=exp)
