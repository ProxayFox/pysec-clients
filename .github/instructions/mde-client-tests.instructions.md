---
applyTo: "tests/mde_client/**/*.py"
---

# MDE Client Tests

Reference examples:

- [test_machines_endpoint.py](../../tests/mde_client/test_machines_endpoint.py) — request construction and return-type tests.
- [test_machine_results.py](../../tests/mde_client/test_machine_results.py) — lazy fetch, pagination, and cache behavior.
- [test_via_files.py](../../tests/mde_client/test_via_files.py) — async export download isolation.
- [test_machines_integration.py](../../tests/mde_client/test_machines_integration.py) — Azure-backed integration gating.

- Prefer focused `just test tests/mde_client/...` runs while iterating.
- Request-construction tests should use `MagicMock(spec=httpx.Client)` plus fake auth and assert `_path`, `_params`, `_method`, or `_request_kwargs` without making real HTTP calls.
- Lazy materialization tests should subclass the endpoint or results wrapper and override `_arequest()` or `_ensure_fetched()` to return canned `httpx.Response` objects.
- For file-export behavior, isolate parsing and streaming with fake response objects and in-memory queues; do not hit Azure Blob storage or the live API in unit tests.
- Integration tests must be marked `pytest.mark.integration` and skipped at module scope when required Azure environment variables are absent.
- When asserting request payloads, match the endpoint's serialization behavior exactly, including `model_dump(exclude_none=True)` when the production method uses it.
