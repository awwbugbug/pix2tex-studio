# Pix2Tex Studio 2.0 release freeze

Freeze started: 2026-08-20

Candidate version: `2.0.0rc1` (`2.0.0-rc1` in Windows resources and filenames)

Backend: UniMERNet 0.2.3 tiny, CPU only

## Frozen product scope

The feature set documented in the root README is frozen. Relative to the public
1.0.0rc1 release, 2.0 replaces pix2tex with UniMERNet and adds handwriting input,
dark-background inversion, and content-aware cropping. Until the candidate is
accepted, changes are limited to release-blocking defects, tests, packaging,
licensing, compatibility corrections, and release evidence.

The public `main` branch, `v1.0.0-rc1` tag, and published 1.0 release are not
modified by this local freeze.

## Reproducible baseline

- Development runtime: `unimernet_env` under the selected runtime root.
- Isolated build runtime: `unimernet_build_env` under the selected runtime root.
- Python 3.10.20, UniMERNet 0.2.3, Torch 2.13.0 CPU, PySide6 6.10.1.
- Model: UniMERNet tiny, 430,075,701-byte weights file.
- Model SHA-256: `6F7608624E2D7549C7F0F05FCFBE073AE521328CF70F1D46374D96F9881D7371`.
- Exact runtime dependency lock: 183 distributions.
- Automated source checks at freeze: 56/56 passed.
- Clean packaged GUI and offline Worker single-image smoke test passed.

The development runtime and model directory are read-only release inputs. The
portable app is built only from the isolated build environment.

## Release gates

1. The 2.0 OCR acceptance set is frozen before scoring and satisfies `ACCEPTANCE.md`.
2. All automated tests pass from the release candidate source.
3. A clean standalone CPU build launches without Anaconda or system Python.
4. The installer passes install, launch, same-path upgrade, uninstall, and offline checks.
5. Windows checks cover Chinese paths, DPI, window/tray behavior, shortcuts,
   capture, handwriting, retry/interruption, and repeated recognition.
6. Artifacts include version metadata, sizes, SHA-256, dependency notices, and
   a reproducible release manifest.
7. The candidate is committed and reviewed locally before any push, tag, or release.

## Current open gates

- The independently labelled real-formula and handwriting acceptance set has not
  yet been frozen and scored for UniMERNet.
- Cross-monitor and negative-coordinate capture still require a multi-monitor machine.
- The versioned 2.0 portable and installer must be rebuilt after this identity freeze.
- Final push, tag, and GitHub release require separate explicit authorization.

The candidate remains `2.0.0rc1`; it must not be described as final `2.0.0`
while these gates are open.
