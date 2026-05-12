# `client.score`

Access exposure and configuration score data.

## Property

`client.score`

## Methods

- `get() -> ScoreResults`: fetch the organization exposure score.
- `byMachineGroups() -> ScoreResults`: fetch exposure score by machine group.
- `configurationScore() -> ScoreResults`: fetch Microsoft Secure Score for Devices.

## Notes

- All methods return the same `ScoreResults` wrapper even though they target different score paths.
