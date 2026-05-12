# Get Related Data for One Machine

Use this guide when you already have a Defender machine ID and need related datasets from the machine surface.

## Fetch the machine itself

```python
machine = client.machines.get("machine-guid").to_dicts()[0]
```

## Fetch related records

The machine endpoint groups several machine-scoped lookups under the same property:

```python
machine_id = "machine-guid"

alerts = client.machines.alerts(machine_id).to_dicts()
logon_users = client.machines.logonusers(machine_id).to_dicts()
software = client.machines.software(machine_id).to_dicts()
vulnerabilities = client.machines.vulnerabilities(machine_id).to_dicts()
recommendations = client.machines.recommendations(machine_id).to_dicts()
```

Each call returns a lazy results wrapper. The materialization method is what performs the request.

## Handle empty related collections safely

Machine-related subresources are not guaranteed to contain rows for every machine. A practical pattern is to materialize the collection and branch on emptiness:

```python
machine_id = "machine-guid"

software_rows = client.machines.software(machine_id).to_dicts()
if software_rows:
    print(software_rows[0]["name"])

vulnerability_rows = client.machines.vulnerabilities(machine_id).to_dicts()
if vulnerability_rows:
    print(vulnerability_rows[0]["name"])
```

The same approach works for alerts, recommendations, missing KBs, and logon users.

## Get missing KBs

If you need missing KB data for a machine:

```python
missing_kbs = client.machines.getmissingkbs("machine-guid").to_dicts()
```

If you are building an inspection workflow, it is reasonable to fetch the machine once and then branch into only the related collections you need:

```python
machine_id = "machine-guid"

machine = client.machines.get(machine_id).to_dicts()[0]
logon_users = client.machines.logonusers(machine_id).to_dicts()
missing_kbs = client.machines.getmissingkbs(machine_id).to_dicts()
```

This keeps the flow explicit and avoids assuming that every related collection will have data.

## Choose the simplest format first

Start with `to_dicts()` unless you already know you need Arrow or Polars. It keeps the integration simple and makes debugging easier.

If you later need tabular processing, you can always re-materialize the same wrapper into Arrow or Polars without building a different request object.

## Next references

- [machines endpoint reference](../reference/endpoints/machines.md)
- [Work with result formats](work-with-result-formats.md)
