from __future__ import annotations

import polars as pl
import orjson
from typing import TYPE_CHECKING
from http_to_arrow import ArrowRecordContainer

from .base import BaseEndpoint

if TYPE_CHECKING:
    import pyarrow as pa


class AdvancedHuntingQueriesResults:
    """Results from the /api/advancedqueries/run endpoint."""

    def __init__(self, endpoint: AdvancedHuntingQueriesEndpoint, path: str, query: str):
        self._endpoint = endpoint
        self._path = path
        self._query = query
        self._container: ArrowRecordContainer | None = None

    def _fetched(self) -> ArrowRecordContainer:
        """Fetch results from the API if they haven't been fetched already, and return a populated container."""
        if self._container is not None:
            return self._container

        # The API returns results in pages, and we want to accumulate them into a single container.
        self._container = ArrowRecordContainer(schema=None)
        ctn = ArrowRecordContainer(schema=None)
        response = self._endpoint._request(
            "POST",
            self._path,
            json={"Query": self._query},
        ).json()

        ctn.extend(response["Results"])

        return ctn

    def to_dicts(self) -> list[dict]:
        """Materialize results into a list of dicts."""
        # Polars is faster at converting from Arrow to dicts than pyarrow.to_pylist, so we use Polars as an intermediary here.
        return self._fetched().to_polars.to_dicts()

    def to_json(self, indent: bool = False) -> str | bytes:
        """Materialize results into a JSON string.

        Returns a str if indent=False, bytes if indent=True (since orjson returns bytes). You can decode the bytes to get a str if needed.
        """
        if indent:
            return orjson.dumps(
                self._fetched().to_polars.to_dicts(), option=orjson.OPT_INDENT_2
            ).decode()
        else:
            return orjson.dumps(self._fetched().to_polars.to_dicts())

    def to_arrow(self) -> pa.Table:
        """Materialize results into a PyArrow Table."""
        return self._fetched().to_arrow

    def to_polars(self) -> pl.DataFrame:
        """Materialize results into a Polars DataFrame."""
        return self._fetched().to_polars

    def refresh(self) -> AdvancedHuntingQueriesResults:
        """Clear any cached results, forcing the next materialization to re-query the API."""
        self._container = None
        return self


class AdvancedHuntingQueriesEndpoint(BaseEndpoint):
    """Endpoint for /api/advancedqueries/run."""

    _PATH = "/api/advancedqueries/run"

    def run(self, query: str) -> AdvancedHuntingQueriesResults:
        """Run an advanced hunting query."""
        return AdvancedHuntingQueriesResults(self, self._PATH, query)
