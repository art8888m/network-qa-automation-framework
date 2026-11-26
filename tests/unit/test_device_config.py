"""Configuration tests use synthetic files and never contact devices."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from framework.device_config import (
    DeviceConfigurationError,
    TcpPortExpectation,
    load_device_profiles,
    select_device,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def valid_document() -> dict:
    return {"devices": {"first": {
        "host": "example.invalid", "timeout": 1.5,
        "tcp_ports": {80: True, 443: False},
    }}}


def write_config(tmp_path: Path, document: object) -> Path:
    path = tmp_path / "devices.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    return path


def test_load_and_select(tmp_path: Path, valid_document: dict) -> None:
    valid_document["devices"]["second"] = {
        "host": "other.invalid", "timeout": 2, "tcp_ports": {65535: True}
    }
    profiles = load_device_profiles(write_config(tmp_path, valid_document))
    profile = select_device(profiles, "first")
    assert profile.host == "example.invalid"
    assert profile.timeout == 1.5
    assert profile.tcp_ports == (
        TcpPortExpectation(80, True), TcpPortExpectation(443, False)
    )
    assert select_device(profiles, "second").timeout == 2.0
    with pytest.raises(FrozenInstanceError):
        profile.host = "changed.invalid"  # type: ignore[misc]
    for name in ["missing", "*", "all"]:
        with pytest.raises(DeviceConfigurationError, match="Selected device"):
            select_device(profiles, name)


@pytest.mark.parametrize("document", [
    None, [], {}, {"devices": {}}, {"devices": []}, {"devices": None},
    {"devices": {}, "extra": 1}, {"devices": {1: {}}},
    {"devices": {" ": {}}}, {"devices": {"first": []}},
])
def test_invalid_structure(tmp_path: Path, document: object) -> None:
    with pytest.raises(DeviceConfigurationError):
        load_device_profiles(write_config(tmp_path, document))


@pytest.mark.parametrize("field, value", [
    ("host", None), ("host", 123), ("host", ""), ("host", "  "),
    ("timeout", True), ("timeout", "3"), ("timeout", None),
    ("timeout", 0), ("timeout", -1), ("timeout", float("nan")),
    ("timeout", float("inf")), ("timeout", 10 ** 400),
    ("tcp_ports", {}), ("tcp_ports", []), ("tcp_ports", None),
    ("tcp_ports", {0: True}), ("tcp_ports", {-1: True}),
    ("tcp_ports", {65536: True}), ("tcp_ports", {True: True}),
    ("tcp_ports", {"80": True}), ("tcp_ports", {1.5: True}),
    ("tcp_ports", {80: "false"}), ("tcp_ports", {80: 1}),
    ("tcp_ports", {80: None}),
], ids=[f"invalid-field-{index}" for index in range(24)])
def test_invalid_fields(
    tmp_path: Path, valid_document: dict, field: str, value: object
) -> None:
    valid_document["devices"]["first"][field] = value
    with pytest.raises(DeviceConfigurationError):
        load_device_profiles(write_config(tmp_path, valid_document))


@pytest.mark.parametrize("field", ["host", "timeout", "tcp_ports"])
def test_missing_field(
    tmp_path: Path, valid_document: dict, field: str
) -> None:
    del valid_document["devices"]["first"][field]
    with pytest.raises(DeviceConfigurationError, match="exactly"):
        load_device_profiles(write_config(tmp_path, valid_document))


def test_unknown_field(tmp_path: Path, valid_document: dict) -> None:
    valid_document["devices"]["first"]["secret"] = "private-value"
    with pytest.raises(DeviceConfigurationError, match="exactly") as error:
        load_device_profiles(write_config(tmp_path, valid_document))
    assert "private-value" not in str(error.value)


def test_negative_requires_positive(
    tmp_path: Path, valid_document: dict
) -> None:
    valid_document["devices"]["first"]["tcp_ports"] = {443: False}
    with pytest.raises(DeviceConfigurationError, match="at least one positive"):
        load_device_profiles(write_config(tmp_path, valid_document))


@pytest.mark.parametrize("text", [
    "", "devices: [private-value", "!!python/object:private-value {}"
])
def test_bad_yaml(tmp_path: Path, text: str) -> None:
    path = tmp_path / "devices.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(DeviceConfigurationError) as error:
        load_device_profiles(path)
    assert "private-value" not in str(error.value)


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(DeviceConfigurationError, match="Cannot read"):
        load_device_profiles(tmp_path / "missing.yaml")


def test_unreadable_file(tmp_path: Path) -> None:
    with patch.object(
        Path, "open", side_effect=PermissionError("private-value")
    ):
        with pytest.raises(DeviceConfigurationError) as error:
            load_device_profiles(tmp_path / "devices.yaml")
    assert "private-value" not in str(error.value)


def test_committed_example() -> None:
    path = Path(__file__).resolve().parents[2] / "config/devices.example.yaml"
    profiles = load_device_profiles(path)
    assert len(profiles) == 2
    assert all(profile.host == "192.0.2.1" for profile in profiles.values())
