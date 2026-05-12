# MDE Client Documentation

This documentation covers the `mde-client` package from four angles:

- Tutorials help a new user reach a first successful outcome.
- How-to guides solve common package tasks.
- Reference pages describe the package surface as it exists today.
- Explanation pages clarify the design choices behind the client.

`mde-client` is a Python client for Microsoft Defender for Endpoint built around a single `MDEClient`, endpoint properties such as `client.machines` and `client.alerts`, and lazy result wrappers that materialize only when you call a terminal method such as `to_dicts()` or `to_polars()`.

## Choose a starting point

- New to the package: [Get started](tutorials/get-started.md)
- Need to solve one task: [How-to guides](how-to/index.md)
- Need exact API details: [Reference](reference/index.md)
- Need to understand the design: [Explanation](explanation/index.md)

## Package overview

The current package surface is organized around these ideas:

- `MDEClient` manages authentication and the underlying HTTP session.
- Each endpoint family is exposed as a property on the client.
- Most endpoint methods return a lazy results wrapper instead of fetching immediately.
- The same result wrapper pattern is used across JSON-backed and export-backed endpoints.
- `httpx.Client` and `msal.TokenCache` can be injected for testing and customization.

## Documentation map

### Tutorials

- [Get started](tutorials/get-started.md): install the package, authenticate, and fetch your first machine records.

### How-to guides

- [How-to index](how-to/index.md)
- [Authenticate with client credentials](how-to/authenticate-with-client-credentials.md)
- [List and filter machines](how-to/list-and-filter-machines.md)
- [Get related data for one machine](how-to/get-machine-related-data.md)
- [Run an advanced hunting query](how-to/run-advanced-hunting.md)
- [Work with result formats](how-to/work-with-result-formats.md)
- [Use export-backed endpoints](how-to/use-export-backed-endpoints.md)
- [Inject a custom HTTP client or token cache](how-to/inject-http-client-and-token-cache.md)

### Reference

- [Reference index](reference/index.md)
- [MDEClient](reference/mde-client.md)
- [Authentication](reference/authentication.md)
- [Results wrappers](reference/results.md)
- [Query models](reference/queries.md)
- [ViaFiles](reference/via-files.md)
- [Endpoint reference](reference/endpoints/index.md)

### Explanation

- [Explanation index](explanation/index.md)
- [Lazy results and caching](explanation/lazy-results.md)
- [Why query models keep Defender field names](explanation/query-models.md)
- [How export-backed endpoints work](explanation/export-backed-endpoints.md)
- [Why the client supports dependency injection](explanation/dependency-injection.md)

## Scope of this docs set

This docs tree focuses on the `mde-client` package under `src/mde_client/`. It does not try to cover Azure portal setup step by step, and it does not replace the repository-level workflow notes in the root README.
