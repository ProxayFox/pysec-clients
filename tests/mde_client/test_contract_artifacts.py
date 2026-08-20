from __future__ import annotations

import importlib
import json
from importlib import resources
from pathlib import Path

import pyarrow as pa
from mde_client import contracts, schemas

CONTRACTS = Path("src/mde-client/src/mde_client/contracts")


def test_every_endpoint_has_exactly_three_generated_files() -> None:
    endpoint_directories = sorted(
        path
        for path in CONTRACTS.iterdir()
        if path.is_dir() and (path / "contract.json").is_file()
    )
    assert len(endpoint_directories) == 51
    for directory in endpoint_directories:
        assert {path.name for path in directory.iterdir() if path.is_file()} == {
            "contract.json",
            "schema.py",
            "schema.schema.json",
        }
        contract = json.loads((directory / "contract.json").read_text(encoding="utf-8"))
        assert contract["generation"]["generated"] is True
        assert contract["generation"]["doNotEdit"] is True
        schema = json.loads(
            (directory / "schema.schema.json").read_text(encoding="utf-8")
        )
        assert "generated: true" in schema["$comment"]
        assert (
            (directory / "schema.py")
            .read_text(encoding="utf-8")
            .startswith("# AUTO-GENERATED")
        )


def test_contract_aggregation_matches_legacy_schema_exports() -> None:
    assert set(contracts.__all__) == set(schemas.__all__)
    for name in contracts.__all__:
        assert getattr(contracts, name) is getattr(schemas, name)
        assert isinstance(getattr(contracts, name), pa.Schema | pa.StructType)


def test_legacy_schema_submodules_are_compatibility_wrappers() -> None:
    legacy = importlib.import_module("mde_client.schemas.machine")
    canonical = importlib.import_module("mde_client.contracts.machine.schema")
    assert legacy.MACHINE_SCHEMA is canonical.MACHINE_SCHEMA
    assert legacy.MACHINE_IP_ADDRESS_TYPE is canonical.MACHINE_IP_ADDRESS_TYPE


def test_json_artifacts_are_importlib_resources() -> None:
    root = resources.files("mde_client.contracts")
    contract = root.joinpath("machine", "contract.json")
    json_schema = root.joinpath("machine", "schema.schema.json")
    assert contract.is_file()
    assert json_schema.is_file()
