# Agent instructions — Network QA Automation Framework

## Goal and scope
Build a reproducible Python network QA portfolio MVP (NET-007), targeting early December 2026. Demonstrate actual functional testing of owned physical network devices, not production SD-WAN or enterprise switch validation. Advanced routing, failover labs, firmware modifications and mobile testing are deferred.

## Stack and structure
- Python, pytest, requests, socket, PyYAML; Playwright with pytest-playwright for UI; Allure for reporting; GitHub Actions for deterministic hardware-independent tests.
- Proposed layout: config/ (sanitized example device profiles), framework/ (network, DNS and HTTP clients), pages/ (Page Objects), tests/ (unit, connectivity, DNS, DHCP, HTTP and UI), conftest.py, pytest.ini, requirements.txt and requirements-ui.txt.
- Keep browser dependencies optional and ensure core test collection works without them. Use explicit fixtures, parametrization, type hints, bounded timeouts and actionable assertions. Prefer simple abstractions over premature complexity.

## Lab and safety
- Initial targets: owned TP-Link TL-WR740N and TECNO TR118, tested sequentially. ThinkPad is the primary development machine; Acer may run UI tests. Intel Atom is optional later; do not disrupt existing Raspberry Pi workloads.
- Verify actual device IPs, ports, firmware capabilities and network interface before testing. Do not assume HTTPS, API, WAN or reboot support.
- Default to read-only tests; configuration changes and disruptive tests require explicit opt-in, isolation and recovery plans.
- Only test authorized targets. Never commit credentials, SIM identifiers, private network configurations or unsanitized captures. Keep local configuration and secrets ignored. Use synthetic examples in public docs.
- Public repository content, including README files, documentation, code comments, commit messages, pull request descriptions, and review comments, must not contain links to the owner's private Trello workspace, boards, or cards. Internal task identifiers such as NET-007-03 are allowed.

## Testing and evidence
- Cover ICMP/TCP connectivity, DNS, DHCP lease/configuration, HTTP and supported TLS, controlled negative cases and read-only management UI.
- Separate deterministic unit/integration tests from physical hardware tests using registered pytest markers and explicit hardware opt-in. CI must not depend on private lab access.
- Do not fabricate results or silently convert failures into passes. Distinguish skipped, unsupported, blocked and failed scenarios. Record commands, environment, actual results and limitations.
- Run relevant tests before proposing changes; report tests not run and why. Sanitize logs, screenshots and reports.

## Workflow
- GitHub is the source of truth for committed code; Trello tracks delivery. Read current repository files and relevant ticket before implementation.
- Use small task-scoped branches and commits referencing NET-007 ticket IDs. Review changes before merging to main; do not merge without owner approval.
- Codex implements in the IDE; ChatGPT can review repository changes and propose architecture or documentation. The owner validates physical hardware and approves decisions.
- Keep README in English and document setup, test commands, architecture, actual evidence and limitations. Update documentation when behavior changes.
- MVP sequence: NET-007-01 repository; 02 framework setup; 03 physical lab configuration; 04 TCP/IP/DNS/DHCP; 05 HTTP/TLS/negative tests; 06 Playwright UI; 07 physical regression and packet analysis; 08 Allure and CI; 09 documentation and portfolio release.
- Prioritize a small working demo over test count or optional tooling. Jenkins, mobile devices and advanced virtual networking must not block the MVP.
