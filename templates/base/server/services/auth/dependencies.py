from fastapi import Depends
from fastapi.security import HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from jose import JWTError
from redis import asyncio as aioredis
import orjson as json

from server.exceptions.auth import (
    EmailNotVerifiedException,
    InvalidCredentialsException,
)
from server.db import get_cache, get_session
from server.db.user.schema import User
from server.db.user.dao import UserDAO
from server.utils.security.tokens import TokenManager
from server.services.auth import get_token_manager
from server.config import settings as s

auth_scheme = HTTPBearer()

# NOTE: This function is used to get the current user from the JWT token. It takes the token as an argument and returns the user's data.


async def _get_current_user(
    credentials=Depends(auth_scheme),
    session: AsyncSession = Depends(get_session),
    cache: aioredis.Redis = Depends(get_cache),
    token_manager: TokenManager = Depends(get_token_manager),
):
    try:
        verified_token = token_manager.verify_access_token(credentials.credentials)
    except JWTError:
        raise InvalidCredentialsException()

    # NOTE: Check if the user is in the cache:
    try:
        cached_user = await cache.get(f"user_id:{verified_token.id}")
    except aioredis.RedisError:
        cached_user = None

    user = User.model_validate(json.loads(cached_user)) if cached_user else None

    if not user:
        user_dao = UserDAO(session, cache)
        user = await user_dao.get_user_by_id(verified_token.id)

        if not user:
            raise InvalidCredentialsException()

        await cache.set(
            f"user_id:{verified_token.id}",
            json.dumps(user.model_dump()).decode("utf-8"),
            ex=s.CACHE_EXPIRATION_TIME,
        )

    if user is None:
        raise InvalidCredentialsException()

    return user


# NOTE: Simple function that check is the user is verified.


async def get_current_active_user(user: User = Depends(_get_current_user)):
    if user.verified:
        return user
    else:
        raise EmailNotVerifiedException()
