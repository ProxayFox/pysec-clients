# Changelog

All notable changes to `mde-client` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-05-31

### Added

- Published documentation site at
  <https://proxayfox.github.io/pysec-clients/mde_client/>, built with MkDocs +
  Material and deployed via GitHub Actions.
- New how-to and explanation pages: error handling, performance tuning, and
  testing with `mde-client`.
- Expanded endpoint documentation, docstrings, and navigation across the
  reference section (now covering the full public surface).
- Auto-enablement and Node.js 24 opt-in in the docs deployment workflow.

### Changed

- `Documentation` project URL now points to the hosted docs site instead of the
  in-repo README, so PyPI links to the rendered docs on the next release.
- Refreshed `mkdocs.yml` with `site_url`, `edit_uri`, and improved navigation
  for better canonical links, sitemap, and per-page edit links.

## [0.1.1] - 2026-05-30

### Added

- Comprehensive test coverage for `mde-client` endpoints.
- Coverage configuration and `just test-cov` wiring in the workspace tooling.

### Changed

- Refactored endpoint imports and normalized user-related endpoint paths for
  consistency across the package.

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

[Unreleased]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.1.2...HEAD
[0.1.2]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.1.1...mde-client-v0.1.2
[0.1.1]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.1.0...mde-client-v0.1.1
[0.1.0]: https://github.com/ProxayFox/pysec-clients/releases/tag/mde-client-v0.1.0
