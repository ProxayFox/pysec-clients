import argparse
import ast
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path("/workspaces/pysec-clients")
XML_PATH = ROOT / "build" / "mde_metadata.xml"
ENDPOINTS_DIR = ROOT / "src" / "mde_client" / "endpoints"
TODO_IGNORE_PATH = ROOT / "scripts" / "mde_todo_ignore.yaml"
NS = {"edm": "http://docs.oasis-open.org/odata/ns/edm"}
API_PREFIX = "microsoft.windowsDefenderATP.api."
TODAY = "2026-05-13"


def strip_prefix(value: str) -> str:
    return value[len(API_PREFIX) :] if value.startswith(API_PREFIX) else value


def unwrap_collection(value: str) -> str:
    if value.startswith("Collection(") and value.endswith(")"):
        return value[len("Collection(") : -1]
    return value


def canonical_segment(name: str) -> str:
    return name[:1].lower() + name[1:] if name else name


def path_domain(path: str) -> str:
    if not path.startswith("/api/"):
        return "Other"
    rest = path[len("/api/") :]
    base = rest.split("/", 1)[0]
    base = base.split("(", 1)[0]
    if not base:
        return "Other"
    mapping = {
        "ips": "IPs",
        "software": "Software",
        "deviceavinfo": "Device AV Info",
        "advancedqueries": "Advanced Queries",
        "machineactions": "Machine Actions",
        "libraryfiles": "Library Files",
        "remediationtasks": "Remediation Tasks",
    }
    lowered = base.lower()
    if lowered in mapping:
        return mapping[lowered]
    return re.sub(r"(?<!^)(?=[A-Z])", " ", base).replace("_", " ").title()


def normalize_path(path: str) -> str:
    path = path.strip()
    if not path:
        return path
    if not path.startswith("/api/"):
        path = "/" + path.lstrip("/")
    path = path.replace("//", "/")
    path = re.sub(r"\{[^}]+\}", "{id}", path)
    path = re.sub(r"/[A-Fa-f0-9-]{36}(?=/|$)", "/{id}", path)
    path = re.sub(r"/'[^']*'", "/{id}", path)
    return path.lower()


def infer_priority(op_type: str, path: str, notes: str) -> str:
    low_notes = notes.lower()
    if "/machines" in path or "/alerts" in path or "/machineactions" in path:
        return "High"
    if op_type in {"Action", "Function"}:
        return "High"
    if "duplicate" in low_notes or "alias" in low_notes:
        return "Low"
    return "Medium"


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                inner = value.value
                if isinstance(inner, ast.Attribute) and inner.attr == "_PATH":
                    parts.append("{_PATH}")
                else:
                    parts.append("{id}")
            else:
                return None
        return "".join(parts)
    return None


