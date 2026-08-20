"""Stable PyArrow descriptors used for compatibility parity gates."""

from __future__ import annotations

from typing import Any

import pyarrow as pa


def schema_descriptor(value: pa.Schema | pa.StructType) -> dict[str, Any]:
    fields = (
        list(value)
        if isinstance(value, pa.Schema)
        else [value.field(index) for index in range(value.num_fields)]
    )
    return {"fields": [_field_descriptor(field) for field in fields]}


def _field_descriptor(field: pa.Field) -> dict[str, Any]:
    return {
        "name": field.name,
        "nullable": field.nullable,
        "type": _type_descriptor(field.type),
    }


def _type_descriptor(data_type: pa.DataType) -> Any:
    if pa.types.is_struct(data_type):
        struct = data_type
        return {
            "kind": "struct",
            "fields": [
                _field_descriptor(struct.field(index))
                for index in range(struct.num_fields)
            ],
        }
    if pa.types.is_list(data_type) or pa.types.is_large_list(data_type):
        return {
            "kind": "large_list" if pa.types.is_large_list(data_type) else "list",
            "valueField": _field_descriptor(data_type.value_field),
        }
    if pa.types.is_timestamp(data_type):
        return {
            "kind": "timestamp",
            "unit": data_type.unit,
            "timezone": data_type.tz,
        }
    if pa.types.is_duration(data_type):
        return {"kind": "duration", "unit": data_type.unit}
    if pa.types.is_time64(data_type) or pa.types.is_time32(data_type):
        return {"kind": "time", "unit": data_type.unit}
    if pa.types.is_decimal(data_type):
        return {
            "kind": "decimal",
            "precision": data_type.precision,
            "scale": data_type.scale,
        }
    return {"kind": str(data_type)}
