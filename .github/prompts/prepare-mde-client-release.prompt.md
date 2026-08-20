---
name: "Prepare MDE Client Release"
description: "Prepare an mde-client version update after Defender schema or endpoint compatibility changes. Use when bumping the package version, changelog, release documentation, and validation gates."
argument-hint: "Target version (optional) and release rationale, e.g. 0.3.0 - Defender schema compatibility update"
agent: "plan"
---

# Prepare MDE Client Release

Prepare an `mde-client` release candidate from the current branch and worktree.

Read [repository guidance](../../AGENTS.md), the [package release checklist](../../src/mde-client/README.md), the [package metadata](../../src/mde-client/pyproject.toml), the [package changelog](../../src/mde-client/CHANGELOG.md), and applicable files in [workspace instructions](../instructions/).

1. Inspect the current worktree and the candidate diff against `main`. Preserve unrelated or pre-existing worktree changes. Identify user-visible schema, endpoint, model/export, dependency, and documentation changes.
2. Determine the release version. If the prompt arguments provide a version, verify that it is appropriate. If no version is provided, summarize the API impact and ask the user to select a patch, minor, or major release before editing. Treat removed or renamed public imports, return types, and behavior as breaking unless a compatibility layer preserves them.
3. Before the first edit, state one falsifiable local hypothesis that identifies the package version source, changelog/release-note source, affected public documentation, and the cheapest relevant validation command.
4. Update the package-local `src/mde-client/pyproject.toml` version. Do not change the root workspace version for package tagging. Synchronize `uv.lock` only through repository tooling when it reflects the editable package version.
5. Add a matching dated release section to `src/mde-client/CHANGELOG.md`, moving release items out of `Unreleased` and preserving the existing Keep a Changelog structure. Clearly call out breaking changes and the required migration action.
6. Update only public documentation that no longer matches the implementation. Do not manually edit generated contracts, schemas, or models; when regeneration is required, use `just contracts-generate` or `just schema-refresh`.
7. Validate incrementally: run the narrowest relevant test or docs command immediately after each substantive edit. For generated-contract changes, run `just contracts-check`, `just contracts-doctor`, and `just quality-contracts`; run focused `just test tests/mde_client/... --skip-integration`; run `just docs-validate` when docs change; then run `just quality`. Do not run `just quality-full` unless Azure-backed integration coverage is intended and credentials are available.
8. Finish by reporting the target version, edited files, user-visible and breaking changes, validation results, and any unrun checks with their reason. Explain that merging the changed package pyproject to `main` creates `mde-client-v<version>`, then triggers PyPI publishing, GitHub Release notes from the matching changelog section, and versioned docs deployment.
