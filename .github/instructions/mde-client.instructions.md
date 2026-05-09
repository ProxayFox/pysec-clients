---
applyTo: "src/mde_client/**/*.py"
---

# MDE Client — Implementation Patterns

Follow the patterns established in the existing code. Reference files:

- [client.py](../../src/mde_client/client.py) — `MDEClient`, lazy endpoint properties, context-manager lifecycle.
- [auth.py](../../src/mde_client/auth.py) — `MSALAuth`, token acquisition, `AuthenticationError`.
- [endpoints/base.py](../../src/mde_client/endpoints/base.py) — shared endpoint, query, and lazy result behavior.
- [endpoints/machines.py](../../src/mde_client/endpoints/machines.py) — endpoint class, query models, result wrappers, pagination, OData filters.
- [README.md](../../src/mde_client/README.md) — current public package behavior and supported endpoint surface.

## Adding a new endpoint

1. Create `endpoints/<area>.py` with:
   - A **query model** built on the existing `BaseQuery` pattern.
   - One or more **results wrappers** that subclass `BaseResults` and bind the correct Arrow schema through `SCHEMA = ...`.
   - Any **response models** needed for normalization using Pydantic v2 with `extra="ignore"`, `populate_by_name=True`, and `Field(alias=...)` where appropriate.
   - An **endpoint class** that receives `httpx.Client` and `MSALAuth`, inherits from `BaseEndpoint`, and returns lazy results wrappers from public methods.
2. Register the endpoint as a `@property` on `MDEClient` in `client.py`.
3. Add domain-specific exceptions in the same module when the package needs clearer errors than raw `httpx` exceptions.
4. Add or extend tests under `tests/mde_client/`.

## Key rules

- Pydantic v2 only: `model_validate()`, `model_dump(by_alias=False)`, `model_config` dict.
- Use `Field(ge=…, le=…)` for numeric constraints — validate at construction, not at request time.
- Endpoint methods return lazy `BaseResults` subclasses. Materialization happens through terminal methods such as `.to_json()`, `.to_arrow()`, `.to_polars()`, and `.refresh()`.
- Use `single=True` on result wrappers for single-item lookups instead of inventing a second return pattern.
- Pagination stays in the shared base behavior; do not fork a new pagination helper unless the API shape genuinely differs.
- Auth: call `self._auth.token` per request in `_request()` — the property handles refresh.
- OData filter strings are built by concatenation — **sanitise or validate user-supplied values** to prevent OData injection.
- Constructor injection: accept `httpx.Client` and `msal.TokenCache` so tests can substitute fakes.
- Preserve Defender API field names in query models when the endpoint intentionally mirrors upstream filters, for example `healthStatus`.
- Use a module-level logger when needed: `log = logging.getLogger(__name__)`.
- If schema files need regeneration, prefer the `just schema-build` or `just schema-refresh` workflow over manual bulk edits.
- Keep `__init__.py` exports minimal and maintain `__all__`.
