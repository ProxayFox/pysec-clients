"""Shared base primitives for all MDE endpoint modules.

This module defines:
- `BaseQuery`: Pydantic model providing common OData query parameters
  (``page_size``, ``top``, ``skip``) and an ``to_odata_filters`` helper that
  serialises field values into an OData ``$filter`` string.
- `BasePayload`: thin Pydantic model base for POST/PATCH request bodies.
- `BaseResults`: lazy result container that defers HTTP requests until a
  terminal materialization method (``to_json``, ``to_arrow``, ``to_polars``,
  ``refresh``) is invoked.
- `BaseEndpoint`: base class for all endpoint classes, owning the shared
  ``httpx.Client`` and ``MSALAuth`` instances and housing the ``_request``
  helper that injects bearer tokens per-request.

**Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/apis-intro
"""

from __future__ import annotations

import httpx
import asyncio
import pyarrow as pa
import polars as pl
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from http_to_arrow import ArrowRecordContainer

from ..auth import MSALAuth
from ..schemas import EXPORT_FILES_RESPONSE_SCHEMA
from ..viaFiles import RecordTransform, ViaFiles


class BaseQuery(BaseModel):
    """Base query parameters for API endpoints.

    All fields are optional — omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Example:
        query = BaseQuery(page_size=500)
    """

    page_size: int | None = Field(default=10000, ge=1, le=10000)
    top: int | None = Field(default=None, ge=1, le=10000)
    skip: int | None = Field(default=None, ge=0)
    # TODO: custom_query: str | list[str] | None = None

    @property
    def to_odata_filters(self) -> dict[str, str]:
        """Convert query fields to OData filter clauses.

        This is used by endpoints that support OData filtering. Only fields
        that are not None are included in the output.
        """
        filter_list: list[str] = []
        params: dict[str, str] = {}
        if self.page_size is not None:
            params["pageSize"] = str(self.page_size)
        if self.top is not None:
            params["$top"] = str(self.top)
        if self.skip is not None:
            params["$skip"] = str(self.skip)

        for field, value in self.model_dump(
            exclude={"page_size", "top", "skip"}
        ).items():
            match value:
                case str():
                    val = value.replace("'", "''")
                    filter_list.append(f"{field} eq '{val}'")
                case datetime():
                    val = value.isoformat()
                    filter_list.append((f"{field} eq {val}"))
                case list() if all(isinstance(v, str) for v in value):
                    values = ", ".join(f"'{v}'" for v in value)
                    filter_list.append(f"{field} in ({values})")
                case None:
                    pass
                case _:
                    raise TypeError(
                        str(
                            f"Unsupported filter value type for field: {field}, value: {value}"
                            "\nRaise an issue if you need support for this type."
                        )
                    )

        if filter_list:
            params["$filter"] = " and ".join(filter_list)

        return params


class BasePayload(BaseModel):
    """Base payload for API endpoints.

    Not all endpoints use a request body, but for those that do, the payload
    should inherit from this class. This is currently just a placeholder for
    consistency and future-proofing, as there are no common fields or logic
    defined here yet.
    """

    model_config = ConfigDict(extra="forbid")


