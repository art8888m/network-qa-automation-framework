# NET-007-02 architecture and validation

## Client contract

`NetworkClient(timeout: float = 3.0)` exposes
`check_tcp_port(host: str, port: int) -> bool`. It uses
`socket.create_connection` and a context manager to close successful sockets.
Successful TCP establishment returns `True`; timeout, refusal, resolution errors,
and other socket `OSError` failures return `False`. Invalid empty hosts, ports,
or nonpositive/nonfinite timeouts raise `ValueError`.

The module logger emits separate warnings for refusal, timeout, and other socket
errors (numeric errno only), plus a debug message on success. It never includes
target addresses, ports, raw exception messages, or tracebacks, and does not
configure global handlers. Unit tests verify categories and sensitive-value
omission while preserving the boolean contract.

The `integration` marker selects one real TCP loopback test. Its fixture binds
only `127.0.0.1` on port zero, letting the OS allocate a port. The listening
backlog permits connecting before accepting, avoiding worker threads. Connect,
accept, and receive use two-second timeouts; context managers close the listener
and accepted socket, and receipt of EOF verifies that the client closed its end.

The client uses only the standard library. Pytest handles configuration and
assertions separately through explicit fixtures. There are no automatic retries,
router defaults, configuration writes, browser imports, or abstract base classes.

## Safety and limitations

Hardware tests are skipped unless `--run-hardware` is supplied. Explicit execution
also requires a host and port. Timeout validation applies to every invocation.
Mocked tests exercise success, failure, validation, socket cleanup, and opt-in
behavior without reaching a device.

TCP success confirms connection establishment only, not application health or
device identity. The boolean interface deliberately groups socket failures;
diagnose the target, interface, firewall, DNS, and port when a smoke test fails.
Socket timeouts apply to connection attempts, not a strict overall deadline:
DNS resolution and multiple address attempts can extend elapsed time.

NET-007-02 used an illustrative profile; NET-007-03 adds validated profile loading
as described in [physical lab configuration](physical-lab.md). UI dependencies
are optional, and no UI implementation is included. Physical execution was not
validated in NET-007-02; see the linked NET-007-03 evidence for later owner runs.
Browser execution, Allure report rendering, and CI remain unvalidated/deferred.

## Dependency verification

Resolution used the existing Windows Python 3.13.14 environment and pip 26.3.
Both core and combined core/UI sets resolved successfully through pip dry runs.
Exact direct and transitive pins are in the two requirements files. UI packages
were not installed; successful resolution is not browser runtime evidence.

| Direct dependency | Pinned version | Verification |
| --- | --- | --- |
| pytest | 9.2.0 | Installed; suite executed |
| requests | 2.34.2 | Installed; dependency check passed |
| PyYAML | 6.0.4 | Installed; Windows CPython 3.13 wheel |
| allure-pytest | 2.16.2 | Installed; loaded during test execution |
| pytest-playwright | 0.10.0 | Combined core/UI resolver check only |
| playwright | 1.65.2 | Combined core/UI resolver check only |

## Execution evidence

Executed on 2026-11-26 using `.venv\Scripts\python.exe` from the repository root.
Core installation (`-m pip install -r requirements.txt`) succeeded. The dry-run
commands were `-m pip install --dry-run --report .venv/core-resolution.json pytest
requests PyYAML allure-pytest` and `-m pip install --dry-run --report
.venv/ui-resolution.json -r requirements.txt pytest-playwright playwright`.
Resolver reports remain ignored inside `.venv`.

| Command arguments | Actual result |
| --- | --- |
| `-m pytest tests/unit -v` | 22 passed in 0.77 seconds |
| `-m pytest -m integration -v` | 1 passed, 23 deselected in 0.23 seconds |
| `-m pytest --collect-only -q` | 24 tests collected in 0.11 seconds |
| `-m pytest -q` | 23 passed, 1 skipped in 0.67 seconds |
| `-m pip check` | No broken requirements found |
| `-m pip show playwright pytest-playwright` | Neither installed (expected exit 1) |
| `git diff --check` | Passed |

The skipped test is the physical TCP smoke test. The opt-in unit test exercises
only a synthetic target fixture and does not make a connection. No physical
device test, UI test, browser download, or router configuration change occurred.
