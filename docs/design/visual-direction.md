# Visual direction: compact research workspace

Status: the user supplied and approved the `ScholarTeX`-style workspace template on 2026-07-29.

## Intent

Pix2Tex Studio is a compact Windows research utility, not a dashboard. The native client area contains a 48 px navigation bar and a two-column recognition workspace: source image on the left, rendered output plus source editing on the right.

## Defining elements

- no simulated outer window or inset shell; Windows DWM owns the real window edge
- compact initial window (`980 × 640`, minimum `820 × 540`)
- equal source/output columns with a dense academic-tool layout
- formula preview above a dark raw/formatted source editor
- neutral light and dark themes using the same semantic tokens
- recognition, history, and settings pages in the top navigation
- no demo formula, fake image, fake history, fake duration, or fake model state

## Interaction principles

- pointer-down feedback on every interactive component
- short opacity/position transitions between pages and editor states
- no smoothing on the screenshot selection rectangle; it follows the pointer 1:1
- CPU inference stays in a separate worker process
- region capture hides the main window and operates on the display under the cursor
- raw and formatted outputs remain independently editable
- format, temperature, theme, and automatic-copy preferences persist locally

## Functional source of truth

See `original-gui-parity.md`. The new implementation preserves the original GUI's region capture, paste/drop/open paths, four output modes, Temperature, Retry, Interrupt, automatic clipboard behavior, small-image enhancement, preview, and error state while retaining the project's local history feature.
