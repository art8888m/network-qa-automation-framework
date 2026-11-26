# Network QA Automation Framework

A Python network QA portfolio project for functional testing of owned physical
devices. NET-007-03 adds validated YAML profiles and selected-device TCP
expectations to the reusable client and explicitly enabled hardware tests.

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
- `framework/device_config.py`: safe YAML loading and validated profiles.
- `tests/unit/`: deterministic socket and hardware opt-in tests.
- `tests/integration/`: deterministic TCP loopback integration test.
- `tests/connectivity/`: opt-in TCP checks parametrized over selected ports.
- `conftest.py`: shared fixtures, command-line configuration, hardware gating.
- `config/`: synthetic example profiles and ignored local device configuration.
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

### Configuration-driven TCP expectations

Copy the example locally, then replace its host values with verified management
addresses. `config/devices.yaml` and `config/*.local.yaml` / `*.local.yml` are
ignored. Never commit actual profiles, credentials, or unsanitized output.

```powershell
Copy-Item config/devices.example.yaml config/devices.yaml
```

The example uses this schema (see the file for both device profiles):

```yaml
devices:
  tplink_example:
    host: "192.0.2.1"  # Documentation address; replace locally before execution.
    timeout: 3.0
    tcp_ports:
      80: true
      443: false
```

Each profile requires a nonempty string host, finite positive numeric timeout,
and a nonempty mapping of integer TCP ports (1-65535) to boolean accessibility.
Unknown fields and invalid values are errors. Profile names are exact selectors.
Configuration is loaded only when explicitly requested, never discovered.
Profiles with negative expectations must include at least one positive TCP
expectation; negative-only profiles are rejected before execution.

After verifying the connected device's physical identity, management address,
Ethernet interface, and route, select exactly one profile:

```powershell
& .\.venv\Scripts\python.exe -m pytest tests/connectivity -v --run-hardware --device-config config/devices.yaml --device tplink_example --confirm-device-identity
```

Disconnect the previous device before connecting the next. Both devices may
share the same management IP. Verify identity again before selecting the TECNO
profile (`--device tecno_example`). The acknowledgement records operator
confirmation; it does not authenticate the device. Do not run parallel sessions
or parallel pytest workers against the physical lab.

`--device-config` and `--device` must appear together, once each. Wildcard/all
selection is unsupported. Profile options conflict with `--target-host`,
`--target-port`, and explicitly supplied `--tcp-timeout`; the profile defines
the timeout. `--confirm-device-identity` requires profile selection and is
mandatory for profile execution with `--run-hardware`. Existing explicit host/
port commands remain supported without the acknowledgement flag.

Supplying a profile or `-m hardware` still leaves hardware tests skipped unless
`--run-hardware` is present. To inspect cases without connecting:

```powershell
& .\.venv\Scripts\python.exe -m pytest tests/connectivity --collect-only -q --device-config config/devices.yaml --device tplink_example
```

`true` expects TCP establishment; `false` expects a socket failure. Before each
negative case, a function-scoped fixture connects to the lowest-numbered port
marked `true` in that selected profile. The port is derived from configuration,
not hardcoded. If it cannot connect, pytest reports a clear **setup ERROR** and
does not check the negative port. The prerequisite is freshly checked for each
negative case, even when selected alone or reordered; it does not depend on
positive tests running first or on `-x`.

A negative port may return `False` for refusal, timeout, or another socket error.
Its prerequisite proves reachability only at the time of that earlier connection;
the device or network could fail between checks. A negative pass therefore does
not prove an explicit refusal or correct device identity. The acknowledgement
still requires manual identity verification. TCP 443 accessibility does not
prove HTTPS support. Unexpected accessibility results fail normally.

For the local profiles, execute the following separately after verifying and
connecting the intended device. Disconnect TP-Link before connecting TECNO:

```powershell
& .\.venv\Scripts\python.exe -m pytest tests/connectivity -v --run-hardware --device-config config/devices.yaml --device tplink_wr740n --confirm-device-identity
& .\.venv\Scripts\python.exe -m pytest tests/connectivity -v --run-hardware --device-config config/devices.yaml --device tecno_tr118 --confirm-device-identity
```

These local profile names correspond to the operator's ignored `devices.yaml`;
the public example uses the `_example` names shown earlier.

Read [physical lab evidence and procedure](docs/physical-lab.md). Pytest failures
can include local values in tracebacks; sanitize output before publishing it.

### Verified physical capabilities

On November 26, 2026, the owner manually validated both device profiles:
TECNO TR118 passed both expected-open TCP checks (2 passed in 0.07s); TP-Link
TL-WR740N passed its expected-open and expected-inaccessible checks (2 passed in
2.13s). With TP-Link deliberately disconnected, pytest reported 1 failed and
1 setup error in 6.25s: the known-open prerequisite was unreachable and the
negative port was not evaluated. This expected failure-injection result verifies
the safeguard; it is not an unexpected regression or a passing connectivity run.

These are lab observations, not vendor guarantees. All identity, TCP-versus-TLS,
socket-error interpretation, and between-probe reachability limitations above
still apply. No additional physical execution was performed for PR preparation.

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

NET-007-02 was merged through PR #2. NET-007-03 is prepared for independent PR
review from `feature/NET-007-03-device-configuration` into `main`, with owner
physical validation documented. Review fixes go to the same feature branch;
merge requires explicit owner approval. Additional physical runs require
operator verification and explicit opt-in. DNS/DHCP protocol coverage, HTTP/TLS,
UI, physical regression, reporting, and CI follow the sequence in `AGENTS.md`.
