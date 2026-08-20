"""Pydantic meta-schema for canonical MDE source contracts.

This module is the single source of truth for ``contract.json``. A generated,
runtime-only copy is vendored into :mod:`mde_client.contracts`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class LogicalType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    ARRAY = "array"
    OBJECT = "object"


class EnumRepresentation(StrEnum):
    NAME = "name"
    VALUE = "value"


class ApiRepresentation(StrEnum):
    NUMBER = "number"
    STRING = "string"
    BIGINT = "bigint"


class StructuralType(StrEnum):
    ENTITY = "EntityType"
    COMPLEX = "ComplexType"


class OperationKind(StrEnum):
    ENTITY_SET = "EntitySet"
    FUNCTION = "Function"
    ACTION = "Action"
    OVERRIDE = "Override"


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Constraints(_Base):
    bit_width: int | None = Field(default=None, alias="bitWidth", gt=0)
    signed: bool | None = None
    precision: str | int | None = None
    scale: int | str | None = None
    max_length: int | str | None = Field(default=None, alias="maxLength")


class FormatSpec(_Base):
    unit: str | None = None
    timezone: str | None = None
    semantic: str | None = None


class WireHints(_Base):
    js_safe_integer: bool | None = Field(default=None, alias="jsSafeInteger")
    recommended_api_representation: ApiRepresentation | None = Field(
        default=None, alias="recommendedApiRepresentation"
    )


class ItemSpec(_Base):
    logical_type: LogicalType = Field(alias="logicalType")
    nullable: bool = True
    source_type: str | None = Field(default=None, alias="sourceType")
    ref: str | None = None
    enum_ref: str | None = Field(default=None, alias="enumRef")
    enum_representation: EnumRepresentation | None = Field(
        default=None, alias="enumRepresentation"
    )
    constraints: Constraints | None = None
    format: FormatSpec | None = None
    wire_hints: WireHints | None = Field(default=None, alias="wireHints")

    @model_validator(mode="after")
    def _validate_shape(self) -> ItemSpec:
        if self.logical_type == LogicalType.OBJECT:
            if not self.ref:
                raise ValueError("array item with logicalType 'object' requires 'ref'")
        elif self.ref is not None:
            raise ValueError("array item 'ref' is only valid for logicalType 'object'")
        if self.enum_ref and self.logical_type != LogicalType.STRING:
            raise ValueError("enum array items must have logicalType 'string'")
        return self


class ContractField(_Base):
    name: str
    source_name: str = Field(alias="sourceName")
    source_type: str = Field(alias="sourceType")
    logical_type: LogicalType = Field(alias="logicalType")
    required: bool
    nullable: bool
    key: bool = False
    description: str | None = None
    notes: str | None = None
    constraints: Constraints | None = None
    format: FormatSpec | None = None
    wire_hints: WireHints | None = Field(default=None, alias="wireHints")
    enum_ref: str | None = Field(default=None, alias="enumRef")
    enum_representation: EnumRepresentation | None = Field(
        default=None, alias="enumRepresentation"
    )
    ref: str | None = None
    items: ItemSpec | None = None

    @model_validator(mode="after")
    def _validate_shape(self) -> ContractField:
        if self.logical_type == LogicalType.ARRAY:
            if self.items is None:
                raise ValueError(f"array field {self.name!r} requires 'items'")
        elif self.items is not None:
            raise ValueError(f"field {self.name!r} has 'items' but is not an array")
        if self.logical_type == LogicalType.OBJECT:
            if not self.ref:
                raise ValueError(f"object field {self.name!r} requires 'ref'")
        elif self.ref is not None:
            raise ValueError(f"field {self.name!r} has 'ref' but is not an object")
        if self.enum_ref and self.logical_type != LogicalType.STRING:
            raise ValueError(f"enum field {self.name!r} must have logicalType 'string'")
        return self


class ComplexTypeDefinition(_Base):
    source_type: str = Field(alias="sourceType")
    logical_type: Literal[LogicalType.OBJECT] = Field(
        default=LogicalType.OBJECT, alias="logicalType"
    )
    fields: list[ContractField]

    @model_validator(mode="after")
    def _unique_fields(self) -> ComplexTypeDefinition:
        _require_unique((field.name for field in self.fields), "definition field")
        return self


class EnumDefinition(_Base):
    underlying_type: str = Field(alias="underlyingType")
    members: list[str]
    is_flags: bool = Field(default=False, alias="isFlags")

    @model_validator(mode="after")
    def _unique_members(self) -> EnumDefinition:
        _require_unique(iter(self.members), "enum member")
        return self


class SourceOperation(_Base):
    kind: OperationKind
    name: str
    binding_type: str | None = Field(default=None, alias="bindingType")
    return_type: str | None = Field(default=None, alias="returnType")
    collection: bool = False


class SourceDescription(_Base):
    system: str
    metadata_format: str = Field(alias="metadataFormat")
    metadata_namespace: str | None = Field(default=None, alias="metadataNamespace")
    structural_type: StructuralType = Field(alias="structuralType")
    entity_type: str = Field(alias="entityType")
    entity_set: str | None = Field(default=None, alias="entitySet")
    bound_function: str | None = Field(default=None, alias="boundFunction")
    return_type: str | None = Field(default=None, alias="returnType")
    keys: list[str] = Field(default_factory=list)
    excluded_navigation_properties: list[str] = Field(
        default_factory=list, alias="excludedNavigationProperties"
    )
    operations: list[SourceOperation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_operations(self) -> SourceDescription:
        identities = (
            f"{operation.kind}:{operation.name}:{operation.binding_type or ''}"
            for operation in self.operations
        )
        _require_unique(identities, "source operation")
        _require_unique(iter(self.keys), "source key")
        return self


class Conventions(_Base):
    required_rule: str | None = Field(default=None, alias="requiredRule")
    required_derived_from: str | None = Field(default=None, alias="requiredDerivedFrom")
    enum_rule: str | None = Field(default=None, alias="enumRule")
    guid_rule: str | None = Field(default=None, alias="guidRule")
    datetime_rule: str | None = Field(default=None, alias="datetimeRule")
    unspecified_nullable_default: bool | None = Field(
        default=None, alias="unspecifiedNullableDefault"
    )
    note: str | None = None


class Hashes(_Base):
    definition: str
    arrow: str

    @field_validator("definition", "arrow")
    @classmethod
    def _valid_hash(cls, value: str) -> str:
        if not _SHA256.fullmatch(value):
            raise ValueError("must be a sha256:<64 lowercase hex> digest")
        return value


class Generation(_Base):
    generated: Literal[True] = True
    generator: str
    source_metadata_hash: str | None = Field(default=None, alias="sourceMetadataHash")
    generated_at: str | None = Field(default=None, alias="generatedAt")
    do_not_edit: Literal[True] = Field(default=True, alias="doNotEdit")

    @field_validator("source_metadata_hash")
    @classmethod
    def _valid_source_hash(cls, value: str | None) -> str | None:
        if value is not None and not _SHA256.fullmatch(value):
            raise ValueError("must be a sha256:<64 lowercase hex> digest")
        return value


class SourceContract(_Base):
    contract_format_version: str = Field(alias="contractFormatVersion")
    name: str
    version: str
    title: str
    description: str | None = None
    stage: Literal["source"] = "source"
    owner: str = "mde-client"
    source: SourceDescription
    conventions: Conventions
    enums: dict[str, EnumDefinition] = Field(default_factory=dict)
    definitions: dict[str, ComplexTypeDefinition] = Field(default_factory=dict)
    fields: list[ContractField]
    hashes: Hashes | None = None
    generation: Generation

    @field_validator("contract_format_version", "version")
    @classmethod
    def _valid_semver(cls, value: str) -> str:
        if not _SEMVER.fullmatch(value):
            raise ValueError("must be a semantic version")
        return value

    @model_validator(mode="after")
    def _validate_contract(self) -> SourceContract:
        _require_unique((field.name for field in self.fields), "contract field")
        known_defs = set(self.definitions)
        known_enums = set(self.enums)

        def validate_field(field: ContractField, where: str) -> None:
            if field.ref and field.ref not in known_defs:
                raise ValueError(f"{where}: ref {field.ref!r} not in definitions")
            if field.enum_ref and field.enum_ref not in known_enums:
                raise ValueError(f"{where}: enumRef {field.enum_ref!r} not in enums")
            if field.items:
                if field.items.ref and field.items.ref not in known_defs:
                    raise ValueError(
                        f"{where}.items: ref {field.items.ref!r} not in definitions"
                    )
                if field.items.enum_ref and field.items.enum_ref not in known_enums:
                    raise ValueError(
                        f"{where}.items: enumRef {field.items.enum_ref!r} not in enums"
                    )

        for field in self.fields:
            validate_field(field, f"fields.{field.name}")
        for definition_name, definition in self.definitions.items():
            for field in definition.fields:
                validate_field(field, f"definitions.{definition_name}.{field.name}")

        field_names = {field.name for field in self.fields}
        missing_keys = set(self.source.keys) - field_names
        if missing_keys:
            raise ValueError(
                f"source keys not present in fields: {sorted(missing_keys)}"
            )
        return self


def _require_unique(values: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        raise ValueError(f"duplicate {label}s: {sorted(duplicates)}")


__all__ = [
    "ApiRepresentation",
    "ComplexTypeDefinition",
    "Constraints",
    "ContractField",
    "Conventions",
    "EnumDefinition",
    "EnumRepresentation",
    "FormatSpec",
    "Generation",
    "Hashes",
    "ItemSpec",
    "LogicalType",
    "OperationKind",
    "SourceContract",
    "SourceDescription",
    "SourceOperation",
    "StructuralType",
    "WireHints",
]
