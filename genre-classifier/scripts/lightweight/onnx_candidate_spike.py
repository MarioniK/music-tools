#!/usr/bin/env python3
"""Offline-only ONNX candidate spike feasibility scaffold.

This script intentionally uses only the Python standard library and does not
import production app, provider, cache, runtime, or inference modules.
"""

import argparse
import hashlib
from datetime import datetime, timezone
import importlib
import importlib.util
import json
import platform
from pathlib import Path
import sys
import time
from typing import Any


DRY_RUN_MESSAGE = (
    "offline ONNX feasibility dry-run; no runtime loaded; no model loaded for inference; "
    "no audio processed; no inference executed"
)

SMOKE_METADATA_ONLY_MESSAGE = (
    "offline ONNX smoke captured raw output metadata only; no production genre "
    "classification was produced"
)

REQUIRED_PROVENANCE_FIELDS = (
    "schema_version",
    "model_id",
    "model_name",
    "model_family",
    "model_format",
    "source_url",
    "source_repository",
    "license",
    "license_url",
    "model_version",
    "model_hash_sha256",
    "model_file_name",
    "model_file_size_bytes",
    "input_names",
    "input_shapes",
    "output_names",
    "output_shapes",
    "label_source",
    "label_count",
    "label_mapping_strategy",
    "intended_use",
    "known_limitations",
    "approval_status",
    "warnings",
)

APPROVED_LOCAL_SMOKE_STATUSES = {"approved", "offline_proof_candidate"}
PLACEHOLDER_HASH_MARKERS = ("placeholder", "not_valid", "example")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def detect_onnxruntime() -> dict[str, Any]:
    spec = importlib.util.find_spec("onnxruntime")
    return {
        "package": "onnxruntime",
        "available": spec is not None,
        "detection_method": 'importlib.util.find_spec("onnxruntime")',
        "imported": False,
    }


def inspect_model_path(model_path: Path | None) -> tuple[dict[str, Any], list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    if model_path is None:
        warnings.append(
            {
                "category": "model_path_missing",
                "message": "No model path was provided; staying in metadata-only dry-run mode.",
            }
        )
        return (
            {
                "path_provided": False,
                "path": None,
                "exists": None,
                "is_file": None,
                "suffix": None,
                "suffix_expected": ".onnx",
                "size_bytes": None,
            },
            warnings,
        )

    exists = model_path.exists()
    is_file = model_path.is_file() if exists else False
    suffix = model_path.suffix.lower()
    size_bytes = model_path.stat().st_size if is_file else None

    if not exists:
        warnings.append(
            {
                "category": "model_path_not_found",
                "message": "The provided local model path does not exist.",
            }
        )
    elif not is_file:
        warnings.append(
            {
                "category": "model_path_not_file",
                "message": "The provided local model path is not a file.",
            }
        )

    if suffix != ".onnx":
        warnings.append(
            {
                "category": "model_suffix_not_onnx",
                "message": "The provided model path does not use the expected .onnx suffix.",
            }
        )

    return (
        {
            "path_provided": True,
            "path": str(model_path),
            "exists": exists,
            "is_file": is_file,
            "suffix": suffix,
            "suffix_expected": ".onnx",
            "size_bytes": size_bytes,
        },
        warnings,
    )


def build_provenance(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, str]]]:
    provenance = {
        "model_name": args.model_name,
        "model_source_url": args.model_source_url,
        "license": args.license,
        "license_url": args.license_url,
        "checksum_sha256": args.checksum_sha256,
        "provenance_status": args.provenance_status,
    }
    warnings: list[dict[str, str]] = []

    if not args.license or not args.license_url:
        warnings.append(
            {
                "category": "license_unknown",
                "message": "Model license or license URL is not recorded.",
            }
        )

    if not args.model_name or not args.model_source_url or args.provenance_status == "unknown":
        warnings.append(
            {
                "category": "model_provenance_unknown",
                "message": "Model name, source URL, or provenance status is incomplete.",
            }
        )

    return provenance, warnings


