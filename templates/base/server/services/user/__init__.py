from fastapi import Depends
from server.db import get_cache
from server.db import get_session
from server.db.user.dao import UserDAO

from .service import UserService


async def get_user_service(
    session=Depends(get_session), cache=Depends(get_cache)
) -> UserService:
    return UserService(UserDAO(session, cache))
