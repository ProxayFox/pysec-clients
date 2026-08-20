from __future__ import annotations

import ast
from pathlib import Path

from mde_client import models
from mde_contract_gen.cli import DEFAULT_METADATA
from mde_contract_gen.edmx import parse_metadata
from mde_contract_gen.emitters.support_models import emit_support_models

RUNTIME_MODELS = Path("src/mde-client/src/mde_client/models")


def _normalized_ast(source: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            node.names.sort(key=lambda alias: alias.name)
    return ast.dump(tree)


def test_support_model_surface_is_generated_by_standalone_tool(
    tmp_path: Path,
) -> None:
    emit_support_models(parse_metadata(DEFAULT_METADATA), tmp_path)
    for filename in (
        "__init__.py",
        "action_payloads.py",
        "auth_params_models.py",
        "enums.py",
    ):
        expected = _normalized_ast((tmp_path / filename).read_text(encoding="utf-8"))
        actual = _normalized_ast(
            (RUNTIME_MODELS / filename).read_text(encoding="utf-8")
        )
        assert actual == expected


def test_public_support_model_exports_are_preserved() -> None:
    assert len(models.__all__) == 94
    assert {
        "ALERT_SEVERITY",
        "BatchUpdateIndicatorPayload",
        "SCANAUTHENTICATIONPARAMS",
        "WindowsAuthParams",
    } <= set(models.__all__)
