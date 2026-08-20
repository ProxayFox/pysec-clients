"""Command-line interface for canonical MDE contract generation."""

from __future__ import annotations

import argparse
import ast
import filecmp
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from .builder import build_contract, camel_to_snake, select_roots
from .canonical import add_hashes, prior_generated_at, verify_hashes, write_contract
from .edmx import parse_metadata
from .emitters.arrow import emit_arrow
from .emitters.json_schema import emit_json_schema
from .emitters.package import emit_package_files
from .emitters.support_models import emit_support_models
from .models import SourceContract
from .overrides import load_overrides
from .versions import load_registry, recommend_bump, write_registry

REPO_ROOT = Path(__file__).resolve().parents[4]
TOOL_ROOT = REPO_ROOT / "tools/mde-contract-gen"
DEFAULT_METADATA = TOOL_ROOT / "metadata/mde_metadata.xml"
DEFAULT_OVERRIDES = TOOL_ROOT / "overrides"
DEFAULT_VERSIONS = TOOL_ROOT / "versions.json"
DEFAULT_CONTRACTS = REPO_ROOT / "src/mde-client/src/mde_client/contracts"
DEFAULT_SCHEMAS = REPO_ROOT / "src/mde-client/src/mde_client/schemas"
DEFAULT_MODELS = REPO_ROOT / "src/mde-client/src/mde_client/models"
SOURCE_MODELS = TOOL_ROOT / "src/mde_contract_gen/models.py"
GENERATED_ENDPOINT_FILES = {"contract.json", "schema.py", "schema.schema.json"}


@dataclass(frozen=True)
class GenerationPaths:
    contracts: Path
    schemas: Path
    models: Path
    baseline_contracts: Path


def main(argv: list[str] | None = None) -> None:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            _command_generate(args)
        elif args.command == "check-drift":
            _command_check_drift(args)
        elif args.command == "doctor":
            _command_doctor(args)
        else:  # pragma: no cover - argparse prevents this
            parser.error(f"Unknown command {args.command!r}")
    except (OSError, TypeError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mde-contract-gen",
        description="Generate canonical MDE contracts from OData EDMX.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate")
    _common_arguments(generate)
    generate.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CONTRACTS,
        help="Vendored contracts output directory.",
    )
    generate.add_argument(
        "--endpoint",
        action="append",
        default=[],
        help="Generate only the named root type or snake-case slug.",
    )
    generate.add_argument(
        "--no-compat",
        action="store_true",
        help="Do not regenerate package aggregation and schema wrappers.",
    )

    drift = subparsers.add_parser("check-drift")
    _common_arguments(drift)

    doctor = subparsers.add_parser("doctor")
    _common_arguments(doctor)
    return parser


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--versions", type=Path, default=DEFAULT_VERSIONS)


