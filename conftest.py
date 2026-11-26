"""Shared fixtures and explicit physical hardware opt-in."""

import math

import pytest

from framework.network_client import NetworkClient


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("network-qa")
    group.addoption("--run-hardware", action="store_true", default=False)
    group.addoption("--target-host", default=None)
    group.addoption("--target-port", type=int, default=None)
    group.addoption("--tcp-timeout", type=float, default=3.0)


def pytest_configure(config: pytest.Config) -> None:
    timeout = config.getoption("--tcp-timeout")
    if not math.isfinite(timeout) or timeout <= 0:
        raise pytest.UsageError("--tcp-timeout must be finite and positive")
    if config.getoption("--run-hardware"):
        host = config.getoption("--target-host")
        port = config.getoption("--target-port")
        if not host or not host.strip() or port is None:
            raise pytest.UsageError(
                "--run-hardware requires --target-host and --target-port"
            )
        if not 1 <= port <= 65535:
            raise pytest.UsageError("--target-port must be between 1 and 65535")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if not config.getoption("--run-hardware"):
        skip = pytest.mark.skip(reason="Hardware disabled; use --run-hardware")
        for item in items:
            if item.get_closest_marker("hardware"):
                item.add_marker(skip)


@pytest.fixture
def network_client(pytestconfig: pytest.Config) -> NetworkClient:
    return NetworkClient(timeout=pytestconfig.getoption("--tcp-timeout"))


@pytest.fixture
def hardware_target(pytestconfig: pytest.Config) -> tuple[str, int]:
    if not pytestconfig.getoption("--run-hardware"):
        pytest.skip("Hardware disabled; use --run-hardware")
    return (
        pytestconfig.getoption("--target-host"),
        pytestconfig.getoption("--target-port"),
    )
