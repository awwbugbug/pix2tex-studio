# Original pix2tex GUI parity checklist

Source of truth: `runtime/pix2tex_env/Lib/site-packages/pix2tex/gui.py` from the cloned pix2tex 0.1.4 environment.

| Original capability | New UI location | HTML prototype | QML implementation requirement |
| --- | --- | --- | --- |
| Region screenshot | Source panel primary action | Interactive selection overlay | Real multi-monitor capture with DPI-aware coordinates and Esc cancel |
| Keyboard screenshot shortcut | Source empty state and Settings | In-app `Ctrl+A`, guarded while editing | Implemented: configurable Windows-wide `Ctrl+Shift+A`, `Alt+S`, or explicitly selected `Ctrl+A` |
| Paste clipboard image/file | Source empty state | Button plus `Ctrl+V` handler | Read image and local-file clipboard MIME data |
| Drag local image | Source image panel | Image drag-and-drop | Accept PNG/JPG/JPEG and retain current BMP/WebP superset |
| Open local image | Source empty state | Native browser file picker | Native Qt file dialog |
| Small-image preprocessing | Settings, enabled by default and configurable | Documented | If enabled and width or height is below 100 px: Lanczos resize, contrast 1.5, sharpness 1.5 |
| Editable raw prediction | Editor: Raw prediction tab | Editable textarea | Editing refreshes preview and formatted output |
| Rendered formula preview | Formula preview panel | Empty-state placeholder only | Local MathJax or equivalent offline renderer |
| Raw output | Output format control | Available | Strip surrounding dollar delimiters |
| Inline LaTeX output | Output format control | Available | Wrap raw result in `$...$` |
| Display LaTeX output | Output format control | Available | Wrap raw result in `$$...$$` |
| SymPy output | Output format control | UI and honest prototype notice | Use bundled SymPy Lark parser; expose parse failure inline |
| Editable formatted output | Editor: Formatted output tab | Editable textarea | Editing writes formatted text to clipboard, matching original behavior |
| Automatic clipboard copy | Settings | Enabled by default | Preserve original automatic formatted-output copy behavior |
| Temperature 0–1 | Source footer | Numeric step input | Send current value on each inference; map zero to a small positive epsilon |
| Retry previous image | Source footer | Enabled after input | Re-run the retained image with current temperature |
| Interrupt inference | Source footer screenshot action while busy | Interactive processing state | Cancel/terminate the active worker request without freezing the UI |
| Processing feedback | Source action and editor status | Interactive | Busy indicator and disabled conflicting controls |
| Prediction failure | Editor status | Status slot reserved | Inline error plus optional dialog; retain the image for Retry |
| Multi-monitor capture | No separate visual control | Not executable in browser | Cover the active display/all displays and handle negative monitor coordinates |
| High-DPI capture | No separate visual control | Not executable in browser | Convert logical and physical coordinates correctly per monitor |
| Light/dark theme | Top bar and Settings | Functional and persisted | QML theme tokens with system/light/dark modes |

The HTML prototype intentionally contains no sample formula, fake recognition result, fake duration, or fake history entry.
