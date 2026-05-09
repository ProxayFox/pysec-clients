"""Schema contract validator

Cross-validates every Arrow schema constant in ``mde_client.schemas.__all__``
against the committed $metadata XML fixture.

What is tested
--------------
- Every ``_SCHEMA`` and ``_TYPE`` constant in ``__all__`` is importable (catches
  module/name mismatches produced by camelCase conversion bugs in the builder).
- Every XML ``Property`` defined on an ``EntityType`` or ``ComplexType`` appears
  as a named field in the corresponding Arrow schema or struct constant.
- ``Nullable="false"`` in XML → ``nullable=False`` on the Arrow field.
- EDM primitive types map to the expected ``pa.DataType``.
- ``Collection(X)`` fields are wrapped in ``pa.list_``.
- ComplexType-valued fields resolve to ``pa.struct`` (not a fallback string).
- Enum-valued fields are ``pa.string()``.

Running
-------
    pytest tests/mde_client/test_schema_validator.py -v

The XML-based tests require the committed fixture:
    tests/mde_client/fixtures/mde_metadata.xml

If it is missing, run ``just schema-refresh`` first.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

import mde_client.schemas as schemas_pkg
from mde_contract import EDM_PA_TYPES

# ── Paths ─────────────────────────────────────────────────────────────────────

FIXTURE_XML = Path("tests/mde_client/fixtures/mde_metadata.xml")

# ── OData constants ───────────────────────────────────────────────────────────

_MDE_NS = "http://docs.oasis-open.org/odata/ns/edm"
_MDE_API_PREFIX = "microsoft.windowsDefenderATP.api."

# Unpack just the pa.DataType half of each tuple — the str half is only needed
# by the code generator, not by tests that compare actual Arrow types.
_EDM_TO_PA: dict[str, pa.DataType] = {
    edm: pa_type for edm, (pa_type, _) in EDM_PA_TYPES.items()
}

# ── Name derivation helpers ───────────────────────────────────────────────────


def _const_to_type_name(const: str, suffix: str) -> str:
    """Reverse the builder's camel_to_snake + upper transformation.

    ``MACHINE_ACTION_SCHEMA`` → ``MachineAction``
    ``MACHINE_IP_ADDRESS_TYPE`` → ``MachineIpAddress``
    """
    base = const.removesuffix(suffix)
    return "".join(part.capitalize() for part in base.split("_"))


def _schema_const_to_entity(const: str) -> str:
    return _const_to_type_name(const, "_SCHEMA")


def _type_const_to_complex(const: str) -> str:
    return _const_to_type_name(const, "_TYPE")


# ── Module-level parametrize lists ───────────────────────────────────────────

_ALL_NAMES: list[str] = list(schemas_pkg.__all__)
_SCHEMA_NAMES: list[str] = [n for n in _ALL_NAMES if n.endswith("_SCHEMA")]
_TYPE_NAMES: list[str] = [n for n in _ALL_NAMES if n.endswith("_TYPE")]

# ── Parsed XML dataclass ──────────────────────────────────────────────────────


@dataclass
class _ParsedMetadata:
    entity_types: dict[str, list[ET.Element]] = field(default_factory=dict)
    complex_types: dict[str, list[ET.Element]] = field(default_factory=dict)
    enum_types: set[str] = field(default_factory=set)
    abstract_types: set[str] = field(default_factory=set)
    base_types: dict[str, str] = field(default_factory=dict)

    def props_for(self, type_name: str) -> list[ET.Element]:
        """Return flattened (inherited → own) Property elements."""
        chain: list[str] = []
        cursor = type_name
        while parent := self.base_types.get(cursor):
            chain.append(parent)
            cursor = parent

        props: list[ET.Element] = []
        for ancestor in reversed(chain):
            props += (
                self.entity_types.get(ancestor)
                or self.complex_types.get(ancestor)
                or []
            )
        props += (
            self.entity_types.get(type_name) or self.complex_types.get(type_name) or []
        )
        return props


def _parse_metadata(path: Path) -> _ParsedMetadata:
    root = ET.parse(path).getroot()
    meta = _ParsedMetadata()

    for el in root.iter(f"{{{_MDE_NS}}}EnumType"):
        meta.enum_types.add(el.get("Name", ""))

    for el in root.iter(f"{{{_MDE_NS}}}ComplexType"):
        name = el.get("Name", "")
        meta.complex_types[name] = el.findall(f"{{{_MDE_NS}}}Property")
        if el.get("Abstract", "false").lower() == "true":
            meta.abstract_types.add(name)
        if base := el.get("BaseType"):
            short = base.removeprefix(_MDE_API_PREFIX)
            meta.base_types[name] = short

    for el in root.iter(f"{{{_MDE_NS}}}EntityType"):
        name = el.get("Name", "")
        meta.entity_types[name] = el.findall(f"{{{_MDE_NS}}}Property")
        if el.get("Abstract", "false").lower() == "true":
            meta.abstract_types.add(name)
        if base := el.get("BaseType"):
            short = base.removeprefix(_MDE_API_PREFIX)
            meta.base_types[name] = short

    return meta


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def mde_xml() -> _ParsedMetadata:
    if not FIXTURE_XML.exists():
        pytest.skip(
            f"Metadata fixture not found at {FIXTURE_XML}. "
            "Run `just schema-refresh` to fetch and regenerate."
        )
    return _parse_metadata(FIXTURE_XML)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _load_const(name: str) -> Any:
    """Import a named constant from the schemas package."""
    return getattr(schemas_pkg, name)


def _expected_pa_type(
    odata_t: str,
    meta: _ParsedMetadata,
) -> pa.DataType | None:
    """Return the expected Arrow type for an OData type string.

    Returns ``None`` for ComplexType-valued fields — callers check
    ``pa.types.is_struct()`` instead, since we don't want to re-implement
    the full type resolution here.
    """
    if odata_t.startswith("Collection("):
        inner = odata_t[len("Collection(") : -1]
        inner_type = _expected_pa_type(inner, meta)
        if inner_type is None:
            return None  # list of struct — caller checks is_list + is_struct
        return pa.list_(inner_type)

    if odata_t in _EDM_TO_PA:
        return _EDM_TO_PA[odata_t]

    short = odata_t.removeprefix(_MDE_API_PREFIX)

    if short in meta.enum_types:
        return pa.string()

    if short in meta.complex_types:
        return None  # struct — caller checks is_struct

    return pa.string()  # fallback (unknown / entity ref)


# ── 1. Module integrity ───────────────────────────────────────────────────────


class TestSchemaModuleIntegrity:
    """Fast smoke tests that don't require the XML fixture."""

    def test_all_is_defined_and_non_empty(self) -> None:
        assert isinstance(schemas_pkg.__all__, list)
        assert len(schemas_pkg.__all__) > 0

    def test_all_contains_only_schema_and_type_constants(self) -> None:
        bad = [
            n for n in _ALL_NAMES if not (n.endswith("_SCHEMA") or n.endswith("_TYPE"))
        ]
        assert not bad, f"Unexpected names in __all__: {bad}"

    def test_no_duplicate_names_in_all(self) -> None:
        seen: set[str] = set()
        dupes = [n for n in _ALL_NAMES if n in seen or seen.add(n)]  # type: ignore[func-returns-value]
        assert not dupes, f"Duplicate names in __all__: {dupes}"

    @pytest.mark.parametrize("const_name", _SCHEMA_NAMES)
    def test_schema_constant_is_importable(self, const_name: str) -> None:
        """Each _SCHEMA in __all__ must resolve to a pa.Schema instance."""
        schema = _load_const(const_name)
        assert isinstance(schema, pa.Schema), (
            f"{const_name} resolved to {type(schema).__name__}, expected pa.Schema"
        )

    @pytest.mark.parametrize("const_name", _TYPE_NAMES)
    def test_type_constant_is_importable(self, const_name: str) -> None:
        """Each _TYPE in __all__ must resolve to a pa.StructType instance."""
        struct_type = _load_const(const_name)
        assert pa.types.is_struct(struct_type), (
            f"{const_name} resolved to {struct_type!r}, expected a StructType"
        )


