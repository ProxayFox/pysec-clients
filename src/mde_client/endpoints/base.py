from __future__ import annotations

import httpx
import asyncio
import pyarrow as pa
from datetime import datetime
from pydantic import BaseModel, Field
from http_to_arrow import ArrowRecordContainer

from ..auth import MSALAuth


class BaseQuery(BaseModel):
    """Base query parameters for API endpoints.

    All fields are optional — omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Example:
        query = BaseQuery(page_size=500)
    """

    page_size: int = Field(default=10000, ge=1, le=10000)
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
                case _:
                    raise TypeError(
                        str(
                            f"Unsupported filter value type for field: {field}."
                            "\nRaise an issue if you need support for this type."
                        )
                    )

        if filter_list:
            params["$filter"] = " and ".join(filter_list)

        return params


class BaseResults:
    SCHEMA: pa.Schema

    def __init__(
        self,
        endpoint: BaseEndpoint,
        params: dict[str, str],
        *,
        path: str | None = None,  # overrides endpoint._PATH for sub-resources
    ) -> None:
        self._endpoint = endpoint
        self._params = params
        self._path = path or endpoint._PATH
        self._container: ArrowRecordContainer | None = None

    def _ensure_fetched(self) -> ArrowRecordContainer:
        if self._container is None:
            self._container = ArrowRecordContainer(
                schema=self.SCHEMA,
                unknown_field_policy="drop",
                coercion_policy="coerce",
            )
            self._endpoint._paginate_into(
                self._path, self._params, self._container)
        return self._container

    def to_json(self) -> list[dict]:
        return self._ensure_fetched().to_table().to_pylist()

    def to_arrow(self) -> pa.Table:
        try:
            import pyarrow  # noqa: F401
        except ImportError:
            raise ImportError(
                "Install with: uv add microsoft-mde-client[arrow]"
            ) from None
        return self._ensure_fetched().to_table()

    def to_polars(self):
        try:
            import polars  # noqa: F401
        except ImportError:
            raise ImportError(
                "Install with: uv add microsoft-mde-client[polars]"
            ) from None
        return self._ensure_fetched().to_polars_frame()

    def refresh(self) -> "BaseResults":
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

    async def _apaginate(self, path: str, params: dict[str, str]) -> list[dict]:
        """Walk OData @odata.nextLink pagination and return all records."""
        all_records: list[dict] = []
        next_url: str | None = None

        while True:
            if next_url:
                response = await self._arequest("GET", next_url)
            else:
                response = await self._arequest("GET", path, params=params)

            response.raise_for_status()
            body: dict = response.json()
            records: list[dict] | dict = body.get("value", [])
            all_records.extend(records)

            next_url = body.get("@odata.nextLink")

            if not next_url:
                break

        return all_records

    def _paginate(self, path: str, params: dict[str, str]) -> list[dict]:
        """Async Wrapper for _paginate to be used in sync methods."""

        # If the caller specified $top or $skip, we should not paginate
        if params.get("$top") or params.get("$skip"):
            raise ValueError(
                "Cannot use _paginate when $top or $skip is specified in params."
                "Use _request instead, or remove $top/$skip to enable pagination."
            )

        return asyncio.run(self._apaginate(path, params))

    async def _apaginate_into(
        self,
        path: str,
        params: dict[str, str],
        container: ArrowRecordContainer,
    ) -> None:
        """Walk OData @odata.nextLink pagination, streaming each page into *container*.

        Unlike ``_apaginate`` this never builds a full ``list[dict]`` — each
        page's ``value`` array is fed directly into the container via
        ``container.extend()``.
        """
        next_url: str | None = None

        while True:
            if next_url:
                response = await self._arequest("GET", next_url)
            else:
                response = await self._arequest("GET", path, params=params)

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
    ) -> None:
        """Sync wrapper for ``_apaginate_into``."""

        # If the caller specified $top or $skip, we should not paginate
        if params.get("$top") or params.get("$skip"):
            raise ValueError(
                "Cannot use _paginate when $top or $skip is specified in params."
                "Use _request instead, or remove $top/$skip to enable pagination."
            )

        asyncio.run(self._apaginate_into(path, params, container))
