from __future__ import annotations

import pytest
from mde_contract_gen.models import (
    ComplexTypeDefinition,
    ContractField,
    Conventions,
    Generation,
    ItemSpec,
    LogicalType,
    SourceContract,
    SourceDescription,
    StructuralType,
)
from pydantic import ValidationError


def _contract(**updates: object) -> SourceContract:
    values: dict[str, object] = {
        "contractFormatVersion": "1.0.0",
        "name": "mde.example.source",
        "version": "1.0.0",
        "title": "Example",
        "source": SourceDescription(
            system="mde",
            metadataFormat="odata-edmx",
            structuralType=StructuralType.ENTITY,
            entityType="Example",
        ),
        "conventions": Conventions(
            requiredRule="test",
            unspecifiedNullableDefault=True,
        ),
        "fields": [
            ContractField(
                name="id",
                sourceName="id",
                sourceType="Edm.String",
                logicalType=LogicalType.STRING,
                required=True,
                nullable=False,
            )
        ],
        "generation": Generation(generator="test"),
    }
    values.update(updates)
    return SourceContract.model_validate(values)


def test_extra_keys_are_forbidden() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        _contract(unexpected=True)


def test_array_requires_items() -> None:
    with pytest.raises(ValidationError, match="requires 'items'"):
        ContractField(
            name="values",
            sourceName="values",
            sourceType="Collection(Edm.String)",
            logicalType=LogicalType.ARRAY,
            required=False,
            nullable=True,
        )


def test_object_requires_ref() -> None:
    with pytest.raises(ValidationError, match="requires 'ref'"):
        ContractField(
            name="value",
            sourceName="value",
            sourceType="MDE.Value",
            logicalType=LogicalType.OBJECT,
            required=False,
            nullable=True,
        )


def test_nested_definition_item_ref_is_validated() -> None:
    nested = ContractField(
        name="children",
        sourceName="children",
        sourceType="Collection(MDE.Missing)",
        logicalType=LogicalType.ARRAY,
        required=False,
        nullable=True,
        items=ItemSpec(
            logicalType=LogicalType.OBJECT,
            sourceType="MDE.Missing",
            ref="Missing",
        ),
    )
    with pytest.raises(ValidationError, match="not in definitions"):
        _contract(
            definitions={
                "Parent": ComplexTypeDefinition(
                    sourceType="MDE.Parent", fields=[nested]
                )
            }
        )


def test_source_key_must_be_a_field() -> None:
    with pytest.raises(ValidationError, match="source keys not present"):
        _contract(
            source=SourceDescription(
                system="mde",
                metadataFormat="odata-edmx",
                structuralType=StructuralType.ENTITY,
                entityType="Example",
                keys=["missing"],
            )
        )
