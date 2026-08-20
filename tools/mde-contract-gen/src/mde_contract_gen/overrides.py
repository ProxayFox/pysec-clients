# pyright: reportCallIssue=false
"""Validated, deterministic contract override handling."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import OperationKind, SourceOperation


class SelectionOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    root_type: str = Field(alias="rootType")
    operations: list[SourceOperation] = Field(default_factory=list)


class OverrideDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selection: SelectionOverride | None = None
    contract: dict[str, Any] = Field(default_factory=dict)


def load_overrides(directory: Path) -> dict[str, OverrideDocument]:
    documents: dict[str, OverrideDocument] = {}
    if not directory.exists():
        return documents
    for path in sorted(directory.glob("*.json")):
        slug = path.stem
        if slug in documents:
            raise ValueError(f"Duplicate override for {slug!r}")
        documents[slug] = OverrideDocument.model_validate_json(
            path.read_text(encoding="utf-8")
        )
    return documents


def selection_root_types(
    overrides: dict[str, OverrideDocument],
) -> set[str]:
    return {
        document.selection.root_type
        for document in overrides.values()
        if document.selection is not None
    }


def selected_operations(
    root_type: str, overrides: dict[str, OverrideDocument]
) -> tuple[SourceOperation, ...]:
    operations: list[SourceOperation] = []
    for document in overrides.values():
        if document.selection and document.selection.root_type == root_type:
            operations.extend(document.selection.operations)
    return tuple(operations)


def apply_contract_override(
    contract: dict[str, Any],
    document: OverrideDocument | None,
) -> dict[str, Any]:
    if document is None or not document.contract:
        return contract
    merged = deepcopy(contract)
    _deep_merge(merged, document.contract, path="contract")
    return merged


def _deep_merge(target: Any, patch: Any, *, path: str) -> None:
    if not isinstance(target, dict) or not isinstance(patch, dict):
        raise TypeError(f"{path}: overrides must merge object values")
    for key, value in patch.items():
        if key not in target:
            raise ValueError(f"{path}: override key {key!r} does not exist")
        current = target[key]
        child_path = f"{path}.{key}"
        if key == "fields" and isinstance(current, list):
            _merge_named_fields(current, value, path=child_path)
        elif isinstance(current, dict) and isinstance(value, dict):
            _deep_merge(current, value, path=child_path)
        elif key == "operations" and isinstance(current, list):
            _merge_operations(current, value, path=child_path)
        else:
            target[key] = deepcopy(value)


def _merge_named_fields(fields: list[dict[str, Any]], patch: Any, *, path: str) -> None:
    if not isinstance(patch, dict):
        raise TypeError(f"{path}: field overrides must be keyed by field name")
    by_name = {field.get("name"): field for field in fields}
    for name, field_patch in patch.items():
        if name not in by_name:
            raise ValueError(f"{path}: unknown field {name!r}")
        if not isinstance(field_patch, dict):
            raise TypeError(f"{path}.{name}: field override must be an object")
        _deep_merge(by_name[name], field_patch, path=f"{path}.{name}")


def _merge_operations(
    operations: list[dict[str, Any]], patch: Any, *, path: str
) -> None:
    if not isinstance(patch, list):
        raise TypeError(f"{path}: operation override must be a list")
    existing = {
        (
            operation.get("kind"),
            operation.get("name"),
            operation.get("bindingType"),
        )
        for operation in operations
    }
    for raw_operation in patch:
        operation = SourceOperation.model_validate(raw_operation)
        dumped = operation.model_dump(mode="json", by_alias=True, exclude_none=True)
        identity = (
            operation.kind.value,
            operation.name,
            operation.binding_type,
        )
        if identity in existing:
            raise ValueError(f"{path}: duplicate operation {identity!r}")
        operations.append(dumped)
        existing.add(identity)


def operation_override(
    *,
    name: str,
    binding_type: str,
    return_type: str,
    collection: bool,
) -> SourceOperation:
    return SourceOperation(
        kind=OperationKind.OVERRIDE,
        name=name,
        binding_type=binding_type,
        return_type=return_type,
        collection=collection,
    )
