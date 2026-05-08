# pysec-clients

Monorepo of Python API clients for security vendors — Defender, CrowdStrike, Tenable, and more to come.

Each vendor ships as its own installable package under `src/`.

## Packages

| Package | Vendor | Install |
| ------- | ------ | ------- |
| [mde-client](src/mde_client/) | Microsoft Defender for Endpoint | `uv add mde-client` |

## Requirements

- Python ≥ 3.14
- [uv](https://docs.astral.sh/uv/) for dependency management

## Quick start

```bash
# clone and bootstrap
git clone <repo-url> && cd pysec-clients
uv sync --all-packages --all-groups

# run the full quality gate (lint → format → typecheck → test)
just quality
```

## Development

All tasks are run through [`just`](https://just.systems/):

```bash
just lint          # ruff check
just lint-fix      # ruff check --fix
just format        # ruff format
just typecheck     # ty + pyright
just test          # pytest
just quality       # all of the above, in order
just docs-serve    # local MkDocs preview
```

> **Note:** Always use `uv` for dependency operations — never `pip` or `poetry`.

## Adding a new vendor client

1. Create `src/<vendor_client>/` with its own `pyproject.toml`.
2. Follow the same architecture as `mde_client` — see the [mde-client README](src/mde_client/README.md).
3. Register the workspace member in the root `pyproject.toml` under `[tool.uv.sources]`.

## License

[AGPL-3.0](LICENSE)
