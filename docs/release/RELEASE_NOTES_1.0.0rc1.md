# Pix2Tex Studio 1.0.0rc1

This is the first public Windows release candidate of Pix2Tex Studio, an
independent local-first desktop application built around the open-source
pix2tex/LaTeX-OCR model.

## Highlights

- Native PySide6 and Qt Quick interface with light, dark, and system themes.
- Region capture, open, paste, drag-and-drop, source zoom, retry, and cancel.
- Persistent background CPU inference with local MathJax formula previews.
- Raw, inline LaTeX, display LaTeX, and SymPy output modes.
- Local history with rendered previews, copy/delete actions, retention, and
  cache cleanup.
- Windows-wide capture shortcut, single-instance activation, system tray, and
  native window behavior.
- Per-user installer with a self-contained CPU runtime and model weights.
- No Anaconda, system Python, CUDA, cloud service, or runtime network access
  required.

## Verification completed

- 30 automated tests passed.
- Frozen GUI startup smoke test passed.
- Frozen worker completed 25 consecutive OCR requests with zero errors.
- Offline installed-build OCR smoke test passed.
- Install, same-path upgrade, uninstall, user-data preservation, and Chinese
  installation path checks passed.
- 125% and 200% DPI render checks passed on the available Windows machine.

## Known release-candidate limitations

- The installer is not digitally signed, so Windows SmartScreen may warn.
- The frozen 30-image independently labelled real-formula acceptance set has
  not yet been completed.
- Cross-monitor capture has not been accepted because the test machine exposes
  only one monitor.
- This is a CPU-only build. The first model startup can take noticeably longer
  than later starts.

## Integrity

Verify the installer against the `SHA256SUMS.txt` release asset before running
it.

- File: `Pix2TexStudio-1.0.0-rc1-Setup.exe`
- Size: `466971154` bytes
- SHA-256: `7103004B1267C898562F14C3BA304156E6493260FBEF14C1AA5BBB3A6769C861`

## Licensing

Pix2Tex Studio's original application code is licensed under MIT. Bundled
third-party software remains under its respective license; the installer and
source tree include the corresponding notices and license texts.
