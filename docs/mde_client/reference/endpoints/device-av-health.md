# `client.device_av_health`

Access device antivirus health reporting.

## Property

`client.device_av_health`

## Methods

- `get_all(query: DeviceAVHealthQuery | None = None) -> DeviceAVHealthResults`: fetch the JSON-backed AV health report.
- `get_all_files() -> DeviceAVHealthResults`: fetch the via-files AV health report.

## Notes

- The export-backed path normalizes nested blob records into the same schema used by the JSON response.
- `DeviceAVHealthQuery` keeps Defender field names such as `machineId`, `computerDnsName`, and `avSignatureVersion`.