# ── 2. Schema field coverage ──────────────────────────────────────────────────


class TestSchemaFieldCoverage:
    """Every XML Property on an EntityType must appear in the Arrow schema."""

    @pytest.mark.parametrize("const_name", _SCHEMA_NAMES)
    def test_all_xml_properties_present(
        self, const_name: str, mde_xml: _ParsedMetadata
    ) -> None:
        entity_name = _schema_const_to_entity(const_name)

        if entity_name not in mde_xml.entity_types:
            pytest.skip(f"EntityType {entity_name!r} not found in XML fixture")

        schema: pa.Schema = _load_const(const_name)
        arrow_field_names = {schema.field(i).name for i in range(len(schema))}
        xml_props = mde_xml.props_for(entity_name)
        xml_field_names = {p.get("Name", "") for p in xml_props}

        missing = xml_field_names - arrow_field_names
        assert not missing, (
            f"{const_name}: fields present in XML but missing from Arrow schema: {missing}"
        )


# ── 3. Nullability ────────────────────────────────────────────────────────────


class TestFieldNullability:
    """Nullable=false in XML must map to nullable=False on the Arrow field."""

    @pytest.mark.parametrize("const_name", _SCHEMA_NAMES)
    def test_schema_nullability_matches_xml(
        self, const_name: str, mde_xml: _ParsedMetadata
    ) -> None:
        entity_name = _schema_const_to_entity(const_name)

        if entity_name not in mde_xml.entity_types:
            pytest.skip(f"EntityType {entity_name!r} not found in XML fixture")

        schema: pa.Schema = _load_const(const_name)
        xml_non_nullable = {
            p.get("Name", "")
            for p in mde_xml.props_for(entity_name)
            if p.get("Nullable", "true").lower() == "false"
        }

        mismatches: list[str] = []
        for field_name in xml_non_nullable:
            idx = schema.get_field_index(field_name)
            if idx == -1:
                continue  # covered by TestSchemaFieldCoverage
            if schema.field(idx).nullable:
                mismatches.append(field_name)

        assert not mismatches, (
            f"{const_name}: fields marked Nullable=false in XML but nullable=True "
            f"in Arrow schema: {mismatches}"
        )

    @pytest.mark.parametrize("const_name", _TYPE_NAMES)
    def test_struct_nullability_matches_xml(
        self, const_name: str, mde_xml: _ParsedMetadata
    ) -> None:
        complex_name = _type_const_to_complex(const_name)

        if complex_name not in mde_xml.complex_types:
            pytest.skip(f"ComplexType {complex_name!r} not found in XML fixture")

        struct_type: pa.StructType = _load_const(const_name)
        xml_non_nullable = {
            p.get("Name", "")
            for p in mde_xml.props_for(complex_name)
            if p.get("Nullable", "true").lower() == "false"
        }

        mismatches: list[str] = []
        for field_name in xml_non_nullable:
            idx = struct_type.get_field_index(field_name)
            if idx == -1:
                continue
            if struct_type.field(idx).nullable:
                mismatches.append(field_name)

        assert not mismatches, (
            f"{const_name}: fields marked Nullable=false in XML but nullable=True "
            f"in struct: {mismatches}"
        )


