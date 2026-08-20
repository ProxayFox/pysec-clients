"""Contract version registry and release protection."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import SourceContract

_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class VersionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    version: str = "1.0.0"
    released: bool = False
    definition_hash: str | None = Field(default=None, alias="definitionHash")

    @field_validator("version")
    @classmethod
    def _valid_semver(cls, value: str) -> str:
        if not _SEMVER.fullmatch(value):
            raise ValueError("must be a semantic version")
        return value

    @field_validator("definition_hash")
    @classmethod
    def _valid_hash(cls, value: str | None) -> str | None:
        if value is not None and not _SHA256.fullmatch(value):
            raise ValueError("must be a sha256:<64 lowercase hex> digest")
        return value


class VersionRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    format_version: str = Field(default="1.0.0", alias="formatVersion")
    contracts: dict[str, VersionEntry] = Field(default_factory=dict)

    def version_for(self, slug: str) -> str:
        entry = self.contracts.get(slug)
        return entry.version if entry else "1.0.0"

    def guard_released(self, slug: str, contract: SourceContract) -> None:
        entry = self.contracts.get(slug)
        if not entry or not entry.released or entry.definition_hash is None:
            return
        if contract.hashes is None:
            raise ValueError(f"{slug}: cannot guard released contract without hashes")
        if entry.definition_hash != contract.hashes.definition:
            raise ValueError(
                f"{slug} {entry.version} is released and immutable; "
                f"definition changed from {entry.definition_hash} to "
                f"{contract.hashes.definition}. Confirm a semver bump in "
                "versions.json."
            )

    def synchronize(self, contracts: dict[str, SourceContract]) -> None:
        for slug, contract in sorted(contracts.items()):
            entry = self.contracts.setdefault(
                slug, VersionEntry(version=contract.version)
            )
            if entry.version != contract.version:
                raise ValueError(
                    f"{slug}: registry version {entry.version} differs from "
                    f"contract version {contract.version}"
                )
            if entry.released and entry.definition_hash is None:
                if contract.hashes is None:
                    raise ValueError(f"{slug}: contract hashes are missing")
                entry.definition_hash = contract.hashes.definition


def load_registry(path: Path) -> VersionRegistry:
    if not path.exists():
        return VersionRegistry()
    return VersionRegistry.model_validate_json(path.read_text(encoding="utf-8"))


def write_registry(path: Path, registry: VersionRegistry) -> None:
    dumped = registry.model_dump(mode="json", by_alias=True, exclude_none=True)
    path.write_text(
        json.dumps(dumped, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def recommend_bump(previous: SourceContract, current: SourceContract) -> str | None:
    if (
        previous.hashes
        and current.hashes
        and previous.hashes.definition == current.hashes.definition
    ):
        return None
    old_fields = {field.name: field for field in previous.fields}
    new_fields = {field.name: field for field in current.fields}
    if set(old_fields) - set(new_fields):
        return "major"
    for name in set(old_fields) & set(new_fields):
        old = old_fields[name]
        new = new_fields[name]
        if (
            old.logical_type != new.logical_type
            or old.source_type != new.source_type
            or (old.nullable and not new.nullable)
            or (not old.required and new.required)
        ):
            return "major"
    if set(new_fields) - set(old_fields):
        return "minor"
    return "patch"
