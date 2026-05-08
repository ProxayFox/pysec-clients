# pysec-clients

Monorepo of Python API clients for security vendors.

Each vendor package lives under `src/` as its own installable workspace member, with shared tooling and quality checks at the repository root.

## Packages

| Package | Vendor | Notes |
| ------- | ------ | ----- |
| [mde-client](src/mde_client/) | Microsoft Defender for Endpoint | OAuth client credentials auth, lazy endpoint results, PyArrow/Polars output helpers |

## Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) for environment and dependency management
- [`just`](https://just.systems/) for common development tasks

## Quick Start

```bash
git clone <repo-url>
cd pysec-clients
uv sync --all-packages --all-groups
just quality
```

Use `uv` for dependency operations throughout the workspace. Do not use `pip` or `poetry` here.

## Project Layout

```text
pysec-clients/
 pyproject.toml      # uv workspace configuration and shared dependency groups
 justfile            # lint, format, typecheck, test, docs tasks
 src/
  mde_client/       # Microsoft Defender for Endpoint package
 test/               # repository-level tests
```

Vendor packages follow the same high-level pattern:

- `client.py` exposes the top-level client and lifecycle management.
- `auth.py` encapsulates vendor authentication.
- `endpoints/` contains endpoint clients and query/result types.
- `schemas/` holds table schemas or response-shaping helpers when needed.

For package-specific API usage, authentication requirements, and examples, start with the vendor README. The current implementation is documented in [src/mde_client/README.md](src/mde_client/README.md).

## Development Workflow

All common tasks are exposed through `just`:

```bash
just lint          # uv run ruff check .
just lint-fix      # uv run ruff check --fix .
just format        # uv run ruff format .
just format-check  # uv run ruff format --check .
just test          # uv run pytest -q
just test-all      # uv run pytest --runslow -q
just typecheck     # uv run ty check --project . && uvx pyright --threads
just quality       # lint, format-check/format, typecheck, test
```

Documentation tasks also exist in `justfile`:

```bash
just docs-build    # uv run --group docs mkdocs build --strict
just docs-serve    # uv run --group docs mkdocs serve
just docs-validate # uv run --group docs mkdocs build --strict
```

Those docs commands currently require a checked-in `mkdocs.yml`. They are part of the intended workflow, but they are not runnable from this repository state until that configuration file is added.

## Adding A New Vendor Client

1. Create `src/<vendor_client>/` with its own `pyproject.toml`.
2. Follow the same package shape as `src/mde_client/`.
3. Register the workspace member in the root `pyproject.toml` under `[tool.uv.sources]`.
4. Add or extend tests under `test/` for the new package surface.
5. Document package-specific setup and examples in that package's README.

## License

[AGPL-3.0](LICENSE)
