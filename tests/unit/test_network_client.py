"""Socket behavior is mocked; these tests never contact devices."""

from collections.abc import Iterator
import logging
from unittest.mock import MagicMock, patch

import pytest

from framework.network_client import NetworkClient

pytestmark = pytest.mark.unit


@pytest.fixture
def connection_mock() -> Iterator[MagicMock]:
    with patch("framework.network_client.socket.create_connection") as mocked:
        yield mocked


def test_success_closes_connection(connection_mock: MagicMock) -> None:
    client = NetworkClient(timeout=1.5)
    assert client.check_tcp_port("example.invalid", 12345) is True
    connection_mock.assert_called_once_with(
        ("example.invalid", 12345), timeout=1.5
    )
    connection_mock.return_value.__enter__.assert_called_once_with()
    connection_mock.return_value.__exit__.assert_called_once_with(
        None, None, None
    )


@pytest.mark.parametrize(
    "error, diagnostic",
    [
        (ConnectionRefusedError("sensitive-detail"), "TCP connection refused."),
        (TimeoutError("sensitive-detail"), "TCP connection timed out."),
        (
            OSError(123, "sensitive-detail"),
            "TCP connection failed: socket error (errno=123).",
        ),
    ],
    ids=["refused", "timeout", "socket-error"],
)
def test_socket_failure(
    connection_mock: MagicMock,
    error: OSError,
    diagnostic: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    connection_mock.side_effect = error
    with caplog.at_level(logging.WARNING, logger="framework.network_client"):
        assert NetworkClient().check_tcp_port("example.invalid", 12345) is False
    assert caplog.messages == [diagnostic]
    assert "example.invalid" not in caplog.text
    assert "12345" not in caplog.text
    assert "sensitive-detail" not in caplog.text


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_invalid_timeout(timeout: float) -> None:
    with pytest.raises(ValueError, match="Timeout"):
        NetworkClient(timeout=timeout)


@pytest.mark.parametrize("host", ["", "   "])
def test_empty_host(host: str, connection_mock: MagicMock) -> None:
    with pytest.raises(ValueError, match="Host"):
        NetworkClient().check_tcp_port(host, 12345)
    connection_mock.assert_not_called()


@pytest.mark.parametrize(
    "host",
    [None, 123, 1.5, True, b"example.invalid", [], {}],
    ids=["none", "integer", "float", "boolean", "bytes", "list", "dict"],
)
def test_invalid_host_type(host: object, connection_mock: MagicMock) -> None:
    with pytest.raises(ValueError, match="Host must be a nonempty string"):
        NetworkClient().check_tcp_port(host, 12345)  # type: ignore[arg-type]
    connection_mock.assert_not_called()


@pytest.mark.parametrize("port", [0, -1, 65536, True, 1.5, "80"])
def test_invalid_port(port: object, connection_mock: MagicMock) -> None:
    with pytest.raises(ValueError, match="Port"):
        NetworkClient().check_tcp_port(
            "example.invalid", port  # type: ignore[arg-type]
        )
    connection_mock.assert_not_called()
