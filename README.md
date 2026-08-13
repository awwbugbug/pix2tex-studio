# Pix2Tex Studio

Pix2Tex Studio is a local-first Windows desktop application for turning formula screenshots and images into editable LaTeX. The development baseline is CPU-only and uses the cloned environment under `runtime/pix2tex_env`.

This is an independent community project built around the open-source
[pix2tex/LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR) model. It is not
affiliated with or endorsed by the upstream pix2tex maintainers.

## Install on Windows

Download the latest Windows installer from
[GitHub Releases](https://github.com/awwbugbug/pix2tex-studio/releases). The
installer contains the CPU inference runtime and model weights, so Anaconda,
Python, CUDA, and an internet connection are not required at runtime.

The current `1.0.0rc1` installer is unsigned. Windows may therefore display a
SmartScreen warning. Verify the SHA-256 value published with the release before
running it.

## Development run

```powershell
.\scripts\run-dev.ps1
```

The QML interface opens at a compact `980 × 640`. Torch and pix2tex load in a separate worker process, so the window remains responsive during cold start.

## Implemented

- PySide6 + Qt Quick/QML desktop interface
- real region capture on the display under the cursor, with Esc cancellation
- open, paste, and drag-and-drop image input
- isolated CPU inference with Temperature support
- optional small-image enhancement, enabled by default and persisted locally
- Retry and interrupt-by-worker-restart
- raw and formatted output editors
- Raw, inline LaTeX, display LaTeX, and SymPy output modes
- local MathJax preview loaded only after a result exists
- automatic or manual clipboard copy
- local recognition history
- per-entry history source copy and deletion
- configurable 50/100/200-entry history retention with reference-safe cache cleanup
- rotating crash logs and privacy-safe diagnostic ZIP export
- system, light, and dark themes
- configurable Windows-wide capture shortcut (`Ctrl+Shift+A`, `Alt+S`, or `Ctrl+A`)
- single-instance activation and a system tray with capture, show, and exit actions
- close-to-tray behavior that keeps the CPU model warm
- Windows DWM rounded-corner preference for the real frameless window

`Ctrl+A` remains available inside the application. The Windows-wide shortcut defaults to
`Ctrl+Shift+A` because registering global `Ctrl+A` overrides Select All in other programs.
The global shortcut can be changed on the Settings page.

The full parity checklist for the original pix2tex GUI is in `docs/design/original-gui-parity.md`.

The possible future evaluation of `PP-FormulaNet_plus-M` is recorded in
`docs/design/model-backend-evaluation.md`. The current backend remains pix2tex;
no Paddle migration has been approved or performed.

## Verification

```powershell
.\scripts\test.ps1
.\scripts\render-preview.ps1
```

## Release build

The release uses a separate CPU-only build environment and never packages the rollback
`runtime/pix2tex_env` directory directly.

```powershell
.\scripts\build-portable.ps1
.\scripts\build-installer.ps1
.\scripts\test-windows-integration.ps1
.\scripts\test-worker-stability.ps1
```

The per-user NSIS installer is written under `installer/output/`. It installs to
`%LOCALAPPDATA%\Programs\Pix2Tex Studio` by default, needs no Anaconda or system
Python, and preserves local history/settings when uninstalled.

## Release status

The feature set is frozen as `1.0.0rc1`. A standalone build and installer now exist.
Release gates and current blockers are
tracked in `docs/release/FREEZE.md`; the frozen OCR and Windows protocol is in
`docs/release/ACCEPTANCE.md`. The candidate is not a final 1.0 release until
those gates pass.

## Licensing and attribution

Pix2Tex Studio's original application code is available under the
[MIT License](LICENSE). Bundled third-party components remain subject to their
own licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the
corresponding `packaging/third-party-licenses/` directory for details.
