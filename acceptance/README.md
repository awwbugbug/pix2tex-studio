# Private OCR acceptance set

Create the private dataset under `acceptance/private/`:

```text
acceptance/private/
├── manifest.jsonl
└── images/
    ├── case-001.png
    └── ...
```

Each line in `manifest.jsonl` is one JSON object:

```json
{"id":"case-001","image":"images/case-001.png","ground_truth":"e^{i\\pi}+1=0","category":"printed","notes":"real research screenshot"}
```

Required fields are `id`, `image`, `ground_truth`, and `category`. Image paths are relative to the manifest. Labels must be written independently rather than copied from Pix2Tex Studio predictions.

Run the evaluator with:

```powershell
.\scripts\evaluate-formulas.ps1
```

Raw results are written to `release-evidence/ocr/`. Review every strict mismatch visually and record whether the prediction is rendered-equivalent before accepting the release gate.
