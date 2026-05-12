from __future__ import annotations

import pyarrow as pa
from datetime import datetime
from httpx import HTTPStatusError
from typing import TYPE_CHECKING, cast

from .base import BaseEndpoint, BaseResults, BaseQuery, BasePayload
from ..schemas import INDICATOR_SCHEMA
from ..models.enums import TI_INDICATOR_TYPE, TI_INDICATOR_ACTION, SEVERITY

if TYPE_CHECKING:
    pass


class IndicatorsQuery(BaseQuery):
    """Query parameters for the /api/indicators endpoint."""

    createdByDisplayName: str | None = None
    expirationTime: datetime | None = None
    generateAlert: bool | None = None
    title: str | None = None
    rbacGroupNames: str | list[str] | None = None
    rbacGroupIds: str | list[str] | None = None
    indicatorValue: str | None = None
    indicatorType: TI_INDICATOR_TYPE | list[TI_INDICATOR_TYPE] | None = None
    creationTimeDateTimeUtc: datetime | None = None
    createdBy: str | None = None
    action: TI_INDICATOR_ACTION | list[TI_INDICATOR_ACTION] | None = None
    severity: SEVERITY | list[SEVERITY] | None = None


class IndicatorsSubmitPayload(BasePayload):
    """Payload for submitting a new indicator."""

    indicatorValue: str | None
    indicatorType: TI_INDICATOR_TYPE | None
    action: TI_INDICATOR_ACTION | None
    application: str | None
    title: str | None
    description: str | None
    expirationTime: datetime | None
    severity: SEVERITY | None
    recommendedActions: str | None
    rbacGroupNames: str | None
    educateUrl: str | None
    generateAlert: bool | None


class IndicatorsResults(BaseResults):
    """Results for the /api/indicators endpoint."""

    SCHEMA = INDICATOR_SCHEMA


class ImportIndicatorResults(BaseResults):
    """Results for the /api/indicators/import endpoint.

    TODO: Fix the mde_contract.py script to generate this schema properly instead of using the same schema as for single indicator submission.
    """

    SCHEMA: pa.Schema = pa.schema(
        [
            pa.field("id", pa.string()),
            pa.field("indicator", pa.string()),
            pa.field("isFailed", pa.bool_(), nullable=False),
            pa.field("failureReason", pa.string()),
        ]
    )


class IndicatorsEndpoint(BaseEndpoint):
    """Endpoint for interacting with indicators."""

    _PATH = "/api/indicators"
    _BATCH_SIZE_LIMIT = 500

    def get_all(self, query: IndicatorsQuery | None = None) -> IndicatorsResults:
        """Get indicators with optional filters.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-ti-indicators-collection
        """
        params = query.to_odata_filters if query else {}
        return IndicatorsResults(self, params)

    def submit(self, payload: IndicatorsSubmitPayload) -> IndicatorsResults:
        """Submit a new indicator.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/post-ti-indicator
        """
        return IndicatorsResults(
            self,
            {},
            single=True,
            method="POST",
            request_kwargs={"json": payload.model_dump(exclude_none=True)},
        )

    def batch_import(
        self, payload: list[IndicatorsSubmitPayload]
    ) -> ImportIndicatorResults | list[ImportIndicatorResults]:
        """Batch import indicators.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/import-ti-indicators
        """
        if len(payload) > self._BATCH_SIZE_LIMIT:
            chunks = list(self._chunks(payload, self._BATCH_SIZE_LIMIT))
            results: list[ImportIndicatorResults] = []
            for chunk in chunks:
                # Cast is required for type checking, since it's been chunked into smaller lists,
                # but the batch_import function still returns a single ImportIndicatorResults object for each chunk.
                result: ImportIndicatorResults = cast(
                    ImportIndicatorResults, self.batch_import(chunk)
                )
                results.append(result)
            return results

        path = f"{self._PATH}/import"
        trf_payload: dict[str, list[dict[str, str | int | bool | datetime | None]]] = {
            "indicators": [p.model_dump(exclude_none=True) for p in payload]
        }

        return ImportIndicatorResults(
            self,
            {},
            single=True,
            method="POST",
            path=path,
            request_kwargs={"json": trf_payload},
        )

    def delete(self, id: str) -> bool:
        """Delete an indicator by ID.\n
        If the indicator is successfully deleted, returns True. If the indicator is not found, returns False. If any other error occurs, raises an exception.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/delete-ti-indicator-by-id
        """
        result = self._request("DELETE", f"{self._PATH}/{id}")

        match result.status_code:
            case 204:
                # If Indicator exists and deleted successfully - 204 OK without content.
                return True
            case 404:
                # If Indicator with the specified ID wasn't found - 404 Not Found.
                return False
            case _:
                try:
                    result.raise_for_status()
                except HTTPStatusError as e:
                    raise RuntimeError(
                        f"Failed to delete indicator with ID {id}: {e}"
                    ) from e
                return False

    def batch_delete(self, ids: list[str]) -> bool:
        """Batch delete indicators by ID.\n

        Note:
            - If Indicators all existed and were deleted successfully - 204 OK without content.
            - If indicator IDs list is empty or exceeds size limit - 400 Bad Request.
            - If any indicator ID is invalid - 400 Bad Request.
            - If any Indicator ID wasn't found - 404 Not Found.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/batch-delete-ti-indicators
        """
        if len(ids) > self._BATCH_SIZE_LIMIT:
            chunks = list(self._chunks(ids, self._BATCH_SIZE_LIMIT))
            results = [self.batch_delete(chunk) for chunk in chunks]
            return all(results)

        payload = {"ids": ids}
        result = self._request("POST", f"{self._PATH}/batchDelete", json=payload)

        match result.status_code:
            case 204:
                # If Indicators all existed and were deleted successfully - 204 OK without content.
                return True
            case 400:
                raise ValueError(
                    f"Invalid request for batch deleting indicators: {result.text}"
                )
            case 404:
                raise ValueError(
                    f"One or more indicator IDs not found for batch deletion: {result.text}"
                )
            case _:
                try:
                    result.raise_for_status()
                except HTTPStatusError as e:
                    raise RuntimeError(
                        f"Failed to batch delete indicators with IDs {ids}: {e}"
                    ) from e
                return False
