# Formula recognition backend evaluation

## Current decision

- Keep the existing CPU-only pix2tex 0.1.4 backend as the application default.
- Do not install PaddleOCR/PaddleX or remove the current pix2tex runtime yet.
- Treat `PP-FormulaNet_plus-M` as the first candidate for a future backend evaluation.
- Do not prioritize `PP-FormulaNet_plus-L` unless a local evaluation shows that it fixes important errors made by the M model.

This is an evaluation idea, not an approved backend migration.

## Why the M model is worth evaluating

PaddleOCR's published internal benchmark reports substantially higher English and Chinese BLEU scores for `PP-FormulaNet_plus-M` than for its `LaTeX_OCR_rec` baseline. The M model also supports Chinese mixed formulas and raises the maximum predicted sequence length from 1,024 to 2,560 tokens. These results are promising for long formulas, matrices, multi-line expressions, and research screenshots.

The figures are from PaddleOCR's internal custom test set, so they must not be treated as proof of better accuracy on this application's real inputs. Its LaTeX-OCR baseline may also differ from the pix2tex 0.1.4 checkpoint and preprocessing used here.

Official reference:

- <https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/module_usage/formula_recognition.html>

## Future evaluation boundary

If this idea is resumed, preserve `runtime/pix2tex_env` as a rollback baseline and create a separate CPU-only Paddle environment. Do not mix both dependency stacks into the current runtime during evaluation.

Compare pix2tex and `PP-FormulaNet_plus-M` on a frozen set of real research inputs covering:

- simple and complex printed formulas;
- long equations, matrices, piecewise functions, and multi-line derivations;
- Chinese text mixed with mathematical notation;
- screenshots, scans, photographs, handwriting, and small images.

Record normalized exact match or rendered equivalence, render/parse failures, truncation, cold start, warm latency, peak memory, and total deployable footprint. BLEU alone is not an acceptance criterion.

## Expected integration impact

The current QProcess/JSONL worker boundary should allow a Paddle worker to return the same LaTeX result contract without rewriting capture, preview, formatting, history, clipboard, tray, or shortcut features. Model-specific behavior still needs explicit handling:

- pix2tex temperature has no direct equivalent in the documented Paddle formula-recognition API;
- small-image enhancement must be evaluated separately for each backend;
- Paddle output may require normalization and rendering fallbacks;
- installer size and CPU latency must be measured on the target Windows machine.

Only after the M model passes the local acceptance set should it become the default or replace pix2tex in a release build.
