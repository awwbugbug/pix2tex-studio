# Reproducible Windows release build

The rollback runtime under `runtime/pix2tex_env` is read-only input. The release
uses a separate CPU-only Conda prefix and a project-local NSIS toolchain.

## Bootstrap

```powershell
.\scripts\create-build-env.ps1
.\scripts\bootstrap-nsis.ps1
```

`create-build-env.ps1` installs the exact runtime/build locks with `--no-deps`,
copies the two validated model files from the rollback runtime, and verifies:

- `weights.pth`: `A63D9141C53D266CB682FB5A8BD83BD5CBE283145E0E78EBDC0F895195A1DFAA`
- `image_resizer.pth`: `1C3820659985AD142B526490BB25C23D977176AC2073591B3BDDADA692718458`

The NSIS 3.12 ZIP is accepted only if its SHA-256 is
`56581F90DB321581C5381193D796FFFCF2D24B2F8FED2160A6C6A3BAA67F2C4F`.

## Build and verify

```powershell
.\scripts\test.ps1
.\scripts\build-portable.ps1
.\scripts\build-installer.ps1
.\scripts\test-windows-integration.ps1
.\scripts\test-worker-stability.ps1
.\scripts\create-release-manifest.ps1
```

`build-portable.ps1` replaces the active shell PATH with the isolated prefix and
Windows system directories before PyInstaller runs. This prevents base-Conda ICU
DLLs from contaminating Qt. The spec also fails closed by filtering the known
foreign ICU 73 filenames; modern Windows supplies the ICU API used by Qt.

The release artifacts are intentionally ignored by Git. Source, locks, spec,
installer script, notices, and tests are versioned; binary artifacts are attached
only after acceptance. No Authenticode certificate is configured for this private
research candidate.
