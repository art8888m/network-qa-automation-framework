"""Exercise real pytest wiring with synthetic targets and mocked sockets."""

from pathlib import Path

import pytest
import yaml

pytest_plugins = ["pytester"]
pytestmark = pytest.mark.unit


@pytest.fixture
def profile_suite(pytester: pytest.Pytester) -> pytest.Pytester:
    root = Path(__file__).resolve().parents[2]
    pytester.syspathinsert(root)
    plugin = (root / "conftest.py").read_text(encoding="utf-8")
    # Every connection is intercepted, including on a selection regression.
    plugin += '''
from unittest.mock import call, patch

@pytest.fixture(autouse=True)
def socket_guard(request, pytestconfig):
    def connect(address, timeout):
        assert address[0] == "selected.invalid", "Unselected device contacted"
        assert timeout == 1.25
        if address[1] == 443:
            raise ConnectionRefusedError("synthetic refusal")
        from unittest.mock import MagicMock
        return MagicMock()
    with patch("framework.network_client.socket.create_connection",
               side_effect=connect) as mocked:
        yield mocked
        case = request.node.callspec.params["tcp_expectation"]
        ports = []
        if not case.accessible:
            profile = pytestconfig.stash[DEVICE_PROFILE]
            ports.append(min(p.port for p in profile.tcp_ports if p.accessible))
        ports.append(case.port)
        assert mocked.call_args_list == [
            call(("selected.invalid", port), timeout=1.25) for port in ports
        ]
'''
    pytester.makeconftest(plugin)
    pytester.makeini(
        "[pytest]\naddopts = --strict-markers\nmarkers =\n"
        " hardware: physical\n smoke: smoke\n network: network\n"
    )
    pytester.makepyfile(
        test_profile=(root / "tests/connectivity/test_tcp_smoke.py").read_text(
            encoding="utf-8"
        )
    )
    document = {"devices": {
        "selected": {"host": "selected.invalid", "timeout": 1.25,
                     "tcp_ports": {80: True, 443: False}},
        "other": {"host": "unselected.invalid", "timeout": 9,
                  "tcp_ports": {9999: True}},
    }}
    (pytester.path / "devices.yaml").write_text(
        yaml.safe_dump(document), encoding="utf-8"
    )
    return pytester


def profile_args() -> list[str]:
    return ["--device-config=devices.yaml", "--device=selected"]


def test_selected_profile_only(profile_suite: pytest.Pytester) -> None:
    result = profile_suite.runpytest(
        *profile_args(), "--run-hardware", "--confirm-device-identity", "-v"
    )
    result.assert_outcomes(passed=2)
    assert "selected.invalid" not in result.stdout.str()
    assert "unselected.invalid" not in result.stdout.str()
    assert "tcp-80-expected-True" in result.stdout.str()
    assert "tcp-443-expected-False" in result.stdout.str()


@pytest.mark.parametrize("actual, expected", [
    (True, True), (False, False), (True, False), (False, True),
])
def test_expected_actual_matrix(
    profile_suite: pytest.Pytester, actual: bool, expected: bool
) -> None:
    path = profile_suite.path / "devices.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    port = 80 if actual else 443
    # Keep the negative first and use a nonstandard positive prerequisite.
    ports = {port: expected}
    if not expected:
        ports[23456] = True
    document["devices"]["selected"]["tcp_ports"] = ports
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    result = profile_suite.runpytest(
        *profile_args(), "--run-hardware", "--confirm-device-identity",
        "-k", f"tcp-{port}-expected-{expected}",
    )
    result.assert_outcomes(
        passed=int(actual == expected), failed=int(actual != expected)
    )


@pytest.mark.parametrize(
    "extra", [[], ["-m", "hardware"], ["--confirm-device-identity"]]
)
def test_profile_still_skipped(
    profile_suite: pytest.Pytester, extra: list[str]
) -> None:
    result = profile_suite.runpytest(*profile_args(), *extra)
    result.assert_outcomes(skipped=2)


@pytest.mark.parametrize("args, message", [
    (["--device=selected"], "exactly one"),
    (["--device-config=devices.yaml"], "exactly one"),
    (profile_args() + ["--device=other"], "exactly one"),
    (profile_args() + ["--device-config=devices.yaml"], "exactly one"),
    (profile_args() + ["--target-host=example.invalid"], "conflict"),
    (profile_args() + ["--target-port=80"], "conflict"),
    (profile_args() + ["--tcp-timeout=3"], "conflict"),
    (profile_args() + ["--run-hardware"], "--confirm-device-identity"),
    (["--confirm-device-identity"], "requires profile selection"),
    (
        ["--device-config=devices.yaml", "--device=missing"],
        "not in configuration",
    ),
    (["--device-config=devices.yaml", "--device=*"], "unsupported"),
    (["--device-config=devices.yaml", "--device=all"], "unsupported"),
    (["--device-config=missing.yaml", "--device=selected"], "Cannot read"),
])
def test_cli_rejections(
    profile_suite: pytest.Pytester, args: list[str], message: str
) -> None:
    result = profile_suite.runpytest(*args)
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert message in result.stderr.str()


def test_legacy_command(profile_suite: pytest.Pytester) -> None:
    result = profile_suite.runpytest(
        "--run-hardware", "--target-host=selected.invalid",
        "--target-port=80", "--tcp-timeout=1.25",
    )
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize("extra", [[], ["-x"]], ids=["default", "stop-first"])
@pytest.mark.parametrize(
    "error_type", ["TimeoutError", "ConnectionRefusedError", "OSError"]
)
def test_failed_prerequisite_blocks_negative(
    profile_suite: pytest.Pytester, extra: list[str], error_type: str
) -> None:
    path = profile_suite.path / "devices.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["devices"]["selected"]["tcp_ports"] = {443: False, 23456: True}
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    test_path = profile_suite.path / "test_profile.py"
    source = test_path.read_text(encoding="utf-8")
    source += '''
from unittest.mock import call, patch

@pytest.fixture(autouse=True)
def socket_guard():
    with patch("framework.network_client.socket.create_connection",
               side_effect=ERROR_TYPE("synthetic unavailable")) as mocked:
        yield mocked
        assert mocked.call_args_list == [
            call(("selected.invalid", 23456), timeout=1.25)
        ], "Negative port must never be contacted after prerequisite failure"
'''.replace("ERROR_TYPE", error_type)
    test_path.write_text(source, encoding="utf-8")
    result = profile_suite.runpytest(
        *profile_args(), "--run-hardware", "--confirm-device-identity",
        "-k", "expected-False", *extra,
    )
    result.assert_outcomes(errors=1)
    assert "TCP setup error: known-open prerequisite port 23456" in (
        result.stdout.str()
    )
    assert "negative expectation was not evaluated" in result.stdout.str()


def test_negative_only_profile_is_usage_error(
    profile_suite: pytest.Pytester,
) -> None:
    path = profile_suite.path / "devices.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["devices"]["selected"]["tcp_ports"] = {443: False}
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    result = profile_suite.runpytest(*profile_args())
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert "at least one positive TCP expectation" in result.stderr.str()