def collect_metadata() -> dict[str, Any]:
    root = ET.parse(XML_PATH).getroot()
    container = root.find(".//edm:EntityContainer", NS)
    if container is None:
        raise SystemExit("EntityContainer not found")

    type_to_sets: dict[str, list[str]] = defaultdict(list)
    metadata_ops: list[dict[str, Any]] = []

    entity_sets = container.findall("edm:EntitySet", NS)
    for entity_set in entity_sets:
        set_name = entity_set.attrib["Name"]
        short_type = strip_prefix(entity_set.attrib["EntityType"])
        type_to_sets[short_type].append(set_name)

    for entity_set in entity_sets:
        set_name = entity_set.attrib["Name"]
        short_type = strip_prefix(entity_set.attrib["EntityType"])
        set_path = f"/api/{canonical_segment(set_name)}"
        duplicate_sets = type_to_sets[short_type]
        notes = []
        if len(duplicate_sets) > 1:
            notes.append(
                f"Duplicate EntitySet for {short_type}: {', '.join(duplicate_sets)}"
            )
        metadata_ops.append(
            {
                "domain": path_domain(set_path),
                "operation": f"{set_name} collection",
                "kind": "EntitySet",
                "http_method": "GET",
                "path": set_path,
                "notes": "; ".join(notes),
                "key": ("GET", normalize_path(set_path)),
            }
        )
        metadata_ops.append(
            {
                "domain": path_domain(set_path),
                "operation": f"{set_name} item",
                "kind": "EntitySet",
                "http_method": "GET",
                "path": f"{set_path}/{{id}}",
                "notes": "; ".join(notes),
                "key": ("GET", normalize_path(f"{set_path}/{{id}}")),
            }
        )
        for binding in entity_set.findall("edm:NavigationPropertyBinding", NS):
            binding_path = binding.attrib["Path"]
            target = binding.attrib["Target"]
            full_path = f"{set_path}/{{id}}/{binding_path}"
            metadata_ops.append(
                {
                    "domain": path_domain(set_path),
                    "operation": f"{set_name}.{binding_path}",
                    "kind": "NavigationProperty",
                    "http_method": "GET",
                    "path": full_path,
                    "notes": f"Target EntitySet: {target}",
                    "key": ("GET", normalize_path(full_path)),
                }
            )

    for kind_tag, method in [("Action", "POST"), ("Function", "GET")]:
        for op in root.findall(f".//edm:{kind_tag}", NS):
            if op.attrib.get("IsBound") != "true":
                continue
            params = op.findall("edm:Parameter", NS)
            if not params:
                continue
            name = op.attrib["Name"]
            binding_raw = params[0].attrib["Type"]
            binding_type = strip_prefix(unwrap_collection(binding_raw))
            collection_bound = binding_raw.startswith("Collection(")
            base_sets = type_to_sets.get(binding_type, [])
            base_path = (
                f"/api/{canonical_segment(base_sets[0])}"
                if base_sets
                else f"/api/{canonical_segment(binding_type)}"
            )
            op_path = (
                f"{base_path}/{canonical_segment(name)}"
                if collection_bound
                else f"{base_path}/{{id}}/{canonical_segment(name)}"
            )
            notes = []
            extra_params = [param.attrib["Name"] for param in params[1:]]
            if extra_params:
                notes.append("Parameters: " + ", ".join(extra_params))
            if len(base_sets) > 1:
                notes.append(
                    "Bound type has duplicate entity sets: " + ", ".join(base_sets)
                )
            metadata_ops.append(
                {
                    "domain": path_domain(base_path),
                    "operation": name,
                    "kind": kind_tag,
                    "http_method": method,
                    "path": op_path,
                    "notes": "; ".join(notes),
                    "key": (method, normalize_path(op_path)),
                }
            )

    return {
        "metadata_ops": metadata_ops,
        "singletons": container.findall("edm:Singleton", NS),
    }


class MethodRecordCollector(ast.NodeVisitor):
    def __init__(self, path_const: str | None, method_name: str):
        self.path_const = path_const
        self.method_name = method_name
        self.records: list[dict[str, Any]] = []
        self.local_vars: dict[str, str] = {}

    def _resolve_string(self, node: ast.AST) -> str | None:
        """Try literal_string first, then fall back to local variable lookup."""
        result = literal_string(node)
        if result is not None:
            return result
        if isinstance(node, ast.Name) and node.id in self.local_vars:
            return self.local_vars[node.id]
        return None

    def visit_Assign(self, node: ast.Assign) -> Any:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            value = literal_string(node.value)
            if value is not None:
                self.local_vars[node.targets[0].id] = value.replace(
                    "{_PATH}", self.path_const or ""
                )
        return self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> Any:
        value = node.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id.endswith("Results")
        ):
            http_method = "GET"
            path = self.path_const
            files = False
            single = False
            for kw in value.keywords:
                if kw.arg == "method" and isinstance(kw.value, ast.Constant):
                    http_method = str(kw.value.value)
                elif kw.arg == "path":
                    candidate = self._resolve_string(kw.value)
                    if candidate is not None:
                        path = candidate.replace("{_PATH}", self.path_const or "")
                elif kw.arg == "files" and isinstance(kw.value, ast.Constant):
                    files = bool(kw.value.value)
                elif kw.arg == "single" and isinstance(kw.value, ast.Constant):
                    single = bool(kw.value.value)
            if path:
                path = path.replace("{_PATH}", self.path_const or "")
            self.records.append(
                {
                    "http_method": http_method,
                    "path": normalize_path(path or ""),
                    "raw_path": path or "",
                    "files": files,
                    "single": single,
                    "method_name": self.method_name,
                    "source": "BaseResults",
                }
            )
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "_request":
            args = list(node.args)
            method: str | None = literal_string(args[0]) if len(args) >= 1 else None
            path_node = args[1] if len(args) >= 2 else None
            for kw in node.keywords:
                if kw.arg == "method":
                    method = literal_string(kw.value)
                elif kw.arg == "path":
                    path_node = kw.value
            path = self._resolve_string(path_node) if path_node is not None else None
            if method and path:
                path = path.replace("{_PATH}", self.path_const or "")
                self.records.append(
                    {
                        "http_method": method,
                        "path": normalize_path(path),
                        "raw_path": path,
                        "files": False,
                        "single": False,
                        "method_name": self.method_name,
                        "source": "direct_request",
                    }
                )
        return self.generic_visit(node)


