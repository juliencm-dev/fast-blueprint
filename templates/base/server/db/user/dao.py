from typing import Sequence 
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from redis import asyncio as aioredis

from server.db.user.schema import User
from server.exceptions.user import UserNotFoundException
from server.models import UserCreateRequest, UserUpdateRequest 

class UserDAO:
    def __init__(self, session:AsyncSession, cache: aioredis.Redis):
        self._session = session
        self._cache = cache

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self._session.exec(select(User).where(User.id == user_id))
        user = result.first()
        return user

    async def get_users(self) -> Sequence[User]:
        users =  await self._session.exec(select(User).order_by(User.last_name))
        return users.all()
    
    async def get_user_by_email(self, email: str) -> User | None :
        result = await self._session.exec(select(User).where(User.email == email))
        user = result.first()
        return user

    async def insert_user(self, user_data: UserCreateRequest) -> User:
        user = User(**user_data.model_dump())
        self._session.add(user)
        await self._session.commit()
        return user

    async def update_user(self, user_id: str, user_data: UserUpdateRequest) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        for key, value in user_data.model_dump(exclude_none=True).items():
                setattr(user, key, value)

        self._session.add(user)
        await self._session.commit()

        await self._cache.delete(f"user_id:{user_id}")
        return user

    async def delete_user(self, user_id: str) -> None:
        user = await self.get_user_by_id(user_id)
        
        if not user:
            raise UserNotFoundException()

        await self._session.delete(user)
        await self._session.commit()
