from __future__ import annotations

import ast
import json
from pathlib import Path

from mde_client import schemas
from mde_contract_gen.emitters.arrow import render_arrow
from mde_contract_gen.models import SourceContract
from mde_contract_gen.parity import schema_descriptor

CONTRACTS = Path("src/mde-client/src/mde_client/contracts")
GOLDEN = Path("tests/mde_client/golden/arrow_manifest.json")


def test_all_arrow_exports_match_legacy_golden() -> None:
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    actual = {
        name: schema_descriptor(getattr(schemas, name))
        for name in sorted(schemas.__all__)
    }
    assert actual == expected


def test_every_arrow_module_is_rendered_from_contract_json() -> None:
    for contract_path in CONTRACTS.glob("*/contract.json"):
        contract = SourceContract.model_validate_json(
            contract_path.read_text(encoding="utf-8")
        )
        generated_source = (contract_path.parent / "schema.py").read_text(
            encoding="utf-8"
        )
        assert ast.dump(ast.parse(generated_source)) == ast.dump(
            ast.parse(render_arrow(contract))
        )


def test_runtime_nullable_exceptions_are_explicit_and_bounded() -> None:
    for slug in ("asset_vulnerability", "delta_asset_vulnerability"):
        contract = SourceContract.model_validate_json(
            (CONTRACTS / slug / "contract.json").read_text(encoding="utf-8")
        )
        cvss = next(field for field in contract.fields if field.name == "cvssScore")
        assert cvss.required is True
        assert cvss.nullable is True

    auth = SourceContract.model_validate_json(
        (CONTRACTS / "device_authenticated_scan_definition/contract.json").read_text(
            encoding="utf-8"
        )
    )
    definition = auth.definitions["AuthParamsBase"]
    by_name = {field.name: field for field in definition.fields}
    assert {name for name, field in by_name.items() if field.nullable} >= {
        "type",
        "isgmsaUser",
        "packetPrivacy",
        "packetIntegrity",
    }
    assert all(field.required is False for field in definition.fields)
