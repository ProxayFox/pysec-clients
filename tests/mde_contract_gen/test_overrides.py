from __future__ import annotations

import pytest
from mde_contract_gen.builder import build_contract
from mde_contract_gen.cli import DEFAULT_METADATA, DEFAULT_OVERRIDES
from mde_contract_gen.edmx import parse_metadata
from mde_contract_gen.overrides import (
    OverrideDocument,
    apply_contract_override,
    load_overrides,
)


def test_runtime_nullable_override_keeps_required_distinct() -> None:
    metadata = parse_metadata(DEFAULT_METADATA)
    overrides = load_overrides(DEFAULT_OVERRIDES)
    contract = build_contract(
        metadata,
        "AssetVulnerability",
        version="1.0.0",
        overrides=overrides,
        generated_at="2026-01-01T00:00:00Z",
    )
    cvss = next(field for field in contract.fields if field.name == "cvssScore")
    assert cvss.required is True
    assert cvss.nullable is True
    assert cvss.notes is not None
    assert "Nullable=false" in cvss.notes


def test_unknown_override_field_fails() -> None:
    contract = {
        "fields": [
            {
                "name": "id",
                "required": True,
            }
        ]
    }
    override = OverrideDocument.model_validate(
        {"contract": {"fields": {"missing": {"required": False}}}}
    )
    with pytest.raises(ValueError, match="unknown field"):
        apply_contract_override(contract, override)


def test_missing_return_override_records_both_operations() -> None:
    metadata = parse_metadata(DEFAULT_METADATA)
    overrides = load_overrides(DEFAULT_OVERRIDES)
    contract = build_contract(
        metadata,
        "AuthScanHistoryContract",
        version="1.0.0",
        overrides=overrides,
        generated_at="2026-01-01T00:00:00Z",
    )
    assert {operation.name for operation in contract.source.operations} == {
        "GetScanHistoryByScanDefinitionId",
        "GetScanHistoryBySessionId",
    }
