from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.action_payloads import (
    AddDeviceGroupsPayload,
    DeleteDeviceGroupsPayload,
    PostDeviceGroupsPayload,
)
from ..schemas import DEVICE_GROUP_SCHEMA
from .base import BaseEndpoint, BaseResults

if TYPE_CHECKING:
    from httpx import Response


class DeviceGroupResults(BaseResults):
    """Results from the /api/deviceGroups endpoint."""

    SCHEMA = DEVICE_GROUP_SCHEMA


class DeviceGroupsEndpoint(BaseEndpoint):
    """Endpoint for /api/deviceGroups."""

    _PATH = "/api/deviceGroups"

    def get_all(self) -> DeviceGroupResults:
        """Retrieves a list of device groups.

        **Docs:** Null (undocumented endpoint)
        """
        return DeviceGroupResults(self, {})

    def get(self, id: str) -> DeviceGroupResults:
        """Retrieves a single device group by ID.

        **Docs:** Null (undocumented endpoint)
        """
        path = f"{self._PATH}/{id}"
        return DeviceGroupResults(self, {}, path=path, single=True)

    def add(self, payload: AddDeviceGroupsPayload) -> Response:
        """Adds AAD device groups to a device group.

        TODO: Needs Testing and Validation

        **Docs:** Null (undocumented endpoint)
        """
        path = f"{self._PATH}/addDeviceGroups"
        return self._request("POST", path, json=payload.model_dump())

    def delete(self, payload: DeleteDeviceGroupsPayload) -> Response:
        """Deletes AAD device groups from a device group.

        TODO: Needs Testing and Validation

        **Docs:** Null (undocumented endpoint)
        """
        path = f"{self._PATH}/deleteDeviceGroups"
        return self._request("POST", path, json=payload.model_dump())

    def post(self, payload: PostDeviceGroupsPayload) -> Response:
        """Creates or updates a device group.

        TODO: Needs Testing and Validation

        **Docs:** Null (undocumented endpoint)
        """
        path = f"{self._PATH}/postDeviceGroups"
        return self._request("POST", path, json=payload.model_dump())
