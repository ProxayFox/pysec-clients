from __future__ import annotations

import pytest
from mde_contract_gen.canonical import add_hashes
from mde_contract_gen.cli import DEFAULT_CONTRACTS
from mde_contract_gen.models import ContractField, LogicalType, SourceContract
from mde_contract_gen.versions import (
    VersionEntry,
    VersionRegistry,
    recommend_bump,
)
from pydantic import ValidationError


def _machine() -> SourceContract:
    return SourceContract.model_validate_json(
        (DEFAULT_CONTRACTS / "machine/contract.json").read_text(encoding="utf-8")
    )


def test_invalid_semver_is_rejected() -> None:
    with pytest.raises(ValidationError, match="semantic version"):
        VersionEntry(version="1.2")


def test_invalid_released_hash_is_rejected() -> None:
    with pytest.raises(ValidationError, match="sha256"):
        VersionEntry(version="1.2.3", definitionHash="not-a-hash")


def test_released_version_cannot_be_overwritten() -> None:
    contract = _machine()
    assert contract.hashes is not None
    registry = VersionRegistry(
        contracts={
            "machine": VersionEntry(
                version=contract.version,
                released=True,
                definitionHash="sha256:" + "0" * 64,
            )
        }
    )
    with pytest.raises(ValueError, match="released and immutable"):
        registry.guard_released("machine", contract)


def test_semver_recommendations_classify_contract_changes() -> None:
    previous = _machine()

    added = previous.model_copy(deep=True)
    added.fields.append(
        ContractField(
            name="futureField",
            sourceName="futureField",
            sourceType="Edm.String",
            logicalType=LogicalType.STRING,
            required=False,
            nullable=True,
        )
    )
    added = add_hashes(added)
    assert recommend_bump(previous, added) == "minor"

    removed = previous.model_copy(update={"fields": previous.fields[1:]}, deep=True)
    removed = add_hashes(removed)
    assert recommend_bump(previous, removed) == "major"

    documentation = previous.model_copy(
        update={"description": "Updated documentation."}, deep=True
    )
    documentation = add_hashes(documentation)
    assert recommend_bump(previous, documentation) == "patch"


def test_hashes_ignore_volatile_generation_metadata() -> None:
    first = _machine()
    second = first.model_copy(deep=True)
    second.generation.generated_at = "2099-01-01T00:00:00Z"
    second.generation.source_metadata_hash = "sha256:" + "f" * 64
    second = add_hashes(second)
    assert second.hashes == first.hashes