def _command_generate(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    is_default_output = output == DEFAULT_CONTRACTS.resolve()
    schemas = DEFAULT_SCHEMAS if is_default_output else output.parent / "schemas"
    models = DEFAULT_MODELS if is_default_output else output.parent / "models"
    contracts = _generate(
        metadata_path=args.metadata,
        overrides_path=args.overrides,
        versions_path=args.versions,
        paths=GenerationPaths(
            contracts=output,
            schemas=schemas,
            models=models,
            baseline_contracts=DEFAULT_CONTRACTS,
        ),
        endpoint_filters=set(args.endpoint),
        emit_compat=not args.no_compat,
        write_versions=is_default_output,
    )
    print(f"Generated {len(contracts)} canonical MDE contracts in {output}")


def _command_check_drift(args: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory(prefix="mde-contract-drift-") as temp:
        root = Path(temp)
        expected_contracts = root / "contracts"
        expected_schemas = root / "schemas"
        expected_models = root / "models"
        _generate(
            metadata_path=args.metadata,
            overrides_path=args.overrides,
            versions_path=args.versions,
            paths=GenerationPaths(
                contracts=expected_contracts,
                schemas=expected_schemas,
                models=expected_models,
                baseline_contracts=DEFAULT_CONTRACTS,
            ),
            endpoint_filters=set(),
            emit_compat=True,
            write_versions=False,
        )
        differences = [
            *_tree_differences(
                expected_contracts,
                DEFAULT_CONTRACTS,
                ignored={"registry.py", "__pycache__"},
            ),
            *_tree_differences(
                expected_schemas,
                DEFAULT_SCHEMAS,
                ignored={"__pycache__"},
            ),
            *_tree_differences(
                expected_models,
                DEFAULT_MODELS,
                ignored={"__pycache__"},
            ),
        ]
    if differences:
        joined = "\n  ".join(differences)
        raise ValueError(
            "Generated contract artifacts have drifted:\n  "
            f"{joined}\nRun `just contracts-generate`."
        )
    print("Contract artifacts are deterministic and up to date.")


def _command_doctor(args: argparse.Namespace) -> None:
    metadata = parse_metadata(args.metadata)
    overrides = load_overrides(args.overrides)
    roots = select_roots(metadata, overrides)
    registry = load_registry(args.versions)
    errors: list[str] = []
    expected_slugs = {camel_to_snake(root) for root in roots}
    expected_source_hash = (
        f"sha256:{hashlib.sha256(args.metadata.read_bytes()).hexdigest()}"
    )

    for root in roots:
        slug = camel_to_snake(root)
        directory = DEFAULT_CONTRACTS / slug
        actual_files = (
            {path.name for path in directory.iterdir() if path.is_file()}
            if directory.exists()
            else set()
        )
        if actual_files != GENERATED_ENDPOINT_FILES:
            errors.append(
                f"{slug}: expected exactly {sorted(GENERATED_ENDPOINT_FILES)}, "
                f"found {sorted(actual_files)}"
            )
            continue
        try:
            contract = SourceContract.model_validate_json(
                (directory / "contract.json").read_text(encoding="utf-8")
            )
            verify_hashes(contract)
            registry.guard_released(slug, contract)
            entry = registry.contracts.get(slug)
            if entry and entry.version != contract.version:
                errors.append(
                    f"{slug}: version registry has {entry.version}, "
                    f"contract has {contract.version}"
                )
            if contract.generation.source_metadata_hash != expected_source_hash:
                errors.append(
                    f"{slug}: source metadata hash does not match {args.metadata}"
                )
            schema = json.loads(
                (directory / "schema.schema.json").read_text(encoding="utf-8")
            )
            Draft202012Validator.check_schema(schema)
            ast.parse(
                (directory / "schema.py").read_text(encoding="utf-8"),
                filename=str(directory / "schema.py"),
            )
        except (OSError, TypeError, ValueError, SyntaxError) as exc:
            errors.append(f"{slug}: {exc}")

    actual_slugs = {
        path.name
        for path in DEFAULT_CONTRACTS.iterdir()
        if path.is_dir() and not path.name.startswith("_")
    }
    stale = actual_slugs - expected_slugs
    if stale:
        errors.append(f"stale contract directories: {sorted(stale)}")
    missing_versions = expected_slugs - set(registry.contracts)
    if missing_versions:
        errors.append(f"version registry missing: {sorted(missing_versions)}")
    stale_versions = set(registry.contracts) - expected_slugs
    if stale_versions:
        errors.append(f"version registry has stale entries: {sorted(stale_versions)}")

    expected_models = _expected_runtime_models()
    runtime_models = DEFAULT_CONTRACTS / "_models.py"
    if not runtime_models.exists() or ast.dump(
        ast.parse(runtime_models.read_text(encoding="utf-8"))
    ) != ast.dump(ast.parse(expected_models)):
        errors.append("vendored contracts/_models.py has drifted")

    if errors:
        raise ValueError("Contract doctor failed:\n  " + "\n  ".join(errors))
    print(
        f"Contract doctor passed for {len(roots)} roots, "
        f"{len(metadata.enum_types)} enums, and "
        f"{len(metadata.complex_types)} complex types."
    )


def _generate(
    *,
    metadata_path: Path,
    overrides_path: Path,
    versions_path: Path,
    paths: GenerationPaths,
    endpoint_filters: set[str],
    emit_compat: bool,
    write_versions: bool,
) -> dict[str, SourceContract]:
    metadata = parse_metadata(metadata_path)
    overrides = load_overrides(overrides_path)
    registry = load_registry(versions_path)
    roots = select_roots(metadata, overrides)
    selected = {
        root
        for root in roots
        if not endpoint_filters
        or root in endpoint_filters
        or camel_to_snake(root) in endpoint_filters
    }
    if endpoint_filters and len(selected) != len(endpoint_filters):
        matched = selected | {camel_to_snake(root) for root in selected}
        unknown = endpoint_filters - matched
        raise ValueError(f"Unknown endpoint filters: {sorted(unknown)}")

    contracts: dict[str, SourceContract] = {}
    recommendations: list[str] = []
    for root in roots:
        slug = camel_to_snake(root)
        baseline_path = paths.baseline_contracts / slug / "contract.json"
        previous = _load_contract(baseline_path)
        contract = build_contract(
            metadata,
            root,
            version=registry.version_for(slug),
            overrides=overrides,
            generated_at=prior_generated_at(baseline_path),
        )
        contract = add_hashes(contract)
        registry.guard_released(slug, contract)
        if previous and previous.version == contract.version:
            recommendation = recommend_bump(previous, contract)
            if recommendation:
                recommendations.append(
                    f"{slug}: recommended {recommendation} version bump"
                )
        contracts[slug] = contract

    paths.contracts.mkdir(parents=True, exist_ok=True)
    for slug, contract in contracts.items():
        if slug not in {camel_to_snake(root) for root in selected}:
            continue
        directory = paths.contracts / slug
        directory.mkdir(parents=True, exist_ok=True)
        _remove_unexpected_endpoint_files(directory)
        contract_path = directory / "contract.json"
        write_contract(contract_path, contract)
        emit_arrow(contract_path, directory / "schema.py")
        emit_json_schema(contract_path, directory / "schema.schema.json")

    if not endpoint_filters:
        _remove_stale_contract_directories(paths.contracts, set(contracts))
    if emit_compat:
        emit_package_files(
            contracts,
            contracts_dir=paths.contracts,
            schemas_dir=paths.schemas,
            source_models_path=SOURCE_MODELS,
        )
        emit_support_models(metadata, paths.models)
    _format_generated_python(paths, set(contracts), emit_compat=emit_compat)
    if write_versions:
        registry.synchronize(contracts)
        write_registry(versions_path, registry)
        for recommendation in recommendations:
            print(f"version: {recommendation}")
    return contracts


def _load_contract(path: Path) -> SourceContract | None:
    if not path.exists():
        return None
    try:
        return SourceContract.model_validate_json(path.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return None


def _format_generated_python(
    paths: GenerationPaths,
    slugs: set[str],
    *,
    emit_compat: bool,
) -> None:
    targets = [
        paths.contracts / slug / "schema.py"
        for slug in sorted(slugs)
        if (paths.contracts / slug / "schema.py").exists()
    ]
    if emit_compat:
        targets.extend(
            [
                paths.contracts / "__init__.py",
                paths.contracts / "_models.py",
                *sorted(paths.schemas.glob("*.py")),
                *sorted(paths.models.glob("*.py")),
            ]
        )
    imports = subprocess.run(
        ["ruff", "check", "--fix", "--select", "I", *map(str, targets)],
        check=False,
        capture_output=True,
        text=True,
    )
    if imports.returncode:
        raise OSError(imports.stderr or imports.stdout or "ruff import sorting failed")
    result = subprocess.run(
        ["ruff", "format", *map(str, targets)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise OSError(result.stderr or result.stdout or "ruff format failed")


def _remove_unexpected_endpoint_files(directory: Path) -> None:
    for path in directory.iterdir():
        if path.is_file() and path.name not in GENERATED_ENDPOINT_FILES:
            path.unlink()
        elif path.is_dir() and path.name == "__pycache__":
            shutil.rmtree(path)


def _remove_stale_contract_directories(contracts_dir: Path, expected: set[str]) -> None:
    for path in contracts_dir.iterdir():
        if not path.is_dir() or path.name.startswith("_") or path.name in expected:
            continue
        contract_file = path / "contract.json"
        if not contract_file.exists():
            continue
        try:
            contract = json.loads(contract_file.read_text(encoding="utf-8"))
        except OSError, json.JSONDecodeError:
            continue
        if contract.get("generation", {}).get("generated") is True:
            shutil.rmtree(path)


def _tree_differences(expected: Path, actual: Path, *, ignored: set[str]) -> list[str]:
    differences: list[str] = []
    expected_files = {
        path.relative_to(expected)
        for path in expected.rglob("*")
        if path.is_file() and not any(part in ignored for part in path.parts)
    }
    actual_files = {
        path.relative_to(actual)
        for path in actual.rglob("*")
        if path.is_file() and not any(part in ignored for part in path.parts)
    }
    for relative in sorted(expected_files - actual_files):
        differences.append(f"missing {actual / relative}")
    for relative in sorted(actual_files - expected_files):
        differences.append(f"stale {actual / relative}")
    for relative in sorted(expected_files & actual_files):
        if not filecmp.cmp(expected / relative, actual / relative, shallow=False):
            differences.append(f"changed {actual / relative}")
    return differences


def _expected_runtime_models() -> str:
    source = SOURCE_MODELS.read_text(encoding="utf-8")
    source = source.replace(
        "from __future__ import annotations\n",
        "from __future__ import annotations\n\n__generated__ = True\n",
        1,
    )
    return (
        "# AUTO-GENERATED by mde-contract-gen — do not edit manually.\n"
        "# Run `just contracts-generate` to regenerate.\n" + source
    )


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
