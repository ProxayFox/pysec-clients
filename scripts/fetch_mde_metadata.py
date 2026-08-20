"""Fetch the upstream MDE EDMX snapshot without performing code generation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from mde_client import MDEClient

DEFAULT_OUTPUT = Path("tools/mde-contract-gen/metadata/mde_metadata.xml")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    required = ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise OSError(f"Missing required environment variables: {', '.join(missing)}")

    with MDEClient(
        tenant_id=os.environ["AZURE_TENANT_ID"],
        client_id=os.environ["AZURE_CLIENT_ID"],
        client_secret=os.environ["AZURE_CLIENT_SECRET"],
    ) as client:
        response = client.misc._request("GET", "/api/$metadata")
        response.raise_for_status()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(response.content)
    print(f"Saved MDE metadata to {args.output}")


if __name__ == "__main__":
    main()
