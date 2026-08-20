"""Deterministic serialization and semantic hashing."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .models import ContractField, Hashes, SourceContract


def canonical_json_bytes(value: Any) -> bytes:
    """Return the repository's documented canonical JSON representation."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json_bytes(value)).hexdigest()}"


def add_hashes(contract: SourceContract) -> SourceContract:
    dumped = contract.model_dump(mode="json", by_alias=True, exclude_none=True)
    projection = deepcopy(dumped)
    projection.pop("hashes", None)
    generation = projection.get("generation")
    if isinstance(generation, dict):
        generation.pop("generatedAt", None)
        generation.pop("sourceMetadataHash", None)
    definition_hash = sha256_json(projection)
    arrow_hash = sha256_json(arrow_descriptor(contract))
    return contract.model_copy(
        update={"hashes": Hashes(definition=definition_hash, arrow=arrow_hash)}
    )


def verify_hashes(contract: SourceContract) -> None:
    expected = add_hashes(contract)
    if contract.hashes is None:
        raise ValueError(f"{contract.name}: hashes are missing")
    if contract.hashes != expected.hashes:
        raise ValueError(
            f"{contract.name}: hash mismatch; expected {expected.hashes}, "
            f"found {contract.hashes}"
        )


def arrow_descriptor(contract: SourceContract) -> dict[str, Any]:
    return {
        "schema": [_field_descriptor(field) for field in contract.fields],
        "definitions": {
            name: [_field_descriptor(field) for field in definition.fields]
            for name, definition in contract.definitions.items()
        },
    }


def write_contract(path: Path, contract: SourceContract) -> None:
    dumped = contract.model_dump(mode="json", by_alias=True, exclude_none=True)
    path.write_text(
        json.dumps(dumped, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    validated = SourceContract.model_validate_json(path.read_text(encoding="utf-8"))
    verify_hashes(validated)


def prior_generated_at(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        contract = SourceContract.model_validate_json(path.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return None
    return contract.generation.generated_at


def _field_descriptor(field: ContractField) -> dict[str, Any]:
    descriptor: dict[str, Any] = {
        "name": field.name,
        "sourceType": field.source_type,
        "logicalType": field.logical_type.value,
        "nullable": field.nullable,
    }
    if field.constraints:
        descriptor["constraints"] = field.constraints.model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
    if field.format:
        descriptor["format"] = field.format.model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
    if field.enum_ref:
        descriptor["enumRef"] = field.enum_ref
    if field.ref:
        descriptor["ref"] = field.ref
    if field.items:
        descriptor["items"] = field.items.model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
    return descriptor
