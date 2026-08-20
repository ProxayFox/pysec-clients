# Optional local shortcuts layered over the existing uv workflows.

set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

help:
    @just --list

# --- Package Management ---
sync +args="":
    uv sync --all-groups --all-packages {{args}}

check-vulns:
    uv export --frozen --no-hashes --no-editable --no-emit-project | uvx pip-audit -r /dev/stdin

upgrade-deps:
    uv lock --upgrade
    uv sync --all-groups --all-packages
    uvx uv-upgrade

# --- Development ---
lint path="." +args="":
    uv run ruff check {{path}} {{args}}

lint-fix path="." +args="":
    uv run ruff check --fix {{path}} {{args}}

format path="." +args="":
    uv run ruff format {{path}} {{args}}

format-check path="." +args="":
    uv run ruff format --check {{path}} {{args}}

#  --- Testing ---
test path="tests/" +args="":
    uv run pytest -q {{path}} {{args}}

test-all path="tests/" +args="":
    uv run pytest --runslow -q {{path}} {{args}}

# Run the full unit-test suite with coverage and emit a terminal + HTML report.
# Non-gating: `just quality` is unaffected.
coverage path="tests/" +args="":
    uv run pytest -q {{path}} --skip-integration --cov=mde_client --cov-branch --cov-report=term-missing --cov-report=html:build/htmlcov {{args}}

typecheck path="." +args="":
    uv run ty check --project {{path}} {{args}}
    uvx pyright --threads

# --- Git Hooks ---
hooks-install:
    uv run pre-commit install

hooks-run +args="":
    uv run pre-commit run --all-files {{args}}

# --- Quality CI/CD Gate ---
quality:
    if ! uv run ruff check .; then uv run ruff check --fix .; fi
    if ! uv run ruff format --check .; then uv run ruff format .; fi
    just contracts-check
    just contracts-doctor
    just typecheck
    just test --skip-integration
    just build-package mde-client

# Build a workspace package and validate the resulting distribution with twine.
# Usage: just build-package mde-client
build-package package:
    rm -rf src/{{package}}/dist
    uv build --package {{package}} --out-dir src/{{package}}/dist
    uvx twine check src/{{package}}/dist/*

# Similar to Quality, but only targets schema validation
quality-schema schemas="src/mde-client/src/mde_client/schemas" models="src/mde-client/src/mde_client/models" schemas_tests="tests/mde_client/test_schema_validator.py" models_tests="tests/mde_client/test_investigation_models.py":
    just quality-contracts

# Like Quality, but also includes integration tests that require Azure credentials. Use with caution in CI/CD pipelines.
quality-full:
    if ! just lint; then just lint-fix; fi
    if ! just format-check; then just format; fi
    just typecheck
    just test
    just build-package mde-client

# --- Documentation ---
docs-build:
    DISABLE_MKDOCS_2_WARNING=true uv run --group docs mkdocs build --strict

docs-serve:
    DISABLE_MKDOCS_2_WARNING=true uv run --group docs mkdocs serve

docs-validate:
    DISABLE_MKDOCS_2_WARNING=true uv run --group docs mkdocs build --strict

# Preview the multi-version docs site (with the version dropdown) via mike. This
# serves the local `gh-pages` branch, so it requires at least one deployed
# version. For a zero-setup local preview use `just docs-versions-preview`; to
# preview a single version's content without mike, use `just docs-serve`.
docs-versions-serve +args="":
    DISABLE_MKDOCS_2_WARNING=true uv run --group docs mike serve {{args}}

# Build the working tree as a throwaway `dev` version and preview the versioned
# site (with the dropdown) locally. Creates/updates a LOCAL-ONLY `gh-pages`
# branch (never pushed); remove it any time with `git branch -D gh-pages`.
docs-versions-preview:
    DISABLE_MKDOCS_2_WARNING=true uv run --group docs mike deploy --update-aliases dev latest
    DISABLE_MKDOCS_2_WARNING=true uv run --group docs mike set-default latest
    DISABLE_MKDOCS_2_WARNING=true uv run --group docs mike serve

# Deploy a docs version with mike. Omit --push to stage on the local gh-pages
# branch; pass --push to publish. Usage: just docs-deploy-version mde-client-0.1.4 latest --push
docs-deploy-version version alias="latest" +args="":
    DISABLE_MKDOCS_2_WARNING=true uv run --group docs mike deploy --update-aliases {{version}} {{alias}} {{args}}

# Set the default docs version served at the site root. The alias/version must
# already exist (deploy first). Usage: just docs-set-default latest --push
docs-set-default alias="latest" +args="":
    DISABLE_MKDOCS_2_WARNING=true uv run --group docs mike set-default {{alias}} {{args}}

# --- Schema management ---

# Generate canonical contracts and both schema projections from checked-in EDMX.
contracts-generate:
    @uv run --package mde-contract-gen mde-contract-gen generate

# Regenerate into a temporary tree and fail when vendored artifacts differ.
contracts-check:
    @uv run --package mde-contract-gen mde-contract-gen check-drift

# Validate metadata, overrides, contracts, hashes, versions, and generated source.
contracts-doctor:
    @uv run --package mde-contract-gen mde-contract-gen doctor

# Focused quality gate for the standalone generator and vendored runtime surface.
quality-contracts:
    @just contracts-check
    @just contracts-doctor
    @just lint tools/mde-contract-gen src/mde-client/src/mde_client/contracts src/mde-client/src/mde_client/schemas src/mde-client/src/mde_client/models scripts/mde_contract.py scripts/fetch_mde_metadata.py tests/mde_contract_gen tests/mde_client/test_contract_artifacts.py tests/mde_client/test_contract_registry.py tests/mde_client/test_schema_parity.py tests/mde_client/test_schema_validator.py
    @just format-check tools/mde-contract-gen src/mde-client/src/mde_client/contracts src/mde-client/src/mde_client/schemas src/mde-client/src/mde_client/models scripts/mde_contract.py scripts/fetch_mde_metadata.py tests/mde_contract_gen tests/mde_client/test_contract_artifacts.py tests/mde_client/test_contract_registry.py tests/mde_client/test_schema_parity.py tests/mde_client/test_schema_validator.py
    @just typecheck
    @just test tests/mde_contract_gen tests/mde_client/test_contract_artifacts.py tests/mde_client/test_contract_registry.py tests/mde_client/test_schema_parity.py tests/mde_client/test_schema_validator.py tests/mde_client/test_investigation_models.py --skip-integration
    @just build-package mde-client

# Backwards-compatible aliases.
schema-build:
    just contracts-generate

schema-build-dry:
    just contracts-check

schema-refresh:
    @uv run scripts/fetch_mde_metadata.py
    @just contracts-generate