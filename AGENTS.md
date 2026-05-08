# Agent Instructions

## Project

Monorepo of Python API clients for security vendors (Defender, CrowdStrike, Tenable, …).
Each vendor lives as its own package under `src/`.

## Workspace layout

```text
pyproject.toml          # root: uv workspace config, dev/docs dependency groups
justfile                # task runner — preferred entrypoint for all commands
src/
  mde_client/           # Microsoft Defender for Endpoint client
    client.py           # MDEClient — top-level client, lazy endpoint properties
    auth.py             # MSALAuth — OAuth token acquisition via MSAL
    endpoints/          # one module per API area (e.g. machines.py)
    pyproject.toml      # package-level deps
test/                   # pytest test root (mirrors src/ structure)
```

## Tooling

| Task | Command |
| ---- | ------- |
| Bootstrap env | `uv sync --all-packages --all-groups` |
| Lint | `just lint` |
| Auto-fix lint | `just lint-fix` |
| Format | `just format` |
| Type-check | `just typecheck` (runs `ty` + `pyright`) |
| Test | `just test` |
| Full quality gate | `just quality` (lint → format → typecheck → test) |
| Docs build | `just docs-build` |

Always use `uv` for dependency operations — never `pip` or `poetry`.
Run `just quality` before considering a change complete.

## Architecture — adding a new vendor client

1. Create `src/<vendor_client>/` with its own `pyproject.toml`.
2. Follow the same pattern as `mde_client`: Client → Auth → Endpoints → Models.
3. Register the new workspace member in the root `pyproject.toml` under `[tool.uv.sources]`.

## Conventions

- Python ≥ 3.14 — use modern syntax (`X | Y` unions, etc.).
- Full type annotations on every public API; validated by `pyright` and `ty`.
- Pydantic v2 for request/response models (`model_validate`, `model_dump`, `model_config`).
- PyArrow `pa.Table` for collection returns; Pydantic model for single-item returns.
- Dependency injection of `httpx.Client` and `msal.TokenCache` for testability.
- Module-level logger: `log = logging.getLogger(__name__)`.
- `extra="ignore"` on response models so upstream API additions don't break the client.
