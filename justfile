# Optional local shortcuts layered over the existing uv workflows.

set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

help:
    @just --list

# --- Development ---
lint path=".":
    uv run ruff check {{path}}

lint-fix path=".":
    uv run ruff check --fix {{path}}

format path=".":
    uv run ruff format {{path}}

format-check path=".":
    uv run ruff format --check {{path}}

#  --- Testing ---
test path="tests/":
    uv run pytest -q {{path}}

test-all path="tests/":
    uv run pytest --runslow -q {{path}}

typecheck path=".":
    uv run ty check --project {{path}}
    uvx pyright --threads

# --- Quality CI/CD Gate ---
quality:
    if ! just lint; then just lint-fix; fi
    if ! just format-check; then just format; fi
    just typecheck
    just test

# Similar to Quality, but only targets schema validation
quality-schema path="src/mde_client/schemas" tests="tests/mde_client/test_schema_validator.py":
    if ! just lint {{path}}; then just lint-fix {{path}}; fi
    if ! just format-check {{path}}; then just format {{path}}; fi
    just typecheck {{path}}
    just test {{tests}}


# --- Documentation ---
docs-build:
    uv run --group docs mkdocs build --strict

docs-serve:
    uv run --group docs mkdocs serve

docs-validate:
    uv run --group docs mkdocs build --strict

# --- Schema management ---

# Regenerate schemas from existing XML (no credentials required)
schema-build:
    uv run scripts/mde_contract.py --no-fetch

# Preview what schema-build would write, without touching any files
schema-build-dry:
    uv run scripts/mde_contract.py --no-fetch --dry-run

# Re-fetch $metadata from the live API then regenerate (requires Azure credentials)
schema-refresh:
    uv run scripts/mde_contract.py --refresh-metadata

# Preview what schema-refresh would write, without touching any files
schema-refresh-dry:
    uv run scripts/mde_contract.py --refresh-metadata --dry-run