def _status_for(model: dict[str, Any]) -> str:
    if not model["path_provided"]:
        return "dry_run_metadata_only"
    if not model["exists"]:
        return "skipped_model_path_not_found"
    if not model["is_file"]:
        return "skipped_model_path_not_file"
    return "local_model_inspected_no_inference"


def build_output(args: argparse.Namespace) -> dict[str, Any]:
    started = _utc_now_iso()
    started_counter = time.perf_counter()
    runtime = detect_onnxruntime()
    model, model_warnings = inspect_model_path(args.model_path)
    provenance, provenance_warnings = build_provenance(args)
    finished = _utc_now_iso()
    duration_ms = round((time.perf_counter() - started_counter) * 1000, 3)
    warnings = model_warnings + provenance_warnings

    return {
        "ok": True,
        "message": DRY_RUN_MESSAGE,
        "genres": [
            {
                "tag": "electronic",
                "prob": 0.0,
            }
        ],
        "genres_pretty": ["Electronic"],
        "spike": {
            "roadmap": "4.8",
            "variant": "B",
            "mode": "dry_run",
            "status": _status_for(model),
            "inference_executed": False,
            "audio_processed": False,
        },
        "runtime": runtime,
        "model": model,
        "provenance": provenance,
        "resource_latency_metadata": {
            "started_at_utc": started,
            "finished_at_utc": finished,
            "duration_ms": duration_ms,
            "python_version": sys.version,
            "platform": platform.platform(),
            "onnxruntime_available": runtime["available"],
            "model_size_bytes": model["size_bytes"],
        },
        "warnings": warnings,
    }


def _warning(category: str, message: str) -> dict[str, str]:
    return {"category": category, "message": message}


def _empty_smoke_metadata(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "mode": "smoke",
        "candidate_provider": "onnx_local_smoke",
        "provider": "onnx_local_smoke",
        "baseline_provider": "legacy_musicnn",
        "model_path": str(args.model_path) if args.model_path is not None else None,
        "provenance_path": (
            str(args.provenance_path) if args.provenance_path is not None else None
        ),
        "onnxruntime_available": False,
        "provenance_approved": False,
        "model_loaded": False,
        "inference_attempted": False,
        "inference_succeeded": False,
        "input_names": [],
        "input_shapes": [],
        "output_names": [],
        "output_shapes": [],
        "raw_output_shape": None,
        "latency_ms": None,
        "warnings": [],
    }


def _build_smoke_payload(
    args: argparse.Namespace,
    *,
    ok: bool,
    message: str,
    metadata: dict[str, Any],
    started: str,
    finished: str,
    duration_ms: float,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "message": message,
        "genres": [],
        "genres_pretty": [],
        "metadata": metadata,
        "spike": {
            "roadmap": "4.10",
            "variant": "local_smoke",
            "mode": "smoke",
            "status": "smoke_completed" if ok else "smoke_no_go",
            "inference_executed": metadata["inference_succeeded"],
            "audio_processed": False,
        },
        "runtime": {
            "package": "onnxruntime",
            "available": metadata["onnxruntime_available"],
            "detection_method": 'importlib.util.find_spec("onnxruntime")',
            "imported": metadata["model_loaded"],
        },
        "resource_latency_metadata": {
            "started_at_utc": started,
            "finished_at_utc": finished,
            "duration_ms": duration_ms,
            "python_version": sys.version,
            "platform": platform.platform(),
            "onnxruntime_available": metadata["onnxruntime_available"],
            "model_size_bytes": (
                args.model_path.stat().st_size
                if args.model_path is not None and args.model_path.is_file()
                else None
            ),
        },
        "warnings": metadata["warnings"],
    }


