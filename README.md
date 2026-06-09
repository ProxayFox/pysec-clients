# pysec-clients

Python API clients for security vendors, developed as a single `uv` workspace.

📖 **Docs:** <https://proxayfox.github.io/pysec-clients/>

The repository currently ships one package, [`mde-client`](src/mde-client/), a Microsoft Defender for Endpoint client built around lazy endpoint results, Arrow and Polars materialization helpers, and dependency injection for HTTP and auth testability.

## Packages

| Package | Vendor | Summary |
| ------- | ------ | ------- |
| [`mde-client`](src/mde-client/) | Microsoft Defender for Endpoint | Client-credentials auth, lazy endpoint wrappers, file-export helpers, Arrow and Polars outputs |

Package-specific setup, examples, and API notes live in [`src/mde-client/README.md`](src/mde-client/README.md).

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
    pyproject.toml             # uv workspace configuration and shared dependency groups
    justfile                   # lint, format, typecheck, test, build, and docs tasks
    scripts/                   # repo utilities such as schema generation helpers
    src/
        mde-client/            # Microsoft Defender for Endpoint client (workspace member)
            pyproject.toml     # package metadata, dependencies, classifiers
            CHANGELOG.md
            README.md
            LICENSE
            src/
                mde_client/    # Python package — `from mde_client import ...`
    tests/
        mde_client/            # package-focused pytest suite
```

Each client package follows the same broad shape:

- The workspace member directory matches the distribution name (e.g. `src/mde-client/`).
- The importable Python package lives at `src/<dist>/src/<import_name>/`.
- `client.py` exposes the top-level client and lifecycle management.
- `auth.py` encapsulates vendor authentication.
- `endpoints/` contains endpoint clients, query models, and lazy result wrappers.
- `schemas/` holds Arrow schemas and response-shaping helpers.

## Documentation

This repository is currently README-first, with structured package documentation starting under [`docs/mde_client/`](docs/mde_client/index.md).

- Start here for workspace setup and development commands.
- Use [`src/mde-client/README.md`](src/mde-client/README.md) for the package summary and quick-start example.
- Use [`docs/mde_client/index.md`](docs/mde_client/index.md) for tutorials, how-to guides, reference pages, and explanation pages for `mde-client`.
- Build the rendered site with `just docs-build` (writes to `site/`) or run `just docs-serve` for a live-reload preview backed by [`mkdocs.yml`](mkdocs.yml).

### Versioned documentation

The published site at <https://proxayfox.github.io/pysec-clients/> is versioned with [`mike`](https://github.com/jimporter/mike) and served from the `gh-pages` branch. A version selector in the page header lets readers switch between releases, so documentation for an older version stays available even after a feature is removed.

- The site root tracks the latest stable `mde-client` release; prerelease docs are published but never move the `latest` alias.
- Pushing a `mde-client-v<version>` release tag publishes a versioned snapshot automatically through the [Docs workflow](.github/workflows/docs.yml).
- Preview the versioned site locally with `just docs-versions-serve`.
- To stage or repair a version by hand, use `just docs-deploy-version <package>-<version> latest` (add `--push` to publish) and `just docs-set-default latest --push`.

> [!NOTE]
> GitHub Pages must be set to deploy from the `gh-pages` branch (root) for the versioned site to serve. The first `mike` deploy creates that branch.

## Adding Another Client

1. Create `src/<distribution-name>/` as a workspace member (e.g. `src/crowdstrike-client/`)
   with its own `pyproject.toml`, `README.md`, `CHANGELOG.md`, and `LICENSE`.
2. Place the importable Python package at `src/<distribution-name>/src/<import_name>/`
   (e.g. `src/crowdstrike-client/src/crowdstrike_client/`). Include a `py.typed`
   marker if the package ships type hints.
3. Follow the same `Client -> Auth -> Endpoint -> Results -> Schema` shape used
   by [`src/mde-client/`](src/mde-client/).
4. The root `[tool.uv.workspace] members = ["src/*"]` picks up the new member
   automatically; add the import name to root `[tool.uv.sources]` if it is
   consumed by the root project.
5. Add or extend tests under [`tests/`](tests/).
6. Document package-specific setup and examples in that package's README.
7. Publish via the shared release workflow by tagging
   `<distribution-name>-v<version>` (see the package's `README.md` Releasing
   section for the full checklist).

## License

[Apache-2.0](LICENSE)
