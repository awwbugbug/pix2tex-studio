# Pix2Tex Studio 2.0 recovery baseline

Recorded: 2026-08-20

This document records the state inherited after the interrupted 2.0 packaging
work. It is evidence for the release-freeze recovery, not proof that the build
is releasable.

## Source boundary

- Freeze branch: `codex/v2-release-freeze`
- Inherited committed source: `b419d924953a0418b093a7283e26bb28dd38b243`
- Public 1.0 baseline: `f07e6dcc3f6b5c3c808c1702fbf97c54e20eae4f`
- The public `main` branch and the `v1.0.0-rc1` tag remain unchanged.
- `packaging/Pix2TexStudio.spec` contained an inherited, uncommitted UniMERNet
  packaging change when this baseline was recorded.

## Runtime and model

- Development runtime: `D:\reasonix_project\pix2tex_project\runtime\unimernet_env`
- Runtime contents at audit: 67,354 files / 2,360,279,580 bytes
- Python: 3.10.20
- UniMERNet: 0.2.3
- PyTorch: 2.13.0
- PySide6: 6.10.1
- Model tier: `unimernet_tiny`
- Model directory contents: 15 files / 432,229,065 bytes
- `unimernet_tiny.pth` SHA-256:
  `6F7608624E2D7549C7F0F05FCFBE073AE521328CF70F1D46374D96F9881D7371`

The 1.0 rollback runtime remains separate and must not be modified during the
2.0 freeze.

## Test evidence before packaging repair

The 2.0 source passed 43 unit tests when run directly with the isolated
UniMERNet development runtime on 2026-08-20.

The inherited portable directory is not a valid release candidate:

- Directory size: 1,502,202,089 bytes across 5,287 files
- `Pix2TexStudio.exe` SHA-256:
  `600FA3A050475CA334AA6E8565EF895E79B8203117D5288F7172B4CAD130B50D`
- `Pix2TexWorker.exe` SHA-256:
  `C1D19F96571A974EB5CF81E567B37F7EC8666B303BE032D76CCC7136AF5A9EBF`
- Both executable version resources still report `1.0.0-rc1`.
- The packaged worker exits before emitting its JSON `ready` event.
- Reproduced error:

  ```text
  ModuleNotFoundError: No module named 'unicodedata'
  [PYI-...:ERROR] Failed to execute script 'pyi_rth_nltk'
  ```

- No 2.0 installer, release manifest, bundled third-party notices, or installed
  Windows acceptance evidence existed at this baseline.

## Recovered packaging failure

The inherited `dist/` and `build/` directories do not represent one successful
clean build. The portable executables were timestamped around 00:52, while the
newer Analysis/COLLECT files were produced around 01:02-01:06.

A minimal probe built with the same Python 3.10.20, PyInstaller 6.21.0, contrib
hooks 2026.6, and PyTorch 2.13.0 established the component boundary:

- PyInstaller resolved `unicodedata.pyd`, `torch._C`, and the Torch DLLs.
- The official Torch hook expanded into thousands of unrelated submodules and
  more than 9,000 collected entries.
- COLLECT then failed with Windows `WinError 206` on a deeply nested
  `torch-2.13.0.dist-info/licenses/...` destination below the Claude worktree.

The packaged worker's missing modules were therefore symptoms of a stale,
incomplete portable directory. The freeze must use a short build path and a
clean isolated build; copying missing modules into the inherited `dist/` is not
an acceptable repair.

## Freeze rule

Do not treat the inherited `dist/` directory as a successful build. Replace it
only after the failure is understood, the build can be recreated from an
isolated locked environment, and the packaged worker completes a ready → one
prediction → clean shutdown smoke test.
