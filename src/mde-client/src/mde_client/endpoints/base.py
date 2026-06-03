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
import random
import time
import pyarrow as pa
import polars as pl
import orjson
from collections import deque
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from collections.abc import Iterator
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
    sinceTime: datetime | int | str | None = None

    @property
    def to_odata_filters(self) -> dict[str, str]:
        """Convert query fields to OData filter clauses.

        This is used by endpoints that support OData filtering. Only fields
        that are not None are included in the output.
        """
        manual_pagination = self.top is not None or self.skip is not None
        if (
            "page_size" in self.model_fields_set
            and self.page_size is not None
            and manual_pagination
        ):
            raise ValueError(
                "page_size cannot be combined with $top or $skip. "
                "Set page_size=None to use manual $top/$skip pagination."
            )

        filter_list: list[str] = []
        params: dict[str, str] = {}
        if self.page_size is not None and not manual_pagination:
            params["pageSize"] = str(self.page_size)
        if self.top is not None:
            params["$top"] = str(self.top)
        if self.skip is not None:
            params["$skip"] = str(self.skip)
        match self.sinceTime:
            case int() as days:
                dateTime = (
                    datetime.now(tz=timezone.utc) - timedelta(days=days)
                ).isoformat()
            case datetime():
                if self.sinceTime.tzinfo is None:
                    dateTime = self.sinceTime.replace(tzinfo=timezone.utc).isoformat()
                else:
                    dateTime = self.sinceTime.astimezone(timezone.utc).isoformat()
            case str() as s:
                dateTime = s.replace("'", "''")
            case None:
                dateTime = None
            case _:
                raise TypeError(
                    str(
                        f"Unsupported type for 'sinceTime' field: {type(self.sinceTime)}, value: {self.sinceTime}"
                        "\nRaise an issue if you need support for this type."
                    )
                )
        if dateTime is not None:
            params["sinceTime"] = dateTime

        for field, value in self.model_dump(
            exclude={"page_size", "top", "skip", "sinceTime"}
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

    def to_datetime_format(
        self, format: str = "%Y-%m-%d", regex: str | None = None
    ) -> BaseQuery:
        """Converts the sinceTime field to a string in the specified format, if it is not already a string."""
        from re import match

        match self.sinceTime:
            case int() as days:
                self.sinceTime = (
                    datetime.now(tz=timezone.utc) - timedelta(days=days)
                ).strftime(format)
            case datetime():
                if self.sinceTime.tzinfo is None:
                    self.sinceTime = self.sinceTime.replace(
                        tzinfo=timezone.utc
                    ).strftime(format)
                else:
                    self.sinceTime = self.sinceTime.astimezone(timezone.utc).strftime(
                        format
                    )
            case str() as s:
                if regex is not None and not match(regex, s):
                    raise ValueError(
                        f"String value for 'sinceTime' must match regex: {regex}"
                    )
                self.sinceTime = s
            case _:
                pass
        return self


class BasePayload(BaseModel):
    """Base payload for API endpoints.

    Not all endpoints use a request body, but for those that do, the payload
    should inherit from this class. This is currently just a placeholder for
    consistency and future-proofing, as there are no common fields or logic
    defined here yet.
    """

    model_config = ConfigDict(extra="forbid")


class BaseResults:
    """Base results wrapper for API endpoints.

    This class provides lazy evaluation of results, deferring HTTP requests until
    a terminal method is called (e.g. ``to_dicts``, ``to_arrow``, ``to_polars``, ``refresh``).
    """

    # Subclasses should override this with a Pydantic schema for the expected record shape, if desired.
    SCHEMA: pa.Schema | None
    USE_CONCURRENT_SKIP_PAGINATION = False
    SKIP_PAGE_SIZE = 8000
    SKIP_MAX_CONCURRENT = 10

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
        use_concurrent_skip_pagination: bool | None = None,
        skip_page_size: int | None = None,
        skip_max_concurrent: int | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._params = params
        self._files = files
        self._path = path or endpoint._PATH
        self._single = single
        self._method = method
        self._request_kwargs = dict(request_kwargs or {})
        self._use_concurrent_skip_pagination = (
            self.USE_CONCURRENT_SKIP_PAGINATION
            if use_concurrent_skip_pagination is None
            else use_concurrent_skip_pagination
        )
        self._skip_page_size = (
            self.SKIP_PAGE_SIZE if skip_page_size is None else skip_page_size
        )
        self._skip_max_concurrent = (
            self.SKIP_MAX_CONCURRENT
            if skip_max_concurrent is None
            else skip_max_concurrent
        )
        self._container: ArrowRecordContainer | None = None

    @staticmethod
    def _records_from_body(body: Any) -> list[dict[str, Any]]:
        """Extract a list of record dicts from the response body, handling various nesting patterns."""
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
        """Fetch results from the API if they haven't been fetched already, and return a populated container."""
        if self._container is not None:
            return self._container

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
        elif self._use_concurrent_skip_pagination:
            self._endpoint._paginate_skip_into(
                self._path,
                self._params,
                self._container,
                page_size=self._skip_page_size,
                max_concurrent=self._skip_max_concurrent,
                method=self._method,
                request_kwargs=self._request_kwargs,
            )
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
        """Materialize results into a list of dicts."""
        # Polars is faster at converting from Arrow to dicts than pyarrow.to_pylist, so we use Polars as an intermediary here.
        return self._ensure_fetched().to_polars.to_dicts()

    def to_json(self, indent: bool = False) -> str | bytes:
        """Materialize results into a JSON string.

        Returns a str if indent=False, bytes if indent=True (since orjson returns bytes). You can decode the bytes to get a str if needed.
        """
        if indent:
            return orjson.dumps(
                self._ensure_fetched().to_polars.to_dicts(), option=orjson.OPT_INDENT_2
            ).decode()
        else:
            return orjson.dumps(self._ensure_fetched().to_polars.to_dicts())

    def to_arrow(self) -> pa.Table:
        """Materialize results into a PyArrow Table."""
        return self._ensure_fetched().to_arrow

    def to_polars(self) -> pl.DataFrame:
        """Materialize results into a Polars DataFrame."""
        return self._ensure_fetched().to_polars

    def refresh(self) -> BaseResults:
        """Clear any cached results, forcing the next materialization to re-query the API."""
        self._container = None
        return self


class BaseEndpoint:
    """Base class for API endpoints."""

    _PATH: str = ""
    _RATE_LIMIT_CALLS_PER_MINUTE: int = 100
    _RATE_LIMIT_CALLS_PER_HOUR: int = 1500
    _RATE_LIMIT_MAX_RETRIES: int = 5
    _RATE_LIMIT_BACKOFF_BASE_SECONDS: float = 5.0

    def __init__(self, http: httpx.Client, auth: MSALAuth) -> None:
        self._http = http
        self._auth = auth
        self._rate_limit_minute_calls: deque[float] = deque()
        self._rate_limit_hour_calls: deque[float] = deque()
        self._rate_limit_lock: asyncio.Lock | None = None
        self._rate_limit_lock_loop: asyncio.AbstractEventLoop | None = None

    # === Helpers for child endpoints ===
    @staticmethod
    def _id_list(ids: str | list[str]) -> list[str]:
        return [ids] if isinstance(ids, str) else ids

    @staticmethod
    def _chunks[T](lst: list[T], n: int) -> Iterator[list[T]]:
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    @staticmethod
    def _trim_rate_window(calls: deque[float], cutoff: float) -> None:
        while calls and calls[0] <= cutoff:
            calls.popleft()

    @staticmethod
    def _raise_for_response_status(response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code == 403:
                error_body = e.response.json()
                if "error" in error_body and "message" in error_body["error"]:
                    raise PermissionError(
                        str(
                            "Insufficient permissions to access this endpoint. Check the message bellow for required permissions.\n"
                            f"Code: {error_body['error']['code']}\n"
                            f"Message:\n{error_body['error']['message']}"
                        )
                    ) from None

            raise httpx.HTTPStatusError(
                str(
                    f"Request failed for URL: {response.url}\n"
                    f"Status code: {response.status_code}\n"
                    f"Response body: {response.text}"
                ),
                request=e.request,
                response=e.response,
            ) from None

    @staticmethod
    def _skip_pagination_params(params: dict[str, str]) -> dict[str, str]:
        return {
            key: value for key, value in params.items() if key.lower() != "pagesize"
        }

    # === Rate Limiting Logic ===
    def _current_rate_limit_lock(self) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        if self._rate_limit_lock is None or self._rate_limit_lock_loop is not loop:
            self._rate_limit_lock = asyncio.Lock()
            self._rate_limit_lock_loop = loop
        return self._rate_limit_lock

    def _monotonic(self) -> float:
        return time.monotonic()

    async def _asleep(self, delay: float) -> None:
        await asyncio.sleep(delay)

    def _rate_limit_jitter(self) -> float:
        return random.uniform(0.0, self._RATE_LIMIT_BACKOFF_BASE_SECONDS)

    async def _wait_for_rate_limit_slot(self) -> None:
        """Wait until this endpoint instance has capacity for another request."""
        while True:
            async with self._current_rate_limit_lock():
                now = self._monotonic()
                self._trim_rate_window(self._rate_limit_minute_calls, now - 60.0)
                self._trim_rate_window(self._rate_limit_hour_calls, now - 3600.0)

                delays: list[float] = []
                if (
                    self._RATE_LIMIT_CALLS_PER_MINUTE > 0
                    and len(self._rate_limit_minute_calls)
                    >= self._RATE_LIMIT_CALLS_PER_MINUTE
                ):
                    delays.append(60.0 - (now - self._rate_limit_minute_calls[0]))
                if (
                    self._RATE_LIMIT_CALLS_PER_HOUR > 0
                    and len(self._rate_limit_hour_calls)
                    >= self._RATE_LIMIT_CALLS_PER_HOUR
                ):
                    delays.append(3600.0 - (now - self._rate_limit_hour_calls[0]))

                if not delays:
                    self._rate_limit_minute_calls.append(now)
                    self._rate_limit_hour_calls.append(now)
                    return

            await self._asleep(max(0.0, max(delays)))

    def _retry_after_delay(self, response: httpx.Response) -> float | None:
        value = response.headers.get("Retry-After")
        if value is None:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
            except TypeError, ValueError:
                return None
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - datetime.now(tz=timezone.utc)).total_seconds())

    def _backoff_delay(self, attempt: int) -> float:
        return (
            self._RATE_LIMIT_BACKOFF_BASE_SECONDS * (2**attempt)
            + self._rate_limit_jitter()
        )

    # === Single HTTP Request ===
    async def _arequest(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an authenticated async request, refreshing the token as needed."""
        async with httpx.AsyncClient(
            base_url=self._http.base_url, timeout=self._http.timeout
        ) as client:
            return await client.request(
                method,
                path,
                headers={"Authorization": f"Bearer {self._auth.token}"},
                **kwargs,
            )

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Async Wrapper for _arequest to be used in sync methods."""
        return asyncio.run(self._arequest(method, path, **kwargs))

    async def _arequest_with_rate_limit(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        """Make an async request with endpoint-scoped throttling and 429 backoff."""
        for attempt in range(self._RATE_LIMIT_MAX_RETRIES + 1):
            await self._wait_for_rate_limit_slot()
            response = await self._arequest(method, path, **kwargs)
            if response.status_code != 429:
                return response
            if attempt >= self._RATE_LIMIT_MAX_RETRIES:
                return response

            delay = self._retry_after_delay(response)
            if delay is None:
                delay = self._backoff_delay(attempt)
            await self._asleep(delay)

        raise RuntimeError("unreachable rate-limit retry state")

    # === Pagination HTTP Requests ===
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
        """Sync wrapper for ``_apaginate``."""

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

            self._raise_for_response_status(response)
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
                "Cannot use _paginate_into when $top or $skip is specified in params."
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

    async def _fetch_skip_page(
        self,
        path: str,
        params: dict[str, str],
        offset: int,
        page_size: int,
        *,
        method: str,
        request_kwargs: dict[str, Any],
    ) -> tuple[int, list[dict[str, Any]]]:
        page_params = self._skip_pagination_params(params)
        page_params["$top"] = str(page_size)
        page_params["$skip"] = str(offset)

        response = await self._arequest_with_rate_limit(
            method,
            path,
            params=page_params,
            **request_kwargs,
        )
        self._raise_for_response_status(response)

        body = response.json()
        records = body.get("value", []) if isinstance(body, dict) else []
        if not isinstance(records, list):
            return offset, []
        return offset, records

    async def _apaginate_skip_into(
        self,
        path: str,
        params: dict[str, str],
        container: ArrowRecordContainer,
        *,
        page_size: int = 8000,
        max_concurrent: int = 10,
        method: str = "GET",
        request_kwargs: dict[str, Any] = dict(),
    ) -> None:
        """Fetch predictable OData $top/$skip windows concurrently into *container*."""
        if params.get("$top") or params.get("$skip"):
            raise ValueError(
                "Cannot use concurrent skip pagination when $top or $skip is specified in params."
            )
        if page_size <= 0:
            raise ValueError("page_size must be greater than 0.")
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be greater than 0.")

        effective_concurrency = max_concurrent
        if self._RATE_LIMIT_CALLS_PER_MINUTE > 0:
            effective_concurrency = min(
                effective_concurrency,
                self._RATE_LIMIT_CALLS_PER_MINUTE,
            )
        if self._RATE_LIMIT_CALLS_PER_HOUR > 0:
            effective_concurrency = min(
                effective_concurrency,
                self._RATE_LIMIT_CALLS_PER_HOUR,
            )

        offset = 0
        while True:
            offsets = [
                offset + (page_size * index) for index in range(effective_concurrency)
            ]
            pages = await asyncio.gather(
                *(
                    self._fetch_skip_page(
                        path,
                        params,
                        skip,
                        page_size,
                        method=method,
                        request_kwargs=request_kwargs,
                    )
                    for skip in offsets
                )
            )

            should_stop = False
            for _, records in sorted(pages, key=lambda page: page[0]):
                if not records:
                    should_stop = True
                    break
                container.extend(records)
                if len(records) < page_size:
                    should_stop = True
                    break

            if should_stop:
                break
            offset += page_size * effective_concurrency

    def _paginate_skip_into(
        self,
        path: str,
        params: dict[str, str],
        container: ArrowRecordContainer,
        *,
        page_size: int = 8000,
        max_concurrent: int = 10,
        method: str = "GET",
        request_kwargs: dict[str, Any] = dict(),
    ) -> None:
        """Sync wrapper for ``_apaginate_skip_into``."""
        asyncio.run(
            self._apaginate_skip_into(
                path,
                params,
                container,
                page_size=page_size,
                max_concurrent=max_concurrent,
                method=method,
                request_kwargs=request_kwargs,
            )
        )
