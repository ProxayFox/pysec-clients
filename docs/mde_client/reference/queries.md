# Query Models

Query models inherit from `BaseQuery`.

## Shared fields

Every query model can inherit these pagination controls:

- `page_size` mapped to `pageSize`
- `top` mapped to `$top`
- `skip` mapped to `$skip`

## Filter translation

Non-null model fields are converted into OData-style filters.

- strings become `field eq 'value'`
- datetimes become ISO-formatted equality filters
- lists of strings become `field in (...)`

Fields set to `None` are omitted.

## Naming convention

Defender-specific query models preserve upstream API field names instead of normalizing them to snake_case. For example:

- `healthStatus`
- `machineTags`
- `lastSeen`
- `creationDateTimeUtc`

This keeps query construction close to the upstream API surface and avoids a second naming layer in the package.

## Common endpoint query models

- `MachinesQuery`
- `AlertsQuery`
- `IndicatorsQuery`
- `InvestigationQuery`
- `MachineActionsQuery`
- `RecommendationQuery`
- `RemediationQuery`
- `SoftwareQuery`
- `VulnerabilitiesQuery`
- `VulnerabilitiesByMachineAndSoftwareQuery`

## See also

- [List and filter machines](../how-to/list-and-filter-machines.md)
- [Why query models keep Defender field names](../explanation/query-models.md)
