"""Opt-in connectivity check for one owner-verified target."""

import pytest

from framework.network_client import NetworkClient
from framework.device_config import DeviceProfile, TcpPortExpectation


@pytest.mark.smoke
@pytest.mark.network
@pytest.mark.hardware
@pytest.mark.usefixtures("tcp_reachability_prerequisite")
def test_tcp_connectivity(
    network_client: NetworkClient,
    hardware_profile: DeviceProfile,
    tcp_expectation: TcpPortExpectation,
) -> None:
    actual = network_client.check_tcp_port(
        hardware_profile.host, tcp_expectation.port
    )
    assert actual is tcp_expectation.accessible, (
        f"TCP port {tcp_expectation.port}: expected accessibility "
        f"{tcp_expectation.accessible}, got {actual}. Verify device identity, "
        "interface, route, listening service, and timeout."
    )
