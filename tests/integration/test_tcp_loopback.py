"""Real TCP connectivity on loopback without external network access."""

from collections.abc import Iterator
import socket

import pytest

from framework.network_client import NetworkClient

pytestmark = [pytest.mark.integration, pytest.mark.network]


@pytest.fixture
def loopback_server() -> Iterator[socket.socket]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.settimeout(2.0)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        yield server


def test_tcp_loopback(loopback_server: socket.socket) -> None:
    host, port = loopback_server.getsockname()
    client = NetworkClient(timeout=2.0)
    assert client.check_tcp_port(host, port), "Local TCP connection failed."

    # The listen backlog completes the handshake without a worker thread.
    connection, _ = loopback_server.accept()
    with connection:
        connection.settimeout(2.0)
        assert connection.recv(1) == b"", "Client did not close its socket."
