#!/usr/bin/env python3
"""Roadmap 4.78 explicit ONNX/MusiCNN provider direct smoke helper.

Скрипт предназначен только для local-only explicit opt-in проверки:

- не вызывает `/classify`;
- не запускает FastAPI app;
- не использует HTTP;
- не трогает Docker Compose;
- не меняет default provider;
- не добавляет production dependencies;
- не претендует на production readiness.

Проверяемая цепочка:

external fixture / explicit artifact paths
→ `OnnxMusiCNNProvider.classify_with_explicit_artifacts`
→ `TensorflowInputMusiCNN` preprocessing
→ ONNX Runtime inference
→ provider result
→ validation / compatibility mapping
→ contract-compatible `genres` и `genres_pretty`
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[4]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-provider-direct-smoke-report.json"
)

ALLOWED_BLOCKER_CODES = {
    "AGENTS_MD_NOT_READ",
    "PROVIDER_DIRECT_IMPORT_NOT_SAFE",
    "PROVIDER_DIRECT_CALL_FAILED",
    "PROVIDER_DIRECT_CALL_NOT_IMPLEMENTED",
    "CONTRACT_COMPATIBILITY_FAILED",
    "ARTIFACT_NOT_FOUND",
    "VALIDATION_FAILED",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}


class SmokeError(Exception):
    """Ожидаемая ошибка local-only direct smoke helper."""


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(SERVICE_ROOT.resolve())
    except ValueError:
        return False
    return True


def _blocker(code: str, message: str) -> dict[str, str]:
    if code not in ALLOWED_BLOCKER_CODES:
        raise SmokeError(f"Unsupported blocker code: {code}")
    return {"code": code, "message": message}


def _load_provider_bundle():
    before_modules = set(sys.modules)
    from app.providers.onnx_musicnn import OnnxMusiCNNProvider  # noqa: WPS433
    from app.providers.compat import (  # noqa: WPS433
        map_validated_result_to_legacy_genres,
        map_validated_result_to_legacy_genres_pretty,
    )
    from app.providers.validation import validate_and_normalize_provider_result  # noqa: WPS433

    imported_modules = set(sys.modules) - before_modules
    lazy_optional_imports_preserved = all(
        module_name not in imported_modules
        for module_name in ("onnxruntime", "essentia", "essentia.standard")
    )
    return {
        "OnnxMusiCNNProvider": OnnxMusiCNNProvider,
        "map_validated_result_to_legacy_genres": map_validated_result_to_legacy_genres,
        "map_validated_result_to_legacy_genres_pretty": map_validated_result_to_legacy_genres_pretty,
        "validate_and_normalize_provider_result": validate_and_normalize_provider_result,
        "lazy_optional_imports_preserved": lazy_optional_imports_preserved,
    }


def _build_provider(args: argparse.Namespace):
    settings_module = SimpleNamespace(
        get_configured_onnx_musicnn_model_path=lambda: args.onnx_model_path,
        get_configured_onnx_musicnn_metadata_path=lambda: args.classes_path,
    )
    return _load_provider_bundle()["OnnxMusiCNNProvider"](settings_module=settings_module)


def _load_metadata_classes(classes_path: Path) -> list[str]:
    data = _load_json(classes_path)
    classes = data.get("classes")
    if not isinstance(classes, list) or not classes:
        raise SmokeError("metadata/classes list is missing")

    normalized_classes: list[str] = []
    for index, item in enumerate(classes):
        if not isinstance(item, str) or not item.strip():
            raise SmokeError(f"metadata/classes[{index}] is not a non-empty string")
        normalized_classes.append(item)

    return normalized_classes


def _load_artifact_report(path: Path) -> dict[str, Any]:
    return _load_json(path)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    warnings: list[str] = []

    report: dict[str, Any] = {
        "roadmap": "4.78",
        "not_production_decision": True,
        "provider_direct_smoke_only": True,
        "explicit_opt_in_only": True,
        "classify_called": False,
        "http_called": False,
        "docker_run": False,
        "runtime_smoke_through_http": False,
        "production_approval": False,
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "provider": {
            "key": "onnx_musicnn",
            "direct_import_ok": False,
            "direct_call_ok": False,
            "lazy_optional_imports_preserved": False,
            "default_provider_changed": False,
        },
        "artifacts": {
            "implicit_discovery_used": False,
            "audio_path_provided": False,
            "audio_path_external": False,
            "onnx_model_path_provided": False,
            "onnx_model_path_external": False,
            "classes_path_provided": False,
            "classes_path_external": False,
        },
        "result": {
            "success": False,
            "genres": [],
            "genres_pretty": [],
            "genres_non_empty": False,
            "genres_pretty_non_empty": False,
            "contract_compatible_fields": {
                "genres": False,
                "genres_pretty": False,
            },
        },
        "production_boundaries": {
            "production_requirements_changed": False,
            "docker_changed": False,
            "provider_default_unchanged": True,
            "onnx_musicnn_disabled_by_default": True,
            "classify_contract_changed": False,
            "response_shape_changed": False,
            "tidal_parser_touched": False,
        },
        "blockers": [],
        "warnings": [],
        "next_step_recommendation": (
            "Proceed to Roadmap 4.79 explicit /classify opt-in smoke only after provider direct smoke succeeds."
        ),
    }

    try:
        _load_artifact_report(args.roadmap_4_77_report)
    except Exception as exc:
        warnings.append(f"roadmap_4_77_report: {_safe_error(exc)}")

    if not args.audio_path.is_file():
        blockers.append(_blocker("ARTIFACT_NOT_FOUND", f"audio artifact missing: {args.audio_path}"))
    if not args.onnx_model_path.is_file():
        blockers.append(_blocker("ARTIFACT_NOT_FOUND", f"onnx model artifact missing: {args.onnx_model_path}"))
    if not args.classes_path.is_file():
        blockers.append(_blocker("ARTIFACT_NOT_FOUND", f"classes metadata artifact missing: {args.classes_path}"))

    report["artifacts"].update(
        {
            "audio_path_provided": True,
            "audio_path_external": not _is_inside_repo(args.audio_path),
            "onnx_model_path_provided": True,
            "onnx_model_path_external": not _is_inside_repo(args.onnx_model_path),
            "classes_path_provided": True,
            "classes_path_external": not _is_inside_repo(args.classes_path),
        }
    )

    if args.audio_path.is_file() and args.onnx_model_path.is_file() and args.classes_path.is_file():
        try:
            bundle = _load_provider_bundle()
        except Exception as exc:
            blockers.append(_blocker("PROVIDER_DIRECT_IMPORT_NOT_SAFE", _safe_error(exc)))
        else:
            report["provider"]["direct_import_ok"] = True
            report["provider"]["lazy_optional_imports_preserved"] = bool(
                bundle["lazy_optional_imports_preserved"]
            )

            try:
                provider = _build_provider(args)
                provider_result = provider.classify_with_explicit_artifacts(
                    str(args.audio_path),
                    top_n=args.top_n,
                )
                validated_result = bundle["validate_and_normalize_provider_result"](
                    provider_result,
                    top_n=args.top_n,
                )
                genres = bundle["map_validated_result_to_legacy_genres"](validated_result)
                genres_pretty = bundle["map_validated_result_to_legacy_genres_pretty"](validated_result)

                report["provider"]["direct_call_ok"] = True
                report["result"] = {
                    "success": True,
                    "genres": genres,
                    "genres_pretty": genres_pretty,
                    "genres_non_empty": bool(genres),
                    "genres_pretty_non_empty": bool(genres_pretty),
                    "contract_compatible_fields": {
                        "genres": isinstance(genres, list),
                        "genres_pretty": isinstance(genres_pretty, list),
                    },
                    "validated": {
                        "provider_name": validated_result.provider_name,
                        "model_name": validated_result.model_name,
                        "total_items_received": validated_result.total_items_received,
                        "total_items_kept": validated_result.total_items_kept,
                        "dropped_items_count": validated_result.dropped_items_count,
                    },
                }

                if not report["result"]["genres_non_empty"] or not report["result"]["genres_pretty_non_empty"]:
                    blockers.append(
                        _blocker(
                            "CONTRACT_COMPATIBILITY_FAILED",
                            "provider direct smoke returned empty contract-compatible genre fields",
                        )
                    )
                    report["result"]["success"] = False

            except Exception as exc:
                report["provider"]["direct_call_ok"] = False
                blockers.append(_blocker("PROVIDER_DIRECT_CALL_FAILED", _safe_error(exc)))

    report["warnings"] = warnings
    report["blockers"] = blockers
    if blockers:
        report["result"]["success"] = False

    return report


def _safe_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Собирает Roadmap 4.78 explicit ONNX/MusiCNN provider direct smoke report."
    )
    parser.add_argument("--audio-path", type=Path, required=True)
    parser.add_argument("--onnx-model-path", type=Path, required=True)
    parser.add_argument("--classes-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument(
        "--roadmap-4-77-report",
        type=Path,
        default=(
            SERVICE_ROOT
            / "docs/lightweight/evaluation/parity-scaffold/"
            / "onnx-musicnn-patch-to-mapping-probe-report.json"
        ),
    )
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