class BaseResults:
    """Base results container for API endpoints."""

    SCHEMA: pa.Schema

    def __init__(
        self,
        endpoint: BaseEndpoint,
        params: dict[str, str],
        *,
        path: str | None = None,  # overrides endpoint._PATH for sub-resources
        single: bool = False,  # True when endpoint returns a bare object, not a collection
        files: bool = False,  # True when endpoint returns file export results
        method: str = "GET",
        request_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._params = params
        self._files = files
        self._path = path or endpoint._PATH
        self._single = single
        self._method = method
        self._request_kwargs = dict(request_kwargs or {})
        self._container: ArrowRecordContainer | None = None

    @staticmethod
    def _records_from_body(body: Any) -> list[dict[str, Any]]:
        if isinstance(body, list):
            return body
        if isinstance(body, dict):
            value = body.get("value", body)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                return [value]
        return []

    def _ensure_fetched(self) -> ArrowRecordContainer:
        if self._container is None:
            self._container = ArrowRecordContainer(
                schema=self.SCHEMA,
                unknown_field_policy="drop",
                coercion_policy="coerce",
            )

        if self._single:
            response = self._endpoint._request(
                self._method,
                self._path,
                params=self._params,
                **self._request_kwargs,
            )
            response.raise_for_status()
            self._container.extend(self._records_from_body(response.json()))
            del response  # free memory
        elif self._files:
            # For file export endpoints, we expect a single record containing the download URL
            response = self._endpoint._request(
                self._method,
                self._path,
                params=self._params,
                **self._request_kwargs,
            )
            response.raise_for_status()

            file_tbl: ArrowRecordContainer = ArrowRecordContainer(
                schema=EXPORT_FILES_RESPONSE_SCHEMA
            )
            file_tbl.extend(self._records_from_body(response.json()))

            urls = (
                file_tbl.to_polars_frame()
                .get_column("exportFiles")
                .explode()
                .drop_nulls()
                .to_list()
            )
            self._container = self._files_to_container(urls)
            del file_tbl, response  # free memory

        elif self._params.get("$top") or self._params.get("$skip"):
            # If $top or $skip is specified, we should not paginate
            response = self._endpoint._request(
                self._method,
                self._path,
                params=self._params,
                **self._request_kwargs,
            )
            response.raise_for_status()
            self._container.extend(self._records_from_body(response.json()))
            del response  # free memory
        else:
            self._endpoint._paginate_into(
                self._path,
                self._params,
                self._container,
                method=self._method,
                request_kwargs=self._request_kwargs,
            )

        return self._container

    def _files_to_container(self, urls: list[str]) -> ArrowRecordContainer:
        """Download export blobs via async streaming and return a populated container."""
        container = ArrowRecordContainer(
            schema=self.SCHEMA,
            unknown_field_policy="drop",
            coercion_policy="coerce",
        )

        asyncio.run(
            ViaFiles().download_export_files(
                urls,
                container,
                record_transform=self._normalize_export_record(),
            )
        )
        return container

    @staticmethod
    def _normalize_export_record() -> RecordTransform | None:
        """Return an optional transform applied to each export-file record.

        Subclasses override this when the export NDJSON nests payload data
        inside a wrapper key (e.g. ``DeviceGatheredInfo``).
        """
        return None

    def to_dicts(self) -> list[dict]:
        return self._ensure_fetched().to_table().to_pylist()

    def to_arrow(self) -> pa.Table:
        try:
            import pyarrow  # noqa: F401
        except ImportError:
            raise ImportError("Install with: uv add mde-client[arrow]") from None
        return self._ensure_fetched().to_table()

    def to_polars(self) -> pl.DataFrame:
        try:
            import polars  # noqa: F401
        except ImportError:
            raise ImportError("Install with: uv add mde-client[polars]") from None
        return self._ensure_fetched().to_polars_frame()

    def refresh(self) -> BaseResults:
        self._container = None
        return self


class BaseEndpoint:
    """Base class for API endpoints.

    Not intended to be used directly. Endpoint clients should inherit from this
    and implement their own methods.
    """

    _PATH: str = ""

    def __init__(self, http: httpx.Client, auth: MSALAuth) -> None:
        self._http = http
        self._auth = auth

    @staticmethod
    def _id_list(ids: str | list[str]) -> list[str]:
        return [ids] if isinstance(ids, str) else ids

    async def _arequest(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an authenticated async request, refreshing the token as needed."""
        async with httpx.AsyncClient(base_url=self._http.base_url) as client:
            return await client.request(
                method,
                path,
                headers={"Authorization": f"Bearer {self._auth.token}"},
                **kwargs,
            )

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Async Wrapper for _arequest to be used in sync methods."""
        return asyncio.run(self._arequest(method, path, **kwargs))

    async def _apaginate(
        self,
        path: str,
        params: dict[str, str],
        *,
        method: str = "GET",
        request_kwargs: dict[str, Any] | None = None,
    ) -> list[dict]:
        """Walk OData @odata.nextLink pagination and return all records."""
        all_records: list[dict] = []
        next_url: str | None = None
        request_kwargs = request_kwargs or {}

        while True:
            if next_url:
                response = await self._arequest(method, next_url, **request_kwargs)
            else:
                response = await self._arequest(
                    method,
                    path,
                    params=params,
                    **request_kwargs,
                )

            response.raise_for_status()
            body: dict = response.json()
            records: list[dict] | dict = body.get("value", [])
            all_records.extend(records)

            next_url = body.get("@odata.nextLink")

            if not next_url:
                break

        return all_records

    def _paginate(
        self,
        path: str,
        params: dict[str, str],
        *,
        method: str = "GET",
        request_kwargs: dict[str, Any] | None = None,
    ) -> list[dict]:
        """Async Wrapper for _paginate to be used in sync methods."""

        # If the caller specified $top or $skip, we should not paginate
        if params.get("$top") or params.get("$skip"):
            raise ValueError(
                "Cannot use _paginate when $top or $skip is specified in params."
                "Use _request instead, or remove $top/$skip to enable pagination."
            )

        return asyncio.run(
            self._apaginate(
                path,
                params,
                method=method,
                request_kwargs=request_kwargs,
            )
        )

    async def _apaginate_into(
        self,
        path: str,
        params: dict[str, str],
        container: ArrowRecordContainer,
        *,
        method: str = "GET",
        request_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Walk OData @odata.nextLink pagination, streaming each page into *container*.

        Unlike ``_apaginate`` this never builds a full ``list[dict]`` — each
        page's ``value`` array is fed directly into the container via
        ``container.extend()``.
        """
        next_url: str | None = None
        request_kwargs = request_kwargs or {}

        while True:
            if next_url:
                response = await self._arequest(method, next_url, **request_kwargs)
            else:
                response = await self._arequest(
                    method,
                    path,
                    params=params,
                    **request_kwargs,
                )

            response.raise_for_status()
            body: dict = response.json()
            container.extend(body.get("value", []))

            next_url = body.get("@odata.nextLink")
            if not next_url:
                break

    def _paginate_into(
        self,
        path: str,
        params: dict[str, str],
        container: ArrowRecordContainer,
        *,
        method: str = "GET",
        request_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Sync wrapper for ``_apaginate_into``."""

        # If the caller specified $top or $skip, we should not paginate
        if params.get("$top") or params.get("$skip"):
            raise ValueError(
                "Cannot use _paginate when $top or $skip is specified in params."
                "Use _request instead, or remove $top/$skip to enable pagination."
            )

        asyncio.run(
            self._apaginate_into(
                path,
                params,
                container,
                method=method,
                request_kwargs=request_kwargs,
            )
        )
