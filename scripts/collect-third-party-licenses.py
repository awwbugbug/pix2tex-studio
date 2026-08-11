from __future__ import annotations

import importlib.metadata
import json
import re
import shutil
from pathlib import Path


def locked_distributions(lock_path: Path) -> list[str]:
    names: list[str] = []
    for raw_line in lock_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--") or line.startswith("#"):
            continue
        names.append(re.split(r"[<>=!~]", line, maxsplit=1)[0])
    return names


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    output_root = project_root / "packaging" / "third-party-licenses"
    expected_parent = project_root / "packaging"
    if output_root.parent.resolve() != expected_parent.resolve():
        raise RuntimeError(f"Unsafe license output path: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    manifest: list[dict[str, object]] = []
    for requested_name in locked_distributions(project_root / "requirements-release.lock"):
        distribution = importlib.metadata.distribution(requested_name)
        canonical_name = distribution.metadata.get("Name", requested_name)
        destination = output_root / f"{canonical_name}-{distribution.version}"
        destination.mkdir()
        copied: list[str] = []
        for entry in distribution.files or []:
            entry_path = Path(str(entry))
            basename = entry_path.name.lower()
            if not basename.startswith(("license", "copying", "notice")):
                continue
            source = Path(distribution.locate_file(entry))
            if not source.is_file():
                continue
            target = destination / entry_path.name
            if target.exists():
                target = destination / ("__".join(entry_path.parts[-2:]))
            shutil.copy2(source, target)
            copied.append(target.name)
        if not copied:
            declared = (distribution.metadata.get("License") or "").strip()
            classifiers = distribution.metadata.get_all("Classifier") or []
            license_classifiers = [item for item in classifiers if "License ::" in item]
            fallback = [
                f"Package: {canonical_name}",
                f"Version: {distribution.version}",
                f"Declared license: {declared or 'not stated in installed metadata'}",
                *license_classifiers,
                "",
                "No standalone license file was present in the installed wheel metadata.",
            ]
            target = destination / "METADATA-LICENSE.txt"
            target.write_text("\n".join(fallback) + "\n", encoding="utf-8")
            copied.append(target.name)
        manifest.append(
            {
                "name": canonical_name,
                "version": distribution.version,
                "files": sorted(copied),
            }
        )

    override_root = project_root / "packaging" / "license-overrides"
    if override_root.is_dir():
        for override in sorted(path for path in override_root.iterdir() if path.is_dir()):
            destination = output_root / override.name
            shutil.copytree(override, destination, dirs_exist_ok=True)
            override_files = sorted(path.name for path in override.iterdir() if path.is_file())
            existing = next(
                (
                    item
                    for item in manifest
                    if f"{item['name']}-{item['version']}".casefold() == override.name.casefold()
                ),
                None,
            )
            if existing:
                existing["files"] = sorted(set(existing["files"]) | set(override_files))
            else:
                name, _, version = override.name.rpartition("-")
                manifest.append(
                    {
                        "name": name or override.name,
                        "version": version or "bundled",
                        "files": override_files,
                    }
                )

    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Collected {len(manifest)} locked runtime distributions into {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
