"""Load explicit local device profiles without contacting devices."""

from dataclasses import dataclass
import math
from pathlib import Path

import yaml


class DeviceConfigurationError(ValueError):
    """Configuration cannot be loaded, validated, or selected."""


@dataclass(frozen=True)
class TcpPortExpectation:
    port: int
    accessible: bool


@dataclass(frozen=True)
class DeviceProfile:
    host: str
    timeout: float
    tcp_ports: tuple[TcpPortExpectation, ...]


def _parse_profile(raw: object) -> DeviceProfile:
    fields = {"host", "timeout", "tcp_ports"}
    if not isinstance(raw, dict) or set(raw) != fields:
        raise DeviceConfigurationError(
            "Each device requires exactly host, timeout, and tcp_ports fields."
        )
    host = raw["host"]
    if not isinstance(host, str) or not host.strip():
        raise DeviceConfigurationError(
            "Device host must be a nonempty string."
        )
    timeout = raw["timeout"]
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or timeout <= 0
    ):
        raise DeviceConfigurationError(
            "Device timeout must be finite and positive."
        )
    try:
        timeout = float(timeout)
    except OverflowError:
        raise DeviceConfigurationError(
            "Device timeout is too large."
        ) from None
    if not math.isfinite(timeout):
        raise DeviceConfigurationError(
            "Device timeout must be finite and positive."
        )
    ports = raw["tcp_ports"]
    if not isinstance(ports, dict) or not ports:
        raise DeviceConfigurationError("tcp_ports must be a nonempty mapping.")
    expectations = []
    for port, accessible in ports.items():
        if type(port) is not int or not 1 <= port <= 65535:
            raise DeviceConfigurationError(
                "TCP ports must be integers 1-65535."
            )
        if not isinstance(accessible, bool):
            raise DeviceConfigurationError(
                "TCP accessibility must be boolean."
            )
        expectations.append(TcpPortExpectation(port, accessible))
    if not any(case.accessible for case in expectations):
        raise DeviceConfigurationError(
            "Negative expectations require at least one positive TCP expectation."
        )
    return DeviceProfile(host.strip(), timeout, tuple(expectations))


def load_device_profiles(path: Path) -> dict[str, DeviceProfile]:
    """Read safe YAML; errors exclude private file contents."""
    try:
        with path.open(encoding="utf-8") as source:
            raw = yaml.safe_load(source)
    except (OSError, UnicodeError, yaml.YAMLError):
        raise DeviceConfigurationError(
            "Cannot read device configuration: "
            "check file access and YAML syntax."
        ) from None
    if not isinstance(raw, dict) or set(raw) != {"devices"}:
        raise DeviceConfigurationError(
            "Configuration requires only a devices mapping."
        )
    devices = raw["devices"]
    if not isinstance(devices, dict) or not devices:
        raise DeviceConfigurationError("devices must be a nonempty mapping.")
    profiles = {}
    for name, profile in devices.items():
        if not isinstance(name, str) or not name.strip():
            raise DeviceConfigurationError(
                "Device names must be nonempty strings."
            )
        profiles[name] = _parse_profile(profile)
    return profiles


def select_device(
    profiles: dict[str, DeviceProfile], name: str
) -> DeviceProfile:
    """Select exactly one named profile, with no wildcard expansion."""
    if not isinstance(name, str) or name not in profiles:
        raise DeviceConfigurationError(
            "Selected device is not in configuration."
        )
    return profiles[name]
