import os
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


sys.setrecursionlimit(sys.getrecursionlimit() * 5)


project_root = Path(SPECPATH).parent
source_root = project_root / "src"
entrypoint = source_root / "pix2tex_app" / "__main__.py"
worker_entrypoint = source_root / "pix2tex_app" / "worker_entry.py"

# UniMERNet is a LAVIS-style registry package: its models/tasks/processors are
# imported dynamically, so pull all submodules and its bundled yaml configs.
unimernet_datas = collect_data_files("unimernet")
metadata_datas = []
for distribution in ("unimernet", "transformers", "timm", "torch", "torchvision"):
    metadata_datas += copy_metadata(distribution)

# Bundle the tiny weights so the frozen worker's package-local default resolves
# (worker._model_dir -> pix2tex_app/models/unimernet_tiny). The weights live
# outside the worktree, so allow an env override and fall back to runtime/.
model_dir = Path(
    os.environ.get("PIX2TEX_UNIMERNET_MODEL_DIR")
    or (project_root / "runtime" / "unimernet_models" / "unimernet_tiny")
)
weight_datas = [
    (str(item), "pix2tex_app/models/unimernet_tiny")
    for item in model_dir.iterdir()
    if item.is_file()
]

common_datas = [
    (str(source_root / "pix2tex_app" / "ui"), "pix2tex_app/ui"),
    *unimernet_datas,
    *weight_datas,
    *metadata_datas,
]
common_hiddenimports = [
    "antlr4",
    "latex2sympy2",
    "transformers",
    "timm",
    "cv2",
    "albumentations",
    *collect_submodules("unimernet"),
]


def without_foreign_conda_icu(entries):
    """Use Windows' ICU API instead of accidentally bundling base-Conda ICU 73."""
    blocked = {"icuuc.dll", "icudt73.dll"}
    return [entry for entry in entries if str(entry[0]).lower() not in blocked]

common_excludes = [
    "PyQt5",
    "PyQt6",
    "tkinter",
    "tensorflow",
    "wandb",
    "streamlit",
    "IPython",
    "notebook",
    "jupyterlab",
]

main_analysis = Analysis(
    [str(entrypoint)],
    pathex=[str(source_root)],
    binaries=[],
    datas=common_datas,
    hiddenimports=common_hiddenimports,
    excludes=common_excludes,
    noarchive=False,
    optimize=1,
)
main_analysis.binaries = without_foreign_conda_icu(main_analysis.binaries)
main_pyz = PYZ(main_analysis.pure)
main_exe = EXE(
    main_pyz,
    main_analysis.scripts,
    [],
    exclude_binaries=True,
    name="Pix2TexStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(project_root / "packaging" / "pix2tex-studio.ico"),
    version=str(project_root / "packaging" / "version_info.txt"),
)

worker_analysis = Analysis(
    [str(worker_entrypoint)],
    pathex=[str(source_root)],
    binaries=[],
    datas=common_datas,
    hiddenimports=common_hiddenimports,
    excludes=common_excludes,
    noarchive=False,
    optimize=1,
)
worker_analysis.binaries = without_foreign_conda_icu(worker_analysis.binaries)
worker_pyz = PYZ(worker_analysis.pure)
worker_exe = EXE(
    worker_pyz,
    worker_analysis.scripts,
    [],
    exclude_binaries=True,
    name="Pix2TexWorker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    icon=str(project_root / "packaging" / "pix2tex-studio.ico"),
    version=str(project_root / "packaging" / "version_info.txt"),
)

bundle = COLLECT(
    main_exe,
    worker_exe,
    main_analysis.binaries,
    main_analysis.datas,
    worker_analysis.binaries,
    worker_analysis.datas,
    strip=False,
    upx=False,
    name="Pix2TexStudio",
)
