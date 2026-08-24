# Pix2Tex Studio 2.0.0rc3

A Word-compatibility update. Everything in 2.0.0rc2 is retained; this build
tightens the **Word** output mode toward the LaTeX subset Microsoft Word
actually supports (Word converts LaTeX to OMML, so "valid LaTeX" is not enough).

## Changed

- The Word output now normalizes toward Word's supported subset so more formulas
  render on **stricter / older Word versions**:
  - OCR Unicode contamination is folded to ASCII: curly quotes / `′` → `'`,
    Unicode minus and dashes → `-`, full-width brackets/comma → ASCII, and
    NBSP / zero-width characters are stripped. (This also improves SymPy.)
  - `\prime` → `'`; scalable `|` / `\|` → `\lvert` / `\lVert`; always-redundant
    `{{...}}` → `{...}` — all without breaking a command/letter boundary.

## Which build should I use?

- **Older / stricter Word** (its LaTeX parser rejects more): use **2.0.0rc3**
  (this build) for the highest chance of clean rendering.
- **Newer Word** (lenient parser): **2.0.0rc2** already works; rc3 also works, so
  rc3 is the safe default either way.

Deeper canonicalization (differential spacing, removing single argument-position
braces, or emitting OMML directly) needs a full LaTeX AST and is out of scope
here.

## Unchanged from 2.0.0rc2

- CPU-only UniMERNet tiny backend; region capture, handwriting board, formula
  preview, history, diagnostics, global shortcut, tray, single-instance.
- Self-contained runtime; no Anaconda, system Python, CUDA, cloud, or network.
- The installer is unsigned; Windows SmartScreen may warn. Verify with
  `SHA256SUMS.txt`.
