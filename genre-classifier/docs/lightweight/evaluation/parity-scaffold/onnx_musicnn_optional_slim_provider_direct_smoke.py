#!/usr/bin/env python3
"""Roadmap 4.91 optional ONNX/MusiCNN provider direct smoke helper.

Скрипт предназначен только для local-only проверки через optional Compose
profile inside container:

- не вызывает `/classify`;
- не запускает FastAPI server;
- не делает network HTTP calls;
- не использует default service;
- не меняет production defaults;
- не претендует на production readiness.

Проверяемая цепочка:

audio fixture
→ `TensorflowInputMusiCNN` preprocessing
→ ONNX Runtime inference
→ validation / mapping
→ contract-compatible `genres` и `genres_pretty`
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import resource
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
    / "onnx-musicnn-optional-slim-provider-direct-smoke-report.json"
)
EXPECTED_ROADMAP = "4.91"
EXPECTED_PROVIDER_ENV = "onnx_musicnn"
EXPECTED_MODEL_PATH = "/opt/genre-classifier/onnx/msd-musicnn-1.onnx"
EXPECTED_METADATA_PATH = "/opt/genre-classifier/onnx/msd-musicnn-1.json"
EXPECTED_MODEL_SHA256 = "49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1"
EXPECTED_METADATA_SHA256 = "8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe"
EXPECTED_PATCH_SHAPE = [187, 96]
EXPECTED_ACTIVATIONS_SHAPE = [50]
EXPECTED_EMBEDDINGS_SHAPE = [200]
DEFAULT_TOP_N = 8


class SmokeError(RuntimeError):
    """Ошибка smoke helper без лишнего traceback на пользовательском уровне."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SmokeError(f"JSON artifact is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SmokeError(f"JSON artifact is invalid: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SmokeError(f"JSON artifact must be an object: {path}")
    return data


def _sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def _blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _load_provider_bundle() -> dict[str, Any]:
    before_modules = set(sys.modules)
    from app.providers.compat import (  # noqa: WPS433
        map_validated_result_to_legacy_genres,
        map_validated_result_to_legacy_genres_pretty,
    )
    from app.providers.onnx_musicnn import OnnxMusiCNNProvider  # noqa: WPS433
    from app.providers.validation import validate_and_normalize_provider_result  # noqa: WPS433

    imported_modules = set(sys.modules) - before_modules
    return {
        "OnnxMusiCNNProvider": OnnxMusiCNNProvider,
        "map_validated_result_to_legacy_genres": map_validated_result_to_legacy_genres,
        "map_validated_result_to_legacy_genres_pretty": map_validated_result_to_legacy_genres_pretty,
        "validate_and_normalize_provider_result": validate_and_normalize_provider_result,
        "provider_module_import_ok": True,
        "lazy_optional_imports_preserved": all(
            module_name not in imported_modules
            for module_name in ("onnxruntime", "essentia", "essentia.standard")
        ),
    }


def _make_provider(args: argparse.Namespace):
    bundle = _load_provider_bundle()
    settings_module = SimpleNamespace(
        get_configured_onnx_musicnn_model_path=lambda: EXPECTED_MODEL_PATH,
        get_configured_onnx_musicnn_metadata_path=lambda: EXPECTED_METADATA_PATH,
    )
    return bundle, bundle["OnnxMusiCNNProvider"](settings_module=settings_module)


def _build_runtime_imports() -> dict[str, Any]:
    tensorflow_spec = importlib.util.find_spec("tensorflow")

    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
    except Exception:
        return {
            "tensorflow_absent": tensorflow_spec is None,
            "essentia_standard_import_ok": False,
            "tensorflow_input_musiccnn_available": False,
            "onnxruntime_import_ok": False,
            "cpu_execution_provider_available": False,
            "provider_module_import_ok": False,
        }

    try:
        from essentia import standard as essentia_standard  # type: ignore[import-not-found]
    except Exception:
        return {
            "tensorflow_absent": tensorflow_spec is None,
            "essentia_standard_import_ok": False,
            "tensorflow_input_musiccnn_available": False,
            "onnxruntime_import_ok": True,
            "cpu_execution_provider_available": "CPUExecutionProvider" in ort.get_available_providers(),
            "provider_module_import_ok": False,
        }

    provider_module_import_ok = False
    try:
        _load_provider_bundle()
        provider_module_import_ok = True
    except Exception:
        provider_module_import_ok = False

    return {
        "tensorflow_absent": tensorflow_spec is None,
        "essentia_standard_import_ok": True,
        "tensorflow_input_musiccnn_available": hasattr(essentia_standard, "TensorflowInputMusiCNN"),
        "onnxruntime_import_ok": True,
        "cpu_execution_provider_available": "CPUExecutionProvider" in ort.get_available_providers(),
        "provider_module_import_ok": provider_module_import_ok,
    }


def _read_env_container_state() -> dict[str, Any]:
    provider_env = os.getenv("GENRE_PROVIDER")
    model_env_path = os.getenv("ONNX_MUSICNN_MODEL_PATH")
    metadata_env_path = os.getenv("ONNX_MUSICNN_METADATA_PATH")
    env_match = (
        provider_env == EXPECTED_PROVIDER_ENV
        and model_env_path == EXPECTED_MODEL_PATH
        and metadata_env_path == EXPECTED_METADATA_PATH
    )

    return {
        "provider_env": provider_env,
        "model_env_path": model_env_path,
        "metadata_env_path": metadata_env_path,
        "env_match": env_match,
    }


def _check_mounted_artifacts() -> dict[str, Any]:
    model_path = Path(EXPECTED_MODEL_PATH)
    metadata_path = Path(EXPECTED_METADATA_PATH)

    model_exists = model_path.is_file()
    metadata_exists = metadata_path.is_file()
    model_checksum_match = model_exists and _sha256_hex(model_path) == EXPECTED_MODEL_SHA256
    metadata_checksum_match = metadata_exists and _sha256_hex(metadata_path) == EXPECTED_METADATA_SHA256

    return {
        "model_exists": model_exists,
        "metadata_exists": metadata_exists,
        "model_checksum_match": model_checksum_match,
        "metadata_checksum_match": metadata_checksum_match,
    }


def _provider_direct_smoke(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, str]], list[str]]:
    total_start = time.perf_counter()
    bundle, provider = _make_provider(args)
    import onnxruntime as ort  # type: ignore[import-not-found]
    from essentia import standard as essentia_standard  # type: ignore[import-not-found]

    if not args.audio_path.is_file():
        raise SmokeError(f"audio artifact missing: {args.audio_path}")

    runtime_status = provider.describe_runtime_status()
    if not runtime_status["available"]:
        raise SmokeError("; ".join(runtime_status.get("reasons") or ["provider unavailable"]))

    if not Path(EXPECTED_MODEL_PATH).is_file():
        raise SmokeError(f"onnx model artifact missing: {EXPECTED_MODEL_PATH}")
    if not Path(EXPECTED_METADATA_PATH).is_file():
        raise SmokeError(f"onnx metadata artifact missing: {EXPECTED_METADATA_PATH}")

    patch_start = time.perf_counter()
    patch = provider._build_tensorflow_input_patch(essentia_standard, str(args.audio_path))  # noqa: WPS421
    preprocessing_seconds = time.perf_counter() - patch_start

    session_start = time.perf_counter()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(Path(EXPECTED_MODEL_PATH)),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    onnx_session_seconds = time.perf_counter() - session_start

    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if not inputs:
        raise SmokeError("onnxruntime session has no inputs")
    if not outputs:
        raise SmokeError("onnxruntime session has no outputs")

    input_meta = inputs[0]
    input_shape = list(input_meta.shape)
    feed_array = patch
    if len(input_shape) == 3 and input_shape[-2:] == EXPECTED_PATCH_SHAPE:
        import numpy as np

        feed_array = np.expand_dims(patch, axis=0)
    elif len(input_shape) != 2 or input_shape != EXPECTED_PATCH_SHAPE:
        raise SmokeError(f"unexpected ONNX input shape: {input_shape}")

    inference_start = time.perf_counter()
    run_outputs = session.run(None, {input_meta.name: feed_array})
    onnx_inference_seconds = time.perf_counter() - inference_start

    output_map = {item.name: value for item, value in zip(outputs, run_outputs)}
    if "activations" not in output_map:
        raise SmokeError("onnx outputs did not include an 'activations' tensor")
    if "embeddings" not in output_map:
        raise SmokeError("onnx outputs did not include an 'embeddings' tensor")

    import numpy as np

    activations = provider._normalize_output_values(output_map["activations"])  # noqa: WPS421
    embeddings = np.asarray(output_map["embeddings"], dtype=float).reshape(-1)

    mapping_start = time.perf_counter()
    provider_result = provider.build_provider_result_from_outputs(
        activations,
        _load_json(Path(EXPECTED_METADATA_PATH))["classes"],
        top_n=DEFAULT_TOP_N,
    )
    validated_result = bundle["validate_and_normalize_provider_result"](provider_result, top_n=DEFAULT_TOP_N)
    genres = bundle["map_validated_result_to_legacy_genres"](validated_result)
    genres_pretty = bundle["map_validated_result_to_legacy_genres_pretty"](validated_result)
    mapping_seconds = time.perf_counter() - mapping_start

    resource_snapshot = resource.getrusage(resource.RUSAGE_SELF)
    total_seconds = time.perf_counter() - total_start

    smoke = {
        "success": True,
        "audio_path": str(args.audio_path),
        "patch_shape": list(patch.shape),
        "activations_shape": list(np.asarray(activations).reshape(-1).shape),
        "embeddings_shape": list(embeddings.shape),
        "genres": genres,
        "genres_pretty": genres_pretty,
        "genres_non_empty": bool(genres),
        "genres_pretty_non_empty": bool(genres_pretty),
        "response_compatible_shape": isinstance(genres, list) and isinstance(genres_pretty, list),
    }
    timing = {
        "total_seconds": total_seconds,
        "preprocessing_seconds": preprocessing_seconds,
        "onnx_inference_seconds": onnx_inference_seconds,
        "mapping_seconds": mapping_seconds,
        "max_rss_kb": getattr(resource_snapshot, "ru_maxrss", None),
    }
    provider_details = {
        "provider_module_import_ok": bundle["provider_module_import_ok"],
        "lazy_optional_imports_preserved": bundle["lazy_optional_imports_preserved"],
    }

    return smoke, timing, provider_details, [], []


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    warnings: list[str] = []

    report: dict[str, Any] = {
        "roadmap": EXPECTED_ROADMAP,
        "optional_slim_provider_direct_smoke": True,
        "not_production_decision": True,
        "production_approval": False,
        "docker_compose_run_command_used": True,
        "docker_compose_up_run": False,
        "server_started": False,
        "classify_called": False,
        "network_http_called": False,
        "default_service_touched": False,
        "service": {
            "name": "genre-classifier-onnx",
            "profile": "onnx",
            "target": "onnx-runtime-slim",
        },
        "container_env": _read_env_container_state(),
        "mounted_artifacts": _check_mounted_artifacts(),
        "runtime_imports": _build_runtime_imports(),
        "provider_direct_smoke": {
            "success": False,
            "audio_path": str(args.audio_path),
            "patch_shape": [],
            "activations_shape": [],
            "embeddings_shape": [],
            "genres": [],
            "genres_pretty": [],
            "genres_non_empty": False,
            "genres_pretty_non_empty": False,
            "response_compatible_shape": False,
        },
        "timing": {
            "total_seconds": None,
            "preprocessing_seconds": None,
            "onnx_inference_seconds": None,
            "mapping_seconds": None,
            "max_rss_kb": None,
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

    if not args.audio_path.is_file():
        blockers.append(
            _blocker(
                "AUDIO_FIXTURE_MISSING_FOR_PROVIDER_DIRECT_SMOKE",
                f"audio artifact missing: {args.audio_path}",
            )
        )
    if not report["mounted_artifacts"]["model_exists"]:
        blockers.append(
            _blocker(
                "ONNX_SLIM_PROVIDER_DIRECT_SMOKE_FAILED",
                f"onnx model artifact missing: {EXPECTED_MODEL_PATH}",
            )
        )
    if not report["mounted_artifacts"]["metadata_exists"]:
        blockers.append(
            _blocker(
                "ONNX_SLIM_PROVIDER_DIRECT_SMOKE_FAILED",
                f"onnx metadata artifact missing: {EXPECTED_METADATA_PATH}",
            )
        )
    if not report["runtime_imports"]["onnxruntime_import_ok"]:
        blockers.append(
            _blocker("ONNX_SLIM_PROVIDER_DIRECT_SMOKE_FAILED", "onnxruntime import failed")
        )
    if not report["runtime_imports"]["essentia_standard_import_ok"]:
        blockers.append(
            _blocker("ONNX_SLIM_PROVIDER_DIRECT_SMOKE_FAILED", "essentia.standard import failed")
        )
    if not report["runtime_imports"]["tensorflow_input_musiccnn_available"]:
        blockers.append(
            _blocker(
                "ONNX_SLIM_PROVIDER_DIRECT_SMOKE_FAILED",
                "TensorflowInputMusiCNN is unavailable",
            )
        )

    if not blockers:
        try:
            smoke, timing, provider_details, smoke_blockers, smoke_warnings = _provider_direct_smoke(args)
        except Exception as exc:
            blockers.append(
                _blocker(
                    "ONNX_SLIM_PROVIDER_DIRECT_SMOKE_FAILED",
                    _safe_error(exc),
                )
            )
        else:
            report["provider_direct_smoke"] = smoke
            report["timing"] = timing
            report["runtime_imports"].update(provider_details)
            blockers.extend(smoke_blockers)
            warnings.extend(smoke_warnings)

    if blockers:
        report["provider_direct_smoke"]["success"] = False
        report["provider_direct_smoke"]["genres_non_empty"] = False
        report["provider_direct_smoke"]["genres_pretty_non_empty"] = False

    report["blockers"] = blockers
    report["warnings"] = warnings
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Собирает Roadmap 4.91 optional ONNX/MusiCNN provider direct smoke report."
    )
    parser.add_argument("--audio-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_report(args)
    except Exception as exc:
        payload = {
            "ok": False,
            "error": _safe_error(exc),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
