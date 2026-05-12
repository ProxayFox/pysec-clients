# Why the Client Supports Dependency Injection

`MDEClient` accepts both an `httpx.Client` and an `msal.TokenCache` because transport and authentication state are common sources of operational variation.

## HTTP client injection

Allowing a caller to pass an `httpx.Client` makes it possible to:

- use a mock transport in tests
- set custom timeouts
- configure proxies or custom networking behavior
- share a client configuration that already exists in the host application

## Token cache injection

Allowing a caller to pass an MSAL token cache makes it possible to:

- persist tokens between runs
- reuse an application-specific cache strategy
- avoid coupling package behavior to one fixed cache implementation

## Why this is a good fit for this package

The package is a client library, not an application. It should make the common path easy while still leaving room for callers with stronger requirements around tests, networking, or auth persistence.

That is why the constructor owns sensible defaults but still exposes both seams.
