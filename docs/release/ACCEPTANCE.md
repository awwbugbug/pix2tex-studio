# Release acceptance protocol

This protocol is frozen before the first scored 1.0 OCR run. Results must be reported even when they are negative.

## OCR dataset

Use at least 30 independently labelled images from the intended research workflow. Do not derive labels from the model prediction. Include:

- at least 8 ordinary printed formulas;
- at least 5 long or multi-line formulas;
- at least 4 matrices, cases, or aligned structures;
- at least 3 screenshots with substantial whitespace or small text;
- at least 3 scans, photographs, or degraded inputs;
- any Chinese-mixed or handwritten formulas that are part of the intended workflow.

Private research screenshots belong under `acceptance/private/`, which is ignored by Git. The manifest format is documented in `acceptance/README.md`.

## OCR gates

- Every case produces a result or an explicitly recorded error; silent omissions are forbidden.
- Zero worker crashes, hangs, or truncated outputs.
- At least 90% rendered-equivalent correctness overall after manual review.
- At least 95% rendered-equivalent correctness for ordinary printed formulas.
- Warm inference p95 no greater than 3.0 seconds on the target Windows machine.
- First-ever model readiness from a newly installed or newly built directory no greater than 30 seconds.
- Subsequent cold-process model readiness no greater than 15 seconds.

The readiness gate was split on 2026-08-11, before any scored real-input run.
The reason is measurable Windows file scanning: a newly created frozen directory
took 26.47-27.02 seconds once, while clean subsequent worker processes took
5.43-6.64 seconds. The UI is already visible and responsive during either case.

Normalized exact match is reported as a strict diagnostic metric. Because different LaTeX strings can render equivalently, manual rendered-equivalence review is the release metric for mismatches.

## Windows and installer gates

- Windows 11 target machine, CPU-only and offline after installation.
- Install and uninstall from a path containing Chinese characters and spaces.
- Launch without Anaconda, a system Python, or network access.
- 100%, 125%, 150%, and 200% scale where available.
- Single-monitor and multi-monitor region capture, including negative monitor coordinates when applicable.
- Minimize/taskbar restore, maximize/restore, close-to-tray, tray exit, and single-instance activation.
- Global-shortcut success and occupied-shortcut failure.
- Open, paste, drag/drop, retry, interrupt, history persistence, history cleanup, and diagnostic export.
- At least 25 consecutive recognitions without growing worker count or an unrecovered failure.

An unchecked item is not a pass. A failed gate blocks the 1.0 label until it is fixed or the acceptance protocol is explicitly revised before another scored run.
