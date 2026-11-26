"""Shared fixtures and explicit physical hardware opt-in."""

import math
from pathlib import Path

import pytest

from framework.network_client import NetworkClient
from framework.device_config import (
    DeviceConfigurationError,
    DeviceProfile,
    TcpPortExpectation,
    load_device_profiles,
    select_device,
)

DEVICE_PROFILE = pytest.StashKey[DeviceProfile | None]()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("network-qa")
    group.addoption("--run-hardware", action="store_true", default=False)
    group.addoption("--target-host", default=None)
    group.addoption("--target-port", type=int, default=None)
    group.addoption("--tcp-timeout", type=float, default=None)
    group.addoption("--device-config", action="append", default=[])
    group.addoption("--device", action="append", default=[])
    group.addoption(
        "--confirm-device-identity", action="store_true", default=False
    )


def pytest_configure(config: pytest.Config) -> None:
    config.stash[DEVICE_PROFILE] = None
    timeout_option = config.getoption("--tcp-timeout")
    timeout = 3.0 if timeout_option is None else timeout_option
    if not math.isfinite(timeout) or timeout <= 0:
        raise pytest.UsageError("--tcp-timeout must be finite and positive")
    paths = config.getoption("--device-config")
    names = config.getoption("--device")
    confirm = config.getoption("--confirm-device-identity")
    if paths or names:
        if len(paths) != 1 or len(names) != 1:
            raise pytest.UsageError(
                "Select exactly one --device-config and --device"
            )
        if names[0] in {"*", "all"}:
            raise pytest.UsageError(
                "Select one device; wildcard/all is unsupported"
            )
        if (
            config.getoption("--target-host") is not None
            or config.getoption("--target-port") is not None
            or timeout_option is not None
        ):
            raise pytest.UsageError(
                "Profile options conflict with explicit target options"
            )
        if config.getoption("--run-hardware") and not confirm:
            raise pytest.UsageError(
                "Profile execution requires --confirm-device-identity"
            )
        try:
            profiles = load_device_profiles(Path(paths[0]))
            config.stash[DEVICE_PROFILE] = select_device(profiles, names[0])
        except DeviceConfigurationError as error:
            raise pytest.UsageError(str(error)) from None
    elif confirm:
        raise pytest.UsageError(
            "--confirm-device-identity requires profile selection"
        )
    elif config.getoption("--run-hardware"):
        host = config.getoption("--target-host")
        port = config.getoption("--target-port")
        if not host or not host.strip() or port is None:
            raise pytest.UsageError(
                "--run-hardware requires --target-host and --target-port"
            )
        if not 1 <= port <= 65535:
            raise pytest.UsageError(
                "--target-port must be between 1 and 65535"
            )
        config.stash[DEVICE_PROFILE] = DeviceProfile(
            host, timeout, (TcpPortExpectation(port, True),)
        )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "tcp_expectation" in metafunc.fixturenames:
        profile = metafunc.config.stash[DEVICE_PROFILE]
        cases = profile.tcp_ports if profile else (None,)
        metafunc.parametrize(
            "tcp_expectation",
            cases,
            ids=[
                f"tcp-{case.port}-expected-{case.accessible}"
                if case else "disabled"
                for case in cases
            ],
        )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if not config.getoption("--run-hardware"):
        skip = pytest.mark.skip(
            reason="Hardware disabled; use --run-hardware"
        )
        for item in items:
            if item.get_closest_marker("hardware"):
                item.add_marker(skip)


@pytest.fixture
def network_client(pytestconfig: pytest.Config) -> NetworkClient:
    profile = pytestconfig.stash[DEVICE_PROFILE]
    timeout = pytestconfig.getoption("--tcp-timeout")
    effective_timeout = 3.0 if timeout is None else timeout
    return NetworkClient(
        timeout=profile.timeout if profile else effective_timeout
    )


@pytest.fixture
def hardware_profile(pytestconfig: pytest.Config) -> DeviceProfile:
    if not pytestconfig.getoption("--run-hardware"):
        pytest.skip("Hardware disabled; use --run-hardware")
    profile = pytestconfig.stash[DEVICE_PROFILE]
    assert profile is not None, "Hardware requires a configured target."
    return profile


@pytest.fixture
def tcp_reachability_prerequisite(
    hardware_profile: DeviceProfile,
    network_client: NetworkClient,
    tcp_expectation: TcpPortExpectation,
) -> None:
    """Recheck a known-open port immediately before each negative case."""
    if tcp_expectation.accessible:
        return
    positive_ports = [
        case.port for case in hardware_profile.tcp_ports if case.accessible
    ]
    if not positive_ports:
        pytest.fail("TCP setup error: no positive prerequisite port configured.")
    prerequisite_port = min(positive_ports)
    if not network_client.check_tcp_port(
        hardware_profile.host, prerequisite_port
    ):
        pytest.fail(
            f"TCP setup error: known-open prerequisite port {prerequisite_port} "
            "is unreachable; negative expectation was not evaluated. "
            "Verify device identity, cabling, interface, route, and service.",
            pytrace=False,
        )


@pytest.fixture
def hardware_target(pytestconfig: pytest.Config) -> tuple[str, int]:
    if not pytestconfig.getoption("--run-hardware"):
        pytest.skip("Hardware disabled; use --run-hardware")
    return (
        pytestconfig.getoption("--target-host"),
        pytestconfig.getoption("--target-port"),
    )