def collect_impl() -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    records: list[dict[str, Any]] = []
    file_notes: dict[str, list[str]] = defaultdict(list)
    for file_path in sorted(ENDPOINTS_DIR.glob("*.py")):
        source = file_path.read_text(encoding="utf-8")
        if re.search(
            r"TODO|not implemented|Needs further Testing", source, re.IGNORECASE
        ):
            for line in source.splitlines():
                if re.search(
                    r"TODO|not implemented|Needs further Testing", line, re.IGNORECASE
                ):
                    file_notes[str(file_path.relative_to(ROOT))].append(line.strip())
        tree = ast.parse(source)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or not node.name.endswith("Endpoint"):
                continue
            path_const = None
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "_PATH":
                            path_const = literal_string(stmt.value)
            for stmt in node.body:
                if not isinstance(stmt, ast.FunctionDef):
                    continue
                collector = MethodRecordCollector(path_const, stmt.name)
                collector.visit(stmt)
                for rec in collector.records:
                    rec["file"] = str(file_path.relative_to(ROOT))
                    rec["class"] = node.name
                    rec["internal_only"] = stmt.name.startswith("_")
                    rec["notes"] = []
                    doc = ast.get_docstring(stmt) or ""
                    if re.search(
                        r"not implemented|Needs further Testing", doc, re.IGNORECASE
                    ):
                        rec["notes"].append(
                            "Docstring marks the operation incomplete or untested"
                        )
                    rec["key"] = (rec["http_method"], rec["path"])
                    records.append(rec)
    dedup: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for record in records:
        dedup[
            (record["file"], record["class"], record["method_name"], record["path"])
        ] = record
    return list(dedup.values()), file_notes


VALIDATION_CACHE_PATH = ROOT / "build" / "endpoint_validation.json"


