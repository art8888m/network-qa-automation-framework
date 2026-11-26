"""Exercise pytest safety controls without opening sockets."""

from pathlib import Path

import pytest

pytest_plugins = ["pytester"]
pytestmark = pytest.mark.unit


@pytest.fixture
def isolated_suite(pytester: pytest.Pytester) -> pytest.Pytester:
    root = Path(__file__).resolve().parents[2]
    pytester.makeconftest((root / "conftest.py").read_text(encoding="utf-8"))
    pytester.syspathinsert(root)
    pytester.makeini("[pytest]\nmarkers =\n    hardware: physical test")
    pytester.makepyfile(
        "import pytest\n"
        "@pytest.mark.hardware\n"
        "def test_target(hardware_target):\n"
        "    assert hardware_target == ('example.invalid', 12345)\n"
    )
    return pytester


@pytest.mark.parametrize("args", [[], ["-m", "hardware"]])
def test_default_skips_hardware(
    isolated_suite: pytest.Pytester, args: list[str]
) -> None:
    result = isolated_suite.runpytest(*args)
    result.assert_outcomes(skipped=1)


def test_explicit_opt_in(isolated_suite: pytest.Pytester) -> None:
    result = isolated_suite.runpytest(
        "--run-hardware", "--target-host=example.invalid", "--target-port=12345"
    )
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize(
    "args, message",
    [
        (["--run-hardware"], "requires --target-host and --target-port"),
        (
            ["--run-hardware", "--target-host=example.invalid", "--target-port=0"],
            "--target-port must be between",
        ),
        (["--tcp-timeout=nan"], "--tcp-timeout must be finite and positive"),
    ],
)
def test_invalid_configuration(
    isolated_suite: pytest.Pytester, args: list[str], message: str
) -> None:
    result = isolated_suite.runpytest(*args)
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert message in result.stderr.str()