def _load_provenance(path: Path | None, warnings: list[dict[str, str]]) -> dict[str, Any] | None:
    if path is None:
        warnings.append(
            _warning("provenance_path_missing", "Smoke mode requires --provenance-path.")
        )
        return None
    if not path.exists() or not path.is_file():
        warnings.append(
            _warning("provenance_unreadable", "The provenance path is missing or not a file.")
        )
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(
            _warning("provenance_unreadable", f"The provenance JSON could not be read: {exc}")
        )
        return None
    if not isinstance(value, dict):
        warnings.append(
            _warning("provenance_unreadable", "The provenance JSON must be an object.")
        )
        return None
    return value


def _validate_provenance_for_smoke(
    provenance: dict[str, Any] | None, warnings: list[dict[str, str]]
) -> bool:
    if provenance is None:
        return False

    missing_fields = [field for field in REQUIRED_PROVENANCE_FIELDS if field not in provenance]
    if missing_fields:
        warnings.append(
            _warning(
                "provenance_not_approved",
                "Provenance is missing required Roadmap 4.9 metadata fields: "
                + ", ".join(missing_fields),
            )
        )
        return False

    if provenance.get("model_format") != "onnx":
        warnings.append(
            _warning("provenance_not_approved", 'Provenance model_format must be "onnx".')
        )
        return False

    approval_status = str(provenance.get("approval_status", "")).strip().casefold()
    if approval_status not in APPROVED_LOCAL_SMOKE_STATUSES:
        warnings.append(
            _warning(
                "provenance_not_approved",
                "Provenance approval_status is not approved for local smoke inference.",
            )
        )
        return False

    return True


def _verify_model_path(args: argparse.Namespace, warnings: list[dict[str, str]]) -> bool:
    if args.model_path is None:
        warnings.append(_warning("model_path_missing", "Smoke mode requires --model-path."))
        return False
    if not args.model_path.exists():
        warnings.append(_warning("model_path_missing", "The model path does not exist."))
        return False
    if not args.model_path.is_file():
        warnings.append(_warning("model_path_not_file", "The model path is not a file."))
        return False
    return True


def _verify_model_hash(
    model_path: Path, provenance: dict[str, Any], warnings: list[dict[str, str]]
) -> bool:
    expected = str(provenance.get("model_hash_sha256", "")).strip().casefold()
    if len(expected) != 64 or any(marker in expected for marker in PLACEHOLDER_HASH_MARKERS):
        warnings.append(
            _warning("model_hash_missing", "Approved provenance must include a real SHA-256 hash.")
        )
        return False

    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if digest != expected:
        warnings.append(
            _warning("model_hash_mismatch", "Local model SHA-256 does not match provenance.")
        )
        return False
    return True


def _shape_from_runtime_value(value: Any) -> Any:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    try:
        return list(shape)
    except TypeError:
        return shape


def _metadata_from_io(values: Any) -> tuple[list[str], list[Any], list[str]]:
    names: list[str] = []
    shapes: list[Any] = []
    types: list[str] = []
    for value in values:
        names.append(str(getattr(value, "name", "")))
        shapes.append(_shape_from_runtime_value(value))
        types.append(str(getattr(value, "type", "")))
    return names, shapes, types


def _safe_dummy_input(input_shape: Any, input_type: str) -> Any | None:
    if not isinstance(input_shape, list) or not input_shape:
        return None
    if not all(isinstance(item, int) and item > 0 for item in input_shape):
        return None
    if not any(token in input_type for token in ("float", "double")):
        return None

    total = 1
    for dimension in input_shape:
        total *= dimension
    if total > 1_000_000:
        return None

    try:
        import numpy as np  # type: ignore[import-not-found]
    except ImportError:
        return None
    return np.zeros(input_shape, dtype=np.float32)


