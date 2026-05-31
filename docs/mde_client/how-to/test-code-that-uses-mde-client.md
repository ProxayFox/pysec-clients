# Test code that uses `mde-client`

`mde-client` is designed for substitution at two seams: the `httpx.Client` it uses for transport, and the `msal.TokenCache` it uses for token caching. This page shows the patterns the package's own test suite uses; reuse them in your project's tests.

## The two injection seams

```python
from mde_client import MDEClient
import httpx, msal

client = MDEClient(
    tenant_id="...",
    client_id="...",
    client_secret="...",
    http_client=httpx.Client(...),       # substitute transport
    token_cache=msal.TokenCache(),       # substitute cache
)
```

For unit tests you almost never want to talk to Azure AD or Defender. Replace both seams with fakes.

## Stub HTTP with `httpx.MockTransport`

The cleanest unit-test pattern is a fake `httpx.Client` whose transport returns canned responses:

```python
import httpx
from mde_client import MDEClient


def _machines_response(request: httpx.Request) -> httpx.Response:
    assert request.url.path.startswith("/api/machines")
    return httpx.Response(
        200,
        json={"value": [{"id": "m-1", "computerDnsName": "host-1"}]},
    )


def test_get_all_machines(monkeypatch):
    # Skip the real MSAL flow.
    monkeypatch.setattr(
        "mde_client.auth.MSALAuth.token",
        property(lambda self: "fake-token"),
    )

    http = httpx.Client(
        base_url="https://api.securitycenter.microsoft.com",
        transport=httpx.MockTransport(_machines_response),
    )
    client = MDEClient(
        tenant_id="t", client_id="c", client_secret="s",
        http_client=http,
    )

    rows = client.machines.get_all().to_dicts()

    assert rows == [{"id": "m-1", "computerDnsName": "host-1"}]
    client.close()
```

Key points:

- Patch `MSALAuth.token` so the test never calls Azure AD.
- Use `httpx.MockTransport` to drive deterministic responses.
- The injected `httpx.Client` is yours; close it (or use a context manager) at the end of the test.

## Inject the real `httpx.Client` for integration tests

The package's own integration tests are gated by `pytest.mark.integration` and require real Defender credentials. Mirror that pattern in your project: gate any test that requires network access with an `@pytest.mark.integration` marker plus the `--skip-integration` flag exposed by the repository's root `conftest.py`.

## Fake the token cache

For tests that exercise multiple endpoint calls, a real `msal.TokenCache` is harmless, but you can also inject a `SerializableTokenCache` to inspect what would have been cached:

```python
import msal

cache = msal.SerializableTokenCache()
client = MDEClient(..., token_cache=cache)
# After the test, cache.serialize() exposes the cached state for assertions.
```

## Test against export-backed endpoints

For export-backed endpoints (browser extensions, AV health, etc.) the first request returns export URLs that `ViaFiles` then downloads. In unit tests, your `MockTransport` should return:

1. A first response containing the export-URL envelope expected by the endpoint.
2. Follow-up responses for the SAS URLs themselves, returning NDJSON (gzipped or plain) bodies that match the endpoint's schema.

Walk the package's `tests/mde_client/test_via_files.py` for the exact envelope shape; reuse the helpers there as fixtures.

## Tips

- Reset the wrapper's cache between assertions with `.refresh()` if you re-stub the transport mid-test.
- The endpoint module also has lazy attribute loading; importing `mde_client.endpoints.MachinesEndpoint` triggers a real import the first time. Tests that monkey-patch `mde_client.endpoints.machines.MachinesEndpoint._request` should do so after that first access.
- Prefer table-driven tests when stubbing OData filter strings — it is easy to break filter construction silently.

## See also

- [Inject a custom HTTP client or token cache](inject-http-client-and-token-cache.md)
- [Handle errors and retries](handle-errors-and-retries.md)
- [Why the client supports dependency injection](../explanation/dependency-injection.md)
