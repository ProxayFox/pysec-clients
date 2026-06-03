# `client.baseline_configurations`

Access security baseline assessments, profiles, and active configurations.

## Property

`client.baseline_configurations`

## Methods

- `get_all() -> AssetBaselineAssessmentResults`: fetch per-device baseline assessment rows.
- `get_all_files() -> AssetBaselineAssessmentResults`: fetch per-device baseline assessment rows through the export-backed path.
- `profiles() -> BaselineConfigurationResults`: list baseline profiles created by the organization.
- `profilesById(id: str) -> BaselineConfigurationResults`: fetch one baseline profile by ID.
- `active() -> BaselineConfigurationResults`: list configurations being assessed in active baseline profiles.
- `activeById(id: str) -> BaselineConfigurationResults`: fetch one active baseline configuration by ID.
- `exceptions() -> BaselineConfigurationResults`: list security baseline assessment exceptions.
- `exceptionsById(id: str) -> BaselineConfigurationResults`: fetch one security baseline assessment exception by ID.
- `assessmentByMachine() -> AssetConfigurationResults`: fetch secure configuration assessment rows by machine.
- `assessmentByMachineFiles() -> AssetConfigurationResults`: fetch secure configuration assessment rows via export files.

## Notes

- `get_all()` and `get_all_files()` return assessment rows, not the same wrapper used by `profiles()` and `active()`.
- Use `profiles()` and `active()` when you need baseline metadata rather than per-device assessment output.
- `exceptions()` and `exceptionsById()` target undocumented baseline exception paths.

## API

::: mde_client.endpoints.securityBaseline
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
