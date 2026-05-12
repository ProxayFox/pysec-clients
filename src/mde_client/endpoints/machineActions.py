from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseQuery, BaseResults
from .machines import MachinesEndpoint
from ..schemas import MACHINE_ACTION_SCHEMA
from ..models.enums import ACTION_TYPE, ACTION_STATUS

if TYPE_CHECKING:
    from ..models.action_payloads import (
        CollectInvestigationPackagePayload,
        IsolatePayload,
        UnisolatePayload,
        RestrictCodeExecutionPayload,
        RunLiveResponsePayload,
        StopAndQuarantineFilePayload,
        UnrestrictCodeExecutionPayload,
        RunAntiVirusScanPayload,
        OffBoardPayload,
        CancelPayload,
    )


class MachineActionsQuery(BaseQuery):
    """Query parameters for the /api/machineactions endpoint."""

    id: str | None
    status: ACTION_STATUS | list[ACTION_STATUS] | None
    machineId: str | None
    type: ACTION_TYPE | list[ACTION_TYPE] | None
    requestor: str | None
    creationDateTimeUtc: datetime | None


class MachineActionsResults(BaseResults):
    """Results from the /api/machineactions endpoint."""

    SCHEMA = MACHINE_ACTION_SCHEMA


class MachineActionsEndpoint(BaseEndpoint):
    """Endpoint for /api/machineactions"""

    _PATH = "/api/machineactions"

    def get_all(
        self, query: MachineActionsQuery | None = None
    ) -> MachineActionsResults:
        """Get machine actions with optional filtering.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machineactions-collection
        """
        params = query.to_odata_filters if query else {}
        return MachineActionsResults(self, params)

    def get(self, id: str) -> MachineActionsResults:
        """Get a specific machine action by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machineaction-object
        """
        path = f"{self._PATH}/{id}"
        return MachineActionsResults(self, {}, path=path)

    def collectInvestigationPackage(
        self, device_id: str, payload: CollectInvestigationPackagePayload
    ) -> MachineActionsResults:
        """Collect an investigation package from a machine.

        If successful, this method returns 201 - Created response code and Machine Action in the response body.
        If a collection is already running, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/collect-investigation-package
        """
        return MachinesEndpoint(self._http, self._auth)._collectInvestigationPackage(
            device_id, payload
        )

    def getPackage(self, id: str) -> str:
        """Get the investigation package content.

        If Successfull it'll return the URI to the package in the "value" parameter of the response.

        If successful, this method returns 200, Ok response code with object that holds the link to the package in the "value" parameter.
        This link is valid for a short time and should be used immediately for downloading the package to a local storage.
        If the machine action for the collection exists but isn't complete, this returns 404 Not Found.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-package-sas-uri
        """
        path = f"{self._PATH}/{id}/GetPackageUri"
        response = self._request("GET", path)

        match response.status_code:
            case 200:
                json_response: dict[str, str] = response.json()
                return json_response.get("value", "")
            case 404:
                raise ValueError(
                    str(
                        f"Investigation package for machine action with ID {id} not found.\n"
                        "This may indicate that the machine action does not exist or that the collection is not yet complete."
                    )
                )
            case _:
                import httpx

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    raise RuntimeError(
                        f"Failed to get investigation package for machine action with ID {id}\nUnexpected status code returned."
                    ) from e

                raise RuntimeError(
                    f"Failed to get investigation package for machine action with ID {id}\nUnexpected status code returned: {response.status_code}"
                )

    def getLiveResponseResultDownloadLink(self, id: str, index: int = 0) -> str:
        """Get the download link for live response result.

        If successful, this method returns 200, Ok response code with object that holds the link to the command result in the value property.
        This link is valid for 30 minutes and should be used immediately for downloading the package to a local storage.
        An expired link can be re-created by another call, and there's no need to run live response again.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-live-response-result
        """
        path = f"{self._PATH}/{id}/GetLiveResponseResultDownloadLink(index={index})"
        response = self._request("GET", path)

        match response.status_code:
            case 200:
                json_response: dict[str, str] = response.json()
                return json_response.get("value", "")
            case 404:
                raise ValueError(
                    str(
                        f"Live response result for machine action with ID {id} and index {index} not found.\n"
                        "This may indicate that the machine action does not exist or that the collection is not yet complete."
                    )
                )
            case _:
                import httpx

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    raise RuntimeError(
                        f"Failed to get live response result download link for machine action with ID {id} and index {index}\nUnexpected status code returned."
                    ) from e

                raise RuntimeError(
                    f"Failed to get live response result download link for machine action with ID {id} and index {index}\nUnexpected status code returned: {response.status_code}"
                )

    def isolate(self, device_id: str, payload: IsolatePayload) -> MachineActionsResults:
        """Isolate a machine.

        If successful, this method returns 201 - Created response code and Machine Action in the response body.
        If the machine is already isolated, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/isolate-machine
        """
        return MachinesEndpoint(self._http, self._auth)._isolate(device_id, payload)

    def unisolate(
        self, device_id: str, payload: UnisolatePayload
    ) -> MachineActionsResults:
        """Unisolate a machine.

        If successful, this method returns 201 - Created response code and Machine Action in the response body.
        If the machine is not isolated, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/unisolate-machine
        """
        return MachinesEndpoint(self._http, self._auth)._unisolate(device_id, payload)

    def restrictCodeExecution(
        self, device_id: str, payload: RestrictCodeExecutionPayload
    ) -> MachineActionsResults:
        """Restrict code execution on a machine.

        If successful, this method returns 201 - Created response code and Machine Action in the response body.
        If code execution is already restricted, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/restrict-code-execution
        """
        return MachinesEndpoint(self._http, self._auth)._restrictCodeExecution(
            device_id, payload
        )

    def unrestrictCodeExecution(
        self, device_id: str, payload: UnrestrictCodeExecutionPayload
    ) -> MachineActionsResults:
        """Unrestrict code execution on a machine.

        If successful, this method returns 201 - Created response code and Machine Action in the response body.
        If code execution is not restricted, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/unrestrict-code-execution
        """
        return MachinesEndpoint(self._http, self._auth)._unrestrictCodeExecution(
            device_id, payload
        )

    def runAntiVirusScan(
        self, device_id: str, payload: RunAntiVirusScanPayload
    ) -> MachineActionsResults:
        """Run an antivirus scan on a machine.

        If successful, this method returns 201 - Created response code and Machine Action in the response body.
        If an antivirus scan is already running, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/run-av-scan
        """
        return MachinesEndpoint(self._http, self._auth)._runAntiVirusScan(
            device_id, payload
        )

    def runLiveResponse(
        self, device_id: str, payload: RunLiveResponsePayload
    ) -> MachineActionsResults:
        """Run a live response command on a machine.

        If successful, this method returns 201 - Created response code and Machine Action in the response body.
        If a live response command is already running, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/run-live-response
        """
        return MachinesEndpoint(self._http, self._auth)._runLiveResponse(
            device_id, payload
        )

    def offBoard(
        self, device_id: str, payload: OffBoardPayload
    ) -> MachineActionsResults:
        """Off-board a machine.

        If successful, this method returns 201 - Created response code and Machine Action in the response body.
        If the machine is already off-boarded, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/offboard-machine-api
        """
        return MachinesEndpoint(self._http, self._auth)._offBoard(device_id, payload)

    def stopAndQuarantineFile(
        self, device_id: str, payload: StopAndQuarantineFilePayload
    ) -> MachineActionsResults:
        """Stop and quarantine a file on a machine.

        If successful, this method returns 201 - Created response code and Machine Action in the response body.
        If the file is already quarantined, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/stop-and-quarantine-file
        """
        return MachinesEndpoint(self._http, self._auth)._stopAndQuarantineFile(
            device_id, payload
        )

    def cancel(self, id: str, payload: CancelPayload) -> MachineActionsResults:
        """Cancel a machine action.

        If successful, this method returns 200, OK response code with a Machine Action entity.\n
        If machine action entity with the specified id wasn't found - 404 Not Found.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/cancel-machine-action
        """
        path = f"{self._PATH}/{id}/cancel"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump(exclude_none=True)},
        )
