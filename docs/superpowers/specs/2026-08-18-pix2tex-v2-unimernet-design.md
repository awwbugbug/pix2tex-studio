# Pix2Tex Studio 2.0 — UniMERNet backend (design)

Date: 2026-08-18
Status: approved design, pre-implementation
Sub-project: 1 of 3 (new-generation app). Sub-projects 2 (canvas/pen input) and
3 (optional GPU backend) are deferred and get their own specs.

## Goal

Ship a new generation of Pix2Tex Studio that fully replaces the pix2tex 0.1.4
backend with UniMERNet, a PyTorch model that natively covers printed, screenshot,
scanned, and handwritten formulas. The frozen 1.0.0rc1 (pix2tex) release stays
intact and isolated as a rollback line.

This is a clean replacement, not a pluggable multi-backend system. There is no
pix2tex fallback in the running app. That decision is deliberate: the two models
differ internally, and a single-backend "new generation" is simpler to build and
maintain (YAGNI). It also makes the earlier pluggable-abstraction idea unnecessary.

## Non-goals (explicitly out of scope for this sub-project)

- Canvas / pen handwriting input (sub-project 2, built after this lands).
- A working GPU backend (sub-project 3). This spec only *preserves the seam* for
  device selection; it does not package or validate a CUDA path.
- An A/B evaluation framework or a frozen accuracy dataset. Dropped by decision;
  the user validates by hands-on use.
- Any change to the frozen 1.0.0rc1 line.

## Milestone 0 (gating): CPU latency benchmark

Verified before writing this spec: UniMERNet is Apache-2.0 (safe to bundle in a
distributed installer) and its own `demo.py` selects the device as
`torch.device("cuda" if torch.cuda.is_available() else "cpu")`, so pure-CPU
inference is supported by the code. The open risk is *speed*: UniMERNet is an
autoregressive transformer decoder, so CPU per-formula latency is expected to be
seconds, not pix2tex's ~0.2s.

Before building the full app, the first implementation step measures real CPU
latency on the target Windows machine:

1. Install `unimernet[full]` into a fresh, isolated env; download `unimernet_tiny`.
2. Run a minimal script that loads the model on CPU and recognizes a few real
   formula images (short and long), recording per-image wall-clock latency and
   peak memory.

Decision rule from the measured number:

- Tolerable (roughly a few seconds/image) → proceed with **`unimernet_tiny`** as
  the bundled default. Revisit `small` only if tiny's quality disappoints in use.
- Intolerable → stop and choose between (a) repositioning the new generation as
  GPU-recommended, or (b) a lighter model. Do not silently ship an unusably slow
  build.

The rest of this spec assumes the tolerable branch.

## Version isolation and runtime

- Branch `2.0.0-dev` off the current line (which already contains the frozen
  1.0.0rc1 commit). Tag the 1.0.0rc1 commit as a rollback point.
- Bump `pyproject.toml` version to `2.0.0-dev` and replace the `pix2tex==0.1.4`
  dependency with `unimernet` (exact version pinned once Milestone 0 confirms it).
- `runtime/pix2tex_env` is the 1.0 rollback baseline. It must not be deleted or
  mutated. Create a separate `runtime/unimernet_env` for the new stack. The two
  dependency stacks are never mixed into one runtime.

## Backend swap (the only deep change)

All model-specific work is contained inside the OCR worker. The worker's JSONL
contract over stdin/stdout is preserved exactly:

- in: `{"type": "predict", "id": ..., "path": "<image path>"}`
- out: `{"type": "result", "id": ..., "latex": "...", "seconds": <float>}`
- lifecycle: `{"type": "ready", ...}` on load, `{"type": "error", ...}` on failure,
  `{"type": "shutdown"}` to stop.

Because the contract is unchanged, `controller.py`, `capture.py`, `desktop.py`,
history, preview, clipboard, tray, and shortcuts need **no changes**.

Changes inside `src/pix2tex_app/worker.py`:

