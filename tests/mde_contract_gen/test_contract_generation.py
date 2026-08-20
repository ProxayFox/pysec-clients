from __future__ import annotations

from mde_contract_gen.builder import build_contract, camel_to_snake, select_roots
from mde_contract_gen.canonical import add_hashes, verify_hashes
from mde_contract_gen.cli import (
    DEFAULT_CONTRACTS,
    DEFAULT_METADATA,
    DEFAULT_OVERRIDES,
)
from mde_contract_gen.edmx import parse_metadata
from mde_contract_gen.models import SourceContract
from mde_contract_gen.overrides import load_overrides


def test_all_vendored_contracts_round_trip_and_verify_hashes() -> None:
    paths = sorted(DEFAULT_CONTRACTS.glob("*/contract.json"))
    assert len(paths) == 51
    for path in paths:
        contract = SourceContract.model_validate_json(path.read_text(encoding="utf-8"))
        verify_hashes(contract)
        assert contract.generation.generated is True
        assert contract.generation.do_not_edit is True
        assert contract.conventions.unspecified_nullable_default is True


def test_contract_build_is_semantically_deterministic() -> None:
    metadata = parse_metadata(DEFAULT_METADATA)
    overrides = load_overrides(DEFAULT_OVERRIDES)
    first = add_hashes(
        build_contract(
            metadata,
            "Machine",
            version="1.0.0",
            overrides=overrides,
            generated_at="2026-01-01T00:00:00Z",
        )
    )
    second = add_hashes(
        build_contract(
            metadata,
            "Machine",
            version="1.0.0",
            overrides=overrides,
            generated_at="2026-02-01T00:00:00Z",
        )
    )
    assert first.hashes == second.hashes
    assert first.source.operations == second.source.operations


def test_every_selected_root_has_a_vendored_contract() -> None:
    metadata = parse_metadata(DEFAULT_METADATA)
    overrides = load_overrides(DEFAULT_OVERRIDES)
    roots = select_roots(metadata, overrides)
    expected = {camel_to_snake(root) for root in roots}
    actual = {path.parent.name for path in DEFAULT_CONTRACTS.glob("*/contract.json")}
    assert actual == expected


def test_machine_contract_records_all_routes_and_nested_catalogues() -> None:
    contract = SourceContract.model_validate_json(
        (DEFAULT_CONTRACTS / "machine/contract.json").read_text(encoding="utf-8")
    )
    assert "MachineIpAddress" in contract.definitions
    assert "VmMetadata" in contract.definitions
    assert "MachineHealthStatus" in contract.enums
    operation_names = {operation.name for operation in contract.source.operations}
    assert {"Machines", "FindByIp", "AddOrRemoveTagForMultipleMachines"} <= (
        operation_names
    )


def test_each_endpoint_directory_contains_exactly_three_files() -> None:
    for contract_path in DEFAULT_CONTRACTS.glob("*/contract.json"):
        directory = contract_path.parent
        assert {path.name for path in directory.iterdir() if path.is_file()} == {
            "contract.json",
            "schema.py",
            "schema.schema.json",
        }
