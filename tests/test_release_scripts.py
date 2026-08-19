from __future__ import annotations

import unittest
from pathlib import Path


class ReleaseScriptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]

    def _script(self, name: str) -> str:
        return (self.project_root / "scripts" / name).read_text(encoding="utf-8")

    def test_installed_worker_smoke_has_timeouts_and_validates_protocol(self) -> None:
        script = self._script("test-installed-release.ps1")
        self.assertIn("ReadLineAsync", script)
        self.assertIn("$ready.type -ne 'ready'", script)
        self.assertIn("$prediction.type -ne 'result'", script)
        self.assertIn("returned blank LaTeX", script)

    def test_worker_release_scripts_do_not_send_retired_pix2tex_options(self) -> None:
        for name in ("test-installed-release.ps1", "test-worker-stability.ps1"):
            with self.subTest(script=name):
                script = self._script(name)
                self.assertNotIn("small_image_enhancement", script)
                self.assertNotIn("temperature =", script)

    def test_stability_check_uses_offline_mode_and_determinism(self) -> None:
        script = self._script("test-worker-stability.ps1")
        self.assertIn("TRANSFORMERS_OFFLINE", script)
        self.assertIn("non-deterministic LaTeX", script)
        self.assertIn("Worker produced no event", script)

    def test_second_generation_scripts_use_the_unimernet_runtime(self) -> None:
        for name in (
            "build-installer.ps1",
            "create-release-manifest.ps1",
            "evaluate-formulas.ps1",
            "render-preview.ps1",
        ):
            with self.subTest(script=name):
                script = self._script(name)
                self.assertNotIn(r"runtime\pix2tex_env", script)
                self.assertIn("RuntimeRoot", script)

        manifest = self._script("create-release-manifest.ps1")
        self.assertIn(r"pix2tex_app\models\unimernet_tiny", manifest)
        self.assertNotIn(r"pix2tex\model\checkpoints", manifest)


if __name__ == "__main__":
    unittest.main()
