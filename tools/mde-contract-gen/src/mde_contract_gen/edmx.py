"""Hardened OData EDMX parsing for MDE metadata."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path
from xml.etree import ElementTree as StdlibET

from defusedxml import ElementTree as ET

EDM_NAMESPACE = "http://docs.oasis-open.org/odata/ns/edm"
MDE_NAMESPACE = "microsoft.windowsDefenderATP.api"


def unwrap_collection(type_name: str) -> tuple[str, bool]:
    prefix = "Collection("
    if type_name.startswith(prefix) and type_name.endswith(")"):
        return type_name[len(prefix) : -1], True
    return type_name, False


def short_type_name(type_name: str) -> str:
    inner, _ = unwrap_collection(type_name)
    return inner.rsplit(".", 1)[-1]


@dataclass(frozen=True, slots=True)
class PropertyDefinition:
    name: str
    type_name: str
    nullable: bool
    precision: int | str | None = None
    scale: int | str | None = None
    max_length: int | str | None = None


@dataclass(frozen=True, slots=True)
class StructuralTypeDefinition:
    name: str
    kind: str
    properties: tuple[PropertyDefinition, ...]
    keys: tuple[str, ...] = ()
    navigation_properties: tuple[str, ...] = ()
    base_type: str | None = None
    abstract: bool = False


@dataclass(frozen=True, slots=True)
class EnumTypeDefinition:
    name: str
    underlying_type: str
    members: tuple[str, ...]
    is_flags: bool


@dataclass(frozen=True, slots=True)
class OperationParameter:
    name: str
    type_name: str
    nullable: bool
    optional: bool


@dataclass(frozen=True, slots=True)
class OperationDefinition:
    kind: str
    name: str
    binding_type: str | None
    return_type: str | None
    parameters: tuple[OperationParameter, ...]

    @property
    def return_root(self) -> str | None:
        if not self.return_type:
            return None
        return short_type_name(self.return_type)

    @property
    def returns_collection(self) -> bool:
        return bool(self.return_type and self.return_type.startswith("Collection("))


@dataclass(slots=True)
class Metadata:
    source: Path
    namespace: str
    entity_types: dict[str, StructuralTypeDefinition] = field(default_factory=dict)
    complex_types: dict[str, StructuralTypeDefinition] = field(default_factory=dict)
    enum_types: dict[str, EnumTypeDefinition] = field(default_factory=dict)
    entity_sets: dict[str, list[str]] = field(default_factory=dict)
    operations: list[OperationDefinition] = field(default_factory=list)

    @property
    def structural_types(self) -> dict[str, StructuralTypeDefinition]:
        # MDE publishes a small number of colliding EntityType/ComplexType
        # names (notably Domain). The legacy generator intentionally resolves
        # those to the EntityType shape, so preserve that public behavior.
        return {**self.complex_types, **self.entity_types}

    def type_definition(self, name: str) -> StructuralTypeDefinition:
        try:
            return self.structural_types[name]
        except KeyError as exc:
            raise ValueError(f"Unknown structural type {name!r}") from exc

    def properties_for(self, name: str) -> tuple[PropertyDefinition, ...]:
        chain: list[StructuralTypeDefinition] = []
        seen: set[str] = set()
        current = self.type_definition(name)
        while current.base_type:
            if current.name in seen:
                raise ValueError(f"Inheritance cycle involving {current.name!r}")
            seen.add(current.name)
            current = self.type_definition(current.base_type)
            chain.append(current)
        properties: list[PropertyDefinition] = []
        for ancestor in reversed(chain):
            properties.extend(ancestor.properties)
        properties.extend(self.type_definition(name).properties)
        names: set[str] = set()
        for prop in properties:
            if prop.name in names:
                raise ValueError(f"Duplicate inherited property {name}.{prop.name}")
            names.add(prop.name)
        return tuple(properties)

    def concrete_descendants(self, name: str) -> tuple[str, ...]:
        descendants = [
            candidate.name
            for candidate in self.complex_types.values()
            if candidate.base_type == name and not candidate.abstract
        ]
        return tuple(descendants)

    def operations_for(self, root_name: str) -> tuple[OperationDefinition, ...]:
        return tuple(
            operation
            for operation in self.operations
            if operation.return_root == root_name
        )

    def referenced_complex_types(self, root_name: str) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        def visit(type_name: str) -> None:
            for prop in self.properties_for(type_name):
                dependency = short_type_name(prop.type_name)
                if dependency not in self.complex_types or dependency in seen:
                    continue
                seen.add(dependency)
                visit(dependency)
                result.append(dependency)

        visit(root_name)
        return tuple(result)


def parse_metadata(path: Path) -> Metadata:
    root = ET.parse(path).getroot()
    if root is None:
        raise ValueError("EDMX document has no root element")
    schema_elements = list(root.iter(_tag("Schema")))
    if not schema_elements:
        raise ValueError("EDMX has no Schema element")
    schema = next(
        (
            candidate
            for candidate in schema_elements
            if candidate.get("Namespace") == MDE_NAMESPACE
        ),
        schema_elements[0],
    )
    namespace = schema.get("Namespace", MDE_NAMESPACE)
    metadata = Metadata(source=path, namespace=namespace)

    for element in schema.findall(_tag("EnumType")):
        name = _required_attr(element, "Name")
        metadata.enum_types[name] = EnumTypeDefinition(
            name=name,
            underlying_type=element.get("UnderlyingType", "Edm.Int32"),
            members=tuple(
                _required_attr(member, "Name")
                for member in element.findall(_tag("Member"))
            ),
            is_flags=element.get("IsFlags", "false").lower() == "true",
        )

    for element_name, target in (
        ("ComplexType", metadata.complex_types),
        ("EntityType", metadata.entity_types),
    ):
        for element in schema.findall(_tag(element_name)):
            definition = _parse_structural_type(element, element_name)
            if definition.name in target:
                raise ValueError(f"Duplicate {element_name} {definition.name!r}")
            target[definition.name] = definition

    for container in schema.findall(_tag("EntityContainer")):
        for entity_set in container.findall(_tag("EntitySet")):
            type_name = short_type_name(_required_attr(entity_set, "EntityType"))
            metadata.entity_sets.setdefault(type_name, []).append(
                _required_attr(entity_set, "Name")
            )

    for kind in ("Function", "Action"):
        for element in schema.findall(_tag(kind)):
            metadata.operations.append(_parse_operation(element, kind))

    _validate_metadata(metadata)
    return metadata


def merged_abstract_properties(
    metadata: Metadata, abstract_name: str
) -> tuple[PropertyDefinition, ...]:
    """Return a stable nullable union view for an abstract complex type."""
    ordered: list[PropertyDefinition] = []
    by_name: dict[str, PropertyDefinition] = {}
    owners = (abstract_name, *metadata.concrete_descendants(abstract_name))
    for owner in owners:
        for prop in metadata.properties_for(owner):
            existing = by_name.get(prop.name)
            if existing is not None:
                if _arrow_compatible_type(metadata, existing.type_name) != (
                    _arrow_compatible_type(metadata, prop.type_name)
                ):
                    raise ValueError(
                        f"Incompatible polymorphic field {abstract_name}.{prop.name}"
                    )
                continue
            nullable = replace(prop, nullable=True)
            by_name[prop.name] = nullable
            ordered.append(nullable)
    return tuple(ordered)


def is_mergeable_abstract(metadata: Metadata, type_name: str) -> bool:
    definition = metadata.complex_types.get(type_name)
    if not definition or not definition.abstract:
        return False
    if not metadata.concrete_descendants(type_name):
        return False
    try:
        merged_abstract_properties(metadata, type_name)
    except ValueError:
        return False
    return True


def _parse_structural_type(
    element: StdlibET.Element, kind: str
) -> StructuralTypeDefinition:
    name = _required_attr(element, "Name")
    properties = tuple(
        PropertyDefinition(
            name=_required_attr(prop, "Name"),
            type_name=_required_attr(prop, "Type"),
            nullable=prop.get("Nullable", "true").lower() != "false",
            precision=_facet(prop.get("Precision")),
            scale=_facet(prop.get("Scale")),
            max_length=_facet(prop.get("MaxLength")),
        )
        for prop in element.findall(_tag("Property"))
    )
    keys = tuple(
        _required_attr(prop_ref, "Name")
        for key in element.findall(_tag("Key"))
        for prop_ref in key.findall(_tag("PropertyRef"))
    )
    navigation = tuple(
        _required_attr(nav, "Name")
        for nav in element.findall(_tag("NavigationProperty"))
    )
    base = element.get("BaseType")
    return StructuralTypeDefinition(
        name=name,
        kind=kind,
        properties=properties,
        keys=keys,
        navigation_properties=navigation,
        base_type=short_type_name(base) if base else None,
        abstract=element.get("Abstract", "false").lower() == "true",
    )


def _parse_operation(element: StdlibET.Element, kind: str) -> OperationDefinition:
    parameters: list[OperationParameter] = []
    binding_type: str | None = None
    for parameter in element.findall(_tag("Parameter")):
        name = _required_attr(parameter, "Name")
        type_name = _required_attr(parameter, "Type")
        if name == "bindingParameter":
            binding_type = type_name
            continue
        optional = any(
            annotation.get("Term") == "Org.OData.Core.V1.OptionalParameter"
            for annotation in parameter.findall(_tag("Annotation"))
        )
        parameters.append(
            OperationParameter(
                name=name,
                type_name=type_name,
                nullable=parameter.get("Nullable", "true").lower() != "false",
                optional=optional,
            )
        )
    return_element = element.find(_tag("ReturnType"))
    return OperationDefinition(
        kind=kind,
        name=_required_attr(element, "Name"),
        binding_type=binding_type,
        return_type=(
            _required_attr(return_element, "Type")
            if return_element is not None
            else None
        ),
        parameters=tuple(parameters),
    )


def _validate_metadata(metadata: Metadata) -> None:
    known = set(metadata.structural_types)
    for definition in metadata.structural_types.values():
        if definition.base_type and definition.base_type not in known:
            raise ValueError(
                f"{definition.name}: unknown base type {definition.base_type!r}"
            )
        metadata.properties_for(definition.name)
    for type_name in metadata.entity_sets:
        if type_name not in metadata.entity_types:
            raise ValueError(f"EntitySet references unknown type {type_name!r}")


def _arrow_compatible_type(metadata: Metadata, type_name: str) -> str:
    inner, collection = unwrap_collection(type_name)
    short = short_type_name(inner)
    normalized = "Edm.String" if short in metadata.enum_types else inner
    return f"Collection({normalized})" if collection else normalized


def _tag(local_name: str) -> str:
    return f"{{{EDM_NAMESPACE}}}{local_name}"


def _required_attr(element: StdlibET.Element, name: str) -> str:
    value = element.get(name)
    if value is None or not value:
        raise ValueError(f"{element.tag} is missing required attribute {name!r}")
    return value


def _facet(value: str | None) -> int | str | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def iter_property_types(metadata: Metadata) -> Iterable[str]:
    for definition in metadata.structural_types.values():
        for prop in definition.properties:
            yield prop.type_name
