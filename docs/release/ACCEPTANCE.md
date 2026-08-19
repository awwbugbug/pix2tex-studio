# Pix2Tex Studio 2.0 release acceptance protocol

This protocol is frozen before the first scored 2.0 OCR run. Results must be
reported even when negative.

## OCR dataset

Use at least 30 independently labelled images from the intended research
workflow. Labels must not be derived from UniMERNet predictions. Categories may
overlap, but the set must include:

- at least 8 ordinary printed formulas;
- at least 5 long, multi-line, matrix, cases, or aligned formulas;
- at least 5 handwritten formulas produced independently of the app;
- at least 4 dark-background screenshots;
- at least 4 inputs with substantial whitespace or small formula content;
- at least 3 scans, photographs, degraded inputs, or Chinese-mixed formulas.

Private research screenshots belong under `acceptance/private/`, which is
ignored by Git. The manifest format is documented in `acceptance/README.md`.

## OCR gates

- Every case produces a result or an explicitly recorded error; silent omissions are forbidden.
- Zero Worker crashes, hangs, or truncated outputs.
- At least 90% rendered-equivalent correctness overall after manual review.
- At least 95% rendered-equivalent correctness for ordinary printed formulas.
- Handwritten, long-structure, dark-background, and degraded subsets are reported separately.
- Warm inference p95 no greater than 3.0 seconds on the target Windows machine.
- First-ever model readiness from a new installed directory no greater than 30 seconds.
- Subsequent cold-process readiness no greater than 15 seconds.

Normalized exact match is a strict diagnostic metric. Manual rendered
equivalence is the release metric for syntactically different LaTeX strings.

## Windows and installer gates

- Windows 11 target machine, CPU-only and offline after installation.
- Install and uninstall from a path containing Chinese characters and spaces.
- Launch without Anaconda, system Python, CUDA, or network access.
- 100%, 125%, 150%, and 200% scale where available.
- Single-monitor and multi-monitor capture, including negative coordinates when available.
- Minimize/taskbar restore, maximize/restore, close-to-tray, tray exit, and single-instance activation.
- Global-shortcut success and occupied-shortcut failure.
- Screenshot, open, paste, drag/drop, handwriting recognition, retry, interrupt,
  history persistence/cleanup, and diagnostic export.
- At least 25 consecutive recognitions without growing Worker count or an unrecovered failure.
- Same-path upgrade preserves settings/history; uninstall removes program files
  while preserving user data unless an explicit removal option is added later.

An unchecked item is not a pass. A failed gate blocks the final 2.0.0 label
until fixed or the protocol is explicitly revised before another scored run.
