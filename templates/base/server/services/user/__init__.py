from fastapi import Depends

from .service import UserService
from server.db import get_session, get_cache
from server.db.user.dao import UserDAO

async def get_user_service(session = Depends(get_session), cache = Depends(get_cache)) -> UserService:
    return UserService(UserDAO(session, cache))