- Replace pix2tex model loading (`LatexOCR()`) with UniMERNet model construction,
  loading weights from the bundled model directory and selecting the device via
  the same `cuda if available else cpu` fallback (this is the preserved GPU seam).
- Remove pix2tex-specific behavior:
  - the `temperature` command field and `model.args.temperature` assignment;
  - the `prediction.replace("<", r"\lt ").replace(">", r"\gt ")` escape hack
    (verify whether UniMERNet output needs any analogous normalization; add only
    if a real problem is observed, not preemptively);
  - the `prepare_image` small-image enhancement is pix2tex-tuned — replace it with
    UniMERNet's own expected preprocessing (its `vis_processor`), or drop the
    custom crop/enhance path if UniMERNet handles raw images well. Decide from
    observed output during Milestone 0.

The predict path still writes the incoming image to a temp file and passes a path,
so capture/open/paste/drag input sources are untouched.

## Frontend changes (localized)

The QML interface stays largely the same. Changes concentrate on settings controls
whose semantics were pix2tex-specific:

- Remove or repurpose the **Temperature** control (UniMERNet inference is
  deterministic; there is no temperature knob).
- Remove or rework the **small-image enhancement** toggle (its pix2tex-tuned
  behavior no longer applies; keep a toggle only if the new preprocessing has a
  meaningful on/off choice).
- Output modes (Raw / inline LaTeX / display LaTeX / SymPy), MathJax preview,
  history, and clipboard are unaffected — output is still a LaTeX string, and the
  SymPy path via `latex2sympy2` is unchanged.

Any settings persistence keys tied to removed controls are migrated or dropped
cleanly so old local settings do not break first launch.

## Packaging and size

- Bundle `unimernet_tiny` weights (~441 MB) into the build. The installer grows
  from ~467 MB accordingly; this is accepted for the new generation.
- Because there is no pix2tex fallback, the model is bundled (not downloaded on
  first use), preserving offline-first launch.
- Update the PyInstaller build scripts to include the model weights and the
  `unimernet` package data, and to drop pix2tex.
- Update `THIRD_PARTY_NOTICES.md` and the license-collection script to include
  UniMERNet (Apache-2.0) and its new transitive dependencies; drop pix2tex-only
  entries no longer shipped.
- Record the replacement decision in `docs/design/model-backend-evaluation.md`
  (it currently states no migration is approved).

## Definition of done

- Automated tests updated and green (release gate 2 requires all automated tests
  to pass):
  - worker smoke test: loads UniMERNet, recognizes a fixture image, emits a valid
    `result` with non-empty LaTeX and a `seconds` field;
  - controller contract test: unchanged JSONL round-trip still works;
  - existing tests touching removed pix2tex fields (temperature, escape) updated.
- Claude builds the feature and writes these automated tests. The user performs
  all frontend / user-level / manual acceptance (recognition quality, latency
  feel, visual checks).

## Risks and fallbacks

- **CPU latency** is the primary risk, gated by Milestone 0. Fallback options are
  named there (GPU-recommended repositioning, or a lighter model).
- **Model API/packaging surprises** (weight loading, `vis_processor`, PyInstaller
  data collection) surface during Milestone 0 and early integration; the isolated
  `runtime/unimernet_env` contains them without touching the 1.0 baseline.
- If UniMERNet proves unworkable on CPU and GPU is rejected, the runner-up is
  TexTeller 3.0 (PyTorch, Apache-2.0). Note it is the same transformer class, so
  it offers no CPU-speed advantage — it is a quality/coverage alternative, not a
  latency fix.

## Sequencing after this sub-project

1. This sub-project: UniMERNet backend + version isolation + frontend edits.
2. Canvas / pen input on the left recognition area — draw, export PNG, feed the
   same image→LaTeX pipeline as a fifth input source. Highest value once the
   handwriting-capable backend is in place.
3. Optional GPU backend — light up the device seam for machines with CUDA.
