# pyright: reportCallIssue=false
"""Build canonical source contracts from parsed EDMX metadata."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from .edmx import (
    Metadata,
    PropertyDefinition,
    is_mergeable_abstract,
    merged_abstract_properties,
)
from .models import (
    ComplexTypeDefinition,
    ContractField,
    Conventions,
    EnumDefinition,
    Generation,
    OperationKind,
    SourceContract,
    SourceDescription,
    SourceOperation,
    StructuralType,
)
from .overrides import (
    OverrideDocument,
    apply_contract_override,
    selected_operations,
    selection_root_types,
)
from .type_map import contract_field

SKIP_ENTITY_TYPES = {"PostDeviceGroupsRequest"}
CONTRACT_FORMAT_VERSION = "1.0.0"
GENERATOR_ID = "mde-contract-gen"

REQUIRED_RULE = (
    'Nullable="false" maps to required=true and nullable=false. An omitted '
    "Nullable attribute uses the OData default true and maps to "
    "required=false and nullable=true. Checked-in overrides may document "
    "verified runtime exceptions."
)
ENUM_RULE = (
    "Enums use logicalType=string for Arrow and API forward compatibility; "
    "enumRef preserves the current member catalogue and closed enums are opt-in."
)


def camel_to_snake(name: str) -> str:
    first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first).lower()


def to_const(name: str) -> str:
    return camel_to_snake(name).upper()


def select_roots(
    metadata: Metadata, overrides: dict[str, OverrideDocument]
) -> tuple[str, ...]:
    roots = set(metadata.entity_types) - SKIP_ENTITY_TYPES
    for operation in metadata.operations:
        root_name = operation.return_root
        if (
            root_name
            and root_name in metadata.complex_types
            and not metadata.complex_types[root_name].abstract
        ):
            roots.add(root_name)
    roots.update(selection_root_types(overrides))
    unknown = roots - set(metadata.structural_types)
    if unknown:
        raise ValueError(f"Selected unknown roots: {sorted(unknown)}")
    return tuple(sorted(roots))


def build_contract(
    metadata: Metadata,
    root_name: str,
    *,
    version: str,
    overrides: dict[str, OverrideDocument],
    generated_at: str | None = None,
) -> SourceContract:
    root = metadata.type_definition(root_name)
    if root.abstract:
        raise ValueError(f"Abstract type {root_name!r} cannot be a contract root")
    slug = camel_to_snake(root_name)
    definitions = _definitions_for(metadata, root_name)
    fields = [
        contract_field(
            metadata,
            prop,
            key=prop.name in root.keys,
        )
        for prop in metadata.properties_for(root_name)
    ]
    enum_names = _referenced_enums(fields, definitions)
    enums = {
        name: EnumDefinition(
            underlying_type=metadata.enum_types[name].underlying_type,
            members=list(metadata.enum_types[name].members),
            is_flags=metadata.enum_types[name].is_flags,
        )
        for name in sorted(enum_names)
    }
    operations = _source_operations(metadata, root_name, overrides)
    primary_function = next(
        (
            operation
            for operation in operations
            if operation.kind == OperationKind.FUNCTION
        ),
        None,
    )
    primary_entity_set = next(
        (
            operation
            for operation in operations
            if operation.kind == OperationKind.ENTITY_SET
        ),
        None,
    )
    structural_type = (
        StructuralType.ENTITY
        if root_name in metadata.entity_types
        else StructuralType.COMPLEX
    )
    source = SourceDescription(
        system="microsoft-defender-for-endpoint",
        metadata_format="odata-edmx",
        metadata_namespace=metadata.namespace,
        structural_type=structural_type,
        entity_type=root_name,
        entity_set=primary_entity_set.name if primary_entity_set else None,
        bound_function=primary_function.name if primary_function else None,
        return_type=(primary_function.return_type if primary_function else None),
        keys=list(root.keys),
        excluded_navigation_properties=list(root.navigation_properties),
        operations=operations,
    )
    contract = SourceContract(
        contract_format_version=CONTRACT_FORMAT_VERSION,
        name=f"mde.{slug.replace('_', '-')}.source",
        version=version,
        title=root_name,
        description=(
            f"Canonical MDE source contract for the {root_name} response shape."
        ),
        source=source,
        conventions=Conventions(
            required_rule=REQUIRED_RULE,
            required_derived_from="odata-nullable",
            enum_rule=ENUM_RULE,
            guid_rule="Edm.Guid is represented as string with semantic uuid.",
            datetime_rule=(
                "Edm.DateTimeOffset is represented as datetime with "
                "microsecond precision and UTC timezone."
            ),
            unspecified_nullable_default=True,
            note=(
                "Runtime corrections and polymorphic union behavior are "
                "declared in checked-in overrides."
            ),
        ),
        enums=enums,
        definitions=definitions,
        fields=fields,
        generation=Generation(
            generator=GENERATOR_ID,
            source_metadata_hash=_source_hash(metadata.source),
            generated_at=generated_at
            or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        ),
    )
    # Preserve optional keys while applying overrides so a keyed correction can
    # add documentation such as field notes. Final artifact serialization still
    # excludes values that remain None.
    dumped = contract.model_dump(mode="json", by_alias=True, exclude_none=False)
    patched = apply_contract_override(dumped, overrides.get(slug))
    return SourceContract.model_validate(patched)


def _definitions_for(
    metadata: Metadata, root_name: str
) -> dict[str, ComplexTypeDefinition]:
    definitions: dict[str, ComplexTypeDefinition] = {}
    for type_name in metadata.referenced_complex_types(root_name):
        type_definition = metadata.complex_types[type_name]
        properties: tuple[PropertyDefinition, ...]
        if type_definition.abstract and is_mergeable_abstract(metadata, type_name):
            properties = merged_abstract_properties(metadata, type_name)
        else:
            properties = metadata.properties_for(type_name)
        fields = [contract_field(metadata, prop) for prop in properties]
        if type_definition.abstract:
            for field in fields:
                field.notes = (
                    "Nullable union projection of an abstract EDMX complex "
                    "type and its concrete descendants."
                )
                field.required = False
                field.nullable = True
        definitions[type_name] = ComplexTypeDefinition(
            source_type=f"{metadata.namespace}.{type_name}",
            fields=fields,
        )
    return definitions


def _source_operations(
    metadata: Metadata,
    root_name: str,
    overrides: dict[str, OverrideDocument],
) -> list[SourceOperation]:
    operations: list[SourceOperation] = []
    for entity_set in metadata.entity_sets.get(root_name, []):
        operations.append(
            SourceOperation(
                kind=OperationKind.ENTITY_SET,
                name=entity_set,
                return_type=f"Collection({metadata.namespace}.{root_name})",
                collection=True,
            )
        )
    for operation in metadata.operations_for(root_name):
        operations.append(
            SourceOperation(
                kind=(
                    OperationKind.FUNCTION
                    if operation.kind == "Function"
                    else OperationKind.ACTION
                ),
                name=operation.name,
                binding_type=operation.binding_type,
                return_type=operation.return_type,
                collection=operation.returns_collection,
            )
        )
    operations.extend(selected_operations(root_name, overrides))
    return operations


def _referenced_enums(
    fields: Sequence[ContractField],
    definitions: dict[str, ComplexTypeDefinition],
) -> set[str]:
    names: set[str] = set()

    def collect(field: ContractField) -> None:
        if field.enum_ref:
            names.add(field.enum_ref)
        items = field.items
        if items and items.enum_ref:
            names.add(items.enum_ref)

    for field in fields:
        collect(field)
    for definition in definitions.values():
        for field in definition.fields:
            collect(field)
    return names


def _source_hash(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
