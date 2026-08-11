from __future__ import annotations

import argparse
import json
import os
import queue
import re
import statistics
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO


@dataclass(frozen=True)
class FormulaCase:
    id: str
    image: Path
    ground_truth: str
    category: str
    notes: str = ""


def normalize_latex(value: str) -> str:
    """Return a conservative representation for strict OCR comparisons."""
    normalized = value.strip()
    if normalized.startswith("$$") and normalized.endswith("$$") and len(normalized) >= 4:
        normalized = normalized[2:-2]
    elif normalized.startswith("$") and normalized.endswith("$") and len(normalized) >= 2:
        normalized = normalized[1:-1]
    normalized = normalized.replace(r"\left", "").replace(r"\right", "")
    return re.sub(r"\s+", "", normalized)


def load_manifest(path: Path) -> list[FormulaCase]:
    manifest = path.resolve()
    cases: list[FormulaCase] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"manifest line {line_number} is not valid JSON: {exc}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"manifest line {line_number} must be a JSON object")
        missing = [key for key in ("id", "image", "ground_truth", "category") if not item.get(key)]
        if missing:
            raise ValueError(f"manifest line {line_number} is missing: {', '.join(missing)}")
        case_id = str(item["id"])
        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        image = (manifest.parent / str(item["image"])).resolve()
        if not image.is_file():
            raise ValueError(f"case {case_id} image does not exist: {image}")
        seen.add(case_id)
        cases.append(
            FormulaCase(
                id=case_id,
                image=image,
                ground_truth=str(item["ground_truth"]),
                category=str(item["category"]),
                notes=str(item.get("notes", "")),
            )
        )
    if not cases:
        raise ValueError("manifest contains no cases")
    return cases


class _LineReader:
    def __init__(self, stream: TextIO) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._thread = threading.Thread(target=self._read, args=(stream,), daemon=True)
        self._thread.start()

    def _read(self, stream: TextIO) -> None:
        for line in stream:
            self._queue.put(line)
        self._queue.put("")

    def json_event(self, timeout: float) -> dict[str, Any]:
        try:
            line = self._queue.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError(f"worker produced no event within {timeout:.0f}s") from exc
        if not line:
            raise RuntimeError("worker exited before returning an event")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"worker returned invalid JSON: {line[:200]}") from exc
        if not isinstance(event, dict):
            raise RuntimeError("worker event is not a JSON object")
        return event


def _percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[94]


def evaluate_manifest(
    manifest: Path,
    output_dir: Path,
    *,
    startup_timeout: float = 30.0,
    prediction_timeout: float = 120.0,
) -> dict[str, Any]:
    cases = load_manifest(manifest)
    worker_path = Path(__file__).with_name("worker.py")
    environment = os.environ.copy()
    environment.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
    process = subprocess.Popen(
        [sys.executable, "-u", str(worker_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    reader = _LineReader(process.stdout)
    results: list[dict[str, Any]] = []
    ready_seconds = 0.0
    started = time.perf_counter()
    try:
        event = reader.json_event(startup_timeout)
        if event.get("type") != "ready":
            raise RuntimeError(f"worker failed to become ready: {event}")
        ready_seconds = float(event.get("seconds", time.perf_counter() - started))
        for case in cases:
            request_id = uuid.uuid4().hex
            process.stdin.write(
                json.dumps(
                    {
                        "type": "predict",
                        "id": request_id,
                        "path": str(case.image),
                        "temperature": 0.3,
                        "small_image_enhancement": True,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            process.stdin.flush()
            while True:
                event = reader.json_event(prediction_timeout)
                if event.get("id") == request_id or event.get("type") == "error":
                    break
            prediction = str(event.get("latex", "")) if event.get("type") == "result" else ""
            ground_truth_normalized = normalize_latex(case.ground_truth)
            prediction_normalized = normalize_latex(prediction)
            results.append(
                {
                    **asdict(case),
                    "image": str(case.image),
                    "prediction": prediction,
                    "normalized_ground_truth": ground_truth_normalized,
                    "normalized_prediction": prediction_normalized,
                    "strict_match": bool(prediction_normalized == ground_truth_normalized),
                    "seconds": float(event.get("seconds", 0.0)),
                    "error": "" if event.get("type") == "result" else str(event.get("message", "unknown")),
                    "manual_rendered_equivalent": None,
                }
            )
    finally:
        if process.poll() is None:
            try:
                process.stdin.write('{"type":"shutdown"}\n')
                process.stdin.flush()
                process.wait(timeout=5)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                process.kill()
                process.wait(timeout=5)

    latencies = [float(item["seconds"]) for item in results if not item["error"]]
    strict_matches = sum(bool(item["strict_match"]) for item in results)
    report = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "manifest": str(manifest.resolve()),
        "python": sys.version,
        "worker_ready_seconds": ready_seconds,
        "summary": {
            "cases": len(results),
            "results": len(latencies),
            "errors": sum(bool(item["error"]) for item in results),
            "strict_matches": strict_matches,
            "strict_accuracy": strict_matches / len(results),
            "mean_seconds": statistics.fmean(latencies) if latencies else 0.0,
            "p95_seconds": _percentile_95(latencies),
        },
        "cases": results,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "ocr-results.json"
    markdown_path = output_dir / "ocr-results.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = report["summary"]
    markdown_lines = [
        "# OCR acceptance results",
        "",
        f"- Cases: {summary['cases']}",
        f"- Strict matches: {summary['strict_matches']}",
        f"- Strict accuracy: {summary['strict_accuracy']:.1%}",
        f"- Errors: {summary['errors']}",
        f"- Worker readiness: {ready_seconds:.2f}s",
        f"- Warm mean: {summary['mean_seconds']:.2f}s",
        f"- Warm p95: {summary['p95_seconds']:.2f}s",
        "",
        "Strict mismatches require manual rendered-equivalence review in `ocr-results.json`.",
    ]
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Pix2Tex Studio on a frozen JSONL manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate_manifest(args.manifest, args.output)
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"acceptance evaluation failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
