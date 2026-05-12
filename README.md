# pysec-clients

Python API clients for security vendors, developed as a single `uv` workspace.

The repository currently ships one package, [`mde-client`](src/mde_client/), a Microsoft Defender for Endpoint client built around lazy endpoint results, Arrow and Polars materialization helpers, and dependency injection for HTTP and auth testability.

## Packages

| Package | Vendor | Summary |
| ------- | ------ | ------- |
| [`mde-client`](src/mde_client/) | Microsoft Defender for Endpoint | Client-credentials auth, lazy endpoint wrappers, file-export helpers, Arrow and Polars outputs |

Package-specific setup, examples, and API notes live in [`src/mde_client/README.md`](src/mde_client/README.md).

## Requirements

- Python >= 3.14
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency management
- [`just`](https://just.systems/) for common development tasks

Use `uv` for dependency operations throughout the workspace. Do not use `pip` or `poetry` here.

## Quick Start

```bash
git clone <repo-url>
cd pysec-clients
uv sync --all-packages --all-groups
just hooks-install
just quality
```

`just quality` is the default repository gate. It runs linting, formatting, type-checking, and the test suite with integration tests skipped.

## Development Workflow

The root [`justfile`](justfile) is the source of truth for local commands.

| Task | Command |
| ---- | ------- |
| Bootstrap the workspace | `uv sync --all-packages --all-groups` |
| Lint | `just lint` |
| Format | `just format` |
| Type-check | `just typecheck` |
| Run focused tests | `just test tests/mde_client/...` |
| Default quality gate | `just quality` |
| Include integration tests | `just quality-full` |
| Install pre-commit hook | `just hooks-install` |
| Run the hook manually | `just hooks-run` |

The repository ships a `.pre-commit-config.yaml` that runs `just quality` before each commit. Because the quality gate can auto-fix lint and formatting issues, the hook may rewrite files and abort the commit once; review the changes, re-stage them, and commit again.

## Project Layout

```text
pysec-clients/
    pyproject.toml         # uv workspace configuration and shared dependency groups
    justfile               # lint, format, typecheck, test, and docs tasks
    scripts/               # repo utilities such as schema generation helpers
    src/
        mde_client/          # Microsoft Defender for Endpoint client package
    tests/
        mde_client/          # package-focused pytest suite
```

Each client package follows the same broad shape:

- `client.py` exposes the top-level client and lifecycle management.
- `auth.py` encapsulates vendor authentication.
- `endpoints/` contains endpoint clients, query models, and lazy result wrappers.
- `schemas/` holds Arrow schemas and response-shaping helpers.

## Documentation

This repository is currently README-first, with structured package documentation starting under [`docs/mde_client/`](docs/mde_client/index.md).

- Start here for workspace setup and development commands.
- Use [`src/mde_client/README.md`](src/mde_client/README.md) for the package summary and quick-start example.
- Use [`docs/mde_client/index.md`](docs/mde_client/index.md) for tutorials, how-to guides, reference pages, and explanation pages for `mde-client`.
- `just docs-build` and `just docs-serve` exist in [`justfile`](justfile), but the repository does not currently include an `mkdocs.yml`, so those tasks are not runnable from the checked-in state yet.

## Adding Another Client

1. Create `src/<vendor_client>/` as a workspace member with its own `pyproject.toml`.
2. Follow the same `Client -> Auth -> Endpoint -> Results -> Schema` shape used by [`src/mde_client/`](src/mde_client/).
3. Register the workspace member in the root [`pyproject.toml`](pyproject.toml).
4. Add or extend tests under [`tests/`](tests/).
5. Document package-specific setup and examples in that package's README.

## License

[AGPL-3.0](LICENSE)
