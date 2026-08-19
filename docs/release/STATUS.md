# 2.0.0rc1 acceptance status

Updated: 2026-08-20

## Passed

| Area | Evidence |
| --- | --- |
| Source regression | 58/58 automated tests passed |
| Build isolation | Python 3.10.20 build prefix; runtime lock matches; `pip check` passed |
| Model integrity | UniMERNet tiny weights matched the frozen SHA-256 |
| Versioned portable | Clean PyInstaller build; both EXEs report 2.0.0-rc1 |
| Offline packaged OCR | GUI smoke 0, nonblank result, clean Worker shutdown |
| Worker stability | 25/25 deterministic predictions, zero errors |
| Handwriting pipeline | Simulated pen stroke saved to PNG and accepted as current input |
| Windows desktop flow | One Worker, taskbar restore, second-instance handoff, close-to-tray passed |
| Isolated installer | Chinese path with spaces; install, same-path upgrade, installed OCR, and uninstall all exit 0 |
| Existing-install isolation | Desktop/start-menu shortcut hashes and v1 uninstall registry unchanged |
| Licensing | 183 locked distributions plus the MathJax override represented |

## Measured candidate artifacts

- Notice-bearing portable: 1,935,633,209 bytes, 10,257 files.
- Portable offline smoke: Worker ready 13.130 seconds; inference 0.410 seconds.
- Stability run: Worker ready 8.724 seconds; mean 0.371 seconds; p95 0.391 seconds.
- Windows integration rerun: Worker ready 8.840 seconds; one Worker process.
- Installed candidate: Worker ready 10.147 seconds; inference 0.399 seconds.
- NSIS installer: 798,090,103 bytes; Authenticode status `NotSigned`.
- Installer SHA-256: `20AE6036AE0CD15A5DDF1CB7C2E6BA2F05D8D71E0F751D122FEF39A5F53C2590`.

One Windows integration attempt immediately after repeated build/install work did
not receive a ready log event within 35 seconds. The same artifact then reached
ready in 9.12 seconds during diagnosis and 8.84 seconds on an unchanged-script
rerun. This non-reproduced stall is retained as an observation rather than
silently discarded; the independently installed fresh-directory run passed in
10.147 seconds.

## Open gates

1. Freeze and score the independently labelled 2.0 real-formula/handwriting acceptance set.
2. Test cross-monitor and negative-coordinate capture on suitable hardware.
3. Generate the final release manifest/checksum file from the committed source candidate.
4. Wait for explicit authorization before pushing, tagging, or creating a GitHub release.

The candidate remains `2.0.0rc1`; it is not final `2.0.0` while the first two
hardware/evidence gates are open.
