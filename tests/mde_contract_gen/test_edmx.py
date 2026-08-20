from __future__ import annotations

from pathlib import Path

from mde_contract_gen.builder import select_roots
from mde_contract_gen.cli import DEFAULT_METADATA, DEFAULT_OVERRIDES
from mde_contract_gen.edmx import (
    is_mergeable_abstract,
    parse_metadata,
    short_type_name,
    unwrap_collection,
)
from mde_contract_gen.overrides import load_overrides
from mde_contract_gen.type_map import contract_field


def test_metadata_catalogue_and_root_selection_are_stable() -> None:
    metadata = parse_metadata(DEFAULT_METADATA)
    roots = select_roots(metadata, load_overrides(DEFAULT_OVERRIDES))

    assert len(metadata.entity_types) == 30
    assert len(metadata.complex_types) == 73
    assert len(metadata.enum_types) == 60
    assert len(metadata.operations) == 92
    assert len(roots) == 51
    assert "PostDeviceGroupsRequest" not in roots
    assert "Machine" in roots
    assert "AssetVulnerability" in roots
    assert "AuthScanHistoryContract" in roots


def test_collection_and_qualified_type_resolution() -> None:
    inner, collection = unwrap_collection(
        "Collection(microsoft.windowsDefenderATP.api.AssetVulnerability)"
    )
    assert collection is True
    assert inner.endswith(".AssetVulnerability")
    assert short_type_name(inner) == "AssetVulnerability"


def test_properties_flatten_inheritance_and_preserve_nullability() -> None:
    metadata = parse_metadata(DEFAULT_METADATA)
    properties = {
        prop.name: prop for prop in metadata.properties_for("DeltaAssetVulnerability")
    }
    assert "cvssScore" in properties
    assert properties["cvssScore"].nullable is False
    assert properties["eventTimestamp"].nullable is False


def test_nested_complex_and_enum_catalogues_are_resolved() -> None:
    metadata = parse_metadata(DEFAULT_METADATA)
    machine_properties = {
        prop.name: prop for prop in metadata.properties_for("Machine")
    }
    assert short_type_name(machine_properties["ipAddresses"].type_name) == (
        "MachineIpAddress"
    )
    assert short_type_name(machine_properties["healthStatus"].type_name) in (
        metadata.enum_types
    )
    assert "MachineIpAddress" in metadata.referenced_complex_types("Machine")


def test_abstract_auth_type_is_mergeable() -> None:
    metadata = parse_metadata(DEFAULT_METADATA)
    assert is_mergeable_abstract(metadata, "AuthParamsBase")
    assert set(metadata.concrete_descendants("AuthParamsBase")) == {
        "LinuxAuthParams",
        "SnmpAuthParams",
        "WindowsAuthParams",
    }


def test_decimal_and_length_facets_are_preserved(tmp_path: Path) -> None:
    metadata_path = tmp_path / "facets.xml"
    metadata_path.write_text(
        """<?xml version="1.0"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test">
      <EntityType Name="Measurement">
        <Property Name="amount" Type="Edm.Decimal" Precision="12" Scale="4" />
        <Property Name="code" Type="Edm.String" MaxLength="32" />
      </EntityType>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
""",
        encoding="utf-8",
    )
    metadata = parse_metadata(metadata_path)
    properties = {
        prop.name: contract_field(metadata, prop)
        for prop in metadata.properties_for("Measurement")
    }
    assert properties["amount"].constraints is not None
    assert properties["amount"].constraints.precision == 12
    assert properties["amount"].constraints.scale == 4
    assert properties["code"].constraints is not None
    assert properties["code"].constraints.max_length == 32
