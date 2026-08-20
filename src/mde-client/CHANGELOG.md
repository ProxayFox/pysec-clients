# Changelog

All notable changes to `mde-client` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Vendored canonical MDE source contracts with PyArrow and Draft 2020-12 JSON
  Schema projections, deterministic hashes, and a runtime contract registry.
- Added a standalone workspace generator with checked-in metadata overrides,
  semantic-version governance, drift checks, and Arrow parity gates.

### Changed

- Existing `mde_client.schemas` imports now delegate to canonical contract
  projections while preserving the same schema and struct objects.

## [0.3.1] - 2026-08-14

### Fixed

- `client.machines.findbyip(...)` now converts ISO 8601 timestamps with an
  explicit UTC offset to UTC `Z` format before calling the Defender API.

## [0.3.0] - 2026-08-13

### Added

- Generated Arrow schemas now expose Defender's `tags` and `softwareTags`
  fields for supported software and product payloads.
- `client.recommendations.software(...)` now materializes recommendation
  software payloads through `PublicProductDTOResults`.

### Changed

- **Breaking:** Renamed the generated public enum export
  `PUBLIC_VULNERABILITY_EXCEPTION_STATUS_DTO` to
  `PUBLIC_VULNERABILITY_EXCEPTION_STATUS`. Update imports from both
  `mde_client.models.enums` and `mde_client.models`.

## [0.2.4] - 2026-07-17

### Fixed

- `client.software.inventoryByMachine(...)` now forwards the optional `since`
  filter to the underlying machine assessment request, matching the machine
  inventory surface and restoring datetime-based filtering from the software
  client surface.

## [0.2.3] - 2026-07-01

### Changed

- Raised the minimum `aiohttp` and `polars` dependency versions in package
  metadata to match the validated workspace set used by the client and tests.

### Fixed

- Generated vulnerability export schemas now keep `cvssScore` nullable for the
  `AssetVulnerability` and `DeltaAssetVulnerability` payloads, matching runtime
  Defender responses so streamed Arrow IPC results can be written to strict
  sinks such as Parquet without schema violations.

## [0.2.2] - 2026-06-15

### Changed

- `findbyip(...)` now accepts `datetime` or ISO 8601 string timestamps and
  normalizes values to UTC `Z` format before calling the Defender API.
- `inventoryNoProductCodeByMachineFiles()` no longer exposes unused
  `page_size` or `since` arguments for the export-backed request path.

### Fixed

- Export-backed result fetching now waits briefly after retrieving export file
  URLs so Microsoft Defender for Endpoint has time to populate blobs before
  downloads begin, reducing transient 404s and unnecessary retries.

## [0.2.1] - 2026-06-09

### Added

- `just docs-versions-preview`: a local workflow for deploying a throwaway
  `dev` docs version and previewing the multi-version docs site with `mike`.

### Changed

- The package `Documentation` URL now points at the docs site root so stable
  releases follow the `latest` versioned docs alias.
- Clarified local multi-version docs preview and deployment commands in the
  workspace `justfile`.
- Bumped package and workspace lock metadata to `0.2.1`.

## [0.2.0] - 2026-06-09

### Added

- `BaseResults.to_ipc_stream(...)`: an async terminal that streams results as
  Arrow IPC stream byte chunks via `http-to-arrow`'s `ArrowIPCStream`, keeping
  peak memory close to a single record batch. Designed for memory-limited
  runtimes such as a 2 GiB Azure Function exporting millions of rows. Unlike the
  cached terminals (`to_dicts`, `to_json`, `to_arrow`, `to_polars`) it never
  materializes the full result set and is not cached. Supports collection
  pagination, concurrent `$top`/`$skip` pagination, single-object and
  manual-pagination responses, and export-backed (`files=True`) endpoints.
- `ViaFiles.stream_export_files(...)`: streams parsed export-file records into
  any async sink (for example an `ArrowIPCStream`) instead of accumulating an
  `ArrowRecordContainer`.
- Versioned documentation site built with `mike`, plus a new how-to,
  "Stream Results as Arrow IPC", covering the streaming terminals end to end.

### Changed

- Requires `http-to-arrow>=0.2.1` for Arrow IPC streaming support.

### Fixed

- `AdvancedHuntingQueriesResults` materialization called `to_polars` and
  `to_arrow` as properties instead of methods, breaking `to_dicts()`,
  `to_json()`, `to_arrow()`, and `to_polars()`; the conversions are now invoked
  correctly.
- Hardened response handling in `BaseEndpoint` with stricter type checks to
  avoid errors on unexpected payload shapes.
- Reworked concurrent processing in `ViaFiles` to improve error propagation and
  prevent deadlocks during export-file downloads.

## [0.1.4] - 2026-06-03

### Added

- Single-record fetch methods across endpoints, covering authenticated scan
  definitions, baseline configurations, indicators, investigations, machine
  actions, machines, score, software, and vulnerabilities.
- `machineReferences(...)` returning `MachineReferencesResults` on the
  recommendations, software, and vulnerabilities endpoints, plus
  `softwareVulnerabilitiesByMachine(...)` and
  `softwareVulnerabilityChangesByMachine(...)` on the vulnerabilities endpoint.
- Concurrent `$skip` pagination in `BaseResults`/`BaseEndpoint` with rate
  limiting, plus tests for pagination behavior and error handling.

### Changed

- Refactored the machines and vulnerabilities endpoints to improve parameter
  handling and use the correct result classes; `since` now defaults to the last
  24 hours when omitted.
- `page_size` can no longer be combined with `top` or `skip`; `BaseQuery`
  validates the combination and raises accordingly.
- Raised minimum versions for `aiohttp`, `msal`, `orjson`, and `requests`, and
  pinned the `arrow`/`polars` optional extras.
- Opted GitHub Actions workflows into Node.js 24 ahead of the Node.js 20 runner
  deprecation.

## [0.1.3] - 2026-06-02

### Fixed

- Declared the missing runtime dependencies `httpx` and `pydantic` in the
  package metadata so installs pull everything the client needs at import time.

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

[Unreleased]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.3.1...HEAD
[0.3.1]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.3.0...mde-client-v0.3.1
[0.2.4]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.2.3...mde-client-v0.2.4
[0.2.3]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.2.2...mde-client-v0.2.3
[0.2.2]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.2.1...mde-client-v0.2.2
[0.2.1]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.2.0...mde-client-v0.2.1
[0.2.0]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.1.4...mde-client-v0.2.0
[0.1.4]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.1.3...mde-client-v0.1.4
[0.1.3]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.1.2...mde-client-v0.1.3
[0.1.2]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.1.1...mde-client-v0.1.2
[0.1.1]: https://github.com/ProxayFox/pysec-clients/compare/mde-client-v0.1.0...mde-client-v0.1.1
[0.1.0]: https://github.com/ProxayFox/pysec-clients/releases/tag/mde-client-v0.1.0
