"""Runtime access to vendored MDE source contracts.

This module never parses EDMX and contains no generation logic.
"""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from functools import cached_property
from importlib import resources
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from . import _CONTRACT_INDEX
from ._models import SourceContract

if TYPE_CHECKING:
    import pyarrow as pa


@dataclass(frozen=True)
class ContractBundle:
    """One canonical source contract and its generated projections."""

    slug: str
    schema_constant: str

    @cached_property
    def contract(self) -> SourceContract:
        text = _resource_text(self.slug, "contract.json")
        return SourceContract.model_validate_json(text)

    @cached_property
    def json_schema(self) -> MappingProxyType[str, Any]:
        value = json.loads(_resource_text(self.slug, "schema.schema.json"))
        if not isinstance(value, dict):
            raise TypeError(f"{self.slug}: JSON Schema root must be an object")
        return MappingProxyType(value)

    @cached_property
    def arrow_schema(self) -> pa.Schema:
        module = importlib.import_module(f"mde_client.contracts.{self.slug}.schema")
        return getattr(module, self.schema_constant)

    @property
    def name(self) -> str:
        return self.contract.name

    @property
    def version(self) -> str:
        return self.contract.version

    @property
    def definition_hash(self) -> str:
        if self.contract.hashes is None:
            raise ValueError(f"{self.slug}: definition hash is missing")
        return self.contract.hashes.definition

    @property
    def arrow_hash(self) -> str:
        if self.contract.hashes is None:
            raise ValueError(f"{self.slug}: Arrow hash is missing")
        return self.contract.hashes.arrow

    @property
    def source_metadata_hash(self) -> str | None:
        return self.contract.generation.source_metadata_hash


def list_contracts() -> tuple[str, ...]:
    """Return stable contract slugs in lexical order."""
    return tuple(sorted(_CONTRACT_INDEX))


def get_contract(slug_or_name: str) -> ContractBundle:
    """Load a contract by its directory slug or canonical contract name."""
    slug = slug_or_name
    if slug not in _CONTRACT_INDEX:
        slug = next(
            (
                candidate
                for candidate, metadata in _CONTRACT_INDEX.items()
                if metadata["name"] == slug_or_name
            ),
            "",
        )
    if not slug:
        raise KeyError(f"Unknown MDE contract {slug_or_name!r}")
    metadata = _CONTRACT_INDEX[slug]
    return ContractBundle(slug=slug, schema_constant=metadata["schema"])


def _resource_text(slug: str, filename: str) -> str:
    resource = resources.files("mde_client.contracts").joinpath(slug, filename)
    return resource.read_text(encoding="utf-8")


__all__ = ["ContractBundle", "get_contract", "list_contracts"]