def build_smoke_output(args: argparse.Namespace) -> dict[str, Any]:
    started = _utc_now_iso()
    started_counter = time.perf_counter()
    metadata = _empty_smoke_metadata(args)
    warnings = metadata["warnings"]

    provenance = _load_provenance(args.provenance_path, warnings)
    provenance_approved = _validate_provenance_for_smoke(provenance, warnings)
    metadata["provenance_approved"] = provenance_approved
    if not provenance_approved:
        warnings.append(
            _warning(
                "not_production_classification",
                "Smoke output is not a production classification.",
            )
        )
        finished = _utc_now_iso()
        return _build_smoke_payload(
            args,
            ok=False,
            message="offline ONNX smoke blocked by provenance gate before model loading",
            metadata=metadata,
            started=started,
            finished=finished,
            duration_ms=round((time.perf_counter() - started_counter) * 1000, 3),
        )

    if not _verify_model_path(args, warnings):
        warnings.append(
            _warning(
                "not_production_classification",
                "Smoke output is not a production classification.",
            )
        )
        finished = _utc_now_iso()
        return _build_smoke_payload(
            args,
            ok=False,
            message="offline ONNX smoke blocked before model loading",
            metadata=metadata,
            started=started,
            finished=finished,
            duration_ms=round((time.perf_counter() - started_counter) * 1000, 3),
        )

    assert args.model_path is not None
    assert provenance is not None
    if not _verify_model_hash(args.model_path, provenance, warnings):
        warnings.append(
            _warning(
                "not_production_classification",
                "Smoke output is not a production classification.",
            )
        )
        finished = _utc_now_iso()
        return _build_smoke_payload(
            args,
            ok=False,
            message="offline ONNX smoke blocked by local model hash gate",
            metadata=metadata,
            started=started,
            finished=finished,
            duration_ms=round((time.perf_counter() - started_counter) * 1000, 3),
        )

    runtime_spec = importlib.util.find_spec("onnxruntime")
    metadata["onnxruntime_available"] = runtime_spec is not None
    if runtime_spec is None:
        warnings.append(
            _warning(
                "onnxruntime_missing",
                "onnxruntime is not installed in this local environment.",
            )
        )
        warnings.append(
            _warning(
                "not_production_classification",
                "Smoke output is not a production classification.",
            )
        )
        finished = _utc_now_iso()
        return _build_smoke_payload(
            args,
            ok=False,
            message="offline ONNX smoke skipped because optional onnxruntime is unavailable",
            metadata=metadata,
            started=started,
            finished=finished,
            duration_ms=round((time.perf_counter() - started_counter) * 1000, 3),
        )

    try:
        onnxruntime = importlib.import_module("onnxruntime")
        session = onnxruntime.InferenceSession(str(args.model_path))
    except Exception as exc:  # pragma: no cover - exercised with mocks in tests
        warnings.append(_warning("model_load_failed", f"ONNX model load failed: {exc}"))
        warnings.append(
            _warning(
                "not_production_classification",
                "Smoke output is not a production classification.",
            )
        )
        finished = _utc_now_iso()
        return _build_smoke_payload(
            args,
            ok=False,
            message="offline ONNX smoke could not load the local model",
            metadata=metadata,
            started=started,
            finished=finished,
            duration_ms=round((time.perf_counter() - started_counter) * 1000, 3),
        )

    metadata["model_loaded"] = True
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    input_names, input_shapes, input_types = _metadata_from_io(inputs)
    output_names, output_shapes, _output_types = _metadata_from_io(outputs)
    metadata["input_names"] = input_names
    metadata["input_shapes"] = input_shapes
    metadata["output_names"] = output_names
    metadata["output_shapes"] = output_shapes

    input_shape = input_shapes[0] if input_shapes else None
    input_type = input_types[0] if input_types else ""
    dummy = _safe_dummy_input(input_shape, input_type)
    if dummy is None or not input_names:
        if not isinstance(input_shape, list) or not all(
            isinstance(item, int) and item > 0 for item in input_shape
        ):
            warnings.append(
                _warning("input_shape_unknown", "Input shape is dynamic or unknown.")
            )
        warnings.append(_warning("dummy_input_unavailable", "Safe dummy input could not be built."))
        warnings.append(
            _warning("label_mapping_missing", "No approved label mapping is available.")
        )
        warnings.append(
            _warning(
                "not_production_classification",
                "Smoke output is not a production classification.",
            )
        )
        finished = _utc_now_iso()
        return _build_smoke_payload(
            args,
            ok=True,
            message=SMOKE_METADATA_ONLY_MESSAGE,
            metadata=metadata,
            started=started,
            finished=finished,
            duration_ms=round((time.perf_counter() - started_counter) * 1000, 3),
        )

    try:
        inference_started = time.perf_counter()
        metadata["inference_attempted"] = True
        raw_outputs = session.run(None, {input_names[0]: dummy})
        metadata["latency_ms"] = round((time.perf_counter() - inference_started) * 1000, 3)
        metadata["inference_succeeded"] = True
        if raw_outputs:
            metadata["raw_output_shape"] = _shape_from_runtime_value(raw_outputs[0])
        else:
            warnings.append(_warning("raw_output_unavailable", "Inference returned no outputs."))
    except Exception as exc:  # pragma: no cover - exercised with mocks in tests
        warnings.append(_warning("inference_failed", f"Dummy ONNX inference failed: {exc}"))

    warnings.append(_warning("label_mapping_missing", "No approved label mapping is available."))
    warnings.append(
        _warning(
            "not_production_classification",
            "Smoke output is not a production classification.",
        )
    )
    finished = _utc_now_iso()
    return _build_smoke_payload(
        args,
        ok=metadata["inference_succeeded"],
        message=SMOKE_METADATA_ONLY_MESSAGE,
        metadata=metadata,
        started=started,
        finished=finished,
        duration_ms=round((time.perf_counter() - started_counter) * 1000, 3),
    )


