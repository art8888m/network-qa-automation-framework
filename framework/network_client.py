"""Small, read-only TCP connectivity client."""

import logging
import math
import socket

logger = logging.getLogger(__name__)


class NetworkClient:
    """Check whether a TCP connection can be established."""

    def __init__(self, timeout: float = 3.0) -> None:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Timeout must be finite and greater than zero.")
        self.timeout = timeout

    def check_tcp_port(self, host: str, port: int) -> bool:
        """Return False for socket failures; raise ValueError for bad inputs."""
        if not isinstance(host, str) or not host.strip():
            raise ValueError("Host must be a nonempty string.")
        if isinstance(port, bool) or not isinstance(port, int):
            raise ValueError("Port must be an integer between 1 and 65535.")
        if not 1 <= port <= 65535:
            raise ValueError("Port must be an integer between 1 and 65535.")
        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                logger.debug("TCP connection established.")
                return True
        except ConnectionRefusedError:
            logger.warning("TCP connection refused.")
            return False
        except TimeoutError:
            logger.warning("TCP connection timed out.")
            return False
        except OSError as error:
            logger.warning(
                "TCP connection failed: socket error (errno=%s).", error.errno
            )
            return False
