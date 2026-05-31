---
applyTo: "**/*.py"
---

# Python Workflow

- Use `uv` for all dependency operations — never `pip`. Bootstrap with `uv sync --all-packages --all-groups`.
- Prefer `just` commands (`just lint`, `just test`, etc.) over raw tool invocations.
- Target Python ≥ 3.14: use `X | Y` union syntax, not `Union[X, Y]`.
- Preserve full type annotations; both `pyright` and `ty` must pass.
- Lint and format with `ruff` — do not introduce `black`, `flake8`, or `isort`.
- Prefer focused path-based commands while iterating, for example `just lint src/mde-client/...` or `just test tests/mde_client/...`.
- Tests live under `tests/` and run with `pytest` via `just test`.
- Run `just quality` as the default final validation before completing work; it skips integration tests on purpose.
- Use `just quality-full` only when integration coverage is intended and credentials are available.
- The pre-commit hook runs `just quality` and may rewrite files before aborting a commit.
- Docs commands (`just docs-build`, `just docs-serve`, `just docs-validate`) render the site from [`mkdocs.yml`](../../mkdocs.yml) into `site/`.
- Security tooling (`bandit`, `checkov`, `deptry`) is available in the dev group for auditing.
