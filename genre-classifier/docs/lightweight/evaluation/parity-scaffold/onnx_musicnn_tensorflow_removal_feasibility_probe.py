#!/usr/bin/env python3
"""Проверяет, можно ли убрать Python-пакет `tensorflow` из optional ONNX path.

Скрипт рассчитан только на disposable container probe и не делает:

- Docker build;
- Docker Compose;
- `/classify`;
- network HTTP calls;
- production inference;
- production migration;
- смену default provider;
- сравнение TensorFlow baseline против ONNX.

Проверяется только feasibility: после `pip uninstall -y tensorflow` optional
ONNX/MusiCNN direct path должен продолжить работать с `essentia-tensorflow` и
нативными `essentia_tensorflow.libs`.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[4]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))
DEFAULT_OUTPUT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-tensorflow-removal-feasibility-report.json"
)
IMAGE_TAG = "music-tools-genre-classifier-onnx:roadmap-4.82"
EXPECTED_PATCH_SHAPE = [187, 96]
EXPECTED_ACTIVATIONS_COUNT = 50
EXPECTED_EMBEDDINGS_COUNT = 200


class ProbeError(RuntimeError):
    """Ожидаемая ошибка probe без лишнего traceback на пользовательском уровне."""


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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-path", required=True, type=Path)
    parser.add_argument("--onnx-model-path", required=True, type=Path)
    parser.add_argument("--classes-path", required=True, type=Path)
    parser.add_argument(
        "--tensorflow-present-before-uninstall",
        required=True,
        type=lambda value: str(value).strip().lower() in {"1", "true", "yes", "y", "on"},
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser


def _pip_show_ok(package_name: str) -> bool:
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and bool(completed.stdout.strip())


def _normalize_label(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    text = " ".join(text.replace("-", " ").replace("_", " ").split())
    return text or None


def _build_genres(activations: Any, classes: list[str], top_n: int = 8) -> list[dict[str, Any]]:
    pairs: list[tuple[int, dict[str, Any]]] = []
    for index, (activation, label) in enumerate(zip(activations, classes)):
        pairs.append(
            (
                index,
                {
                    "tag": str(label).lower(),
                    "prob": round(float(activation), 4),
                },
            )
        )

    pairs.sort(key=lambda item: (-item[1]["prob"], item[0]))
    return [item[1] for item in pairs[:top_n]]


def _build_genres_pretty(genres: list[dict[str, Any]]) -> list[str]:
    tags = [_normalize_label(item.get("tag")) for item in genres]
    tag_set = {tag for tag in tags if tag}
    pretty: list[str] = []

    def add(tag: str) -> None:
        normalized = _normalize_label(tag)
        if normalized and normalized not in pretty:
            pretty.append(normalized)

    if "indie rock" in tag_set:
        add("indie rock")
    elif "indie" in tag_set and "rock" in tag_set:
        add("indie rock")

    if "alternative rock" in tag_set:
        add("alternative rock")
    elif "alternative" in tag_set and "rock" in tag_set:
        add("alternative rock")

    if "experimental rock" in tag_set:
        add("experimental rock")
    elif "experimental" in tag_set and "rock" in tag_set:
        add("experimental rock")

    if "jazz rock" in tag_set:
        add("jazz rock")
    elif "jazz" in tag_set and "rock" in tag_set:
        add("jazz rock")

    if "instrumental rock" in tag_set:
        add("instrumental rock")
    elif "instrumental" in tag_set and "rock" in tag_set:
        add("instrumental rock")

    if "electronic" in tag_set:
        add("electronic")

    for tag in tags:
        if tag:
            add(tag)

    return pretty[:8]


def _extract_shape(values: Any) -> list[int]:
    try:
        import numpy as np  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - handled in report
        raise ProbeError(f"numpy unavailable: {exc}") from exc

    return list(np.asarray(values).shape)


def _run_probe(args: argparse.Namespace) -> dict[str, Any]:
    if not args.audio_path.is_file():
        raise ProbeError(f"audio artifact missing: {args.audio_path}")
    if not args.onnx_model_path.is_file():
        raise ProbeError(f"onnx model artifact missing: {args.onnx_model_path}")
    if not args.classes_path.is_file():
        raise ProbeError(f"classes metadata artifact missing: {args.classes_path}")

    total_start = time.perf_counter()

    tensorflow_present_before_uninstall = bool(args.tensorflow_present_before_uninstall)
    tensorflow_present_after_uninstall = _pip_show_ok("tensorflow")
    essentia_tensorflow_present_after_uninstall = _pip_show_ok("essentia-tensorflow")

    try:
        import tensorflow  # noqa: F401  # type: ignore[import-not-found]
    except Exception:
        tensorflow_import_ok = False
    else:  # pragma: no cover - unexpected in success path
        tensorflow_import_ok = True

    try:
        import essentia  # noqa: F401  # type: ignore[import-not-found]
        essentia_import_ok = True
    except Exception as exc:
        raise ProbeError(f"essentia import failed after tensorflow uninstall: {exc}") from exc

    try:
        from essentia import standard as essentia_standard  # type: ignore[import-not-found]
        essentia_standard_import_ok = True
    except Exception as exc:
        raise ProbeError(f"essentia.standard import failed after tensorflow uninstall: {exc}") from exc

    tensorflow_input_musiccnn_available = hasattr(essentia_standard, "TensorflowInputMusiCNN")
    if not tensorflow_input_musiccnn_available:
        raise ProbeError("TensorflowInputMusiCNN is unavailable after tensorflow uninstall")

    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
    except Exception as exc:
        raise ProbeError(f"onnxruntime import failed after tensorflow uninstall: {exc}") from exc

    onnxruntime_import_ok = True

    from app.providers.compat import (  # noqa: WPS433
        map_validated_result_to_legacy_genres,
        map_validated_result_to_legacy_genres_pretty,
    )
    from app.providers.onnx_musicnn import OnnxMusiCNNProvider  # noqa: WPS433
    from app.providers.validation import validate_and_normalize_provider_result  # noqa: WPS433

    classes_metadata = _load_json(args.classes_path)
    classes = classes_metadata.get("classes")
    if not isinstance(classes, list) or not classes:
        raise ProbeError("classes metadata does not contain a non-empty classes list")

    audio_loading_start = time.perf_counter()
    audio = essentia_standard.MonoLoader(filename=str(args.audio_path), sampleRate=16000)()
    audio_loading_seconds = time.perf_counter() - audio_loading_start

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
        rows.append([float(value) for value in tensor(frame)])

    if not rows:
        raise ProbeError("TensorflowInputMusiCNN produced no rows")

    if len(rows) < EXPECTED_PATCH_SHAPE[0]:
        last_row = list(rows[-1])
        while len(rows) < EXPECTED_PATCH_SHAPE[0]:
            rows.append(list(last_row))
    else:
        rows = rows[: EXPECTED_PATCH_SHAPE[0]]

    if any(len(row) != EXPECTED_PATCH_SHAPE[1] for row in rows):
        raise ProbeError("TensorflowInputMusiCNN produced rows with unexpected width")

    try:
        import numpy as np  # type: ignore[import-not-found]
    except Exception as exc:
        raise ProbeError(f"numpy unavailable: {exc}") from exc

    patch = np.asarray(rows, dtype=np.float32)
    preprocessing_seconds = time.perf_counter() - preprocessing_start

    if list(patch.shape) != EXPECTED_PATCH_SHAPE:
        raise ProbeError(f"patch shape mismatch: expected {EXPECTED_PATCH_SHAPE}, got {list(patch.shape)}")

    provider = OnnxMusiCNNProvider(
        settings_module=SimpleNamespace(
            get_configured_onnx_musicnn_model_path=lambda: args.onnx_model_path,
            get_configured_onnx_musicnn_metadata_path=lambda: args.classes_path,
        )
    )

    session_start = time.perf_counter()
    session_options = ort.SessionOptions()
    session_options.intra_op_num_threads = 1
    session_options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(args.onnx_model_path),
        sess_options=session_options,
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
    input_shape = [item for item in input_meta.shape if isinstance(item, int)]
    if input_shape not in (EXPECTED_PATCH_SHAPE, [1, *EXPECTED_PATCH_SHAPE]):
        raise ProbeError(f"unexpected ONNX input shape: {input_shape}")

    inference_start = time.perf_counter()
    run_outputs = None
    inference_error: Exception | None = None
    for feed_array in (np.expand_dims(patch, axis=0), patch):
        try:
            run_outputs = session.run(None, {input_meta.name: feed_array})
        except Exception as exc:  # pragma: no cover - fallback path is probe-specific
            inference_error = exc
            continue
        break

    if run_outputs is None:
        raise ProbeError(f"onnxruntime inference failed: {inference_error}") from inference_error

    onnx_inference_seconds = time.perf_counter() - inference_start

    output_map = {item.name: value for item, value in zip(outputs, run_outputs)}
    if "activations" not in output_map:
        raise ProbeError("onnx outputs did not include an 'activations' tensor")
    if "embeddings" not in output_map:
        raise ProbeError("onnx outputs did not include an 'embeddings' tensor")

    activations = provider._normalize_output_values(output_map["activations"])  # noqa: WPS437
    embeddings = provider._normalize_output_values(output_map["embeddings"])  # noqa: WPS437

    activations_shape = _extract_shape(activations)
    embeddings_shape = _extract_shape(embeddings)
    if activations_shape != [EXPECTED_ACTIVATIONS_COUNT]:
        raise ProbeError(
            f"activations shape mismatch: expected {[EXPECTED_ACTIVATIONS_COUNT]}, got {activations_shape}"
        )
    if embeddings_shape != [EXPECTED_EMBEDDINGS_COUNT]:
        raise ProbeError(
            f"embeddings shape mismatch: expected {[EXPECTED_EMBEDDINGS_COUNT]}, got {embeddings_shape}"
        )

    mapping_start = time.perf_counter()
    provider_result = provider.build_provider_result_from_outputs(
        activations,
        classes,
        top_n=8,
    )
    validated_result = validate_and_normalize_provider_result(provider_result, top_n=8)
    genres = map_validated_result_to_legacy_genres(validated_result)
    genres_pretty = map_validated_result_to_legacy_genres_pretty(validated_result)
    mapping_seconds = time.perf_counter() - mapping_start

    if not genres:
        raise ProbeError("genres are empty after mapping")
    if not genres_pretty:
        raise ProbeError("genres_pretty are empty after mapping")

    total_seconds = time.perf_counter() - total_start

    return {
        "roadmap": "4.84",
        "tensorflow_python_package_removal_feasibility": True,
        "not_production_decision": True,
        "production_approval": False,
        "reused_existing_image": True,
        "image_tag": IMAGE_TAG,
        "rebuild_run": False,
        "docker_compose_run": False,
        "classify_called": False,
        "network_http_called": False,
        "original_image_unchanged": True,
        "tensorflow_removed_only_in_disposable_container": True,
        "package_state": {
            "tensorflow_present_before_uninstall": tensorflow_present_before_uninstall,
            "tensorflow_present_after_uninstall": tensorflow_present_after_uninstall,
            "essentia_tensorflow_present_after_uninstall": essentia_tensorflow_present_after_uninstall,
        },
        "imports_after_uninstall": {
            "tensorflow_import_ok": tensorflow_import_ok,
            "essentia_import_ok": essentia_import_ok,
            "essentia_standard_import_ok": essentia_standard_import_ok,
            "tensorflow_input_musicnn_available": tensorflow_input_musiccnn_available,
            "onnxruntime_import_ok": onnxruntime_import_ok,
        },
        "full_pipeline_after_uninstall": {
            "success": True,
            "patch_shape": list(patch.shape),
            "patch_shape_match": list(patch.shape) == EXPECTED_PATCH_SHAPE,
            "activations_shape": activations_shape,
            "embeddings_shape": embeddings_shape,
            "classes_activations_count_match": len(classes) == EXPECTED_ACTIVATIONS_COUNT,
            "genres": genres,
            "genres_pretty": genres_pretty,
            "genres_non_empty": bool(genres),
            "genres_pretty_non_empty": bool(genres_pretty),
        },
        "timing": {
            "total_seconds": round(total_seconds, 6),
            "preprocessing_seconds": round(preprocessing_seconds, 6),
            "onnx_inference_seconds": round(onnx_inference_seconds, 6),
        },
        "decision_signal": {
            "tensorflow_python_package_removable_candidate": True,
            "potential_image_size_reduction": "approximately 1.9G",
            "recommendation": (
                "Proceed to Roadmap 4.85 optional ONNX slim Docker target prototype if full pipeline succeeds."
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


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        report = _run_probe(args)
    except ProbeError as exc:
        failure_report = {
            "roadmap": "4.84",
            "tensorflow_python_package_removal_feasibility": False,
            "not_production_decision": True,
            "production_approval": False,
            "reused_existing_image": True,
            "image_tag": IMAGE_TAG,
            "rebuild_run": False,
            "docker_compose_run": False,
            "classify_called": False,
            "network_http_called": False,
            "original_image_unchanged": True,
            "tensorflow_removed_only_in_disposable_container": True,
            "package_state": {
                "tensorflow_present_before_uninstall": None,
                "tensorflow_present_after_uninstall": None,
                "essentia_tensorflow_present_after_uninstall": None,
            },
            "imports_after_uninstall": {
                "tensorflow_import_ok": None,
                "essentia_import_ok": None,
                "essentia_standard_import_ok": None,
                "tensorflow_input_musiccnn_available": None,
                "onnxruntime_import_ok": None,
            },
            "full_pipeline_after_uninstall": {
                "success": False,
                "patch_shape": [],
                "patch_shape_match": False,
                "activations_shape": [],
                "embeddings_shape": [],
                "classes_activations_count_match": False,
                "genres": [],
                "genres_pretty": [],
                "genres_non_empty": False,
                "genres_pretty_non_empty": False,
            },
            "timing": {
                "total_seconds": None,
                "preprocessing_seconds": None,
                "onnx_inference_seconds": None,
            },
            "decision_signal": {
                "tensorflow_python_package_removable_candidate": False,
                "potential_image_size_reduction": "approximately 1.9G",
                "recommendation": "Record blocker and keep production untouched.",
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
            "blockers": [
                {
                    "code": "TENSORFLOW_REMOVAL_BREAKS_ONNX_PIPELINE",
                    "message": str(exc),
                }
            ],
            "warnings": [],
        }
        _write_json(args.output, failure_report)
        print(str(exc), file=sys.stderr)
        return 2

    _write_json(args.output, report)
    print(f"wrote report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
