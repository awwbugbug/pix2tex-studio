# Pix2Tex Studio 2.0.0rc1

This is the local Windows release candidate for the second-generation
recognition backend. It is not published yet.

## Highlights

- Replaces pix2tex with the CPU-only UniMERNet tiny model.
- Adds an integrated pen/eraser handwriting board with undo and clear actions.
- Converts completed drawings to ordinary image input before recognition.
- Automatically inverts light-on-dark captures and crops excess whitespace.
- Retains the established PySide6/Qt Quick interface, formula preview, output
  modes, history, diagnostics, global shortcut, tray, and single-instance flow.
- Ships a self-contained model and runtime; no Anaconda, system Python, CUDA,
  cloud service, or runtime network access is required.

## Candidate verification so far

- 58 automated tests passed.
- Clean one-folder portable build completed from the isolated CPU build prefix.
- Packaged GUI smoke test passed.
- Packaged Worker loaded offline, recognized the regression fixture, and shut down cleanly.
- A 25-request deterministic stability run completed with zero errors.
- Isolated Chinese-path install, same-path upgrade, installed OCR, and uninstall passed.
- Taskbar restore, single-instance handoff, and close-to-tray integration passed.
- Generated third-party notices represent the locked 2.0 runtime and model stack.

The candidate installer is unsigned and measures 798,090,103 bytes. Its
SHA-256 is `20AE6036AE0CD15A5DDF1CB7C2E6BA2F05D8D71E0F751D122FEF39A5F53C2590`.

## Known candidate limitations

- The installer is unsigned, so Windows SmartScreen may warn.
- The independently labelled real-input acceptance set has not yet been scored.
- Cross-monitor and negative-coordinate capture require suitable hardware and
  remain an open gate on a single-monitor machine.
- CPU model loading is intentionally separated from the UI and can take several
  seconds on a cold process.

## Licensing

Pix2Tex Studio's original application code is licensed under MIT. UniMERNet
code and the bundled tiny model declare Apache-2.0. Other bundled components
remain under their respective licenses in `third-party-licenses`.
