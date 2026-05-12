---
applyTo: "src/mde_client/**/*.py"
---

# MDE Client — Implementation Patterns

Follow the patterns established in the existing code. Reference files:

- [client.py](../../src/mde_client/client.py) — `MDEClient`, lazy endpoint properties, context-manager lifecycle.
- [auth.py](../../src/mde_client/auth.py) — `MSALAuth`, token acquisition, `AuthenticationError`.
- [endpoints/base.py](../../src/mde_client/endpoints/base.py) — `BaseQuery`, `BaseResults`, authenticated requests, and shared pagination.
- [endpoints/alerts.py](../../src/mde_client/endpoints/alerts.py) — mutating methods that return either lazy results or `bool`, depending on API shape.
- [endpoints/library.py](../../src/mde_client/endpoints/library.py) — eager `bool` write helpers for library uploads and deletes.
- [endpoints/machines.py](../../src/mde_client/endpoints/machines.py) — endpoint class, query models, result wrappers, pagination, and OData filters.
- [viaFiles.py](../../src/mde_client/viaFiles.py) — async export download, decompression, NDJSON parsing, and batching.
- [README.md](../../src/mde_client/README.md) — current public package behavior and supported endpoint surface.
- [mde_contract.py](../../scripts/mde_contract.py) — schema generation workflow and `quality-schema` handoff.

## Adding or changing an endpoint

1. Keep read and list endpoints on the existing `BaseEndpoint -> BaseResults` path:
   - Build query models on `BaseQuery`.
   - Return lazy results wrappers that bind `SCHEMA = ...`.
   - Use `single=True` for single-resource lookups instead of inventing a second return pattern.
2. Match mutating endpoint return types to the API shape:
   - Return a `BaseResults` subclass when the API returns a meaningful resource body, even for `POST` or `PATCH`.
   - Return `bool` only for helpers that issue the request immediately and only need a success/failure signal.
3. For file-export endpoints, use `files=True` and let `ViaFiles` handle SAS downloads, gzip/NDJSON parsing, and batching. Override `_normalize_export_record()` when the export payload wraps the entity under a nested key.
4. Register new endpoint surfaces as `@property` methods on `MDEClient` in `client.py`.
5. Add domain-specific exceptions in the same module when the package needs clearer errors than raw `httpx` exceptions.
6. Add or extend focused tests under `tests/mde_client/`.

## Key rules

- Pydantic v2 only: `model_validate()`, `model_dump(...)`, `model_config` dict.
- For API-shaped models, prefer tolerant parsing with `extra="ignore"`, `populate_by_name=True`, and `Field(alias=...)` where the upstream payload uses different names.
- Use `Field(ge=…, le=…)` for numeric constraints — validate at construction, not at request time.
- Read and list methods usually return lazy `BaseResults` subclasses. Do not generalize that rule to every public method; some write helpers are eager and return `bool`.
- If a write operation returns a resource body, keep it on the lazy results path by setting `method=...` and `request_kwargs=...` on the results wrapper.
- Pagination stays in the shared base behavior; do not fork a new pagination helper unless the API shape genuinely differs.
- Auth: call `self._auth.token` per request in `_request()` — the property handles refresh.
- OData filter strings are built by concatenation — **sanitise or validate user-supplied values** to prevent OData injection.
- Constructor injection: accept `httpx.Client` and `msal.TokenCache` so tests can substitute fakes.
- Preserve Defender API field names in query models when the endpoint intentionally mirrors upstream filters, for example `healthStatus`.
- File-export endpoints should reuse `ViaFiles`; do not reimplement async download, decompression, or NDJSON parsing inside endpoint modules.
- Use a module-level logger when needed: `log = logging.getLogger(__name__)`.
- If schema or generated model surfaces need regeneration, prefer `just schema-build`, `just schema-build-dry`, `just schema-refresh`, or `just schema-refresh-dry` over manual bulk edits.
- Keep `__init__.py` exports minimal and maintain `__all__`.
