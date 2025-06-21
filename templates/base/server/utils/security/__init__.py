from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from redis import asyncio as aioredis

from server.db.user.dao import UserDAO
from .password import PasswordManager
from .tokens import TokenManager
from .devices import DeviceManager
from server.db.auth.dao import AuthDAO
from server.db import get_session, get_cache

def get_password_manager() -> PasswordManager:
    return PasswordManager()

def get_token_manager(session: AsyncSession = Depends(get_session), cache: aioredis.Redis = Depends(get_cache)) -> TokenManager:
    return TokenManager(AuthDAO(session), UserDAO(session, cache))

def get_device_manager(session: AsyncSession = Depends(get_session)) -> DeviceManager:
    return DeviceManager(AuthDAO(session))
