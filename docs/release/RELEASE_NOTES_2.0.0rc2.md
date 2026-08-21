# Pix2Tex Studio 2.0.0rc2

A maintenance update to the second-generation UniMERNet release candidate.
Everything in 2.0.0rc1 is retained; this update adds a Word-friendly output and
fixes SymPy conversion.

## Added

- **"Word" output mode** (next to Raw): emits compact, delimiter-free LaTeX for
  Microsoft Word's equation input. It unwraps UniMERNet's single-row `array`,
  drops layout-only commands, and collapses token spaces while keeping the space
  that terminates a command name before a letter (so `\sin x` stays `\sin x`,
  not `\sinx`).

## Fixed

- **SymPy output** now handles the model's `array`-wrapped predictions. The raw
  LaTeX is cleaned before it reaches the SymPy LaTeX parser, so real recognized
  formulas convert instead of failing.

## Unchanged from 2.0.0rc1

- CPU-only UniMERNet tiny backend with bundled weights.
- Region capture (clean pre-grab, dark-background inversion), handwriting board,
  formula preview, history, diagnostics, global shortcut, tray, single-instance.
- Self-contained runtime; no Anaconda, system Python, CUDA, cloud service, or
  runtime network access required.
- The installer is unsigned, so Windows SmartScreen may warn on first launch.