def load_validation_cache() -> dict[str, dict[str, Any]]:
    """Load cached validation results from disk."""
    if VALIDATION_CACHE_PATH.exists():
        return json.loads(VALIDATION_CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_validation_cache(cache: dict[str, dict[str, Any]]) -> None:
    """Save validation results to disk."""
    VALIDATION_CACHE_PATH.write_text(
        json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8"
    )


def _probe_endpoint(client: Any, method: str, path: str) -> dict[str, Any]:
    """Issue a single request and return {status_code, message, http_method}."""
    try:
        response = client.misc._request(method, path)
        status = response.status_code
        try:
            body = response.json()
            msg = ""
            if "error" in body:
                error = body["error"]
                msg = error.get("message", error.get("code", ""))
                if len(msg) > 120:
                    msg = msg[:117] + "..."
        except Exception:
            msg = response.text[:120] if response.text else ""
    except Exception as exc:
        status = 0
        msg = str(exc)[:120]
    return {"status_code": status, "message": msg, "http_method": method}


def _fetch_sample_id(client: Any, collection_path: str) -> str | None:
    """GET ``collection_path?$top=1`` and return the ``id`` of the first item."""
    try:
        response = client.misc._request("GET", collection_path, params={"$top": "1"})
        if response.status_code != 200:
            return None
        body = response.json()
        items = body.get("value", [])
        if items and isinstance(items, list) and "id" in items[0]:
            return str(items[0]["id"])
    except Exception:
        pass
    return None


def validate_endpoints(ops: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Probe missing endpoints against the live API and record status codes.

    Returns a dict keyed by ``"METHOD /path"`` →
    ``{status_code, message, http_method}``.

    Collection endpoints are probed directly.  For ``{id}``-dependent paths the
    function first fetches a sample ID from the parent collection using
    ``$top=1``, then substitutes it into the path before probing.

    Requires AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET env vars.
    """
    from mde_client import MDEClient

    tenant_id: str = str(os.environ.get("AZURE_TENANT_ID"))
    client_id: str = str(os.environ.get("AZURE_CLIENT_ID"))
    client_secret: str = str(os.environ.get("AZURE_CLIENT_SECRET"))

    if not all([tenant_id, client_id, client_secret]):
        raise SystemExit(
            "--validate requires AZURE_TENANT_ID, AZURE_CLIENT_ID, and "
            "AZURE_CLIENT_SECRET environment variables."
        )

    client = MDEClient(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )

    results: dict[str, dict[str, Any]] = {}
    seen: set[tuple[str, str]] = set()

    # --- Phase 1: probe collection-level (no {id}) endpoints ---
    for op in ops:
        method = op["http_method"]
        path = op["path"]
        if "{id}" in path:
            continue
        probe_key = (method, path)
        if probe_key in seen:
            continue
        seen.add(probe_key)

        result = _probe_endpoint(client, method, path)
        results[f"{method} {path}"] = result
        icon = "✓" if result["status_code"] in (200, 403) else "✗"
        print(f"  {icon} {method} {path} -> {result['status_code']}")

    # --- Phase 2: resolve sample IDs for parent collections, then probe {id} paths ---
    # Group {id} ops by their parent collection path
    id_ops_by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for op in ops:
        path = op["path"]
        if "{id}" not in path:
            continue
        # Parent collection is everything before the first /{id}
        parent = path.split("/{id}")[0]
        id_ops_by_parent[parent].append(op)

    sample_ids: dict[str, str | None] = {}
    for parent, child_ops in sorted(id_ops_by_parent.items()):
        if parent not in sample_ids:
            print(f"  ↳ fetching sample ID from {parent}?$top=1 ...")
            sample_ids[parent] = _fetch_sample_id(client, parent)
            sample_id = sample_ids[parent]
            if sample_id:
                preview = sample_id[:20] if len(sample_id) > 20 else sample_id
                print(f"    got id={preview}...")
            else:
                print("    no ID available (404/403/empty)")

        sample_id = sample_ids[parent]
        if sample_id is None:
            # Can't probe without an ID — record as "not probed"
            for op in child_ops:
                method = op["http_method"]
                key = f"{method} {op['path']}"
                if key not in results:
                    results[key] = {
                        "status_code": -1,
                        "message": f"Could not fetch sample ID from {parent}",
                        "http_method": method,
                    }
            continue

        for op in child_ops:
            method = op["http_method"]
            template_path = op["path"]
            probe_key = (method, template_path)
            if probe_key in seen:
                continue
            seen.add(probe_key)

            real_path = template_path.replace("{id}", sample_id)
            result = _probe_endpoint(client, method, real_path)
            # Store under the template path so it maps back to the TODO rows
            results[f"{method} {template_path}"] = result
            icon = "✓" if result["status_code"] in (200, 403) else "✗"
            print(f"  {icon} {method} {template_path} -> {result['status_code']}")

    return results


def load_ignore_list() -> list[dict[str, str]]:
    """Load the suppress list from mde_todo_ignore.yaml.

    Returns a list of rule dicts with optional keys: path, operation, http_method.
    """
    if not TODO_IGNORE_PATH.exists():
        return []
    raw = yaml.safe_load(TODO_IGNORE_PATH.read_text(encoding="utf-8")) or {}
    return raw.get("ignore", [])


def is_ignored(op: dict[str, Any], ignore_rules: list[dict[str, str]]) -> bool:
    """Return True if *op* matches any rule in *ignore_rules*."""
    for rule in ignore_rules:
        rule_path = rule.get("path")
        rule_operation = rule.get("operation")
        rule_method = rule.get("http_method")

        if rule_path and not op["path"].startswith(rule_path):
            continue
        if rule_operation and op["operation"] != rule_operation:
            continue
        if rule_method and op["http_method"].upper() != rule_method.upper():
            continue
        # All specified fields matched
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate MDE endpoint coverage TODO from metadata XML."
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Probe missing endpoints against the live API and annotate with status codes. "
        "Requires AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET env vars.",
    )
    args = parser.parse_args()

    ignore_rules = load_ignore_list()

    meta = collect_metadata()
    # Apply ignore list to the raw metadata operations before any classification
    meta["metadata_ops"] = [
        op for op in meta["metadata_ops"] if not is_ignored(op, ignore_rules)
    ]

    impl_records, file_notes = collect_impl()
    impl_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in impl_records:
        impl_by_key[record["key"]].append(record)

    covered: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    partial_ops: list[dict[str, Any]] = []
    covered_rows: list[dict[str, Any]] = []
    partial_files: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"missing": set(), "notes": set()}
    )

    for op in meta["metadata_ops"]:
        matches = impl_by_key.get(op["key"], [])
        if not matches:
            missing.append(op)
            continue
        if any(match["notes"] for match in matches):
            merged_notes = "; ".join(
                sorted({note for match in matches for note in match["notes"]})
            )
            partial_ops.append(
                {**op, "notes": "; ".join(filter(None, [op["notes"], merged_notes]))}
            )
            for match in matches:
                entry = partial_files[match["file"]]
                entry["missing"].add(op["operation"])
                for note in match["notes"]:
                    entry["notes"].add(note)
            covered_rows.append(
                {
                    "operation": op["operation"],
                    "implemented_in": ", ".join(
                        sorted(
                            {
                                f"{m['file']}::{m['class']}.{m['method_name']}"
                                for m in matches
                            }
                        )
                    ),
                    "status": "⚠️",
                }
            )
            continue
        covered.append(op)
        covered_rows.append(
            {
                "operation": op["operation"],
                "implemented_in": ", ".join(
                    sorted(
                        {
                            f"{m['file']}::{m['class']}.{m['method_name']}"
                            for m in matches
                        }
                    )
                ),
                "status": "✅",
            }
        )

    ops_by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    status_by_key: dict[tuple[str, str], str] = {}
    for op in covered:
        status_by_key[op["key"]] = "covered"
    for op in partial_ops:
        status_by_key[op["key"]] = "partial"
    for op in missing:
        status_by_key[op["key"]] = "missing"
    for op in meta["metadata_ops"]:
        ops_by_domain[op["domain"]].append(op)

    for domain, ops in ops_by_domain.items():
        has_impl = any(
            status_by_key.get(op["key"]) in {"covered", "partial"} for op in ops
        )
        domain_missing = [op for op in ops if status_by_key.get(op["key"]) == "missing"]
        if not has_impl or not domain_missing:
            continue
        impl_files = set()
        for op in ops:
            for match in impl_by_key.get(op["key"], []):
                impl_files.add(match["file"])
        missing_names = sorted({op["operation"] for op in domain_missing})
        for file in impl_files:
            partial_files[file]["notes"].add(
                f"{domain} domain has uncovered metadata operations"
            )
            for name in missing_names[:10]:
                partial_files[file]["missing"].add(name)

    for file, notes in file_notes.items():
        for note in notes[:5]:
            partial_files[file]["notes"].add(note)

    # --- Validation ---
    validation_results: dict[str, dict[str, Any]] = {}
    if args.validate:
        print("Validating missing endpoints against live API...")
        validation_results = validate_endpoints(missing)
        # Merge with any existing cache (preserves results for {id} endpoints from prior runs)
        cache = load_validation_cache()
        cache.update(validation_results)
        save_validation_cache(cache)
        print(f"Validation results saved to {VALIDATION_CACHE_PATH}")
    else:
        # Load from cache if available
        validation_results = load_validation_cache()

    # --- Generate output ---
    meta_total = len(meta["metadata_ops"])
    implemented_total = len(covered)
    partial_total = len(partial_files)
    missing_total = len(missing)
    coverage_pct = (implemented_total / meta_total * 100) if meta_total else 0.0

    lines: list[str] = []
    lines.append("# MDE Client — Endpoint Coverage TODO")
    lines.append("")
    lines.append(
        "> Auto-generated gap analysis comparing `build/mde_metadata.xml` against `src/mde_client/endpoints/`"
    )
    lines.append(f"> Generated: {TODAY}")
    lines.append("")
    lines.append(
        "Assumptions: EntitySets are counted as separate collection/item GET operations; "
        "private endpoint helpers that issue real requests count as implemented; "
        "duplicate EntitySets are preserved as separate contract rows."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total operations in metadata contract: {meta_total}")
    lines.append(f"- Currently implemented: {implemented_total}")
    lines.append(f"- Partially implemented: {partial_total}")
    lines.append(f"- Missing: {missing_total}")
    lines.append(f"- Coverage: {coverage_pct:.1f}%")
    if validation_results:
        phantom_count = sum(
            1 for v in validation_results.values() if v["status_code"] in (404, 405)
        )
        valid_count = sum(
            1 for v in validation_results.values() if v["status_code"] in (200, 403)
        )
        lines.append(
            f"- Validated endpoints: {len(validation_results)} probed, "
            f"{valid_count} confirmed valid, {phantom_count} phantom (404/405)"
        )
    lines.append("")
    lines.append("## Missing Endpoints")
    lines.append("")
    if validation_results:
        lines.append(
            "> API Status column from live validation: "
            "✓ = confirmed (200/403), ✗ = phantom (404/405), ? = not probed"
        )
        lines.append("")
    missing_by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for op in missing:
        missing_by_domain[op["domain"]].append(op)
    for domain in sorted(missing_by_domain):
        lines.append(f"### {domain}")
        lines.append("")
        if validation_results:
            lines.append(
                "| Operation | Type | HTTP Method | Path | Priority | API Status | Notes |"
            )
            lines.append(
                "|-----------|------|-------------|------|----------|------------|-------|"
            )
        else:
            lines.append("| Operation | Type | HTTP Method | Path | Priority | Notes |")
            lines.append("|-----------|------|-------------|------|----------|-------|")
        for op in sorted(
            missing_by_domain[domain],
            key=lambda item: (item["path"], item["operation"]),
        ):
            notes = op["notes"] or "Not implemented in endpoint modules"
            notes = notes.replace("|", "/")
            priority = infer_priority(op["kind"], op["path"], notes)

            if validation_results:
                lookup_key = f"{op['http_method']} {op['path']}"
                vr = validation_results.get(lookup_key)
                if vr:
                    sc = vr["status_code"]
                    icon = "✓" if sc in (200, 403) else "✗" if sc in (404, 405) else "?"
                    api_status = f"{icon} {sc}"
                    if vr["message"]:
                        msg = vr["message"].replace("|", "/")
                        notes = f"{notes}; API: {msg}" if notes else f"API: {msg}"
                else:
                    api_status = "? (not probed)"
                lines.append(
                    f"| {op['operation']} | {op['kind']} | {op['http_method']} "
                    f"| {op['path']} | {priority} | {api_status} | {notes} |"
                )
            else:
                lines.append(
                    f"| {op['operation']} | {op['kind']} | {op['http_method']} "
                    f"| {op['path']} | {priority} | {notes} |"
                )
        lines.append("")
    lines.append("## Partially Implemented")
    lines.append("")
    lines.append("| Endpoint File | Missing Operations | Notes |")
    lines.append("|---------------|-------------------|-------|")
    for file in sorted(partial_files):
        missing_ops = ", ".join(sorted(partial_files[file]["missing"])) or "See notes"
        notes = (
            "; ".join(sorted(partial_files[file]["notes"]))
            or "Partial coverage inferred from metadata mismatch"
        )
        lines.append(
            f"| {file} | {missing_ops.replace('|', '/')} | {notes.replace('|', '/')} |"
        )
    lines.append("")
    lines.append("## Already Covered (Reference)")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Click to expand full coverage list</summary>")
    lines.append("")
    lines.append("| Operation | Implemented In | Status |")
    lines.append("|-----------|---------------|--------|")
    for row in sorted(
        covered_rows, key=lambda item: (item["operation"], item["implemented_in"])
    ):
        lines.append(
            f"| {row['operation']} | {row['implemented_in']} | {row['status']} |"
        )
    lines.append("")
    lines.append("</details>")
    lines.append("")
    lines.append("## Singletons")
    lines.append("")
    if meta["singletons"]:
        for singleton in meta["singletons"]:
            lines.append(f"- {singleton.attrib.get('Name', '')}")
    else:
        lines.append("- None present in `build/mde_metadata.xml`.")
    lines.append("")

    output: str = "\n".join(lines)

    todo_file = Path("src/mde_client/TODO.md")

    with todo_file.open("w", encoding="utf-8") as f:
        f.write(output)

    print(f"TODO file generated at {todo_file.resolve()}")


if __name__ == "__main__":
    main()
