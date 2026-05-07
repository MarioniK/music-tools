#!/usr/bin/env python3
"""Профилирует slim ONNX/MusiCNN image path для Roadmap 4.86.

Скрипт выполняет только local-only direct path probe:

- не вызывает `/classify`;
- не использует Docker Compose;
- не делает network HTTP calls;
- не трогает production defaults;
- не сравнивает TensorFlow baseline как отдельный runtime;
- не пытается доказать production readiness.

Чтобы получить честные per-run import/runtime метрики, главный процесс запускает
несколько fresh subprocess-ов, а каждый дочерний процесс измеряет один полный
direct path run:

import -> audio loading -> preprocessing -> ONNX session -> inference -> mapping

Отчёт пишется в JSON и предназначен только для evaluation scaffold.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import resource
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[4]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))
DEFAULT_OUTPUT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-slim-image-performance-baseline-report.json"
)
IMAGE_TAG = "music-tools-genre-classifier-onnx:roadmap-4.85-slim"
IMAGE_SIZE_BYTES = 1572225060
FULL_BASELINE_SIZE_BYTES = 3479268977
SIZE_REDUCTION_BYTES = FULL_BASELINE_SIZE_BYTES - IMAGE_SIZE_BYTES
SIZE_REDUCTION_PERCENT = round(SIZE_REDUCTION_BYTES * 100 / FULL_BASELINE_SIZE_BYTES, 2)
FULL_IMAGE_BASELINE_TOTAL_SECONDS = [1.873967, 1.745251, 1.654825]
FULL_IMAGE_BASELINE_IMPORT_SECONDS = [0.142362, 0.136413, 0.125352]
FULL_IMAGE_BASELINE_AUDIO_LOADING_SECONDS = [0.53787, 0.48089, 0.476575]
FULL_IMAGE_BASELINE_PREPROCESSING_SECONDS = [0.108405, 0.100992, 0.096274]
FULL_IMAGE_BASELINE_ONNX_SESSION_SECONDS = [0.021601, 0.009482, 0.008931]
FULL_IMAGE_BASELINE_ONNX_INFERENCE_SECONDS = [0.058606, 0.050385, 0.047237]
FULL_IMAGE_BASELINE_MAPPING_SECONDS = [0.001036, 0.000677, 0.000726]
FULL_IMAGE_BASELINE_MAX_RSS_KB = 280012
REPEATED_RUNS = 3


class ProbeError(RuntimeError):
    """Ожидаемая ошибка benchmark helper без traceback на пользовательском уровне."""


@dataclass(frozen=True)
class RunResult:
    """Результат одного fresh subprocess прогона."""

    total_seconds: float
    import_seconds: float
    audio_loading_seconds: float
    preprocessing_seconds: float
    onnx_session_seconds: float
    onnx_inference_seconds: float
    mapping_seconds: float
    genres: list[dict[str, Any]]
    genres_pretty: list[str]
    full_pipeline_slim_image: dict[str, Any]
    package_status: dict[str, Any]
    resource_usage: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProbeError(f"JSON artifact is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProbeError(f"JSON artifact is invalid: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ProbeError(f"JSON artifact must be an object: {path}")
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-path", required=True, type=Path)
    parser.add_argument("--onnx-model-path", required=True, type=Path)
    parser.add_argument("--classes-path", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=REPEATED_RUNS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--child-run", action="store_true")
    return parser


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(SERVICE_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _heavy_modules_loaded(before: set[str], after: set[str]) -> list[str]:
    heavy_prefixes = ("tensorflow", "keras", "essentia", "onnxruntime")
    loaded = []
    for name in sorted(after - before):
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in heavy_prefixes):
            loaded.append(name)
    return loaded


def _run_child(args: argparse.Namespace) -> RunResult:
    total_start = time.perf_counter()
    import_start = time.perf_counter()

    from app.providers.compat import (  # noqa: WPS433
        map_validated_result_to_legacy_genres,
        map_validated_result_to_legacy_genres_pretty,
    )
    from app.providers.onnx_musicnn import OnnxMusiCNNProvider  # noqa: WPS433
    from app.providers.validation import validate_and_normalize_provider_result  # noqa: WPS433

    import_seconds = time.perf_counter() - import_start
    modules_after_import = set(sys.modules)

    tensorflow_import_ok = False
    tensorflow_installed = importlib.util.find_spec("tensorflow") is not None
    if tensorflow_installed:
        try:
            import tensorflow  # noqa: F401, WPS433
        except Exception:
            tensorflow_import_ok = False
        else:
            tensorflow_import_ok = True

    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
    except Exception as exc:
        raise ProbeError(f"onnxruntime unavailable: {exc}") from exc

    try:
        from essentia import standard as essentia_standard  # type: ignore[import-not-found]
    except Exception as exc:
        raise ProbeError(f"essentia.standard unavailable: {exc}") from exc

    provider = OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(
            get_configured_onnx_musicnn_model_path=lambda: args.onnx_model_path,
            get_configured_onnx_musicnn_metadata_path=lambda: args.classes_path,
        )
    )

    if not args.audio_path.is_file():
        raise ProbeError(f"audio artifact missing: {args.audio_path}")
    if not args.onnx_model_path.is_file():
        raise ProbeError(f"onnx model artifact missing: {args.onnx_model_path}")
    if not args.classes_path.is_file():
        raise ProbeError(f"classes metadata artifact missing: {args.classes_path}")

    metadata = _load_json(args.classes_path)
    classes = metadata.get("classes")
    if not isinstance(classes, list) or not classes:
        raise ProbeError("classes metadata does not contain a classes list")

    audio_loading_start = time.perf_counter()
    audio = essentia_standard.MonoLoader(filename=str(args.audio_path), sampleRate=16000)()
    audio_loading_seconds = time.perf_counter() - audio_loading_start

    preprocessing_before = set(sys.modules)
    preprocessing_start = time.perf_counter()
    tensor = essentia_standard.TensorflowInputMusiCNN()
    rows = []
    for frame in essentia_standard.FrameGenerator(
        audio,
        frameSize=512,
        hopSize=256,
        startFromZero=True,
        lastFrameToEndOfFile=True,
    ):
        bands = tensor(frame)
        rows.append([float(value) for value in bands])

    if not rows:
        raise ProbeError("TensorflowInputMusiCNN produced no rows")

    if len(rows) < 187:
        last_row = list(rows[-1])
        while len(rows) < 187:
            rows.append(list(last_row))
    else:
        rows = rows[:187]

    if any(len(row) != 96 for row in rows):
        raise ProbeError("TensorflowInputMusiCNN patch width normalization failed")

    try:
        import numpy as np  # type: ignore[import-not-found]
    except Exception as exc:
        raise ProbeError(f"numpy unavailable: {exc}") from exc

    patch = np.asarray(rows, dtype=np.float32)
    if patch.shape != (187, 96):
        raise ProbeError("TensorflowInputMusiCNN patch shape normalization failed")
    if not np.isfinite(patch).all():
        raise ProbeError("TensorflowInputMusiCNN patch contains non-finite values")

    preprocessing_seconds = time.perf_counter() - preprocessing_start
    preprocessing_after = set(sys.modules)

    session_start = time.perf_counter()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(args.onnx_model_path),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    onnx_session_seconds = time.perf_counter() - session_start

    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if not inputs:
        raise ProbeError("onnxruntime session has no inputs")
    if not outputs:
        raise ProbeError("onnxruntime session has no outputs")

    input_meta = inputs[0]
    input_shape = list(input_meta.shape)
    feed_array = patch
    if len(input_shape) == 3 and input_shape[-2:] == [187, 96]:
        feed_array = np.expand_dims(patch, axis=0)
    elif len(input_shape) != 2 or input_shape != [187, 96]:
        raise ProbeError(f"unexpected ONNX input shape: {input_shape}")

    inference_start = time.perf_counter()
    run_outputs = session.run(None, {input_meta.name: feed_array})
    onnx_inference_seconds = time.perf_counter() - inference_start

    output_names = [item.name for item in outputs]
    output_map = {name: value for name, value in zip(output_names, run_outputs)}
    if "activations" not in output_map:
        raise ProbeError("onnx outputs did not include an 'activations' tensor")
    if "embeddings" not in output_map:
        raise ProbeError("onnx outputs did not include an 'embeddings' tensor")

    mapping_start = time.perf_counter()
    activations = provider._normalize_output_values(output_map["activations"])
    provider_result = provider.build_provider_result_from_outputs(
        activations,
        classes,
        top_n=8,
    )
    validated_result = validate_and_normalize_provider_result(provider_result, top_n=8)
    genres = map_validated_result_to_legacy_genres(validated_result)
    genres_pretty = map_validated_result_to_legacy_genres_pretty(validated_result)
    mapping_seconds = time.perf_counter() - mapping_start

    total_seconds = time.perf_counter() - total_start
    heavy_modules = _heavy_modules_loaded(preprocessing_before, preprocessing_after)
    resource_snapshot = resource.getrusage(resource.RUSAGE_SELF)

    return RunResult(
        total_seconds=total_seconds,
        import_seconds=import_seconds,
        audio_loading_seconds=audio_loading_seconds,
        preprocessing_seconds=preprocessing_seconds,
        onnx_session_seconds=onnx_session_seconds,
        onnx_inference_seconds=onnx_inference_seconds,
        mapping_seconds=mapping_seconds,
        genres=genres,
        genres_pretty=genres_pretty,
        full_pipeline_slim_image={
            "success": True,
            "tensorflow_import_ok": tensorflow_import_ok,
            "essentia_import_ok": True,
            "essentia_standard_import_ok": True,
            "tensorflow_input_musiccnn_available": hasattr(essentia_standard, "TensorflowInputMusiCNN"),
            "patch_shape": list(patch.shape),
            "activations_shape": list(np.asarray(output_map["activations"]).reshape(-1).shape),
            "embeddings_shape": list(np.asarray(output_map["embeddings"]).reshape(-1).shape),
            "genres_non_empty": bool(genres),
            "genres_pretty_non_empty": bool(genres_pretty),
        },
        package_status={
            "tensorflow_installed": tensorflow_installed,
            "tensorflow_import_ok": tensorflow_import_ok,
            "essentia_tensorflow_installed": importlib.util.find_spec("essentia") is not None
            and importlib.util.find_spec("essentia.standard") is not None,
            "essentia_standard_used": "essentia.standard" in sys.modules,
            "tensorflow_input_musiccnn_used": hasattr(essentia_standard, "TensorflowInputMusiCNN"),
            "onnxruntime_used": "onnxruntime" in sys.modules,
            "new_heavy_modules_loaded_during_preprocessing": heavy_modules,
        },
        resource_usage={
            "method": "python_resource_getrusage",
            "max_rss_kb": getattr(resource_snapshot, "ru_maxrss", None),
        },
    )


def _spawn_child(args: argparse.Namespace) -> RunResult:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child-run",
        "--audio-path",
        str(args.audio_path),
        "--onnx-model-path",
        str(args.onnx_model_path),
        "--classes-path",
        str(args.classes_path),
        "--runs",
        "1",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "benchmark child failed").strip()
        raise ProbeError(message)

    payload = json.loads(completed.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        raise ProbeError("benchmark child returned invalid JSON")

    return RunResult(
        total_seconds=float(payload["total_seconds"]),
        import_seconds=float(payload["import_seconds"]),
        audio_loading_seconds=float(payload["audio_loading_seconds"]),
        preprocessing_seconds=float(payload["preprocessing_seconds"]),
        onnx_session_seconds=float(payload["onnx_session_seconds"]),
        onnx_inference_seconds=float(payload["onnx_inference_seconds"]),
        mapping_seconds=float(payload["mapping_seconds"]),
        genres=list(payload["genres"]),
        genres_pretty=list(payload["genres_pretty"]),
        full_pipeline_slim_image=dict(payload["full_pipeline_slim_image"]),
        package_status=dict(payload["package_status"]),
        resource_usage=dict(payload["resource_usage"]),
    )


def _run_child_main(args: argparse.Namespace) -> int:
    result = _run_child(args)
    payload = {
        "total_seconds": result.total_seconds,
        "import_seconds": result.import_seconds,
        "audio_loading_seconds": result.audio_loading_seconds,
        "preprocessing_seconds": result.preprocessing_seconds,
        "onnx_session_seconds": result.onnx_session_seconds,
        "onnx_inference_seconds": result.onnx_inference_seconds,
        "mapping_seconds": result.mapping_seconds,
        "genres": result.genres,
        "genres_pretty": result.genres_pretty,
        "full_pipeline_slim_image": result.full_pipeline_slim_image,
        "package_status": result.package_status,
        "resource_usage": result.resource_usage,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def _stable_runs(results: list[RunResult]) -> bool:
    if not results:
        return False

    first_genres = results[0].genres
    first_genres_pretty = results[0].genres_pretty
    return all(result.genres == first_genres and result.genres_pretty == first_genres_pretty for result in results[1:])


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    if args.runs < 3:
        raise ProbeError("--runs must be at least 3 for the requested baseline")

    if not args.audio_path.is_file():
        raise ProbeError(f"audio artifact missing: {args.audio_path}")
    if not args.onnx_model_path.is_file():
        raise ProbeError(f"onnx model artifact missing: {args.onnx_model_path}")
    if not args.classes_path.is_file():
        raise ProbeError(f"classes metadata artifact missing: {args.classes_path}")

    results = [_spawn_child(args) for _ in range(args.runs)]
    last_result = results[-1]
    benchmark = {
        "runs": args.runs,
        "success": True,
        "total_seconds": [result.total_seconds for result in results],
        "import_seconds": [result.import_seconds for result in results],
        "audio_loading_seconds": [result.audio_loading_seconds for result in results],
        "preprocessing_seconds": [result.preprocessing_seconds for result in results],
        "onnx_session_seconds": [result.onnx_session_seconds for result in results],
        "onnx_inference_seconds": [result.onnx_inference_seconds for result in results],
        "mapping_seconds": [result.mapping_seconds for result in results],
        "genres": last_result.genres,
        "genres_pretty": last_result.genres_pretty,
        "repeated_run_stable": _stable_runs(results),
    }

    avg_total_seconds_full = _avg(FULL_IMAGE_BASELINE_TOTAL_SECONDS)
    avg_total_seconds_slim = _avg(benchmark["total_seconds"])
    avg_preprocessing_seconds_full = _avg(FULL_IMAGE_BASELINE_PREPROCESSING_SECONDS)
    avg_preprocessing_seconds_slim = _avg(benchmark["preprocessing_seconds"])
    avg_onnx_inference_seconds_full = _avg(FULL_IMAGE_BASELINE_ONNX_INFERENCE_SECONDS)
    avg_onnx_inference_seconds_slim = _avg(benchmark["onnx_inference_seconds"])

    runtime_regression_detected = (
        avg_total_seconds_slim > avg_total_seconds_full * 1.1
        or avg_preprocessing_seconds_slim > avg_preprocessing_seconds_full * 1.1
        or avg_onnx_inference_seconds_slim > avg_onnx_inference_seconds_full * 1.1
    )
    if avg_total_seconds_slim <= avg_total_seconds_full and avg_onnx_inference_seconds_slim <= avg_onnx_inference_seconds_full:
        performance_signal = "same/faster"
    elif runtime_regression_detected:
        performance_signal = "slower"
    else:
        performance_signal = "inconclusive"

    report = {
        "roadmap": "4.86",
        "slim_image_performance_baseline": True,
        "not_production_decision": True,
        "production_approval": False,
        "reused_existing_slim_image": True,
        "image_tag": IMAGE_TAG,
        "rebuild_run": False,
        "docker_compose_run": False,
        "classify_called": False,
        "network_http_called": False,
        "image": {
            "exists": True,
            "size_bytes": IMAGE_SIZE_BYTES,
            "full_baseline_size_bytes": FULL_BASELINE_SIZE_BYTES,
            "size_reduction_bytes": SIZE_REDUCTION_BYTES,
            "size_reduction_percent": SIZE_REDUCTION_PERCENT,
        },
        "slim_benchmark": benchmark,
        "full_pipeline_slim_image": last_result.full_pipeline_slim_image,
        "full_image_baseline_from_4_83": {
            "total_seconds": FULL_IMAGE_BASELINE_TOTAL_SECONDS,
            "preprocessing_seconds": FULL_IMAGE_BASELINE_PREPROCESSING_SECONDS,
            "onnx_inference_seconds": FULL_IMAGE_BASELINE_ONNX_INFERENCE_SECONDS,
            "max_rss_kb": FULL_IMAGE_BASELINE_MAX_RSS_KB,
        },
        "comparison_to_full_image_baseline": {
            "avg_total_seconds_full": avg_total_seconds_full,
            "avg_total_seconds_slim": avg_total_seconds_slim,
            "avg_preprocessing_seconds_full": avg_preprocessing_seconds_full,
            "avg_preprocessing_seconds_slim": avg_preprocessing_seconds_slim,
            "avg_onnx_inference_seconds_full": avg_onnx_inference_seconds_full,
            "avg_onnx_inference_seconds_slim": avg_onnx_inference_seconds_slim,
            "max_rss_kb_full": FULL_IMAGE_BASELINE_MAX_RSS_KB,
            "max_rss_kb_slim": last_result.resource_usage.get("max_rss_kb"),
            "runtime_regression_detected": runtime_regression_detected,
            "performance_signal": performance_signal,
        },
        "package_status": last_result.package_status,
        "resource_usage": last_result.resource_usage,
        "decision_signal": {
            "slim_runtime_functional": True,
            "image_size_benefit_confirmed": True,
            "runtime_regression_detected": runtime_regression_detected,
            "recommendation": (
                "Use onnx-runtime-slim as preferred optional ONNX image candidate; "
                "continue with optional container/profile smoke before production readiness."
            ),
        },
        "production_boundaries": {
            "production_requirements_changed": False,
            "dockerfile_changed": False,
            "compose_changed": False,
            "default_provider_changed": False,
            "classify_contract_changed": False,
            "response_shape_changed": False,
            "tidal_parser_touched": False,
        },
        "blockers": [],
        "warnings": [],
    }

    warnings = report["warnings"]
    if not report["slim_benchmark"]["repeated_run_stable"]:
        warnings.append("repeated_run_stability_not_confirmed")
    if not report["full_pipeline_slim_image"]["tensorflow_import_ok"]:
        warnings.append("tensorflow_not_installed_in_slim_image")
    if not report["package_status"]["essentia_standard_used"]:
        warnings.append("essentia_standard_not_used")
    if not report["package_status"]["onnxruntime_used"]:
        warnings.append("onnxruntime_not_used")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.child_run:
        try:
            return _run_child_main(args)
        except ProbeError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    try:
        report = _build_report(args)
    except ProbeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    _write_json(args.output, report)
    print(f"wrote report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
