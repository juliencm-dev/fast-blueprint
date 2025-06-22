from typing import Sequence

from server.db.auth.schema import Device
from server.db.auth.schema import RefreshToken
from server.db.auth.schema import ValidationToken
from server.db.auth.schema import ValidationTokenType
from server.exceptions.auth import DeviceNotCreatedException
from server.exceptions.auth import DeviceNotFoundException
from server.exceptions.auth import TokenNotCreatedException
from server.exceptions.auth import TokenNotFoundException
from server.models import DeviceData
from server.models import RefreshTokenData
from server.models import UpdateDeviceData
from server.models import ValidationTokenData
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


class AuthDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    # NOTE: Refresh tokens DAO methods:

    async def get_refresh_token_by_jti(self, jti: str) -> RefreshToken:
        result = await self.session.exec(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        token_data = result.first()

        if not token_data:
            raise TokenNotFoundException()

        return token_data

    async def insert_refresh_token(self, token_data: RefreshTokenData):
        try:
            self.session.add(RefreshToken(**token_data.model_dump()))
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise TokenNotCreatedException()

    async def delete_refresh_token(self, jti: str):
        token = await self.get_refresh_token_by_jti(jti)

        if not token:
            raise TokenNotFoundException()

        await self.session.delete(token)
        await self.session.commit()

    # NOTE: Validation tokens DAO methods:
    async def get_validation_token(self, token: str):
        token_data = await self.session.exec(
            select(ValidationToken).where(ValidationToken.token == token)
        )
        return token_data.first()

    async def get_validation_token_by_user_id_and_type(
        self, user_id: str, token_type: ValidationTokenType
    ):
        token_data = await self.session.exec(
            select(ValidationToken).where(
                ValidationToken.user_id == user_id,
                ValidationToken.token_type == token_type,
            )
        )
        return token_data.first()

    async def insert_validation_token(self, token_data: ValidationTokenData):
        try:
            self.session.add(ValidationToken(**token_data.model_dump()))
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise TokenNotCreatedException()

        return token_data

    async def delete_validation_token(self, token_str: str):
        result = await self.session.exec(
            select(ValidationToken).where(ValidationToken.token == token_str)
        )
        token = result.first()

        if not token:
            raise TokenNotFoundException()

        await self.session.delete(token)
        await self.session.commit()

    # NOTE: Devices DAO methods:

    async def get_device_id(
        self, raw_user_agent: str, ip_address: str, user_id: str
    ) -> str | None:
        result = await self.session.exec(
            select(Device).where(
                Device.raw_user_agent == raw_user_agent,
                Device.ip_address == ip_address,
                Device.user_id == user_id,
            )
        )
        device = result.first()

        if not device:
            return None

        return device.id

    async def get_device_by_id(self, device_id: str) -> Device | None:
        device = await self.session.exec(select(Device).where(Device.id == device_id))
        device = device.first()
        return device

    async def get_devices_by_user_id(self, user_id: str) -> Sequence[Device]:
        devices = await self.session.exec(
            select(Device).where(Device.user_id == user_id)
        )
        return devices.all()

    async def insert_device(self, device_data: DeviceData) -> str:
        try:
            new_device = Device(**device_data.model_dump())
            self.session.add(new_device)
            await self.session.commit()
            await self.session.refresh(new_device)
            return new_device.id
        except Exception:
            await self.session.rollback()
            raise DeviceNotCreatedException()

    async def update_device(
        self, device_id: str, update_device_data: UpdateDeviceData
    ) -> None:
        device = await self.get_device_by_id(device_id)

        if not device:
            raise DeviceNotFoundException()

        for key, value in update_device_data.model_dump(exclude_none=True).items():
            if value is not None:
                setattr(device, key, value)

        self.session.add(device)
        await self.session.commit()

    async def delete_user_devices(self, user_id: str) -> None:
        devices = await self.get_devices_by_user_id(user_id)

        if not devices:
            raise DeviceNotFoundException()

        await self.session.delete(devices)
        await self.session.commit()

    async def delete_device(self, device_id: str) -> None:
        device = await self.get_device_by_id(device_id)

        if not device:
            raise DeviceNotFoundException()

        await self.session.delete(device)
        await self.session.commit()
