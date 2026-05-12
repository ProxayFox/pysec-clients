# Get Started

This tutorial helps you complete one successful workflow with `mde-client`: authenticate to Microsoft Defender for Endpoint, fetch a filtered machines result, and inspect the returned records.

By the end, you will have a working `MDEClient` in your own code and a list of machine dictionaries you can build on.

## Before you begin

You need:

- Python 3.14 or newer
- an Azure AD app registration that can use the client-credentials flow
- a tenant ID, client ID, and client secret
- Defender application permissions granted to that app registration

## Install the package

Install from a project that uses `uv`:

```bash
uv add mde-client
```

If you are working inside this repository instead of consuming the published package, use the workspace bootstrap flow:

```bash
uv sync --all-packages --all-groups
```

## Create a client

Create a new file and start with a minimal client setup:

```python
from mde_client import AuthenticationError, MDEClient
from mde_client.endpoints.machines import MachinesQuery

try:
    with MDEClient(
        tenant_id="YOUR_TENANT_ID",
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
    ) as client:
        query = MachinesQuery(healthStatus="Active", page_size=100)
        results = client.machines.get_all(query)
except AuthenticationError as exc:
    raise SystemExit(f"Authentication failed: {exc}")
```

At this point no API request has been made yet. `results` is a lazy wrapper.

## Materialize the results

Trigger the request by calling a terminal method:

```python
from mde_client import AuthenticationError, MDEClient
from mde_client.endpoints.machines import MachinesQuery

try:
    with MDEClient(
        tenant_id="YOUR_TENANT_ID",
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
    ) as client:
        query = MachinesQuery(healthStatus="Active", page_size=100)
        machines = client.machines.get_all(query).to_dicts()

        print(f"Fetched {len(machines)} machines")
        if machines:
            print(machines[0]["computerDnsName"])
except AuthenticationError as exc:
    raise SystemExit(f"Authentication failed: {exc}")
```

`to_dicts()` returns a Python `list[dict]`, which is the simplest representation for a first integration.

## Read one machine by ID

Once you have a machine ID, fetch a single machine record:

```python
machine = client.machines.get("machine-guid").to_dicts()[0]
print(machine["computerDnsName"])
```

Single-item lookups still use the same results-wrapper pattern.

## What to expect

When the tutorial succeeds:

- authentication completes without raising `AuthenticationError`
- `client.machines.get_all(...)` returns one or more records, or an empty list if the filter matches nothing
- `to_dicts()` gives you ordinary Python dictionaries ready for downstream processing

## Next steps

- Learn common workflows in [How-to guides](../how-to/index.md)
- Look up the full client surface in [MDEClient reference](../reference/mde-client.md)
- Understand lazy execution in [Lazy results and caching](../explanation/lazy-results.md)
