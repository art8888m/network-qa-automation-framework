# Network QA Automation Framework

A Python network QA portfolio project for functional testing of owned physical
devices. NET-007-02 provides a TCP client, deterministic unit tests, and one
explicitly enabled physical connectivity smoke test.

## Setup on Windows

Validated environment: Windows, PyCharm, Python 3.13.14, existing `.venv`.
Select `.venv\Scripts\python.exe` as the PyCharm project interpreter. From the
repository root in PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe -m pytest tests/unit -v
& .\.venv\Scripts\python.exe -m pytest -v
```

The default suite skips hardware tests and requires no browser packages or lab
access. Unit tests mock sockets and test the pytest safety controls in isolation.
The integration test uses a real local TCP listener on `127.0.0.1` with an
OS-assigned ephemeral port, bounded timeouts, and automatic socket cleanup.
Requirements pin direct and transitive dependencies resolved for this Windows
Python 3.13 environment; other platforms have not been validated.

## Architecture

- `framework/`: reusable clients; `NetworkClient` currently checks TCP ports.
- `tests/unit/`: deterministic socket and hardware opt-in tests.
- `tests/integration/`: deterministic TCP loopback integration test.
- `tests/connectivity/`: one opt-in physical TCP smoke test.
- `conftest.py`: shared fixtures, command-line configuration, hardware gating.
- `config/`: synthetic example profiles; YAML loading is deferred.
- `pages/`: placeholder for optional UI Page Objects.
- `docs/`: architecture and actual validation evidence.

See [architecture and evidence](docs/framework-setup.md) for the client contract,
versions, execution results, and limitations.

Registered markers: `smoke`, `unit`, `integration`, `network`, `hardware`, `ui`,
`regression`.
Unknown markers are errors. Selecting `-m hardware` alone does not enable devices.

`NetworkClient` uses standard Python logging under `framework.network_client`.
Warnings distinguish refusal, timeout, and other socket errors (numeric errno).
Debug logging records successful connections. Logs omit targets, ports, raw
exception messages, and tracebacks. Configure handlers in the caller; the client
does not change global logging settings. To run only the local integration test:

```powershell
& .\.venv\Scripts\python.exe -m pytest -m integration -v
```

## Physical smoke test

First verify ownership/authorization, actual target IP, listening TCP port, and
the active network interface. Hardware tests are read-only connection attempts;
they do not change device settings. No target address or port is assumed.

Replace both placeholders below with a verified authorized target before running:

```powershell
& .\.venv\Scripts\python.exe -m pytest tests/connectivity -v --run-hardware --target-host "<verified-host>" --target-port <verified-port> --tcp-timeout 3
```

`--run-hardware` requires a nonempty host and port 1–65535. The timeout must be
finite and positive (default: 3 seconds). Missing/invalid configuration is a
usage error. A connection failure is a failed test, not a skip or pass.

`config/devices.example.yaml` uses a reserved documentation address and is never
loaded automatically. Keep actual profiles in ignored `config/*.local.yaml` or
`config/*.local.yml`. Do not commit credentials, private configurations, captures,
or unsanitized reports. Pytest failures can include local values; review output
before sharing it.

## Optional UI and reporting

Install UI dependencies only when starting NET-007-06:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
& .\.venv\Scripts\python.exe -m playwright install chromium
```

No browser installation or UI tests are needed for core collection. UI dependency
resolution is checked separately; browser execution has not been validated.
The core includes the Allure pytest adapter. Allure report generation, its CLI,
and CI workflows are deferred to NET-007-08. Generated reports are ignored.

## Next steps

NET-007-02 is under review in [PR #2](https://github.com/art8888m/network-qa-automation-framework/pull/2).
Commit and push review fixes to `feature/NET-007-02-framework-setup` to update
the existing pull request. Re-run the default test suite and dependency checks
before pushing. Merge into `main` only after review and explicit owner approval.
After merging, NET-007-03 verifies and documents the physical lab locally.
Protocol coverage, UI automation, physical regression, reporting, and CI follow
the sequence in `AGENTS.md`.
