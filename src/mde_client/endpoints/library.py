from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import BaseEndpoint, BasePayload, BaseResults
from ..schemas import LIBRARY_FILES_SCHEMA


class LibraryFilesUpdatePayload(BasePayload):
    """Multipart form-data payload for uploading live response library files."""

    file_name: str = Field(min_length=1)
    file_content: bytes = Field(min_length=1)
    content_type: str = Field(default="application/octet-stream")
    description: str = Field(min_length=1)
    parameters_description: str = Field(default="")
    override_if_exists: bool | None = Field(default=None)
    has_parameters: bool | None = Field(default=None)

    def to_request_kwargs(self) -> dict[str, Any]:
        """Serialize the payload into httpx multipart request kwargs."""
        data: dict[str, str] = {
            "Description": self.description,
            "ParametersDescription": self.parameters_description,
        }

        has_parameters = self.has_parameters
        if has_parameters is None and self.parameters_description:
            has_parameters = True

        if has_parameters is not None:
            data["HasParameters"] = str(has_parameters).lower()
        if self.override_if_exists is not None:
            data["OverrideIfExists"] = str(self.override_if_exists).lower()

        return {
            "files": {
                "File": (
                    self.file_name,
                    self.file_content,
                    self.content_type,
                )
            },
            "data": data,
        }


class LibraryFilesResults(BaseResults):
    """Results from the /api/libraryfiles endpoint."""

    SCHEMA = LIBRARY_FILES_SCHEMA


class LibraryFilesEndpoint(BaseEndpoint):
    """Endpoint for /api/libraryfiles."""

    _PATH = "/api/libraryfiles"

    def get_all(self) -> LibraryFilesResults:
        """Get all library files.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/list-library-files
        """
        return LibraryFilesResults(self, {})

    def upload(self, payload: LibraryFilesUpdatePayload) -> bool:
        """Update a library file.

        If successful, this method returns 200 - OK response code and the uploaded live response library entity in the response body.
        If not successful: this method returns 400 - Bad Request. Bad request usually indicates incorrect body.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/upload-library
        """
        response = self._request("POST", self._PATH, json=payload.model_dump())
        match response.status_code:
            case 200:
                return True
            case 400:
                raise ValueError(
                    f"Failed to update library file: {payload.file_name}\nBad Request - usually indicates that the request payload is malformed."
                )
            case _:
                import httpx

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    raise RuntimeError(
                        f"Failed to update library file: {payload.file_name}\nUnexpected status code returned."
                    ) from e
                return False  # Should not be reached, but included for completeness

    def delete(self, file_name: str) -> bool:
        """Delete a library file.

        If successful, this method returns 204 - No Content response code.
        If not successful: this method returns 404 - Not Found. Not Found usually indicates that the file with the specified name does not exist.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/delete-library-file
        """
        path = f"{self._PATH}/{file_name}"
        response = self._request("DELETE", path)
        match response.status_code:
            case 204:
                return True
            case 404:
                raise ValueError(
                    f"Failed to delete library file with name {file_name}: Not Found - usually indicates that the file with the specified name does not exist."
                )
            case _:
                import httpx

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    raise RuntimeError(
                        f"Failed to delete library file with name {file_name}: Unexpected status code returned."
                    ) from e
                return False  # Should not be reached, but included for completeness
