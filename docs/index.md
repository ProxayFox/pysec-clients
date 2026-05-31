# pysec-clients

Structured documentation for the packages in the `pysec-clients` workspace — a monorepo of typed Python clients for security-vendor APIs, built around lazy result wrappers and Arrow/Polars output.

## Packages

| Package | What it covers | Docs |
| ------- | -------------- | ---- |
| `mde-client` | Microsoft Defender for Endpoint API: machines, alerts, incidents, advanced hunting, file-export endpoints, vulnerabilities, and more. | [MDE Client docs](mde_client/index.md) |

## Quick start

```bash
uv add "mde-client[arrow,polars]"
```

```python
from mde_client import MDEClient

with MDEClient(tenant_id, client_id, client_secret) as client:
    df = client.machines.get_all().to_polars()
    print(df.shape)
```

For a guided walkthrough see the [Get started tutorial](mde_client/tutorials/get-started.md).

## How the docs are organised

Each package follows the [Diátaxis](https://diataxis.fr/) four-quadrant split:

- **Tutorials** — for the first time you use the package.
- **How-to guides** — task-oriented recipes for specific problems.
- **Reference** — the API surface, with auto-generated method signatures from the package source.
- **Explanation** — design decisions and the rationale behind the package shape.

## Project entry points

- Repository workflow lives in the root [`README.md`](https://github.com/ProxayFox/pysec-clients/blob/main/README.md) (uv workspace, `just` commands, schema regeneration).
- Per-package quick-start material lives in each package's `README.md`.
- This site is the structured documentation for users of the packages.
