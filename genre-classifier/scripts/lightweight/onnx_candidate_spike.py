#!/usr/bin/env python3
"""Offline-only ONNX candidate spike feasibility scaffold.

This script intentionally uses only the Python standard library and does not
import production app, provider, cache, runtime, or inference modules.
"""

import argparse
from datetime import datetime, timezone
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


def build_dry_run_output() -> dict[str, Any]:
    parser = build_parser()
    args = parser.parse_args([])
    return build_output(args)


def write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the offline-only ONNX candidate feasibility dry-run scaffold."
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
        help="Optional local-only ONNX model path for shallow metadata checks.",
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
        type=Path,
        help="Optional path for the structured JSON feasibility artifact.",
    )
    parser.add_argument(
        "--write-output",
        type=Path,
        help="Backward-compatible alias for --output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    payload = build_output(args)
    print(json.dumps(payload, indent=2, sort_keys=True))

    output_path = args.output or args.write_output
    if output_path is not None:
        write_output(output_path, payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
