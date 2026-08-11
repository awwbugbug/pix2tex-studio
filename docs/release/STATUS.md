# 1.0.0rc1 acceptance status

Updated: 2026-08-11

## Passed

| Area | Evidence |
| --- | --- |
| Source regression | 26/26 tests in the rollback runtime and isolated release build environment |
| Frozen GUI | GUI-subsystem EXE, QML smoke exit 0, no foreign Conda ICU DLLs |
| Frozen OCR | Package-local weights, exact smoke prediction, 0.199-0.241 s inference |
| Worker stability | 25/25 consecutive predictions, 0 errors, p95 0.171 s |
| Normal desktop flow | one worker, 8.85 s ready, single-instance restore, close-to-tray |
| Offline install | invalid HTTP/HTTPS proxy plus offline flags; GUI and OCR still passed |
| Installer | per-user install and uninstall exit 0; shortcuts and registry verified |
| Chinese path | install, GUI, OCR, and uninstall passed under `安装测试\Pix2Tex Studio` |
| DPI | 125% and 200% rendered and visually checked without clipping or overlap |
| User data | uninstall removed program state but preserved `%LOCALAPPDATA%\Reasonix\Pix2TexStudio` |
| Licensing | 55 locked runtime distributions represented; PySide/Qt and MathJax terms included |

## Measured artifacts

- Notice-bearing portable directory: 1,429,739,639 bytes, 8,905 files.
- Zero-warning notice-bearing NSIS installer: 466,976,568 bytes.
- Installer SHA-256: `19CD4A71A16AFC8B412C3A0368DEEAEBF78DC5F003EC5410A9ECE9E45645402A`.
- Final install: 73.3 seconds; same-path upgrade: 56.39 seconds; uninstall: exit 0.
- New-directory first model readiness: 26.47-27.02 seconds.
- Subsequent cold-process readiness: 5.43-6.64 seconds.

All current sizes and SHA-256 values are regenerated in
`release-evidence/release-manifest.json`.

## Blocked or not yet accepted

1. The frozen 30-image, independently labelled real research formula set does not exist yet.
   A single regression fixture proves the pipeline and a whitespace fix, not broad OCR accuracy.
2. This Windows machine exposes only one 2560x1440 display. Multi-monitor and negative-coordinate
   region capture therefore remain untested.
3. No Git remote is configured. GitHub publication is deliberately the final step.

The candidate must remain `1.0.0rc1`; it is not honest to tag it `1.0.0` while these gates are open.
