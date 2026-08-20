"""Deprecated compatibility entry point for MDE contract generation.

Generation moved to the standalone ``mde-contract-gen`` workspace package.
Use ``just contracts-generate`` or ``mde-contract-gen`` directly.
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

from mde_contract_gen.cli import main as generator_main


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh-metadata", action="store_true")
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--schemas-dir", type=Path)
    parser.add_argument("--models-dir", type=Path)
    parser.add_argument("--no-quality", action="store_true")
    args = parser.parse_args()

    warnings.warn(
        "scripts/mde_contract.py is deprecated; use mde-contract-gen",
        DeprecationWarning,
        stacklevel=2,
    )
    if args.refresh_metadata:
        parser.error(
            "metadata acquisition is now separate; run "
            "`uv run scripts/fetch_mde_metadata.py` first"
        )
    if args.schemas_dir or args.models_dir:
        parser.error(
            "custom legacy schema/model outputs are unsupported; use "
            "`mde-contract-gen generate --output PATH`"
        )

    command = "check-drift" if args.dry_run else "generate"
    forwarded = [command]
    if args.metadata:
        forwarded.extend(["--metadata", str(args.metadata)])
    generator_main(forwarded)


if __name__ == "__main__":
    main()
