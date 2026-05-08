---
applyTo: "**/*.py"
---

# Python Workflow

- Use `uv` for all dependency operations — never `pip`.
- Prefer `just` commands (`just lint`, `just test`, etc.) over raw tool invocations.
- Target Python ≥ 3.14: use `X | Y` union syntax, not `Union[X, Y]`.
- Preserve full type annotations; both `pyright` and `ty` must pass.
- Tests live under `test/` and run with `pytest` (`just test`).
- Run `just quality` as the final validation before completing work.
- Lint and format with `ruff` — do not introduce `black`, `flake8`, or `isort`.
- Security tooling (`bandit`, `checkov`, `deptry`) is available in the dev group for auditing.
