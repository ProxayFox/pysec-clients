# Agent Instructions

## Project

Monorepo of Python API clients for security vendors. Each client package lives under `src/` as a uv workspace member.

Start with:

- [README.md](README.md) for repository workflow and task runner commands.
- [src/mde_client/README.md](src/mde_client/README.md) for the current package surface and API usage.

## Current repo shape

- `pyproject.toml`: uv workspace, dependency groups, pytest and typechecker config.
- `justfile`: preferred entrypoint for lint, format, typecheck, test, docs, and schema-generation tasks.
- `src/mde_client/`: current Microsoft Defender for Endpoint client package.
- `tests/`: pytest suite.
- `scripts/mde_contract.py`: regenerates schema modules from Defender metadata.

## Working rules

- Use `uv` for all dependency operations. Do not use `pip` or `poetry`.
- Prefer `just` commands over raw tool invocations.
- Run `just quality` before finishing a change. This skips integration tests via `--skip-integration`.
- Use `just quality-full` only when Azure-backed integration coverage is required and credentials are available.
- When changing generated schema surfaces, prefer `just schema-build` or `just schema-refresh` over broad manual edits.

## Common commands

| Task | Command |
| ---- | ------- |
| Bootstrap env | `uv sync --all-packages --all-groups` |
| Lint | `just lint` |
| Format | `just format` |
| Type-check | `just typecheck` |
| Focused tests | `just test tests/...` |
| Default quality gate | `just quality` |
| Full gate with integration | `just quality-full` |
| Regenerate schemas from local metadata | `just schema-build` |
| Refresh metadata and regenerate schemas | `just schema-refresh` |

## MDE client architecture

The current package follows `Client -> Auth -> Endpoint -> Results -> Schema`.

- `client.py`: `MDEClient`, context-manager lifecycle, lazy endpoint properties.
- `auth.py`: `MSALAuth`, token acquisition, cache injection.
- `endpoints/base.py`: shared endpoint/query/results behavior.
- `endpoints/machines.py`: endpoint methods and `BaseResults` subclasses.
- `schemas/`: Arrow schemas used by result materialization.

Important implementation detail: endpoint methods currently return lazy `BaseResults` wrappers such as `MachineResults`, not eager tables or single Pydantic models. Terminal methods like `.to_json()`, `.to_arrow()`, `.to_polars()`, and `.refresh()` control fetch/materialization.

## Conventions that matter

- Python >= 3.14 with modern typing syntax.
- Preserve full type annotations; both `ty` and `pyright` must pass.
- Pydantic v2 only.
- Keep constructor injection for `httpx.Client` and `msal.TokenCache` to preserve testability.
- Use module-level loggers as `log = logging.getLogger(__name__)`.
- For API-shaped models, prefer tolerant parsing with `extra="ignore"`, `populate_by_name=True`, and `Field(alias=...)` where the upstream payload uses different names.
- Defender filter/query models intentionally preserve API field names such as `healthStatus`; do not normalize those to snake_case unless the package surface already does so.

## Scoped instructions

Use the narrower instruction files when they apply instead of repeating them here:

- `.github/instructions/python-workflow.instructions.md`
- `.github/instructions/mde-client.instructions.md`
