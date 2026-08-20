from __future__ import annotations

from types import MappingProxyType

import pyarrow as pa
import pytest
from mde_client.contracts.registry import get_contract, list_contracts
from mde_client.schemas import MACHINE_SCHEMA


def test_registry_lists_every_vendored_contract() -> None:
    slugs = list_contracts()
    assert len(slugs) == 51
    assert slugs == tuple(sorted(slugs))
    assert {"asset_vulnerability", "machine"} <= set(slugs)


def test_bundle_exposes_contract_manager_handshake() -> None:
    bundle = get_contract("machine")
    by_name = get_contract("mde.machine.source")
    assert by_name == bundle
    assert bundle.name == "mde.machine.source"
    assert bundle.version == "1.0.0"
    assert bundle.definition_hash.startswith("sha256:")
    assert bundle.arrow_hash.startswith("sha256:")
    assert bundle.source_metadata_hash is not None
    assert isinstance(bundle.json_schema, MappingProxyType)
    assert bundle.json_schema["$schema"].endswith("draft/2020-12/schema")


def test_arrow_schema_is_the_compatibility_export() -> None:
    schema = get_contract("machine").arrow_schema
    assert isinstance(schema, pa.Schema)
    assert schema == MACHINE_SCHEMA


def test_unknown_contract_raises_key_error() -> None:
    with pytest.raises(KeyError, match="Unknown MDE contract"):
        get_contract("does-not-exist")
