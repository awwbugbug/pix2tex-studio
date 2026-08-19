from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


def canonicalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


class LicenseManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.manifest = json.loads(
            (
                cls.project_root
                / "packaging"
                / "third-party-licenses"
                / "manifest.json"
            ).read_text(encoding="utf-8")
        )

    def test_every_locked_runtime_distribution_has_a_license_entry(self) -> None:
        lock_lines = (
            self.project_root / "requirements-release.lock"
        ).read_text(encoding="utf-8").splitlines()
        expected: dict[str, str] = {}
        for raw_line in lock_lines:
            line = raw_line.strip()
            if not line or line.startswith(("#", "--")):
                continue
            name, version = line.split("==", 1)
            expected[canonicalize(name)] = version

        actual = {
            canonicalize(str(item["name"])): str(item["version"])
            for item in self.manifest
        }
        self.assertEqual(len(expected), 183)
        for name, version in expected.items():
            with self.subTest(distribution=name):
                self.assertEqual(actual.get(name), version)

    def test_manifest_represents_the_second_generation_backend(self) -> None:
        names = {canonicalize(str(item["name"])) for item in self.manifest}
        self.assertIn("unimernet", names)
        self.assertNotIn("pix2tex", names)
        self.assertNotIn("latex2sympy2", names)
        self.assertIn("mathjax", names)


if __name__ == "__main__":
    unittest.main()
