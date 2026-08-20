# pyright: reportCallIssue=false
"""OData type mapping into canonical contract descriptors."""

from __future__ import annotations

from dataclasses import dataclass

from .edmx import Metadata, PropertyDefinition, short_type_name, unwrap_collection
from .models import (
    ApiRepresentation,
    Constraints,
    ContractField,
    EnumRepresentation,
    FormatSpec,
    ItemSpec,
    LogicalType,
    WireHints,
)


@dataclass(frozen=True, slots=True)
class TypeDescriptor:
    logical_type: LogicalType
    constraints: Constraints | None = None
    format: FormatSpec | None = None
    wire_hints: WireHints | None = None
    ref: str | None = None
    enum_ref: str | None = None


PRIMITIVE_DESCRIPTORS: dict[str, TypeDescriptor] = {
    "Edm.String": TypeDescriptor(LogicalType.STRING),
    "Edm.Int16": TypeDescriptor(
        LogicalType.INTEGER, Constraints(bit_width=16, signed=True)
    ),
    "Edm.Int32": TypeDescriptor(
        LogicalType.INTEGER, Constraints(bit_width=32, signed=True)
    ),
    "Edm.Int64": TypeDescriptor(
        LogicalType.INTEGER,
        Constraints(bit_width=64, signed=True),
        wire_hints=WireHints(
            js_safe_integer=False,
            recommended_api_representation=ApiRepresentation.STRING,
        ),
    ),
    "Edm.Boolean": TypeDescriptor(LogicalType.BOOLEAN),
    "Edm.Double": TypeDescriptor(LogicalType.NUMBER, Constraints(precision="double")),
    "Edm.Single": TypeDescriptor(LogicalType.NUMBER, Constraints(precision="single")),
    "Edm.Byte": TypeDescriptor(
        LogicalType.INTEGER, Constraints(bit_width=8, signed=False)
    ),
    "Edm.SByte": TypeDescriptor(
        LogicalType.INTEGER, Constraints(bit_width=8, signed=True)
    ),
    "Edm.Guid": TypeDescriptor(LogicalType.STRING, format=FormatSpec(semantic="uuid")),
    "Edm.DateTimeOffset": TypeDescriptor(
        LogicalType.DATETIME,
        format=FormatSpec(unit="microsecond", timezone="UTC"),
    ),
    "Edm.Duration": TypeDescriptor(
        LogicalType.STRING,
        format=FormatSpec(unit="microsecond", semantic="duration"),
    ),
    "Edm.TimeOfDay": TypeDescriptor(
        LogicalType.STRING,
        format=FormatSpec(unit="microsecond", semantic="time"),
    ),
    "Edm.Binary": TypeDescriptor(
        LogicalType.STRING, format=FormatSpec(semantic="base64")
    ),
}


def describe_type(metadata: Metadata, type_name: str) -> TypeDescriptor:
    descriptor = PRIMITIVE_DESCRIPTORS.get(type_name)
    if descriptor is not None:
        return descriptor
    if type_name == "Edm.Decimal":
        return TypeDescriptor(LogicalType.NUMBER)
    short_name = short_type_name(type_name)
    if short_name in metadata.enum_types:
        return TypeDescriptor(LogicalType.STRING, enum_ref=short_name)
    if short_name in metadata.complex_types:
        return TypeDescriptor(LogicalType.OBJECT, ref=short_name)
    return TypeDescriptor(LogicalType.STRING)


def contract_field(
    metadata: Metadata,
    prop: PropertyDefinition,
    *,
    key: bool = False,
) -> ContractField:
    inner_type, collection = unwrap_collection(prop.type_name)
    if collection:
        item_descriptor = describe_type(metadata, inner_type)
        item_constraints = _property_constraints(prop, item_descriptor.constraints)
        return ContractField(
            name=prop.name,
            source_name=prop.name,
            source_type=prop.type_name,
            logical_type=LogicalType.ARRAY,
            required=not prop.nullable,
            nullable=prop.nullable,
            key=key,
            items=ItemSpec(
                logical_type=item_descriptor.logical_type,
                nullable=True,
                source_type=inner_type,
                ref=item_descriptor.ref,
                enum_ref=item_descriptor.enum_ref,
                enum_representation=(
                    EnumRepresentation.NAME if item_descriptor.enum_ref else None
                ),
                constraints=item_constraints,
                format=item_descriptor.format,
                wire_hints=item_descriptor.wire_hints,
            ),
        )

    descriptor = describe_type(metadata, prop.type_name)
    constraints = _property_constraints(prop, descriptor.constraints)
    return ContractField(
        name=prop.name,
        source_name=prop.name,
        source_type=prop.type_name,
        logical_type=descriptor.logical_type,
        required=not prop.nullable,
        nullable=prop.nullable,
        key=key,
        constraints=constraints,
        format=descriptor.format,
        wire_hints=descriptor.wire_hints,
        enum_ref=descriptor.enum_ref,
        enum_representation=(EnumRepresentation.NAME if descriptor.enum_ref else None),
        ref=descriptor.ref,
    )


def _property_constraints(
    prop: PropertyDefinition, base: Constraints | None
) -> Constraints | None:
    values = base.model_dump(exclude_none=True) if base is not None else {}
    if prop.precision is not None:
        values["precision"] = prop.precision
    if prop.scale is not None:
        values["scale"] = prop.scale
    if prop.max_length is not None:
        values["max_length"] = prop.max_length
    return Constraints.model_validate(values) if values else None
