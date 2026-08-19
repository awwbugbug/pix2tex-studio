# Reproducible Windows 2.0 release build

The release uses separate CPU-only development and build prefixes. The runtime
root may be supplied with `-RuntimeRoot` or `PIX2TEX_RUNTIME_ROOT`; otherwise the
scripts use the repository's `runtime` directory.

Because PyInstaller and Torch produce deeply nested paths, use a short source
worktree path. This is a functional requirement on Windows: the interrupted
long-path build failed with `WinError 206`, while the same locked environment
succeeded from the short release worktree.

## Bootstrap

```powershell
.\scripts\create-build-env.ps1 -RuntimeRoot D:\path\to\runtime
.\scripts\bootstrap-nsis.ps1
```

The isolated build environment is Python 3.10.20 with the exact packages in
`requirements-release.lock` and `requirements-build.txt`. The UniMERNet tiny
weights must match:

`6F7608624E2D7549C7F0F05FCFBE073AE521328CF70F1D46374D96F9881D7371`

The NSIS 3.12 ZIP is accepted only if its SHA-256 is
`56581F90DB321581C5381193D796FFFCF2D24B2F8FED2160A6C6A3BAA67F2C4F`.

## Build and verify

```powershell
$runtime = 'D:\path\to\runtime'
.\scripts\test.ps1 -RuntimeRoot $runtime
.\scripts\build-portable.ps1 -RuntimeRoot $runtime
.\scripts\test-installed-release.ps1 `
  -InstallDir .\dist\Pix2TexStudio `
  -Fixture D:\path\to\worker-fixture.png
.\scripts\test-worker-stability.ps1 `
  -Fixture D:\path\to\worker-fixture.png
.\scripts\build-installer.ps1 -RuntimeRoot $runtime
.\scripts\test-windows-integration.ps1
.\scripts\create-release-manifest.ps1 -RuntimeRoot $runtime
```

`build-portable.ps1` replaces the shell PATH with the isolated prefix and
Windows system directories before PyInstaller runs. The frozen Worker embeds
the model and dynamically loaded Transformers configuration modules. The
packaged-worker tests force offline mode and fail on timeout, invalid protocol
events, blank LaTeX, or a non-zero process exit.

The portable directory and installer are intentionally ignored by Git. Source,
locks, spec, NSIS script, notices, tests, and release documentation are
versioned. The installer is unsigned because no Authenticode certificate is
configured; this must remain disclosed with the release candidate.
