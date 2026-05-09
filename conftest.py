from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--skip-integration",
        action="store_true",
        default=False,
        help="Skip tests marked as integration (live API tests).",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if not config.getoption("--skip-integration"):
        return
    skip = pytest.mark.skip(reason="--skip-integration flag provided")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
