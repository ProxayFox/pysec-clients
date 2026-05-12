# `client.baseline_configurations`

Access security baseline assessments, profiles, and active configurations.

## Property

`client.baseline_configurations`

## Methods

- `get_all() -> AssetBaselineAssessmentResults`: fetch per-device baseline assessment rows.
- `get_all_files() -> AssetBaselineAssessmentResults`: fetch per-device baseline assessment rows through the export-backed path.
- `profiles() -> BaselineConfigurationResults`: list baseline profiles created by the organization.
- `active() -> BaselineConfigurationResults`: list configurations being assessed in active baseline profiles.

## Notes

- `get_all()` and `get_all_files()` return assessment rows, not the same wrapper used by `profiles()` and `active()`.
- Use `profiles()` and `active()` when you need baseline metadata rather than per-device assessment output.