def build_dry_run_output() -> dict[str, Any]:
    parser = build_parser()
    args = parser.parse_args([])
    return build_output(args)


def write_output(path: Path, payload: dict[str, Any], *, allow_overwrite: bool = True) -> None:
    if path.exists() and not allow_overwrite:
        raise FileExistsError(f"output file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the offline-only ONNX candidate feasibility scaffold."
    )
    parser.add_argument(
        "--mode",
        default="dry-run",
        choices=("dry-run", "smoke"),
        help="Execution mode. Defaults to dry-run; smoke is an explicit local-only experiment.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Default behavior; emit JSON without loading runtime, audio, or inference code.",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        help="Local-only ONNX model path. Optional for dry-run; required for smoke.",
    )
    parser.add_argument(
        "--provenance-path",
        type=Path,
        help="Approved local provenance JSON path required for smoke mode.",
    )
    parser.add_argument(
        "--model-name",
        help="Optional candidate model name for provenance metadata.",
    )
    parser.add_argument(
        "--model-source-url",
        help="Optional candidate model source URL for provenance metadata.",
    )
    parser.add_argument(
        "--license",
        help="Optional candidate model license name or identifier.",
    )
    parser.add_argument(
        "--license-url",
        help="Optional candidate model license URL.",
    )
    parser.add_argument(
        "--checksum-sha256",
        help="Optional externally computed SHA-256 checksum for the local model file.",
    )
    parser.add_argument(
        "--provenance-status",
        default="unknown",
        choices=("unknown", "incomplete", "review_required", "recorded"),
        help="Provenance review status for the candidate model metadata.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        help="Optional path for the structured JSON feasibility artifact.",
    )
    parser.add_argument(
        "--output-path",
        dest="output_path",
        type=Path,
        help="Optional path for the structured JSON feasibility artifact.",
    )
    parser.add_argument(
        "--write-output",
        dest="output_path",
        type=Path,
        help="Backward-compatible alias for --output.",
    )
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Allow smoke mode to replace an existing output file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    payload = build_smoke_output(args) if args.mode == "smoke" else build_output(args)
    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.output_path is not None:
        try:
            write_output(
                args.output_path,
                payload,
                allow_overwrite=args.mode != "smoke" or args.allow_overwrite,
            )
        except FileExistsError as exc:
            print(f"output write refused: {exc}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
