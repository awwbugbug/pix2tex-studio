# Third-party notices

Pix2Tex Studio bundles third-party software. The complete license, copyright,
and notice files found in the locked runtime wheels are distributed in the
`third-party-licenses` directory. The generated `manifest.json` records the
exact package versions and copied files.

Important runtime components include:

| Component | Version | Declared license |
| --- | ---: | --- |
| UniMERNet code and tiny model | 0.2.3 | Apache-2.0 |
| PySide6 / Shiboken6 / Qt | 6.10.1 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only |
| PyTorch | 2.13.0 (CPU) | BSD-3-Clause |
| torchvision | 0.28.0 | BSD |
| Transformers | 4.42.4 | Apache-2.0 |
| timm | 0.9.16 | Apache-2.0 |
| OpenCV Python | 4.11.0.86 | Apache-2.0 |
| NumPy | 1.26.4 | BSD-3-Clause and bundled-component notices |
| SciPy | 1.15.3 | BSD-3-Clause and bundled-component notices |
| Pillow | 12.3.0 | HPND |
| MathJax JavaScript | bundled with the application | Apache-2.0 |

Qt/PySide libraries remain separate dynamically loaded files inside the
installed application directory. They are not statically linked into the
Pix2Tex Studio executable.

This notice summarizes installed metadata; the accompanying license files are
authoritative. Pix2Tex Studio does not claim ownership of third-party code,
models, names, or trademarks.