# ── 4. Field types ────────────────────────────────────────────────────────────


class TestFieldTypes:
    """Arrow field types must match the EDM type mapping used by the builder."""

    @pytest.mark.parametrize("const_name", _SCHEMA_NAMES)
    def test_primitive_field_types(
        self, const_name: str, mde_xml: _ParsedMetadata
    ) -> None:
        entity_name = _schema_const_to_entity(const_name)

        if entity_name not in mde_xml.entity_types:
            pytest.skip(f"EntityType {entity_name!r} not found in XML fixture")

        schema: pa.Schema = _load_const(const_name)
        mismatches: list[str] = []

        for prop in mde_xml.props_for(entity_name):
            field_name = prop.get("Name", "")
            odata_t = prop.get("Type", "Edm.String")
            expected = _expected_pa_type(odata_t, mde_xml)

            if expected is None:
                continue  # struct or list-of-struct — tested separately

            idx = schema.get_field_index(field_name)
            if idx == -1:
                continue  # covered by TestSchemaFieldCoverage

            actual = schema.field(idx).type
            if actual != expected:
                mismatches.append(
                    f"{field_name}: expected {expected} (from {odata_t}), got {actual}"
                )

        assert not mismatches, f"{const_name} has type mismatches:\n  " + "\n  ".join(
            mismatches
        )

    @pytest.mark.parametrize("const_name", _SCHEMA_NAMES)
    def test_collection_fields_are_lists(
        self, const_name: str, mde_xml: _ParsedMetadata
    ) -> None:
        entity_name = _schema_const_to_entity(const_name)

        if entity_name not in mde_xml.entity_types:
            pytest.skip(f"EntityType {entity_name!r} not found in XML fixture")

        schema: pa.Schema = _load_const(const_name)
        mismatches: list[str] = []

        for prop in mde_xml.props_for(entity_name):
            if not prop.get("Type", "").startswith("Collection("):
                continue
            field_name = prop.get("Name", "")
            idx = schema.get_field_index(field_name)
            if idx == -1:
                continue
            if not pa.types.is_list(schema.field(idx).type):
                mismatches.append(
                    f"{field_name}: expected pa.list_, got {schema.field(idx).type}"
                )

        assert not mismatches, (
            f"{const_name} has Collection fields not wrapped in pa.list_:\n  "
            + "\n  ".join(mismatches)
        )

    @pytest.mark.parametrize("const_name", _SCHEMA_NAMES)
    def test_non_abstract_complex_type_fields_are_structs(
        self, const_name: str, mde_xml: _ParsedMetadata
    ) -> None:
        entity_name = _schema_const_to_entity(const_name)

        if entity_name not in mde_xml.entity_types:
            pytest.skip(f"EntityType {entity_name!r} not found in XML fixture")

        schema: pa.Schema = _load_const(const_name)
        mismatches: list[str] = []

        for prop in mde_xml.props_for(entity_name):
            odata_t = prop.get("Type", "")
            # Unwrap Collection to check inner type
            inner = (
                odata_t[len("Collection(") : -1]
                if odata_t.startswith("Collection(")
                else odata_t
            )
            short = inner.removeprefix(_MDE_API_PREFIX)

            if short not in mde_xml.complex_types:
                continue
            if short in mde_xml.abstract_types:
                continue  # abstract → pa.string(), not a struct

            field_name = prop.get("Name", "")
            idx = schema.get_field_index(field_name)
            if idx == -1:
                continue

            arrow_field_type = schema.field(idx).type
            # Unwrap list if it was a collection
            if pa.types.is_list(arrow_field_type):
                arrow_field_type = arrow_field_type.value_type

            if not pa.types.is_struct(arrow_field_type):
                mismatches.append(
                    f"{field_name}: ComplexType {short!r} should be a struct, "
                    f"got {arrow_field_type}"
                )

        assert not mismatches, (
            f"{const_name} has ComplexType fields not resolved to structs:\n  "
            + "\n  ".join(mismatches)
        )


# ── 5. Struct type coverage ───────────────────────────────────────────────────


class TestStructTypeConstants:
    """Every _TYPE constant must cover all XML Properties of its ComplexType."""

    @pytest.mark.parametrize("const_name", _TYPE_NAMES)
    def test_all_xml_properties_present_in_struct(
        self, const_name: str, mde_xml: _ParsedMetadata
    ) -> None:
        complex_name = _type_const_to_complex(const_name)

        if complex_name not in mde_xml.complex_types:
            pytest.skip(f"ComplexType {complex_name!r} not found in XML fixture")

        struct_type: pa.StructType = _load_const(const_name)
        struct_field_names = {
            struct_type.field(i).name for i in range(struct_type.num_fields)
        }
        xml_field_names = {p.get("Name", "") for p in mde_xml.props_for(complex_name)}

        missing = xml_field_names - struct_field_names
        assert not missing, (
            f"{const_name}: fields present in XML ComplexType {complex_name!r} "
            f"but missing from struct: {missing}"
        )
