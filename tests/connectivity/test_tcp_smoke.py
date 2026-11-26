"""Opt-in connectivity check for one owner-verified target."""

import pytest

from framework.network_client import NetworkClient


@pytest.mark.smoke
@pytest.mark.network
@pytest.mark.hardware
def test_tcp_connectivity(
    network_client: NetworkClient, hardware_target: tuple[str, int]
) -> None:
    host, port = hardware_target
    assert network_client.check_tcp_port(host, port), (
        "TCP connection failed: verify the configured target, listening port, "
        "network interface, firewall, and timeout."
    )
