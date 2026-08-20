from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from mde_contract_gen.emitters.json_schema import build_json_schema
from mde_contract_gen.models import SourceContract

CONTRACTS = Path("src/mde-client/src/mde_client/contracts")


def _load(slug: str) -> tuple[SourceContract, dict[str, Any]]:
    directory = CONTRACTS / slug
    contract = SourceContract.model_validate_json(
        (directory / "contract.json").read_text(encoding="utf-8")
    )
    schema = json.loads((directory / "schema.schema.json").read_text(encoding="utf-8"))
    return contract, schema


def test_all_json_schemas_are_draft_2020_12_and_contract_derived() -> None:
    paths = sorted(CONTRACTS.glob("*/schema.schema.json"))
    assert len(paths) == 51
    for path in paths:
        contract = SourceContract.model_validate_json(
            (path.parent / "contract.json").read_text(encoding="utf-8")
        )
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema == build_json_schema(contract)
        assert schema["$schema"].endswith("draft/2020-12/schema")
        assert "generated: true" in schema["$comment"]


def test_required_and_nullable_are_independent() -> None:
    _, schema = _load("asset_vulnerability")
    assert "cvssScore" in schema["required"]
    assert schema["properties"]["cvssScore"]["type"] == ["number", "null"]
    assert "securityUpdateAvailable" in schema["required"]
    assert schema["properties"]["securityUpdateAvailable"]["type"] == "boolean"
    assert "id" not in schema["required"]
    assert schema["properties"]["id"]["type"] == ["string", "null"]


def test_nested_types_use_defs_and_nullable_refs() -> None:
    _, schema = _load("machine")
    assert {"MachineIpAddress", "VmMetadata"} <= set(schema["$defs"])
    ip_addresses = schema["properties"]["ipAddresses"]
    assert ip_addresses["type"] == ["array", "null"]
    assert ip_addresses["items"]["anyOf"][0]["$ref"] == ("#/$defs/MachineIpAddress")


def test_datetime_and_uuid_use_standard_formats() -> None:
    _, schema = _load("machine_action")
    assert schema["properties"]["id"]["format"] == "uuid"
    assert schema["properties"]["creationDateTimeUtc"]["format"] == "date-time"


def test_enums_remain_open_and_physical_hints_do_not_leak() -> None:
    _, schema = _load("machine")
    serialized = json.dumps(schema)
    assert '"enum"' not in serialized
    assert "bitWidth" not in serialized
    assert "wireHints" not in serialized
    assert "x-generated" not in serialized
