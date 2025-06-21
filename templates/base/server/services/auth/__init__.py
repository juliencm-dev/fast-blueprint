from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends
from redis import asyncio as aioredis

from .service import AuthService
from server.services.email import get_email_service
from server.services.email.service import EmailService
from server.db import get_session, get_cache
from server.db.user.dao import UserDAO
from server.utils.security.password import PasswordManager
from server.utils.security.tokens import TokenManager
from server.utils.security.devices import DeviceManager
from server.utils.security import get_password_manager, get_token_manager, get_device_manager

def get_auth_service(session: AsyncSession = Depends(get_session), 
                     pwd_manager: PasswordManager = Depends(get_password_manager), 
                     token_manager: TokenManager = Depends(get_token_manager),
                     email_service: EmailService = Depends(get_email_service),
                     device_manager: DeviceManager = Depends(get_device_manager),
                     cache: aioredis.Redis = Depends(get_cache)):
   
    return AuthService(UserDAO(session, cache), pwd_manager=pwd_manager, token_manager=token_manager, email_service=email_service , device_manager=device_manager)
