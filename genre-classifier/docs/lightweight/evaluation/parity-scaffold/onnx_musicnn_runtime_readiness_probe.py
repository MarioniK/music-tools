#!/usr/bin/env python3
"""Изолированный probe readiness для ONNX/MusiCNN runtime lane.

Скрипт предназначен только для safe local-only проверки окружения и
подготовленности lane, без inference, без `/classify`, без provider wiring и
без implicit artifact discovery.

Проверяются только:

- версия и путь Python;
- import `onnxruntime` и доступные providers;
- наличие `CPUExecutionProvider`;
- import `essentia` и `essentia.standard`;
- наличие `TensorflowInputMusiCNN`;
- явная проверка переданных путей к артефактам без автоматического поиска;
- сохранение JSON report на диск.

Это не production readiness decision и не runtime smoke.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-runtime-readiness-probe-report.json"
)
EXPECTED_ONNXRUNTIME_VERSION = "1.25.1"
EXPECTED_ESSENTIA_TENSORFLOW_VERSION = "2.1b6.dev1389"
EXPECTED_CLASSES_COUNT = 50
FORBIDDEN_ARTIFACT_PATTERNS = (
    "*.onnx",
    "*.pb",
    "*.whl",
    "*.mp3",
    "*.wav",
    "*.flac",
    "*.m4a",
    "*.aac",
    "venv",
    ".venv",
)


def _as_bool(value: bool) -> bool:
    return bool(value)


def _read_text_file(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _check_optional_file(path_value: str | None, *, count_lines: bool = False) -> dict[str, Any]:
    """Проверяет явный путь к артефакту без implicit discovery."""

    result: dict[str, Any] = {
        "provided": path_value is not None,
        "file_exists": None,
        "read_ok": None,
        "count": None,
    }

    if path_value is None:
        return result

    path = Path(path_value)
    file_exists = path.is_file()
    result["file_exists"] = file_exists
    if not file_exists:
        result["read_ok"] = False
        return result

    try:
        content = _read_text_file(path)
    except OSError:
        result["read_ok"] = False
        return result

    result["read_ok"] = True
    if count_lines:
        result["count"] = sum(1 for line in content.splitlines() if line.strip())
    return result


def _collect_preexisting_forbidden_artifacts() -> list[str]:
    """Собирает только уже существующие запрещённые артефакты в repo tree."""

    matches: set[str] = set()
    for pattern in FORBIDDEN_ARTIFACT_PATTERNS:
        for path in SERVICE_ROOT.rglob(pattern):
            if ".git" in path.parts:
                continue
            if path.is_dir() and path.name not in {"venv", ".venv"}:
                continue
            matches.add(path.relative_to(SERVICE_ROOT).as_posix())
    return sorted(matches)


def _probe_onnxruntime() -> dict[str, Any]:
    """Собирает факты об onnxruntime без создания InferenceSession."""

    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
    except Exception:
        return {
            "expected_version": EXPECTED_ONNXRUNTIME_VERSION,
            "installed_version": None,
            "import_ok": False,
            "available_providers": [],
            "cpu_execution_provider_available": False,
        }

    available_providers = list(ort.get_available_providers())
    return {
        "expected_version": EXPECTED_ONNXRUNTIME_VERSION,
        "installed_version": getattr(ort, "__version__", None),
        "import_ok": True,
        "available_providers": available_providers,
        "cpu_execution_provider_available": "CPUExecutionProvider" in available_providers,
    }


def _probe_essentia_tensorflow() -> dict[str, Any]:
    """Проверяет импорт Essentia runtime и наличие TensorflowInputMusiCNN."""

    import_essentia_ok = False
    import_essentia_standard_ok = False
    tensorflow_input_musiccnn_available = False

    try:
        import essentia  # type: ignore[import-not-found]
    except Exception:
        return {
            "expected_version": EXPECTED_ESSENTIA_TENSORFLOW_VERSION,
            "import_essentia_ok": False,
            "import_essentia_standard_ok": False,
            "tensorflow_input_musiccnn_available": False,
        }

    import_essentia_ok = True
    try:
        from essentia import standard as essentia_standard  # type: ignore[import-not-found]
    except Exception:
        return {
            "expected_version": EXPECTED_ESSENTIA_TENSORFLOW_VERSION,
            "import_essentia_ok": import_essentia_ok,
            "import_essentia_standard_ok": False,
            "tensorflow_input_musiccnn_available": False,
        }

    import_essentia_standard_ok = True
    tensorflow_input_musiccnn_available = _as_bool(
        hasattr(essentia_standard, "TensorflowInputMusiCNN")
    )

    return {
        "expected_version": EXPECTED_ESSENTIA_TENSORFLOW_VERSION,
        "import_essentia_ok": import_essentia_ok,
        "import_essentia_standard_ok": import_essentia_standard_ok,
        "tensorflow_input_musiccnn_available": tensorflow_input_musiccnn_available,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    """Собирает JSON report для isolated runtime readiness probe."""

    python_info = {
        "version": platform.python_version(),
        "executable": sys.executable,
    }

    onnxruntime_info = _probe_onnxruntime()
    essentia_info = _probe_essentia_tensorflow()

    artifact_paths = {
        "implicit_discovery_used": False,
        "onnx_model_path_provided": args.onnx_model_path is not None,
        "classes_path_provided": args.classes_path is not None,
    }

    onnx_model_probe = _check_optional_file(args.onnx_model_path)
    classes_probe = _check_optional_file(args.classes_path, count_lines=True)

    artifact_paths.update(
        {
            "onnx_model_file_exists": onnx_model_probe["file_exists"],
            "onnx_model_read_ok": onnx_model_probe["read_ok"],
            "classes_file_exists": classes_probe["file_exists"],
            "classes_read_ok": classes_probe["read_ok"],
            "classes_count": classes_probe["count"],
            "classes_count_expected": EXPECTED_CLASSES_COUNT,
            "classes_count_match": (
                classes_probe["count"] == EXPECTED_CLASSES_COUNT
                if classes_probe["count"] is not None
                else None
            ),
        }
    )

    blockers: list[dict[str, str]] = []
    warnings: list[str] = []

    if not onnxruntime_info["import_ok"]:
        blockers.append(
            {
                "code": "ONNXRUNTIME_IMPORT_FAILED",
                "message": "onnxruntime import failed in isolated probe environment.",
            }
        )
    elif not onnxruntime_info["cpu_execution_provider_available"]:
        warnings.append(
            "CPUExecutionProvider не найден в доступных provider-ах onnxruntime."
        )

    if not essentia_info["import_essentia_ok"]:
        blockers.append(
            {
                "code": "ESSENTIA_IMPORT_FAILED",
                "message": "essentia import failed in isolated probe environment.",
            }
        )
    elif not essentia_info["import_essentia_standard_ok"]:
        blockers.append(
            {
                "code": "ESSENTIA_STANDARD_IMPORT_FAILED",
                "message": "essentia.standard import failed in isolated probe environment.",
            }
        )
    elif not essentia_info["tensorflow_input_musiccnn_available"]:
        blockers.append(
            {
                "code": "TENSORFLOW_INPUT_MUSICCNN_UNAVAILABLE",
                "message": "essentia.standard.TensorflowInputMusiCNN is not available.",
            }
        )

    if onnx_model_probe["provided"] and not onnx_model_probe["file_exists"]:
        blockers.append(
            {
                "code": "ONNX_MODEL_PATH_INVALID",
                "message": "explicit ONNX model path was provided but the file is missing.",
            }
        )
    if classes_probe["provided"] and not classes_probe["file_exists"]:
        blockers.append(
            {
                "code": "CLASSES_PATH_INVALID",
                "message": "explicit classes path was provided but the file is missing.",
            }
        )
    if classes_probe["provided"] and classes_probe["file_exists"] and not classes_probe["read_ok"]:
        blockers.append(
            {
                "code": "CLASSES_PATH_UNREADABLE",
                "message": "explicit classes path was provided but the file could not be read.",
            }
        )

    if not args.onnx_model_path:
        warnings.append("ONNX model artifact check skipped because --onnx-model-path was not provided.")
    if not args.classes_path:
        warnings.append("Classes artifact check skipped because --classes-path was not provided.")
    if args.onnx_model_path is None and args.classes_path is None:
        warnings.append("Implicit artifact discovery is disabled by design and was not attempted.")

    preexisting_forbidden_artifacts = _collect_preexisting_forbidden_artifacts()
    if preexisting_forbidden_artifacts:
        warnings.append(
            "Pre-existing forbidden artifacts were found in the repository tree and were not modified: "
            + ", ".join(preexisting_forbidden_artifacts)
        )

    report = {
        "schema_version": "0.1",
        "report_type": "onnx_musicnn_runtime_readiness_probe_report",
        "roadmap": "4.76",
        "not_production_decision": True,
        "runtime_readiness_probe_only": True,
        "isolated_environment_required": True,
        "classify_called": False,
        "runtime_smoke_run": False,
        "onnx_inference_run": False,
        "preprocessing_probe_run": False,
        "production_approval": False,
        "python": python_info,
        "onnxruntime": onnxruntime_info,
        "essentia_tensorflow": essentia_info,
        "artifact_paths": artifact_paths,
        "production_boundaries": {
            "production_requirements_changed": False,
            "docker_changed": False,
            "provider_default_unchanged": True,
            "onnx_musicnn_disabled_by_default": True,
            "tidal_parser_touched": False,
        },
        "blockers": blockers,
        "warnings": warnings,
        "next_step_recommendation": (
            "Proceed to Roadmap 4.77 isolated patch-to-ONNX-to-mapping vertical probe "
            "only after explicit artifact paths are available."
        ),
    }
    return report


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Изолированный runtime readiness probe для ONNX/MusiCNN lane."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Путь для JSON report.",
    )
    parser.add_argument(
        "--onnx-model-path",
        type=str,
        default=None,
        help="Явный путь к ONNX model artifact. Без этого проверка пропускается.",
    )
    parser.add_argument(
        "--classes-path",
        type=str,
        default=None,
        help="Явный путь к classes artifact. Без этого проверка пропускается.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(args)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = {
        "roadmap": report["roadmap"],
        "status": "ok" if not report["blockers"] else "blocked",
        "blockers": len(report["blockers"]),
        "warnings": len(report["warnings"]),
        "report": str(args.output),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
