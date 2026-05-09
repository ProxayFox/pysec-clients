---
applyTo: "**/*.py"
---

# Python Workflow

- Use `uv` for all dependency operations — never `pip`.
- Prefer `just` commands (`just lint`, `just test`, etc.) over raw tool invocations.
- Target Python ≥ 3.14: use `X | Y` union syntax, not `Union[X, Y]`.
- Preserve full type annotations; both `pyright` and `ty` must pass.
- Tests live under `tests/` and run with `pytest` via `just test`.
- Run `just quality` as the default final validation before completing work; it skips integration tests.
- Use `just quality-full` only when integration coverage is intended and credentials are available.
- Lint and format with `ruff` — do not introduce `black`, `flake8`, or `isort`.
- Prefer focused paths when possible, for example `just test tests/mde_client/...` or `just lint src/mde_client/...`.
- Security tooling (`bandit`, `checkov`, `deptry`) is available in the dev group for auditing.
