# Changelog

All notable changes to Pix2Tex Studio are recorded here.

## [2.0.0] - 2026-08-28

First formal 2.0 release: the old-Word-compatible, optimized build.

### Changed

- Finalized the Word output mode against the LaTeX subset older Microsoft Word
  actually renders (empirically determined, since Word converts to OMML):
  - Double-bar norms (`\|`, `\lVert`, `\rVert`) now emit the named `\Vert` — old
    Word renders `\Vert` but treats the `\|` shorthand as a single bar. This
    supersedes rc3's `\|` → `\lVert` mapping, which older Word rendered as text.
  - Single-bar `\lvert`/`\rvert` fold to `|` (Word shows the named forms as text).
  - Bold font commands (`\mathbf`/`\boldsymbol`) are dropped to plain letters,
    because old Word cannot render a bold run together with `\Vert`; the double
    bar is kept in preference to the (cosmetic) bold.
  - Redundant grouping braces (e.g. a stray `{}` inside `\left|...\right|`) are
    removed, which is what lets such fractions render — all without breaking a
    command/letter boundary.
- 2.0.0rc2 remains published as the lighter-constraint build for newer Word.

## [2.0.0rc3] - 2026-08-24

### Changed

- The Word output mode now constrains the LaTeX toward Microsoft Word's
  supported subset (which Word converts to OMML), so more formulas render on
  stricter/older Word versions. It folds OCR Unicode contamination to ASCII
  (curly quotes/prime → `'`, Unicode minus/dashes → `-`, full-width brackets →
  ASCII, stripped NBSP/zero-width), normalizes `\prime` → `'` and scalable
  `|`/`\|` → `\lvert`/`\lVert`, and removes always-redundant `{{...}}` — without
  breaking command/letter boundaries. The Unicode folding also feeds SymPy.
- 2.0.0rc2 remains published as the lighter-constraint build for newer Word.

## [2.0.0rc2] - 2026-08-21

### Added

- "Word" output mode (next to Raw): emits compact, delimiter-free LaTeX for
  Microsoft Word's equation input — unwraps UniMERNet's single-row `array`,
  drops layout-only commands, and collapses token spaces while keeping the space
  that ends a command name before a letter (so `\sin x` stays `\sin x`).

### Fixed

- SymPy output now handles the model's `array`-wrapped predictions: the raw
  LaTeX is cleaned before it reaches the SymPy parser, so real formulas convert
  instead of failing.

## [Unreleased] - 2.0.0-dev

### Changed

- Replaced the pix2tex 0.1.4 backend with UniMERNet (image→LaTeX, CPU-first,
  bundled `unimernet_tiny`); the OCR worker keeps the same JSONL contract, so the
  rest of the app is unchanged. Runs from an isolated `runtime/unimernet_env`.
- Removed the pix2tex-specific Temperature control and small-image-enhancement
  toggle from the UI and controller.

### Added

- Pen/canvas handwriting input: draw a formula and recognize it through the same
  image pipeline (pen/eraser tools with a circle eraser cursor, undo, clear).
- Automatic dark-background inversion and content cropping in the worker, fixing
  poor recognition of black-background formulas (also present in 1.0's capture).
- Post-processing that drops layout-only `\limits`/`\nolimits` so handwritten
  integrals/sums render compactly.

### Fixed

- Region capture no longer bakes the overlay's white selection border into the
  saved image (it grabbed the composited screen); it now crops from a clean
  pre-capture, which was the main cause of dark-background recognition failures.

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
- Unified the executable, installer, window, and tray icon as a dark rounded square with a white integral symbol.
- Shortened the desktop shortcut name to `pix2tex` while retaining `Pix2Tex Studio` as the product name.
- Added offline installed-build, Chinese-path, DPI, single-instance, tray, and stability checks.
- Added reproducible locked runtime inputs and complete third-party license collection.

### Remaining before final 1.0

- Formula accuracy has not yet passed the frozen 30-image real-input acceptance set.
- Multi-monitor capture cannot be accepted on the current single-monitor machine.
