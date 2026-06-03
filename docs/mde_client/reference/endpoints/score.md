# `client.score`

Access exposure and configuration score data.

## Property

`client.score`

## Methods

- `get() -> ScoreResults`: fetch the organization exposure score.
- `byMachineGroups() -> ScoreResults`: fetch exposure score by machine group.
- `configurationScore() -> ScoreResults`: fetch Microsoft Secure Score for Devices.
- `configurationScoreById(id: str) -> ScoreResults`: fetch Microsoft Secure Score for Devices by ID.

## Notes

- All methods return the same `ScoreResults` wrapper even though they target different score paths.

## API

::: mde_client.endpoints.score
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
