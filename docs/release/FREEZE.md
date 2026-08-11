# Pix2Tex Studio 1.0 release freeze

Freeze started: 2026-08-11

Candidate version: `1.0.0rc1`
Backend: `pix2tex 0.1.4`, CPU only

## Frozen product scope

The feature set documented in the root README is frozen. Until 1.0 is accepted, changes are limited to:

- release-blocking defects;
- OCR acceptance infrastructure and evidence;
- runtime slimming, packaging, installer, and licensing work;
- Windows compatibility and accessibility corrections;
- tests and release documentation.

New convenience features and model-backend migration are deferred until after 1.0. `PP-FormulaNet_plus-M` remains an evaluation idea only.

## Baseline

- Development runtime: `runtime/pix2tex_env`
- Runtime files: 50,136
- Runtime bytes: 2,519,488,161
- Automated checks at freeze start: 20/20 passed
- Current automated checks: 26/26 passed in both rollback and release build environments
- Git state at freeze start: the directory was not yet a Git repository
- GitHub CLI: authenticated as `awwbugbug`; no target repository selected

The development runtime is a rollback baseline. It must not be deleted or mutated to make a release build. Packaging uses a separate build environment.

## Release gates

1. OCR acceptance set is frozen before the scored run and satisfies `ACCEPTANCE.md`.
2. All automated tests pass from the release candidate source.
3. A standalone CPU build launches without Anaconda or a system Python.
4. The installer passes install, launch, upgrade, uninstall, and offline checks.
5. Windows checks cover Chinese paths, standard and high DPI, multiple monitors, taskbar restore, tray, shortcut conflicts, retry/interruption, and repeated recognition.
6. Release artifacts include version, file size, SHA-256, dependency notices, and a reproducible build record.
7. Only after all gates pass may the candidate become `1.0.0` and be pushed to GitHub.

## Current release blockers

- No user-labelled 30-image real-formula acceptance dataset has been frozen or scored yet.
- The target machine has only one monitor, so cross-monitor capture is not yet accepted.
- The final GitHub repository/remote and visibility have not been selected.

## Candidate artifacts

- Standalone one-folder CPU build: 1.36 GiB before third-party notices.
- NSIS per-user installer: approximately 445 MiB before final notice refresh.
- The installer is intentionally unsigned because no code-signing certificate is available;
  Windows SmartScreen may warn on first launch. This is acceptable for the private research
  candidate but must be disclosed.
