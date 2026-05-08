---
applyTo: "src/mde_client/**/*.py"
---

# MDE Client — Implementation Patterns

Follow the patterns established in the existing code. Reference files:

- [client.py](../../src/mde_client/client.py) — `MDEClient`, lazy endpoint properties, context-manager lifecycle.
- [auth.py](../../src/mde_client/auth.py) — `MSALAuth`, token acquisition, `AuthenticationError`.
- [endpoints/machines.py](../../src/mde_client/endpoints/machines.py) — endpoint class, query/response models, pagination, OData filters.

## Adding a new endpoint

1. Create `endpoints/<area>.py` with:
   - A **query model** (`BaseModel`) with `to_odata_params() -> dict[str, str]`.
   - A **response model** (`BaseModel`, `extra="ignore"`, `populate_by_name=True`) using `Field(alias=...)` for API field names.
   - An **endpoint class** that receives `httpx.Client` and `MSALAuth`, exposes `get_all()` → `pa.Table` and `get()` → model.
2. Register the endpoint as a `@property` on `MDEClient` in `client.py`.
3. Add domain-specific exceptions in the same module.

## Key rules

- Pydantic v2 only: `model_validate()`, `model_dump(by_alias=False)`, `model_config` dict.
- Use `Field(ge=…, le=…)` for numeric constraints — validate at construction, not at request time.
- Collection endpoints return `pa.Table`; single-item endpoints return the Pydantic model.
- Pagination: walk `@odata.nextLink` in `_paginate()`; do not invent a new pagination helper.
- Auth: call `self._auth.token` per request in `_request()` — the property handles refresh.
- OData filter strings are built by concatenation — **sanitise or validate user-supplied values** to prevent OData injection.
- Constructor injection: accept `httpx.Client` and `msal.TokenCache` so tests can substitute fakes.
- Keep `__init__.py` exports minimal and maintain `__all__`.
