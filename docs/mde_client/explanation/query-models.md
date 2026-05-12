# Why Query Models Keep Defender Field Names

The query models intentionally preserve upstream Defender field names such as `healthStatus` and `creationDateTimeUtc`.

## Why not normalize everything to snake_case

Normalizing the query surface would create a second vocabulary on top of the upstream API. That tends to make documentation, debugging, and cross-checking harder.

When a user reads the Defender API docs or inspects a payload, the field names in `mde-client` line up with what they already see.

## What this buys the user

- fewer translation mistakes when building filters
- easier comparison with raw Defender payloads
- less hidden behavior in the query serialization layer

## Tradeoff

The package accepts that some query models look less Pythonic than a fully normalized surface. The goal is operational clarity rather than stylistic purity.
