from typing import cast
from fastapi import Request
from user_agents import parse

from server.db.auth.dao import AuthDAO
from server.models import DeviceData, UserDevicesData, UpdateDeviceData
from server.utils import nowutc

class DeviceManager:
    def __init__(self, auth_dao):
        self._auth_dao: AuthDAO = auth_dao

    async def get_or_create_device(self, device_data: DeviceData) -> str:
        """Get or create a device. Takes the device data as an argument."""
        device_id = await self._auth_dao.get_device_id(device_data.raw_user_agent, device_data.ip_address, device_data.user_id)

        if not device_id:
            device_id = await self._auth_dao.insert_device(device_data)
        else:
            last_seen = nowutc()
            update_device_data = UpdateDeviceData(last_seen=last_seen)
            await self._auth_dao.update_device(device_id, update_device_data)

        return device_id

    async def get_devices_by_user_id(self, device_id: str) -> UserDevicesData:
        """Get the devices associated to a specific user_id."""
        user_devices = await self._auth_dao.get_devices_by_user_id(device_id)
        devices_data = [DeviceData(**device.model_dump()) for device in user_devices]
        return UserDevicesData(devices=devices_data)

    async def revoke_device(self, device_id: str) -> None:
        """Revoke a specific device."""
        await self._auth_dao.delete_device(device_id)

    async def parse_user_device(self, request: Request, user_id: str):
        """Process the user device information."""
        raw_user_agent = request.headers.get("user-agent", "unknown")
        user_agent = parse(raw_user_agent)
        
        device_data: DeviceData = DeviceData(
            user_id=user_id,
            browser=user_agent.browser.family,
            browser_version= user_agent.browser.version_string,
            os= user_agent.os.family,
            device_type= user_agent.device.family,
            is_mobile= user_agent.is_mobile,
            is_tablet= user_agent.is_tablet,
            is_desktop= user_agent.is_pc,
            raw_user_agent= raw_user_agent,
            ip_address= cast(str, self._get_client_ip(request)),
            last_seen= nowutc()
        )

        return await self.get_or_create_device(device_data)


    def _get_client_ip(self,request: Request) -> str:
        """Get the client IP address from the request."""
        if request.client is None:
            return "unknown"
        return request.client.host
