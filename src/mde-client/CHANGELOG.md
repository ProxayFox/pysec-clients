# Changelog

All notable changes to `mde-client` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-20

### Added

- Initial public release on PyPI.
- `MDEClient` with context-manager lifecycle and lazy endpoint properties.
- MSAL-backed client-credentials authentication via `MSALAuth`, with constructor
  injection for `msal.TokenCache` and `httpx.Client`.
- Endpoint coverage across machine inventory, alerts, investigations,
  authenticated scans, advanced hunting, assessments, remediation, machine
  actions, browser extensions, certificate inventory, device AV health,
  device groups, domain, library, and related Defender resources.
- Lazy result wrappers with `to_dicts()`, `to_json()`, `to_arrow()`,
  `to_polars()`, and `refresh()` terminal methods.
- `ViaFiles` and `ViaFilesConfig` for async download, decompression, NDJSON
  parsing, and batching of Defender file-export endpoints.
- Optional extras: `mde-client[arrow]` and `mde-client[arrow,polars]`.
- Arrow schemas and request models generated from the Defender `$metadata`
  contract.
- `py.typed` PEP 561 marker — type information is shipped with the package.

[Unreleased]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.1.0...HEAD
[0.1.0]: https://github.com/ProxayFox/pysec-clients/releases/tag/mde-client-v0.1.0
