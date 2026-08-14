# Handle errors and retries

This page shows how to surface and recover from the failure modes you will encounter when using `mde-client` in production: authentication failures, HTTP errors from the Defender API (including rate limiting), and empty or failed export blobs.

## Failure modes at a glance

| Error                                        | Raised from                            | Typical cause                                          |
| -------------------------------------------- | -------------------------------------- | ------------------------------------------------------ |
| `mde_client.AuthenticationError`             | `MSALAuth.token`                       | Bad tenant/client/secret, missing app permissions      |
| `httpx.HTTPStatusError` (`429`)              | Endpoint `_request()` calls            | Defender API rate limiting                             |
| `httpx.HTTPStatusError` (`4xx` / `5xx`)      | Endpoint `_request()` calls            | Permission denied, not found, server-side failures     |
| `httpx.RequestError` (subclasses)            | The injected `httpx.Client`            | DNS, TLS, connection, or timeout failures              |
| `mde_client.EmptyExportBlobError`            | `ViaFiles` internals                   | Export URL returned `200 OK` with no records           |
| `RuntimeError` from `ViaFiles`               | After exhausted retries                | Hard download failure on at least one export blob      |

## Catch authentication failures separately

```python
from mde_client import MDEClient, AuthenticationError

try:
    with MDEClient(tenant_id, client_id, client_secret) as client:
        rows = client.machines.get_all().to_dicts()
except AuthenticationError as e:
    # Treat as configuration error: do not retry.
    log.error("MSAL token acquisition failed: %s", e)
    raise
```

`AuthenticationError` indicates a configuration problem (bad credentials, wrong tenant, missing app permissions). Retrying will not help.

## Catch HTTP errors from the Defender API

Endpoint methods raise from `httpx` directly. Inspect the response on the exception:

```python
import httpx
from mde_client import MDEClient

with MDEClient(...) as client:
    try:
        results = client.machines.get_all()
        rows = results.to_dicts()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        log.warning("Defender API returned %s: %s", status, exc.response.text[:500])
        raise
```

### Rate limiting (`429 Too Many Requests`)

Defender returns `429` when you exceed the API rate budget. Inspect the `Retry-After` header and back off:

```python
import time
import httpx


def call_with_retry(fn, *, attempts: int = 5):
    for attempt in range(attempts):
        try:
            return fn()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 429 or attempt == attempts - 1:
                raise
            wait = int(exc.response.headers.get("Retry-After", 2**attempt))
            time.sleep(wait)
    raise RuntimeError("unreachable")
```

For long-running batch workloads, prefer to wire retry policy into the injected `httpx.Client` via [`httpx-retries`](https://pypi.org/project/httpx-retries/) or a similar transport-level retry layer rather than wrapping every call site.

### Permanent client errors (`4xx`)

`401` / `403` indicate the app registration lacks the required permission or admin consent was not granted; do not retry. `404` usually means the resource ID does not exist; treat as an empty result if that is acceptable for your workflow.

## Handle failed exports

Export-backed endpoints use [`ViaFiles`](../reference/via-files.md) internally. Transient download failures are retried per `ViaFilesConfig`; permanent failures surface as `RuntimeError` after retries are exhausted. Truly empty blobs are recognised via `EmptyExportBlobError` and skipped — you do not need to catch that exception yourself unless you are calling `ViaFiles` directly.

```python
try:
    rows = client.browser_extension.get_all_files().to_arrow()
except RuntimeError as exc:
    # All retries exhausted on at least one blob.
    log.error("Export download failed: %s", exc)
    raise
```

## Logging and diagnostics

`mde-client` uses module-level loggers as `log = logging.getLogger(__name__)`. To see request- and retry-level detail, enable DEBUG on the package and its dependencies:

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("mde_client").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("msal").setLevel(logging.INFO)
```

## See also

- [Authenticate with client credentials](authenticate-with-client-credentials.md)
- [Tune performance](tune-performance.md)
- [ViaFiles reference](../reference/via-files.md)
