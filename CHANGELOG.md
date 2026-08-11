# Changelog

All notable changes to Pix2Tex Studio are recorded here.

## [1.0.0rc1] - 2026-08-11

### Release freeze

- Froze the feature set for the first local Windows release candidate.
- Preserved the CPU-only pix2tex 0.1.4 backend and independent rollback runtime.
- Added release, OCR-accuracy, packaging, and Windows acceptance gates.

### Included

- PySide6 and Qt Quick desktop interface with light, dark, and system themes.
- Region capture, open, paste, drag-and-drop, source zoom, retry, and interruption.
- Persistent background CPU inference and local MathJax formula preview.
- Raw, inline, display, and SymPy output with clipboard integration.
- Local history with rendered previews, per-entry copy/delete, retention, and cache cleanup.
- Global capture shortcut, single-instance activation, tray behavior, and native Windows window transitions.
- Rotating crash logs and privacy-safe diagnostic export.

### Release engineering

- Added a CPU-only PyInstaller one-folder build with separate GUI and OCR worker executables.
- Added a per-user NSIS installer, uninstall registration, and Windows shortcuts.
- Added offline installed-build, Chinese-path, DPI, single-instance, tray, and stability checks.
- Added reproducible locked runtime inputs and complete third-party license collection.

### Remaining before final 1.0

- Formula accuracy has not yet passed the frozen 30-image real-input acceptance set.
- Multi-monitor capture cannot be accepted on the current single-monitor machine.
