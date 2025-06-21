from typing import Sequence

from server.db.user.dao import UserDAO
from server.db.user.schema import User, UserRole
from server.models import UserCreateRequest, UserUpdateRequest
from server.exceptions.user import (
    UserNotFoundException,
    UserRoleNotAllowedException,
    UserWithEmailAlreadyExistsException,
)
from server.utils.security import get_password_manager
from server.utils.security.password import PasswordManager


class UserService:
    def __init__(self, user_dao: UserDAO):
        self._user_dao: UserDAO = user_dao
        self._pwd_manager: PasswordManager = get_password_manager()

    async def get_user(self, user_id: str, current_user: User) -> User | None:
        self._check_user_permission(user_id, current_user)
        user = await self._user_dao.get_user_by_id(user_id)
        return user

    async def get_users(self, current_user: User) -> Sequence[User]:
        self._require_admin(current_user)
        users = await self._user_dao.get_users()
        return users

    async def create_user(self, user_data: UserCreateRequest) -> User:
        try:
            user = await self._user_dao.get_user_by_email(user_data.email)
            if user:
                raise UserWithEmailAlreadyExistsException()
        except UserNotFoundException:
            pass

        user_data.password = self._pwd_manager.hash_password(user_data.password)
        new_user = await self._user_dao.insert_user(user_data)
        return new_user

    async def update_user(
        self, user_id: str, user_data: UserUpdateRequest, current_user: User
    ) -> User:
        self._check_user_permission(user_id, current_user)
        updated_user = await self._user_dao.update_user(user_id, user_data)
        return updated_user

    async def delete_user(self, user_id: str, current_user: User) -> None:
        self._check_user_permission(user_id, current_user)
        await self._user_dao.delete_user(user_id)

    # NOTE: Permissions check functions:

    def _require_admin(self, current_user: User):
        if current_user.role != UserRole.ADMIN:
            raise UserRoleNotAllowedException()

    def _check_user_permission(self, target_user_id: str, current_user: User) -> None:
        if current_user.id != target_user_id and current_user.role != UserRole.ADMIN:
            raise UserRoleNotAllowedException()
