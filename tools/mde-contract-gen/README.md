# mde-contract-gen

Standalone workspace tool for generating canonical Microsoft Defender for
Endpoint source contracts from a checked-in OData EDMX snapshot.

The tool owns XML parsing and code generation. `mde-client` only vendors the
generated contracts and a runtime accessor.

```bash
uv run --package mde-contract-gen mde-contract-gen generate
uv run --package mde-contract-gen mde-contract-gen check-drift
uv run --package mde-contract-gen mde-contract-gen doctor
```

Generated response artifacts always flow in this order:

```text
EDMX + overrides -> contract.json -> schema.py + schema.schema.json
```

The authoritative metadata snapshot is `metadata/mde_metadata.xml`.
Corrections and missing return-shape declarations belong in keyed JSON
documents under `overrides/`; generated files and the snapshot are not patched
to represent runtime exceptions.

`versions.json` is the human-reviewed semantic-version registry. Marking an
entry released with its definition hash prevents that version from being
overwritten. See the rendered canonical-contract documentation for the full
override, release, and rollback workflow.
