from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from pix2tex_app.controller import (
    AppController,
    _clean_latex,
    _normalize_unicode,
    _word_latex,
    _worker_process_command,
)


class ControllerTests(unittest.TestCase):
    def test_frozen_build_uses_sibling_console_worker(self) -> None:
        program, arguments = _worker_process_command(
            frozen=True,
            executable=r"C:\Program Files\Pix2Tex Studio\Pix2TexStudio.exe",
        )

        self.assertEqual(
            program,
            r"C:\Program Files\Pix2Tex Studio\Pix2TexWorker.exe",
        )
        self.assertEqual(arguments, [])

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_history_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            controller = AppController(start_worker=False, data_dir=data_dir)
            controller._record_history("x^2", "", "0.42s")
            restored = AppController(start_worker=False, data_dir=data_dir)
            self.assertEqual(restored.historyModel.rowCount(), 1)
            self.assertEqual(restored.historyModel.entry(0)["formula"], "x^2")

    def test_clear_image_resets_to_initial_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller._image_path = str(Path(directory) / "x.png")
            controller._set_latex("x^2")
            controller._last_duration = "0.42s"

            controller.clearImage()

            self.assertEqual(controller.imageUrl, "")
            self.assertEqual(controller.latex, "")
            self.assertEqual(controller.formattedLatex, "")
            self.assertEqual(controller.lastDuration, "—")

    def test_history_preview_roles_update_without_polluting_saved_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller._record_history("x^2", "", "0.10s")
            controller.historyModel.set_preview_for_formula("x^2", "light.png", "dark.png", 120, 48)

            index = controller.historyModel.index(0, 0)
            self.assertTrue(controller.historyModel.data(index, controller.historyModel.PreviewReadyRole))
            self.assertEqual(controller.historyModel.data(index, controller.historyModel.PreviewWidthRole), 120)
            self.assertFalse(any(key.startswith("_") for key in controller.historyModel.serializable()[0]))

    def test_history_copy_and_single_delete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            controller = AppController(start_worker=False, data_dir=data_dir)
            controller._record_history(r"\frac{a}{b}", "", "0.10s")
            copied: list[str] = []
            controller._copy_to_clipboard = copied.append

            controller.copyHistoryFormula(0)
            self.assertEqual(copied, [r"\frac{a}{b}"])
            controller.removeHistory(0)
            self.assertEqual(controller.historyModel.rowCount(), 0)
            self.assertEqual(json.loads((data_dir / "history.json").read_text(encoding="utf-8")), [])

    def test_history_limit_and_generated_cache_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            controller = AppController(start_worker=False, data_dir=data_dir)
            controller.setHistoryLimit(50)
            for index in range(55):
                controller._record_history(f"x_{index}", "", "0.10s")
            self.assertEqual(controller.historyModel.rowCount(), 50)
            self.assertEqual(controller.historyModel.entry(49)["formula"], "x_5")

            retained = data_dir / "cache" / "capture-retained.png"
            stale = data_dir / "cache" / "clipboard-stale.png"
            retained.write_bytes(b"retained")
            stale.write_bytes(b"stale")
            controller._record_history("y", str(retained), "0.10s")
            controller._cleanup_generated_cache()
            self.assertTrue(retained.exists())
            self.assertFalse(stale.exists())

    def test_editing_latex_updates_property(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller.setLatex(r"\frac{a}{b}")
            self.assertEqual(controller.latex, r"\frac{a}{b}")

    def test_initial_state_contains_no_demo_formula(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            self.assertEqual(controller.latex, "")
            self.assertEqual(controller.formattedLatex, "")

    def test_output_formats_follow_raw_prediction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller.setLatex("x^2")
            self.assertEqual(controller.formattedLatex, "$x^2$")
            controller.setFormatMode("raw")
            self.assertEqual(controller.formattedLatex, "x^2")
            controller.setFormatMode("latex-display")
            self.assertEqual(controller.formattedLatex, "$$x^2$$")

    def test_sympy_output_uses_the_runtime_compatible_parser(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller.setLatex(r"\frac{1}{2}")
            controller.setFormatMode("sympy")
            self.assertEqual(controller.formattedLatex, "1/2")
            self.assertEqual(controller.formatError, "")

    def test_word_format_mode_outputs_clean_compact_latex(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller.setFormatMode("word")
            controller.setLatex(
                r"\begin{array} { r } { x = \frac { - b \pm \sqrt { b ^ { 2 } - 4 a c } } { 2 a } } \end{array}"
            )
            self.assertEqual(
                controller.formattedLatex,
                r"x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}",
            )

    def test_sympy_parses_array_wrapped_output_after_cleaning(self) -> None:
        # UniMERNet wraps plain formulas in \begin{array}, which the parser
        # rejects; cleaning the input first lets SymPy succeed.
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller.setFormatMode("sympy")
            controller.setLatex(r"\begin{array} { r } { \frac { a } { b } } \end{array}")
            self.assertEqual(controller.formattedLatex, "a/b")
            self.assertEqual(controller.formatError, "")

    def test_preferences_persist_in_project_data_dir(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            controller = AppController(start_worker=False, data_dir=data_dir)
            controller.setThemeMode("dark")
            controller.setAutoCopy(False)
            controller.setGlobalHotkey("Alt+S")
            restored = AppController(start_worker=False, data_dir=data_dir)
            self.assertEqual(restored.themeMode, "dark")
            self.assertFalse(restored.autoCopy)
            self.assertEqual(restored.globalHotkey, "Alt+S")

    def test_prediction_payload_contains_only_type_id_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            payloads: list[dict] = []
            controller._engine_state = "ready"
            controller._send = payloads.append
            controller._predict("formula.png")
            self.assertEqual(payloads[0]["type"], "predict")
            self.assertEqual(payloads[0]["path"], "formula.png")
            self.assertEqual(set(payloads[0]), {"type", "id", "path"})

    def test_global_hotkey_rejects_an_occupied_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller.bind_global_hotkey(lambda value: (value != "Alt+S", "occupied"))
            controller.setGlobalHotkey("Alt+S")
            self.assertEqual(controller.globalHotkey, "Ctrl+Shift+A")
            self.assertEqual(controller.globalHotkeyStatus, "occupied")


class CleanLatexTests(unittest.TestCase):
    def test_unwraps_single_row_array(self) -> None:
        self.assertEqual(
            _clean_latex(r"\begin{array} { r } { E = m c ^ { 2 } } \end{array}"),
            r"E=mc^{2}",
        )

    def test_keeps_space_terminating_a_command_before_a_letter(self) -> None:
        self.assertEqual(_clean_latex(r"a \sin x + \pi r"), r"a\sin x+\pi r")

    def test_multi_row_array_is_left_intact(self) -> None:
        matrix = r"\begin{array} { c c } { a } & { b } \\ { c } & { d } \end{array}"
        self.assertIn(r"\begin{array}", _clean_latex(matrix))


class NormalizeUnicodeTests(unittest.TestCase):
    def test_folds_ocr_contamination_to_ascii(self) -> None:
        self.assertEqual(_normalize_unicode("a − b"), "a - b")            # minus
        self.assertEqual(_normalize_unicode("x’"), "x'")                  # curly apostrophe
        self.assertEqual(_normalize_unicode("f（x）"), "f(x)")        # full-width parens
        self.assertEqual(_normalize_unicode("a +​b"), "a +b")       # nbsp + zero-width


class WordNormalizerTests(unittest.TestCase):
    def test_prime_becomes_apostrophe(self) -> None:
        self.assertEqual(_word_latex(r"x^{\prime\prime}+y^{\prime}"), "x''+y'")

    def test_word_supported_bars_are_left_alone(self) -> None:
        # | and \| render in Word, so the model's own delimiters are untouched.
        self.assertEqual(
            _word_latex(r"\left\|v\right\|+\left|x\right|"),
            r"\left\|v\right\|+\left|x\right|",
        )

    def test_lvert_family_folds_to_plain_bars(self) -> None:
        # Word leaves \lvert/\rvert as literal text, so fold them to | and \|.
        self.assertEqual(_word_latex(r"\left\lvert x\right\rvert"), r"\left| x\right|")
        self.assertEqual(_word_latex(r"\left\lVert v\right\rVert"), r"\left\| v\right\|")

    def test_keeps_argument_braces(self) -> None:
        self.assertEqual(_word_latex(r"x^{a+b}+\frac{a+b}{c}"), r"x^{a+b}+\frac{a+b}{c}")

    def test_unicode_is_normalized_in_word_output(self) -> None:
        self.assertEqual(_word_latex("f（x）−y"), "f(x)-y")


if __name__ == "__main__":
    unittest.main()
