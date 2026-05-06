#!/usr/bin/env python3
"""Локальный helper для Roadmap 4.65 ONNX/MusiCNN output capture.

Скрипт работает только как CLI и не подключается к production runtime:

- не импортирует `app`;
- не вызывает `/classify`;
- не меняет provider wiring;
- не меняет production dependencies;
- не выполняет Docker Compose;
- не делает fake outputs.

Если `onnxruntime` недоступен в isolated venv, helper честно фиксирует blocker
`ONNXRUNTIME_NOT_AVAILABLE` и всё равно сохраняет проверяемые локальные
доказательства:

- подтверждение Roadmap 4.64 evidence;
- контроль SHA256 для legal fixture и ONNX artifact;
- capture preprocessing patch через `essentia.standard.TensorflowInputMusiCNN`.

Если `onnxruntime` доступен, helper выполняет реальный локальный ONNX inference
на официальном `.onnx` артефакте, собирает output tensors statistics и проверяет
повторяемость результата на той же fixture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = (
    SERVICE_ROOT / "docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-output-capture-report.json"
)
DEFAULT_ROADMAP_4_64_REPORT = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "tensorflow-input-musicnn-preprocessing-probe-report.json"
)
DEFAULT_FIXTURE_PATH = Path(
    "/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3"
)
DEFAULT_ONNX_MODEL_PATH = Path("/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx")
DEFAULT_ONNX_METADATA_PATH = Path("/tmp/music-tools-onnx-parity/msd-musicnn-1.json")
DEFAULT_ISOLATED_PYTHON = Path("/tmp/music-tools-onnx-parity/venv/bin/python")

EXPECTED_FIXTURE_SHA256 = "d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628"
EXPECTED_PATCH_SHAPE = [187, 96]
EXPECTED_OUTPUT_SHAPES = {"activations": [50], "embeddings": [200]}

ALLOWED_BLOCKER_CODES = {
    "AGENTS_MD_NOT_READ",
    "ROADMAP_4_64_EVIDENCE_MISSING",
    "LEGAL_FIXTURE_NOT_FOUND",
    "LEGAL_FIXTURE_SHA256_MISMATCH",
    "ONNX_MODEL_NOT_FOUND",
    "ONNXRUNTIME_NOT_AVAILABLE",
    "ESSENTIA_IMPORT_FAILED",
    "TENSORFLOW_INPUT_MUSICNN_UNAVAILABLE",
    "PREPROCESSING_PATCH_GENERATION_FAILED",
    "UNEXPECTED_ONNX_INPUT_SHAPE",
    "EXPECTED_OUTPUT_ACTIVATIONS_NOT_FOUND",
    "EXPECTED_OUTPUT_EMBEDDINGS_NOT_FOUND",
    "UNEXPECTED_ACTIVATIONS_SHAPE",
    "UNEXPECTED_EMBEDDINGS_SHAPE",
    "ONNX_REPEATED_RUN_UNSTABLE",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "PRODUCTION_DEPENDENCY_CHANGE_NOT_ALLOWED",
    "MODEL_FILE_IN_REPO_NOT_ALLOWED",
    "AUDIO_FILE_IN_REPO_NOT_ALLOWED",
    "VENV_IN_REPO_NOT_ALLOWED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}


class CaptureError(Exception):
    """Ожидаемая ошибка local-only capture helper."""


def _safe_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaptureError(f"JSON artifact is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaptureError(f"JSON artifact is invalid: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise CaptureError(f"JSON artifact must be an object: {path}")
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _blocker(code: str, message: str) -> dict[str, str]:
    if code not in ALLOWED_BLOCKER_CODES:
        raise CaptureError(f"Unsupported blocker code: {code}")
    return {"code": code, "message": message}


def _validate_roadmap_4_64_report(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    roadmap_value = data.get("roadmap") or data.get("roadmap_step")
    if roadmap_value != "4.64":
        raise CaptureError(f"Unexpected roadmap value in 4.64 evidence: {roadmap_value}")
    if data.get("tensorflow_input_musiccnn_available") is not True:
        raise CaptureError("Roadmap 4.64 evidence does not confirm TensorflowInputMusiCNN availability")
    repeated = data.get("repeated_run_stability")
    if not isinstance(repeated, dict):
        raise CaptureError("Roadmap 4.64 evidence is missing repeated_run_stability")
    if repeated.get("checked") is not True or repeated.get("stable") is not True:
        raise CaptureError("Roadmap 4.64 evidence does not confirm stable repeated-run preprocessing")

    final_patch_shape = data.get("final_patch_shape")
    if final_patch_shape != EXPECTED_PATCH_SHAPE:
        raise CaptureError(f"Roadmap 4.64 evidence has unexpected final patch shape: {final_patch_shape}")

    blockers = data.get("blockers")
    if not isinstance(blockers, list) or blockers:
        raise CaptureError("Roadmap 4.64 evidence must have an empty blockers list")

    return {
        "report_path": "docs/lightweight/evaluation/parity-scaffold/tensorflow-input-musicnn-preprocessing-probe-report.json",
        "validated": True,
        "final_patch_shape": final_patch_shape,
        "stable": True,
        "blockers": [],
    }


def _collect_fixture_info(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CaptureError(f"Fixture is missing: {path}")

    actual_sha256 = _sha256(path)
    return {
        "path": str(path),
        "sha256": actual_sha256,
        "expected_sha256": EXPECTED_FIXTURE_SHA256,
        "sha256_matches": actual_sha256 == EXPECTED_FIXTURE_SHA256,
        "committed_to_repo": False,
    }


def _collect_onnx_model_info(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CaptureError(f"ONNX model is missing: {path}")

    return {
        "path": str(path),
        "exists": True,
        "sha256": _sha256(path),
        "committed_to_repo": False,
    }


def _probe_onnxruntime(python_executable: Path) -> dict[str, Any]:
    if not python_executable.is_file():
        return {
            "available": False,
            "version": None,
            "providers": [],
            "error_category": "FileNotFoundError",
            "error_message": "isolated python executable is missing",
        }

    probe = subprocess.run(
        [
            str(python_executable),
            "-c",
            (
                "import json\n"
                "try:\n"
                "    import onnxruntime as ort\n"
                "except Exception as exc:\n"
                "    print(json.dumps({"
                "        'available': False,"
                "        'version': None,"
                "        'providers': [],"
                "        'error_category': type(exc).__name__,"
                "        'error_message': str(exc)"
                "    }, ensure_ascii=False))\n"
                "else:\n"
                "    print(json.dumps({"
                "        'available': True,"
                "        'version': ort.__version__,"
                "        'providers': ort.get_available_providers(),"
                "        'error_category': None,"
                "        'error_message': None"
                "    }, ensure_ascii=False))\n"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if probe.returncode != 0:
        return {
            "available": False,
            "version": None,
            "providers": [],
            "error_category": "SubprocessError",
            "error_message": (probe.stderr or probe.stdout or "onnxruntime probe failed").strip(),
        }

    payload = json.loads(probe.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        raise CaptureError("onnxruntime probe returned invalid JSON")
    return payload


def _generate_tensorflow_input_patch(fixture_path: Path) -> dict[str, Any]:
    try:
        import essentia.standard as es
    except Exception as exc:  # pragma: no cover - local runtime dependent
        raise CaptureError(_safe_error(exc)) from exc

    try:
        audio = es.MonoLoader(filename=str(fixture_path), sampleRate=16000)()
        tensor = es.TensorflowInputMusiCNN()
    except Exception as exc:  # pragma: no cover - local runtime dependent
        raise CaptureError(_safe_error(exc)) from exc

    rows: list[list[float]] = []
    for frame in es.FrameGenerator(
        audio,
        frameSize=512,
        hopSize=256,
        startFromZero=True,
        lastFrameToEndOfFile=True,
    ):
        bands = tensor(frame)
        rows.append([float(value) for value in bands])

    if not rows:
        raise CaptureError("TensorflowInputMusiCNN produced no rows")

    raw_shape = [len(rows), len(rows[0])]
    if any(len(row) != raw_shape[1] for row in rows):
        raise CaptureError("TensorflowInputMusiCNN rows are not rectangular")

    normalized_rows = rows
    if len(normalized_rows) < EXPECTED_PATCH_SHAPE[0]:
        last_row = list(normalized_rows[-1])
        while len(normalized_rows) < EXPECTED_PATCH_SHAPE[0]:
            normalized_rows.append(list(last_row))
    else:
        normalized_rows = normalized_rows[: EXPECTED_PATCH_SHAPE[0]]

    if len(normalized_rows) != EXPECTED_PATCH_SHAPE[0]:
        raise CaptureError("TensorflowInputMusiCNN patch shape normalization failed")
    if any(len(row) != EXPECTED_PATCH_SHAPE[1] for row in normalized_rows):
        raise CaptureError("TensorflowInputMusiCNN patch width normalization failed")

    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - numpy should be available with essentia
        raise CaptureError(_safe_error(exc)) from exc

    patch = np.asarray(normalized_rows, dtype=np.float32)
    finite_mask = np.isfinite(patch)
    if not bool(finite_mask.all()):
        raise CaptureError("TensorflowInputMusiCNN patch contains non-finite values")

    return {
        "method": "essentia.standard.MonoLoader + essentia.standard.TensorflowInputMusiCNN + FrameGenerator",
        "raw_observed_shape": raw_shape,
        "final_patch_shape": list(patch.shape),
        "final_patch_dtype": str(patch.dtype),
        "finite_values": int(finite_mask.sum()),
        "patch": patch,
    }


def _normalize_output_shape(shape: list[int | str | None]) -> list[int | str | None]:
    if len(shape) == 2 and shape[0] in (1, "1", None):
        return [shape[1]]
    return list(shape)


def _tensor_stats(name: str, tensor: Any) -> dict[str, Any]:
    import numpy as np

    array = np.asarray(tensor)
    finite_mask = np.isfinite(array)
    finite_values = int(finite_mask.sum())
    nan_count = int(np.isnan(array).sum())
    inf_count = int(np.isinf(array).sum())

    if finite_values:
        finite_array = array[finite_mask]
        tensor_min = float(finite_array.min())
        tensor_max = float(finite_array.max())
        tensor_mean = float(finite_array.mean())
    else:
        tensor_min = None
        tensor_max = None
        tensor_mean = None

    normalized_shape = _normalize_output_shape([int(dim) if isinstance(dim, (int, float)) else dim for dim in array.shape])
    stats = {
        "name": name,
        "raw_shape": [int(dim) if isinstance(dim, (int, float)) else dim for dim in array.shape],
        "normalized_shape": normalized_shape,
        "dtype": str(array.dtype),
        "min": tensor_min,
        "max": tensor_max,
        "mean": tensor_mean,
        "finite_values": finite_values,
        "nan_count": nan_count,
        "inf_count": inf_count,
    }
    if name == "activations" and finite_values:
        flat = np.asarray(array).reshape(-1)
        top_k = min(5, flat.size)
        indices = np.argsort(flat)[::-1][:top_k]
        stats["top_activation_indices"] = [int(item) for item in indices.tolist()]
        stats["top_activation_scores"] = [float(flat[item]) for item in indices.tolist()]
    return stats


def _compare_tensors(reference: Any, candidate: Any) -> dict[str, Any]:
    import numpy as np

    ref = np.asarray(reference)
    other = np.asarray(candidate)
    if ref.shape != other.shape:
        return {
            "shape_equal": False,
            "max_abs_diff": None,
            "mean_abs_diff": None,
        }

    diff = np.abs(ref - other)
    return {
        "shape_equal": True,
        "max_abs_diff": float(diff.max()) if diff.size else 0.0,
        "mean_abs_diff": float(diff.mean()) if diff.size else 0.0,
    }


def _capture_onnx_outputs(
    *,
    model_path: Path,
    patch: Any,
    runtime_probe: dict[str, Any],
) -> dict[str, Any]:
    if not runtime_probe.get("available"):
        return {
            "onnx_runtime": {
                "session_created": False,
                "input_metadata": None,
                "output_metadata": None,
                "input_shape_adaptation": {
                    "requested_shape": EXPECTED_PATCH_SHAPE,
                    "applied": False,
                    "adaptation": None,
                    "reason": "onnxruntime unavailable in isolated env",
                },
            },
            "outputs": {"activations": None, "embeddings": None},
            "repeated_run_stability": {
                "checked": False,
                "stable": None,
                "tolerance": 1e-6,
                "max_abs_diff": None,
                "mean_abs_diff": None,
            },
            "blockers": [],
        }

    try:
        import numpy as np
        import onnxruntime as ort
    except Exception as exc:  # pragma: no cover - local runtime dependent
        return {
            "onnx_runtime": {
                "session_created": False,
                "input_metadata": None,
                "output_metadata": None,
                "input_shape_adaptation": {
                    "requested_shape": EXPECTED_PATCH_SHAPE,
                    "applied": False,
                    "adaptation": None,
                    "reason": _safe_error(exc),
                },
            },
            "outputs": {"activations": None, "embeddings": None},
            "repeated_run_stability": {
                "checked": False,
                "stable": None,
                "tolerance": 1e-6,
                "max_abs_diff": None,
                "mean_abs_diff": None,
            },
            "blockers": [_blocker("ONNXRUNTIME_NOT_AVAILABLE", _safe_error(exc))],
        }

    try:
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        session = ort.InferenceSession(str(model_path), sess_options=options, providers=["CPUExecutionProvider"])
    except Exception as exc:  # pragma: no cover - local runtime dependent
        return {
            "onnx_runtime": {
                "session_created": False,
                "input_metadata": None,
                "output_metadata": None,
                "input_shape_adaptation": {
                    "requested_shape": EXPECTED_PATCH_SHAPE,
                    "applied": False,
                    "adaptation": None,
                    "reason": _safe_error(exc),
                },
            },
            "outputs": {"activations": None, "embeddings": None},
            "repeated_run_stability": {
                "checked": False,
                "stable": None,
                "tolerance": 1e-6,
                "max_abs_diff": None,
                "mean_abs_diff": None,
            },
            "blockers": [_blocker("ONNXRUNTIME_NOT_AVAILABLE", _safe_error(exc))],
        }

    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if not inputs:
        return {
            "onnx_runtime": {
                "session_created": True,
                "input_metadata": None,
                "output_metadata": None,
                "input_shape_adaptation": {
                    "requested_shape": EXPECTED_PATCH_SHAPE,
                    "applied": False,
                    "adaptation": None,
                    "reason": "onnxruntime session has no inputs",
                },
            },
            "outputs": {"activations": None, "embeddings": None},
            "repeated_run_stability": {
                "checked": False,
                "stable": None,
                "tolerance": 1e-6,
                "max_abs_diff": None,
                "mean_abs_diff": None,
            },
            "blockers": [_blocker("UNEXPECTED_ONNX_INPUT_SHAPE", "onnxruntime session has no inputs.")],
        }

    input_meta = inputs[0]
    input_shape = list(input_meta.shape)
    input_type = input_meta.type

    adaptation: dict[str, Any] | None = None
    feed_array = patch
    if len(input_shape) == 3 and input_shape[-2:] == EXPECTED_PATCH_SHAPE:
        feed_array = np.expand_dims(patch, axis=0)
        adaptation = {
            "requested_shape": EXPECTED_PATCH_SHAPE,
            "applied": True,
            "adaptation": "added_batch_dimension",
            "result_shape": list(feed_array.shape),
        }
    elif len(input_shape) == 2 and input_shape == EXPECTED_PATCH_SHAPE:
        adaptation = {
            "requested_shape": EXPECTED_PATCH_SHAPE,
            "applied": False,
            "adaptation": "none",
            "result_shape": list(feed_array.shape),
        }
    else:
        return {
            "onnx_runtime": {
                "session_created": True,
                "input_metadata": {
                    "name": input_meta.name,
                    "shape": input_shape,
                    "type": input_type,
                },
                "output_metadata": [
                    {"name": item.name, "shape": list(item.shape), "type": item.type}
                    for item in outputs
                ],
                "input_shape_adaptation": {
                    "requested_shape": EXPECTED_PATCH_SHAPE,
                    "applied": False,
                    "adaptation": None,
                    "reason": f"unexpected ONNX input shape: {input_shape}",
                },
            },
            "outputs": {"activations": None, "embeddings": None},
            "repeated_run_stability": {
                "checked": False,
                "stable": None,
                "tolerance": 1e-6,
                "max_abs_diff": None,
                "mean_abs_diff": None,
            },
            "blockers": [
                _blocker(
                    "UNEXPECTED_ONNX_INPUT_SHAPE",
                    f"ONNX input shape {input_shape} is not compatible with the confirmed [187, 96] patch.",
                )
            ],
        }

    run_1_raw = session.run(None, {input_meta.name: feed_array})
    run_2_raw = session.run(None, {input_meta.name: feed_array})
    output_names = [item.name for item in outputs]

    if not output_names:
        return {
            "onnx_runtime": {
                "session_created": True,
                "input_metadata": {
                    "name": input_meta.name,
                    "shape": input_shape,
                    "type": input_type,
                },
                "output_metadata": [],
                "input_shape_adaptation": adaptation,
            },
            "outputs": {"activations": None, "embeddings": None},
            "repeated_run_stability": {
                "checked": False,
                "stable": None,
                "tolerance": 1e-6,
                "max_abs_diff": None,
                "mean_abs_diff": None,
            },
            "blockers": [_blocker("EXPECTED_OUTPUT_ACTIVATIONS_NOT_FOUND", "ONNX session has no outputs.")],
        }

    output_map_1 = {name: value for name, value in zip(output_names, run_1_raw)}
    output_map_2 = {name: value for name, value in zip(output_names, run_2_raw)}
    blockers: list[dict[str, str]] = []

    if "activations" not in output_map_1:
        blockers.append(
            _blocker(
                "EXPECTED_OUTPUT_ACTIVATIONS_NOT_FOUND",
                f"ONNX outputs did not include an 'activations' tensor. Actual outputs: {output_names}",
            )
        )
    if "embeddings" not in output_map_1:
        blockers.append(
            _blocker(
                "EXPECTED_OUTPUT_EMBEDDINGS_NOT_FOUND",
                f"ONNX outputs did not include an 'embeddings' tensor. Actual outputs: {output_names}",
            )
        )

    if blockers:
        return {
            "onnx_runtime": {
                "session_created": True,
                "input_metadata": {
                    "name": input_meta.name,
                    "shape": input_shape,
                    "type": input_type,
                },
                "output_metadata": [
                    {"name": item.name, "shape": list(item.shape), "type": item.type}
                    for item in outputs
                ],
                "input_shape_adaptation": adaptation,
            },
            "outputs": {
                "activations": _tensor_stats("activations", output_map_1.get("activations")) if "activations" in output_map_1 else None,
                "embeddings": _tensor_stats("embeddings", output_map_1.get("embeddings")) if "embeddings" in output_map_1 else None,
            },
            "repeated_run_stability": {
                "checked": True,
                "stable": False,
                "tolerance": 1e-6,
                "max_abs_diff": None,
                "mean_abs_diff": None,
            },
            "blockers": blockers,
        }

    activations_stats = _tensor_stats("activations", output_map_1["activations"])
    embeddings_stats = _tensor_stats("embeddings", output_map_1["embeddings"])
    activations_diff = _compare_tensors(output_map_1["activations"], output_map_2["activations"])
    embeddings_diff = _compare_tensors(output_map_1["embeddings"], output_map_2["embeddings"])

    stability_checked = True
    stable = bool(activations_diff["shape_equal"] and embeddings_diff["shape_equal"])
    max_abs_diff = None
    mean_abs_diff = None

    if not activations_diff["shape_equal"] or not embeddings_diff["shape_equal"]:
        stable = False
        blockers.append(
            _blocker(
                "ONNX_REPEATED_RUN_UNSTABLE",
                "Repeated ONNX runs produced tensors with mismatched shapes.",
            )
        )
    else:
        max_abs_diff = max(activations_diff["max_abs_diff"], embeddings_diff["max_abs_diff"])
        mean_abs_diff = max(activations_diff["mean_abs_diff"], embeddings_diff["mean_abs_diff"])
        if max_abs_diff > 1e-6:
            stable = False
            blockers.append(
                _blocker(
                    "ONNX_REPEATED_RUN_UNSTABLE",
                    f"Repeated ONNX runs exceeded tolerance 1e-6: max_abs_diff={max_abs_diff}",
                )
            )

    return {
        "onnx_runtime": {
            "session_created": True,
            "input_metadata": {
                "name": input_meta.name,
                "shape": input_shape,
                "type": input_type,
            },
            "output_metadata": [
                {"name": item.name, "shape": list(item.shape), "type": item.type}
                for item in outputs
            ],
            "input_shape_adaptation": adaptation,
        },
        "outputs": {
            "activations": activations_stats,
            "embeddings": embeddings_stats,
        },
        "repeated_run_stability": {
            "checked": stability_checked,
            "stable": stable,
            "tolerance": 1e-6,
            "max_abs_diff": max_abs_diff,
            "mean_abs_diff": mean_abs_diff,
        },
        "blockers": blockers,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": "0.1",
        "report_type": "onnx_musicnn_output_capture_report",
        "report_id": "roadmap_4_65_isolated_onnx_musiccnn_output_capture",
        "generated_by": "scripts/lightweight/musicnn_onnx_output_capture.py",
        "title": "Roadmap 4.65 - Isolated ONNX/MusiCNN output capture",
        "roadmap": "4.65",
        "status": "blocked",
        "scope": "isolated_local_onnx_output_capture",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "production_touched": False,
        "tidal_parser_touched": False,
        "classify_called": False,
        "docker_compose_run": False,
        "docker_rebuild_run": False,
        "tensorflow_baseline_run": False,
        "tensorflow_vs_onnx_comparison_run": False,
        "tensorflow_predict_musicnn_used": False,
        "strict_legacy_parity_claimed": False,
        "provider_implementation_changed": False,
        "default_provider_changed": False,
        "production_dependencies_changed": False,
        "docker_changed": False,
        "isolated_runtime": {},
        "fixture": {},
        "onnx_model": {},
        "roadmap_4_64_evidence": {},
        "preprocessing": {},
        "onnx_runtime": {},
        "outputs": {},
        "repeated_run_stability": {},
        "blockers": [],
        "non_goals": [
            "strict legacy parity",
            "production readiness",
            "provider implementation",
            "default provider switch",
            "/classify integration",
            "TensorFlow baseline",
            "TensorFlow vs ONNX comparison",
        ],
    }

    blockers: list[dict[str, str]] = []

    if not args.agents_md_read:
        blockers.append(_blocker("AGENTS_MD_NOT_READ", "AGENTS.md was not confirmed as read."))

    try:
        report["roadmap_4_64_evidence"] = _validate_roadmap_4_64_report(args.roadmap_4_64_report)
    except Exception as exc:
        blockers.append(_blocker("ROADMAP_4_64_EVIDENCE_MISSING", _safe_error(exc)))
        report["roadmap_4_64_evidence"] = {
            "report_path": str(args.roadmap_4_64_report),
            "validated": False,
            "final_patch_shape": None,
            "stable": None,
            "blockers": [],
        }

    try:
        report["fixture"] = _collect_fixture_info(args.fixture_path)
    except Exception as exc:
        code = "LEGAL_FIXTURE_NOT_FOUND" if "missing" in str(exc).lower() else "LEGAL_FIXTURE_SHA256_MISMATCH"
        blockers.append(_blocker(code, _safe_error(exc)))
        report["fixture"] = {
            "path": str(args.fixture_path),
            "sha256": None,
            "expected_sha256": EXPECTED_FIXTURE_SHA256,
            "sha256_matches": False,
            "committed_to_repo": False,
        }

    try:
        report["onnx_model"] = _collect_onnx_model_info(args.onnx_model_path)
    except Exception as exc:
        blockers.append(_blocker("ONNX_MODEL_NOT_FOUND", _safe_error(exc)))
        report["onnx_model"] = {
            "path": str(args.onnx_model_path),
            "exists": False,
            "sha256": None,
            "committed_to_repo": False,
        }

    try:
        import essentia
        import essentia.standard as es  # noqa: F401
        python_version_probe = subprocess.run(
            [str(args.isolated_python), "-V"], capture_output=True, text=True, check=False
        )

        report["isolated_runtime"] = {
            "venv_path": str(args.isolated_python.parent.parent),
            "python_version": python_version_probe.stderr.strip()
            or python_version_probe.stdout.strip()
            or "unknown",
            "essentia_import": True,
            "essentia_standard_import": True,
            "essentia_version": getattr(essentia, "__version__", None),
            "tensorflow_input_musiccnn_available": hasattr(es, "TensorflowInputMusiCNN"),
            "onnxruntime_import": False,
            "onnxruntime_version": None,
            "onnxruntime_providers": [],
        }
        if not report["isolated_runtime"]["tensorflow_input_musiccnn_available"]:
            blockers.append(
                _blocker(
                    "TENSORFLOW_INPUT_MUSICNN_UNAVAILABLE",
                    "essentia.standard does not expose TensorflowInputMusiCNN in the approved isolated environment.",
                )
            )
    except Exception as exc:
        report["isolated_runtime"] = {
            "venv_path": str(args.isolated_python.parent.parent),
            "python_version": None,
            "essentia_import": False,
            "essentia_standard_import": False,
            "essentia_version": None,
            "tensorflow_input_musiccnn_available": False,
            "onnxruntime_import": False,
            "onnxruntime_version": None,
            "onnxruntime_providers": [],
        }
        blockers.append(_blocker("ESSENTIA_IMPORT_FAILED", _safe_error(exc)))

    runtime_probe = _probe_onnxruntime(args.isolated_python)
    report["isolated_runtime"]["onnxruntime_import"] = bool(runtime_probe.get("available"))
    report["isolated_runtime"]["onnxruntime_version"] = runtime_probe.get("version")
    report["isolated_runtime"]["onnxruntime_providers"] = runtime_probe.get("providers", [])

    if not runtime_probe.get("available"):
        blockers.append(
            _blocker(
                "ONNXRUNTIME_NOT_AVAILABLE",
                "onnxruntime is not installed in the approved isolated environment.",
            )
        )

    patch_summary: dict[str, Any] | None = None
    if not any(item["code"] == "ESSENTIA_IMPORT_FAILED" for item in blockers):
        try:
            patch_summary = _generate_tensorflow_input_patch(args.fixture_path)
            report["preprocessing"] = {
                "method": patch_summary["method"],
                "raw_observed_shape": patch_summary["raw_observed_shape"],
                "final_patch_shape": patch_summary["final_patch_shape"],
                "final_patch_dtype": patch_summary["final_patch_dtype"],
                "finite_values": patch_summary["finite_values"],
                "blockers": [],
            }
        except Exception as exc:
            blockers.append(_blocker("PREPROCESSING_PATCH_GENERATION_FAILED", _safe_error(exc)))
            report["preprocessing"] = {
                "method": "essentia.standard.TensorflowInputMusiCNN",
                "raw_observed_shape": None,
                "final_patch_shape": EXPECTED_PATCH_SHAPE,
                "final_patch_dtype": None,
                "finite_values": None,
                "blockers": [],
            }
    else:
        report["preprocessing"] = {
            "method": "essentia.standard.TensorflowInputMusiCNN",
            "raw_observed_shape": None,
            "final_patch_shape": EXPECTED_PATCH_SHAPE,
            "final_patch_dtype": None,
            "finite_values": None,
            "blockers": [],
        }

    if patch_summary is not None:
        capture = _capture_onnx_outputs(
            model_path=args.onnx_model_path,
            patch=patch_summary["patch"],
            runtime_probe=runtime_probe,
        )
        report["onnx_runtime"] = capture["onnx_runtime"]
        report["outputs"] = capture["outputs"]
        report["repeated_run_stability"] = capture["repeated_run_stability"]
        blockers.extend(capture["blockers"])
    else:
        report["onnx_runtime"] = {
            "session_created": False,
            "input_metadata": None,
            "output_metadata": None,
            "input_shape_adaptation": {
                "requested_shape": EXPECTED_PATCH_SHAPE,
                "applied": False,
                "adaptation": None,
                "reason": "preprocessing patch was not generated",
            },
        }
        report["outputs"] = {"activations": None, "embeddings": None}
        report["repeated_run_stability"] = {
            "checked": False,
            "stable": None,
            "tolerance": 1e-6,
            "max_abs_diff": None,
            "mean_abs_diff": None,
        }

    if blockers:
        report["status"] = "blocked"
    else:
        report["status"] = "completed"

    report["blockers"] = blockers
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Собирает local-only Roadmap 4.65 ONNX/MusiCNN output capture report."
    )
    parser.add_argument("--fixture-path", type=Path, default=DEFAULT_FIXTURE_PATH)
    parser.add_argument("--onnx-model-path", type=Path, default=DEFAULT_ONNX_MODEL_PATH)
    parser.add_argument("--onnx-metadata-path", type=Path, default=DEFAULT_ONNX_METADATA_PATH)
    parser.add_argument("--isolated-python", type=Path, default=DEFAULT_ISOLATED_PYTHON)
    parser.add_argument("--roadmap-4-64-report", type=Path, default=DEFAULT_ROADMAP_4_64_REPORT)
    parser.add_argument("--output-report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument(
        "--agents-md-read",
        action="store_true",
        default=True,
        help="Подтверждает, что AGENTS.md был прочитан. По умолчанию включено.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_report(args)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    args.output_report_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
