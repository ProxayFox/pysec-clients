# Canonical MDE source contracts

The MDE response schema pipeline has one direction of authority:

```text
Defender $metadata snapshot + checked-in overrides
    -> canonical contract.json
        -> PyArrow schema.py
        -> JSON Schema schema.schema.json
```

The upstream XML is the vendor authority. `contract.json` is the repository's
internal canonical representation. Every runtime projection is generated from
that contract; PyArrow is never generated from JSON Schema because JSON Schema
cannot preserve details such as integer width, timestamp unit and timezone, or
list element physical types.

## Ownership boundary

`tools/mde-contract-gen/` is a standalone `uv` workspace package. It owns EDMX
parsing, override application, contract validation, hashing, version governance,
and artifact generation. It does not depend on `mde-client`.

`mde-client` vendors generated runtime artifacts under
`mde_client/contracts/`. The package does not parse XML and does not depend on
the generator, `defusedxml`, or JSON Schema tooling. Each response root has an
implicit-package directory containing exactly:

- `contract.json` — validated canonical source contract
- `schema.py` — PyArrow schema and reusable struct constants
- `schema.schema.json` — portable JSON Schema Draft 2020-12

The generated `mde_client.schemas` modules are compatibility wrappers. Existing
endpoint declarations such as `SCHEMA = MACHINE_SCHEMA` therefore retain the
same public objects and behavior.

## Contract identity and root selection

A contract represents one response schema root/type, not one HTTP route.
`source.operations` records all entity sets, bound functions, and actions that
return that root.

Generation selects:

- non-internal EDMX `EntityType` roots;
- non-abstract `ComplexType` roots returned by a function or action; and
- roots declared by a checked-in selection override when upstream metadata
  omits an operation return type.

Nested `ComplexType` values are reusable contract `definitions` referenced by
`ref` or `items.ref`. They become Arrow structs and JSON Schema `$defs`.

## Required and nullable

Required presence and null acceptance are separate contract properties:

- `Nullable="false"` maps to `required: true, nullable: false`;
- omitted or `Nullable="true"` maps to
  `required: false, nullable: true`, following the OData default;
- a verified runtime correction may change nullability without changing
  required presence.

The known `AssetVulnerability.cvssScore` and
`DeltaAssetVulnerability.cvssScore` runtime exceptions are checked-in
overrides. They remain required fields whose values may be null.

JSON Schema places required properties in the object-level `required` array and
adds `"null"` only to nullable property schemas.

## Type and enum behavior

The canonical contract preserves physical information under `constraints`,
`format`, and `wireHints`. Important mappings include:

- `Edm.Int32` / `Edm.Int64` -> integer with 32/64-bit constraints;
- `Edm.Double` / `Edm.Single` -> number with double/single precision;
- `Edm.Byte` -> unsigned 8-bit integer;
- `Edm.Guid` -> string with UUID semantics;
- `Edm.DateTimeOffset` -> microsecond UTC datetime;
- `Collection(T)` -> array with an explicit item descriptor.

Enums intentionally project to Arrow strings. Their current members remain in
the contract's enum catalogue and fields carry `enumRef`. JSON Schema keeps
them as open strings so new Defender enum values do not break consumers.

## Regeneration and overrides

Use the checked-in snapshot for deterministic local generation:

```bash
just contracts-generate
just contracts-check
just contracts-doctor
just quality-contracts
```

Authenticated metadata acquisition is deliberately separate:

```bash
uv run scripts/fetch_mde_metadata.py
just contracts-generate
```

Never edit EDMX or generated artifacts to correct vendor metadata. Add or
change a keyed document under `tools/mde-contract-gen/overrides/`, document the
runtime evidence in review, regenerate, and run the parity gate. Unknown
override keys and fields fail generation.

All Python artifacts start with an `AUTO-GENERATED` header and expose
`__generated__ = True`. Canonical JSON uses
`generation.generated: true` and `generation.doNotEdit: true`. JSON Schema uses
the standard `$comment` keyword.

## Hashes and versions

`tools/mde-contract-gen/versions.json` assigns a semantic version to every
contract. Generation records:

- `hashes.definition` over canonical contract JSON, excluding volatile
  `generatedAt`, `sourceMetadataHash`, and the hashes themselves;
- `hashes.arrow` over the Arrow-relevant physical projection.

The tool recommends a major, minor, or patch bump when an unchanged version's
definition changes. Marking a registry entry as released and recording its
definition hash makes that version immutable; generation refuses to overwrite
it. A human reviews and confirms version changes.

## Contract-manager handshake

Downstream code should use the runtime registry rather than package paths:

```python
from mde_client.contracts.registry import get_contract

source = get_contract("machine")

canonical = source.contract
portable_schema = source.json_schema
arrow_schema = source.arrow_schema

identity = (source.name, source.version, source.definition_hash, source.arrow_hash)
```

The stable integration guarantees are:

- lookup by directory slug or canonical contract name;
- canonical `name` and semantic `version`;
- deterministic definition and Arrow hashes;
- parsed runtime contract, read-only JSON Schema mapping, and PyArrow schema;
- no XML parsing or generator dependency at runtime.

Exporter, storage, collector, API, and Zod/TypeScript contracts remain the
responsibility of the downstream contract manager.

## Rollout and rollback

The rollout gate is endpoint-by-endpoint even though the final committed set is
generated together:

1. validate vulnerability contracts and the documented nullability override;
2. validate `Machine`, including enums and nested structs;
3. validate merged abstract authenticated-scan structs;
4. expand to every selected root and require complete Arrow export parity.

If parity fails, do not update endpoint imports or remove legacy wrappers.
Revert the generated contract commit (or restore the last released artifacts),
fix parsing or a reviewed override in the standalone tool, and regenerate. The
legacy `mde_client.schemas` wrapper boundary provides the rollback seam; endpoint
and `BaseResults` APIs require no rollback changes.
