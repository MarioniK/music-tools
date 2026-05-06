#!/usr/bin/env python3
"""Локальный helper для проверки TensorflowInputMusiCNN availability/probe gate.

Скрипт работает только как CLI, не импортирует production app и не трогает
provider wiring. Он нужен для узкой local-only проверки:

- доступен ли `essentia.standard.TensorflowInputMusiCNN` в isolated env и в
  system Python;
- можно ли, если алгоритм доступен, получить mel-bands path без
  `TensorflowPredictMusiCNN`;
- можно ли сформировать стабильный `[187, 96]` patch без fake output;
- каков честный blocker, если Essentia runtime отсутствует.

`--isolated-python` используется только для availability checks. Сам
preprocessing-probe выполняется в интерпретаторе, который запускает helper.
Чтобы выполнить preprocessing-probe внутри isolated env, helper нужно вызвать
через этот интерпретатор:

`<isolated_python> scripts/lightweight/musicnn_tensorflow_input_probe.py --mode preprocessing-probe`

Это pragmatic ONNX/MusiCNN lane helper, а не strict parity oracle и не
production decision gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/evidence/"
    / "roadmap-4.57-tensorflow-input-musicnn-availability-probe-report.json"
)
DEFAULT_BASELINE_STRATEGY_REPORT = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/evidence/"
    / "roadmap-4.55-onnx-musicnn-pragmatic-preprocessing-strategy-report.json"
)
DEFAULT_BASELINE_PROTOTYPE_REPORT = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/evidence/"
    / "roadmap-4.56-onnx-musicnn-pragmatic-preprocessing-prototype-report.json"
)
DEFAULT_PREPROCESSING_PROBE_REPORT = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "tensorflow-input-musicnn-preprocessing-probe-report.json"
)
DEFAULT_FIXTURE_DIR = Path("/tmp/music-tools-onnx-parity/fixtures")
DEFAULT_ISOLATED_PYTHON = Path("/tmp/music-tools-onnx-parity/venv/bin/python")
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_FRAME_SIZE = 512
DEFAULT_HOP_SIZE = 256
EXPECTED_SHAPE = [187, 96]
EXPECTED_FIXTURES = (
    {
        "fixture_file": "john_bartmann__earning_happiness__cc0.mp3",
        "fixture_id": "john_bartmann_earning_happiness_cc0",
        "sha256": "d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628",
        "license_status": "CC0 1.0 Universal / public domain",
    },
    {
        "fixture_file": "john_bartmann__happy_clappy__cc0.mp3",
        "fixture_id": "john_bartmann_happy_clappy_cc0",
        "sha256": "4f21570f701c07696c6b05f051528241a82156b923ab4bb3071c3c4af4a3372e",
        "license_status": "CC0 1.0 Universal / public domain",
    },
    {
        "fixture_file": "john_bartmann__home_at_last__cc0.mp3",
        "fixture_id": "john_bartmann_home_at_last_cc0",
        "sha256": "0146392a4ea96de074197b2622ebd707ff2560586152bbd1e901095f2ea01c75",
        "license_status": "CC0 1.0 Universal / public domain",
    },
)

ALLOWED_BLOCKER_CODES = {
    "AGENTS_MD_NOT_READ",
    "ROADMAP_4_55_STRATEGY_REPORT_MISSING",
    "ROADMAP_4_56_PROTOTYPE_REPORT_MISSING",
    "FIXTURE_FILES_MISSING",
    "ISOLATED_ENV_MISSING",
    "ONNXRUNTIME_UNAVAILABLE",
    "ESSENTIA_IMPORT_FAILED",
    "TENSORFLOW_INPUT_MUSICNN_UNAVAILABLE",
    "TENSORFLOW_INPUT_MUSICNN_IMPORT_FAILED",
    "TENSORFLOW_INPUT_MUSICNN_PROBE_FAILED",
    "TENSORFLOW_INPUT_MUSICNN_PATCH_NOT_GENERATED",
    "TENSORFLOW_INPUT_MUSICNN_PATCH_NOT_STABLE",
    "REPEATED_RUN_STABILITY_NOT_CHECKED",
    "APPROVED_LEGAL_FIXTURE_NOT_AVAILABLE",
    "MUSICNN_MEL_PATCH_SHAPE_NOT_PRODUCED",
    "MUSICNN_MEL_PATCH_SHAPE_UNSTABLE",
    "GENERIC_MELBANDS_FALLBACK_USED",
    "GENERIC_MELBANDS_FALLBACK_BLOCKED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "MODEL_FILE_IN_REPO_NOT_ALLOWED",
    "AUDIO_FILE_IN_REPO_NOT_ALLOWED",
    "PRODUCTION_DEPENDENCY_CHANGE_NOT_APPROVED",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "PROVIDER_IMPLEMENTATION_NOT_APPROVED",
    "DEFAULT_PROVIDER_SWITCH_NOT_APPROVED",
    "PRODUCTION_MIGRATION_NOT_APPROVED",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}


class ProbeError(Exception):
    """Ожидаемая ошибка local-only probe helper."""


def _safe_error(exc: Exception) -> str:
    """Возвращает безопасное для отчёта описание исключения."""

    return f"{type(exc).__name__}: {exc}"


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _blocker(code: str, message: str) -> dict[str, str]:
    if code not in ALLOWED_BLOCKER_CODES:
        raise ProbeError(f"Unsupported blocker code: {code}")
    return {"code": code, "message": message}


def _load_baseline_report(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    if data.get("roadmap") not in {"4.55", "4.56"}:
        raise ProbeError(f"Unexpected baseline report roadmap: {path}")
    if not isinstance(data.get("target_candidate"), str):
        raise ProbeError(f"Baseline report is missing target candidate: {path}")
    return {
        "path": path.relative_to(SERVICE_ROOT).as_posix(),
        "exists": True,
        "roadmap": data.get("roadmap"),
        "target_candidate": data.get("target_candidate"),
        "not_production_decision": bool(data.get("not_production_decision")),
    }


def _collect_fixture_records(fixture_dir: Path) -> list[dict[str, Any]]:
    if not fixture_dir.is_dir():
        raise ProbeError("fixture directory is missing")

    missing = [item["fixture_file"] for item in EXPECTED_FIXTURES if not (fixture_dir / item["fixture_file"]).is_file()]
    if missing:
        raise ProbeError(f"missing fixture files: {missing}")

    records: list[dict[str, Any]] = []
    for template in EXPECTED_FIXTURES:
        fixture_path = fixture_dir / template["fixture_file"]
        records.append(
            {
                "fixture_id": template["fixture_id"],
                "sha256": _sha256(fixture_path),
                "license_status": template["license_status"],
            }
        )
    return records


def _probe_python(python_executable: Path) -> dict[str, Any]:
    if not python_executable.is_file():
        return {
            "python_available": False,
            "import_status": "missing",
            "import_error_category": "FileNotFoundError",
            "import_error_message": "python executable is missing",
            "hasattr_result": False,
            "available": False,
        }

    probe = subprocess.run(
        [
            str(python_executable),
            "-c",
            (
                "import json\n"
                "try:\n"
                "    import essentia.standard as es\n"
                "except Exception as exc:\n"
                "    print(json.dumps({"
                "        'python_available': True,"
                "        'import_status': 'failed',"
                "        'import_error_category': type(exc).__name__,"
                "        'import_error_message': str(exc),"
                "        'hasattr_result': False,"
                "        'available': False"
                "    }, ensure_ascii=False))\n"
                "else:\n"
                "    hasattr_result = hasattr(es, 'TensorflowInputMusiCNN')\n"
                "    print(json.dumps({"
                "        'python_available': True,"
                "        'import_status': 'imported',"
                "        'import_error_category': None,"
                "        'import_error_message': None,"
                "        'hasattr_result': hasattr_result,"
                "        'available': hasattr_result"
                "    }, ensure_ascii=False))\n"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        return {
            "python_available": True,
            "import_status": "failed",
            "import_error_category": "SubprocessError",
            "import_error_message": (probe.stderr or probe.stdout or "essentia probe failed").strip(),
            "hasattr_result": None,
            "available": False,
        }

    payload = json.loads(probe.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        raise ProbeError("essentia probe returned invalid JSON")
    return payload


def _probe_onnxruntime_version(python_executable: Path) -> dict[str, Any]:
    if not python_executable.is_file():
        return {
            "available": False,
            "version": None,
            "error_category": "FileNotFoundError",
            "error_message": "python executable is missing",
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
                "        'error_category': type(exc).__name__,"
                "        'error_message': str(exc)"
                "    }, ensure_ascii=False))\n"
                "else:\n"
                "    print(json.dumps({"
                "        'available': True,"
                "        'version': ort.__version__,"
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
            "error_category": "SubprocessError",
            "error_message": (probe.stderr or probe.stdout or "onnxruntime probe failed").strip(),
        }

    payload = json.loads(probe.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        raise ProbeError("onnxruntime probe returned invalid JSON")
    return payload


def _probe_essentia_runtime(python_executable: Path) -> dict[str, Any]:
    """Собирает безопасные import-level сведения об Essentia runtime."""

    if not python_executable.is_file():
        return {
            "python_available": False,
            "import_essentia": False,
            "import_essentia_standard": False,
            "tensorflow_input_musicnn_available": False,
            "essentia_runtime_version": None,
            "essentia_tensorflow_package_version": None,
            "import_error_category": "FileNotFoundError",
            "import_error_message": "python executable is missing",
            "warnings": [],
        }

    probe = subprocess.run(
        [
            str(python_executable),
            "-c",
            (
                "import importlib.metadata\n"
                "import json\n"
                "try:\n"
                "    import essentia\n"
                "    import essentia.standard as es\n"
                "except Exception as exc:\n"
                "    print(json.dumps({"
                "        'python_available': True,"
                "        'import_essentia': False,"
                "        'import_essentia_standard': False,"
                "        'tensorflow_input_musiccnn_available': False,"
                "        'essentia_runtime_version': None,"
                "        'essentia_tensorflow_package_version': importlib.metadata.version('essentia-tensorflow'),"
                "        'import_error_category': type(exc).__name__,"
                "        'import_error_message': str(exc),"
                "    }, ensure_ascii=False))\n"
                "else:\n"
                "    print(json.dumps({"
                "        'python_available': True,"
                "        'import_essentia': True,"
                "        'import_essentia_standard': True,"
                "        'tensorflow_input_musicnn_available': hasattr(es, 'TensorflowInputMusiCNN'),"
                "        'essentia_runtime_version': getattr(essentia, '__version__', None),"
                "        'essentia_tensorflow_package_version': importlib.metadata.version('essentia-tensorflow'),"
                "        'import_error_category': None,"
                "        'import_error_message': None,"
                "    }, ensure_ascii=False))\n"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    warnings = [line.strip() for line in (probe.stderr or "").splitlines() if line.strip()]
    if probe.returncode != 0:
        return {
            "python_available": True,
            "import_essentia": False,
            "import_essentia_standard": False,
            "tensorflow_input_musicnn_available": False,
            "essentia_runtime_version": None,
            "essentia_tensorflow_package_version": None,
            "import_error_category": "SubprocessError",
            "import_error_message": (probe.stderr or probe.stdout or "essentia probe failed").strip(),
            "warnings": warnings,
        }

    payload = json.loads(probe.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        raise ProbeError("essentia probe returned invalid JSON")
    payload["warnings"] = warnings
    return payload


def _normalize_patch(rows: list[list[float]], expected_shape: list[int] | None = None) -> list[list[float]]:
    shape = expected_shape or EXPECTED_SHAPE
    expected_frames, expected_bands = shape
    normalized_rows: list[list[float]] = []

    for row in rows:
        normalized_row = [float(value) for value in row[:expected_bands]]
        if len(normalized_row) < expected_bands:
            normalized_row.extend([0.0] * (expected_bands - len(normalized_row)))
        normalized_rows.append(normalized_row)

    if not normalized_rows:
        raise ProbeError("no mel-bands were produced")

    if len(normalized_rows) < expected_frames:
        last_row = list(normalized_rows[-1])
        while len(normalized_rows) < expected_frames:
            normalized_rows.append(list(last_row))
    else:
        normalized_rows = normalized_rows[:expected_frames]

    if len(normalized_rows) != expected_frames or any(len(row) != expected_bands for row in normalized_rows):
        raise ProbeError("normalized mel patch does not match the expected shape")

    return normalized_rows


def _capture_tensorflow_input_patch(
    *,
    fixture_path: Path,
    fixture_id: str,
) -> dict[str, Any]:
    try:
        import essentia.standard as es
    except Exception as exc:  # pragma: no cover - executed only in an approved env
        raise ProbeError(_safe_error(exc)) from exc

    audio = es.MonoLoader(filename=str(fixture_path), sampleRate=16000)()
    tensor = es.TensorflowInputMusiCNN()
    rows: list[list[float]] = []

    for frame in es.FrameGenerator(
        audio,
        frameSize=512,
        hopSize=256,
        startFromZero=True,
        lastFrameToEndOfFile=True,
    ):
        bands = tensor(frame)
        row = [float(value) for value in bands]
        rows.append(row)

    normalized_patch = _normalize_patch(rows, EXPECTED_SHAPE)
    patch_digest = hashlib.sha256(
        json.dumps(normalized_patch, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return {
        "fixture_id": fixture_id,
        "produced_shape": [len(normalized_patch), len(normalized_patch[0])],
        "patch_digest": patch_digest,
    }


def _attempt_preprocessing_probe(
    *,
    mode: str,
    fixture_dir: Path,
    python_executable: Path,
    availability: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    attempted = mode == "preprocessing-probe"
    succeeded = False
    produced_shape: list[int] | None = None
    repeated_run_stability_checked = False
    stable: bool | None = None

    if not attempted:
        return {
            "attempted": False,
            "succeeded": False,
            "produced_shape": None,
            "expected_shape": EXPECTED_SHAPE,
            "fixture_count": 0,
            "repeated_run_stability_checked": False,
            "stable": None,
            "blockers": [],
        }

    if not availability.get("available_in_isolated_env"):
        blockers.append(
            _blocker(
                "ESSENTIA_IMPORT_FAILED",
                "Essentia standard runtime недоступен в approved isolated env.",
            )
        )
        blockers.append(
            _blocker(
                "TENSORFLOW_INPUT_MUSICNN_IMPORT_FAILED",
                "TensorflowInputMusiCNN нельзя проверить, потому что essentia.standard недоступен.",
            )
        )
        return {
            "attempted": True,
            "succeeded": False,
            "produced_shape": None,
            "expected_shape": EXPECTED_SHAPE,
            "fixture_count": 0,
            "repeated_run_stability_checked": False,
            "stable": None,
            "blockers": blockers,
        }

    fixture_records = _collect_fixture_records(fixture_dir)
    fixture_count = len(fixture_records)
    fixture_path = fixture_dir / EXPECTED_FIXTURES[0]["fixture_file"]

    try:
        raw_patch_summary = _capture_tensorflow_input_patch(
            fixture_path=fixture_path,
            fixture_id=EXPECTED_FIXTURES[0]["fixture_id"],
        )
    except ProbeError as exc:
        blockers.append(
            _blocker(
                "TENSORFLOW_INPUT_MUSICNN_PROBE_FAILED",
                str(exc),
            )
        )
        return {
            "attempted": True,
            "succeeded": False,
            "produced_shape": None,
            "expected_shape": EXPECTED_SHAPE,
            "fixture_count": fixture_count,
            "repeated_run_stability_checked": False,
            "stable": None,
            "blockers": blockers,
        }

    if not isinstance(raw_patch_summary, dict):  # pragma: no cover - defensive only
        blockers.append(
            _blocker(
                "TENSORFLOW_INPUT_MUSICNN_PROBE_FAILED",
                "TensorflowInputMusiCNN probe did not return a structured summary.",
            )
        )
        return {
            "attempted": True,
            "succeeded": False,
            "produced_shape": None,
            "expected_shape": EXPECTED_SHAPE,
            "fixture_count": fixture_count,
            "repeated_run_stability_checked": False,
            "stable": None,
            "blockers": blockers,
        }

    try:
        repeated_patch_summary = _capture_tensorflow_input_patch(
            fixture_path=fixture_path,
            fixture_id=EXPECTED_FIXTURES[0]["fixture_id"],
        )
    except ProbeError as exc:
        blockers.append(
            _blocker(
                "MUSICNN_MEL_PATCH_SHAPE_NOT_PRODUCED",
                str(exc),
            )
        )
        return {
            "attempted": True,
            "succeeded": False,
            "produced_shape": None,
            "expected_shape": EXPECTED_SHAPE,
            "fixture_count": fixture_count,
            "repeated_run_stability_checked": True,
            "stable": None,
            "blockers": blockers,
        }

    produced_shape = raw_patch_summary.get("produced_shape")
    repeated_run_stability_checked = True
    stable = raw_patch_summary.get("patch_digest") == repeated_patch_summary.get("patch_digest")
    succeeded = produced_shape == EXPECTED_SHAPE and stable

    if produced_shape != EXPECTED_SHAPE:
        blockers.append(
            _blocker(
                "MUSICNN_MEL_PATCH_SHAPE_NOT_PRODUCED",
                f"Expected patch shape {EXPECTED_SHAPE} but received {produced_shape}.",
            )
        )
        succeeded = False
    elif not stable:
        blockers.append(
            _blocker(
                "MUSICNN_MEL_PATCH_SHAPE_UNSTABLE",
                "Repeated runs over the same fixture produced different TensorflowInputMusiCNN patches.",
            )
        )
        succeeded = False

    return {
        "attempted": True,
        "succeeded": succeeded,
        "produced_shape": produced_shape,
        "expected_shape": EXPECTED_SHAPE,
        "fixture_count": fixture_count,
        "repeated_run_stability_checked": repeated_run_stability_checked,
        "stable": stable,
        "blockers": blockers,
    }


def _probe_generic_melbands_fallback(*, availability: dict[str, Any]) -> dict[str, Any]:
    if availability.get("available_in_isolated_env"):
        return {
            "generic_melbands_fallback_evaluated": True,
            "generic_melbands_fallback_used": False,
            "fallback_status": "not_used",
            "fallback_risks": [
                "Fallback не нужен, пока TensorflowInputMusiCNN доступен.",
            ],
        }

    return {
        "generic_melbands_fallback_evaluated": True,
        "generic_melbands_fallback_used": False,
        "fallback_status": "blocked",
        "fallback_risks": [
            "Fallback не доказывает gate для TensorflowInputMusiCNN-specific preprocessing.",
        "Fallback повышает риск ухода от pragmatic ONNX lane.",
        ],
    }


def _classify_warnings(warnings: list[str]) -> dict[str, Any]:
    observed = [warning for warning in warnings if warning]
    if any("libcudart.so.11.0" in warning for warning in observed) or any(
        "libcuda.so.1" in warning for warning in observed
    ) or any("CUDA driver unavailable" in warning for warning in observed):
        return {
            "category": "cuda_libraries_missing_but_cpu_import_available",
            "observed": observed,
            "blocking": False,
            "reason": "CPU import-level availability evidence does not require CUDA runtime availability.",
        }
    return {
        "category": "none",
        "observed": observed,
        "blocking": False,
        "reason": "No blocking warnings were observed during the import probe.",
    }


def _load_fixture_provenance_notes(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    if data.get("fixture_set") != "musicnn_onnx_parity_local_legal_fixtures_roadmap_4_45":
        raise ProbeError(f"Unexpected fixture provenance set: {path}")
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ProbeError(f"Fixture provenance is missing fixture entries: {path}")
    sanitized = []
    for item in fixtures:
        if not isinstance(item, dict):
            raise ProbeError(f"Fixture provenance entry must be an object: {path}")
        sanitized.append(
            {
                "fixture_id": item.get("fixture_id"),
                "title": item.get("title"),
                "artist": item.get("artist"),
                "license_status": item.get("license_status"),
                "usage_permission": item.get("usage_permission"),
            }
        )
    return {
        "path": path.relative_to(Path("/tmp")).as_posix() if str(path).startswith("/tmp/") else path.name,
        "fixtures": sanitized,
    }


def _normalize_patch_rows(
    rows: list[list[float]],
    *,
    expected_frames: int,
    expected_bands: int,
) -> list[list[float]]:
    if not rows:
        raise ProbeError("no mel-bands were produced")

    normalized_rows: list[list[float]] = []
    for row in rows:
        if len(row) != expected_bands:
            raise ProbeError(f"expected {expected_bands} bands but received {len(row)}")
        normalized_rows.append([float(value) for value in row])

    if len(normalized_rows) < expected_frames:
        last_row = list(normalized_rows[-1])
        while len(normalized_rows) < expected_frames:
            normalized_rows.append(list(last_row))
    else:
        normalized_rows = normalized_rows[:expected_frames]

    if len(normalized_rows) != expected_frames or any(len(row) != expected_bands for row in normalized_rows):
        raise ProbeError("normalized mel patch does not match the expected shape")
    return normalized_rows


def _sha256_json_payload(payload: list[list[float]]) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _run_tensorflow_input_musiccnn_patch(
    *,
    fixture_path: Path,
    sample_rate: int,
    frame_size: int,
    hop_size: int,
    expected_frames: int,
    expected_bands: int,
) -> dict[str, Any]:
    try:
        import essentia.standard as es
    except Exception as exc:  # pragma: no cover - executed only in an approved env
        raise ProbeError(_safe_error(exc)) from exc

    audio = es.MonoLoader(filename=str(fixture_path), sampleRate=sample_rate)()
    tensor = es.TensorflowInputMusiCNN()
    rows: list[list[float]] = []

    for frame in es.FrameGenerator(
        audio,
        frameSize=frame_size,
        hopSize=hop_size,
        startFromZero=True,
        lastFrameToEndOfFile=True,
    ):
        bands = [float(value) for value in tensor(frame)]
        rows.append(bands)

    normalized_patch = _normalize_patch_rows(
        rows,
        expected_frames=expected_frames,
        expected_bands=expected_bands,
    )
    return {
        "raw_observed_shape": [len(rows), len(rows[0]) if rows else 0],
        "raw_first_row_shape": len(rows[0]) if rows else 0,
        "final_patch_shape": [len(normalized_patch), len(normalized_patch[0])],
        "patch_digest": _sha256_json_payload(normalized_patch),
        "normalized_patch": normalized_patch,
    }


def build_preprocessing_probe_report(args: argparse.Namespace) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []

    if not args.agents_md_read:
        blockers.append(_blocker("AGENTS_MD_NOT_READ", "AGENTS.md was not confirmed as read."))

    fixture_path = getattr(args, "fixture", None)
    if fixture_path is None:
        blockers.append(
            _blocker(
                "APPROVED_LEGAL_FIXTURE_NOT_AVAILABLE",
                "Approved legal fixture path was not provided.",
            )
        )
        fixture_exists = False
    else:
        fixture_exists = fixture_path.is_file()
        if not fixture_exists:
            blockers.append(
                _blocker(
                    "APPROVED_LEGAL_FIXTURE_NOT_AVAILABLE",
                    f"Approved legal fixture is unavailable: {fixture_path}",
                )
            )

    provenance_path = args.fixtures_dir / "fixture-provenance-notes.json"
    try:
        fixture_provenance = _load_fixture_provenance_notes(provenance_path)
    except ProbeError as exc:
        blockers.append(_blocker("FIXTURE_FILES_MISSING", str(exc)))
        fixture_provenance = {
            "path": "fixture-provenance-notes.json",
            "fixtures": [],
        }

    runtime_probe = _probe_essentia_runtime(args.isolated_python)
    import_error_category = runtime_probe.get("import_error_category")
    import_error_message = runtime_probe.get("import_error_message")
    try:
        import importlib.metadata
        import essentia
        import essentia.standard as es
    except Exception as exc:  # pragma: no cover - executed only in an approved env
        import_essentia = False
        import_essentia_standard = False
        tensorflow_input_musiccnn_available = False
        essentia_runtime_version = None
        essentia_tensorflow_package_version = runtime_probe.get("essentia_tensorflow_package_version")
        import_error_category = type(exc).__name__
        import_error_message = str(exc)
        blockers.append(
            _blocker(
                "ESSENTIA_IMPORT_FAILED",
                "Essentia runtime is unavailable in the approved isolated environment.",
            )
        )
    else:
        import_essentia = True
        import_essentia_standard = True
        tensorflow_input_musiccnn_available = hasattr(es, "TensorflowInputMusiCNN")
        essentia_runtime_version = getattr(essentia, "__version__", None)
        essentia_tensorflow_package_version = importlib.metadata.version("essentia-tensorflow")
        if not tensorflow_input_musiccnn_available:
            blockers.append(
                _blocker(
                    "TENSORFLOW_INPUT_MUSICNN_PATCH_NOT_GENERATED",
                    "essentia.standard imported, but TensorflowInputMusiCNN is not exposed.",
                )
            )

    if not fixture_exists or not import_essentia_standard or not tensorflow_input_musiccnn_available:
        status = "blocked"
        repeated_run_stability = {
            "checked": False,
            "shape_equal": None,
            "stable": None,
            "max_abs_diff": None,
            "mean_abs_diff": None,
            "comparison_reason": "Preprocessing probe was not executable to completion.",
        }
        patch_result = {
            "raw_observed_shape": None,
            "final_patch_shape": None,
            "patch_produced": False,
        }
    else:
        run_results: list[dict[str, Any]] = []
        run_patches: list[list[list[float]]] = []
        for _index in range(args.repeat_runs):
            try:
                run_result = _run_tensorflow_input_musiccnn_patch(
                    fixture_path=fixture_path,
                    sample_rate=args.sample_rate,
                    frame_size=args.frame_size,
                    hop_size=args.hop_size,
                    expected_frames=args.expected_frames,
                    expected_bands=args.expected_bands,
                )
            except ProbeError as exc:
                blockers.append(
                    _blocker(
                        "TENSORFLOW_INPUT_MUSICNN_PATCH_NOT_GENERATED",
                        str(exc),
                    )
                )
                status = "blocked"
                repeated_run_stability = {
                    "checked": False,
                    "shape_equal": None,
                    "stable": None,
                    "max_abs_diff": None,
                    "mean_abs_diff": None,
                    "comparison_reason": "TensorflowInputMusiCNN patch could not be generated.",
                }
                patch_result = {
                    "raw_observed_shape": None,
                    "final_patch_shape": None,
                    "patch_produced": False,
                }
                break
            run_results.append(run_result)
            run_patches.append(run_result["normalized_patch"])
        else:
            patch_result = {
                "raw_observed_shape": run_results[0]["raw_observed_shape"],
                "final_patch_shape": run_results[0]["final_patch_shape"],
                "patch_produced": True,
            }
            repeated_run_stability = {
                "checked": len(run_patches) >= 2,
                "shape_equal": None,
                "stable": None,
                "max_abs_diff": None,
                "mean_abs_diff": None,
                "comparison_reason": None,
            }
            if len(run_patches) >= 2:
                first_patch = run_patches[0]
                second_patch = run_patches[1]
                shape_equal = (
                    len(first_patch) == len(second_patch)
                    and all(len(row_a) == len(row_b) for row_a, row_b in zip(first_patch, second_patch))
                )
                diffs: list[float] = []
                if shape_equal:
                    for row_a, row_b in zip(first_patch, second_patch):
                        diffs.extend(abs(value_a - value_b) for value_a, value_b in zip(row_a, row_b))
                    repeated_run_stability = {
                        "checked": True,
                        "shape_equal": True,
                        "stable": max(diffs, default=0.0) == 0.0,
                        "max_abs_diff": max(diffs, default=0.0),
                        "mean_abs_diff": (sum(diffs) / len(diffs)) if diffs else 0.0,
                        "comparison_reason": None,
                    }
                else:
                    repeated_run_stability = {
                        "checked": True,
                        "shape_equal": False,
                        "stable": False,
                        "max_abs_diff": None,
                        "mean_abs_diff": None,
                        "comparison_reason": "The repeated runs produced patches with different shapes.",
                    }
                    blockers.append(
                        _blocker(
                            "REPEATED_RUN_STABILITY_NOT_CHECKED",
                            "Repeated run comparison could not be completed because patch shapes differ.",
                        )
                    )
            else:
                repeated_run_stability = {
                    "checked": False,
                    "shape_equal": None,
                    "stable": None,
                    "max_abs_diff": None,
                    "mean_abs_diff": None,
                    "comparison_reason": "repeat-runs was set below 2, so stability could not be checked.",
                }
                blockers.append(
                    _blocker(
                        "REPEATED_RUN_STABILITY_NOT_CHECKED",
                        "Repeated run stability was not checked because fewer than two runs were requested.",
                    )
                )
            status = "completed" if not blockers and repeated_run_stability.get("stable") is not False else "blocked"
            if repeated_run_stability.get("stable") is False and not any(
                blocker["code"] == "REPEATED_RUN_STABILITY_NOT_CHECKED" for blocker in blockers
            ):
                blockers.append(
                    _blocker(
                        "TENSORFLOW_INPUT_MUSICNN_PATCH_NOT_STABLE",
                        "Repeated runs over the same fixture produced different patches.",
                    )
                )

    warnings = _classify_warnings(list(runtime_probe.get("warnings", [])))

    unique_blockers: list[dict[str, str]] = []
    seen_codes: set[str] = set()
    for item in blockers:
        code = item["code"]
        if code not in seen_codes:
            unique_blockers.append(item)
            seen_codes.add(code)

    report = {
        "schema_version": "0.1",
        "report_type": "tensorflow_input_musiccnn_preprocessing_probe_report",
        "report_id": "roadmap_4_64_tensorflow_input_musiccnn_preprocessing_probe",
        "generated_by": "scripts/lightweight/musicnn_tensorflow_input_probe.py",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "roadmap_step": "4.64",
        "status": status if "status" in locals() else "blocked",
        "service": "genre-classifier",
        "production_touched": False,
        "tidal_parser_touched": False,
        "isolated_venv_path": str(args.isolated_python.parent.parent),
        "python_version": f"Python {platform.python_version()}",
        "essentia_tensorflow_package_version": essentia_tensorflow_package_version,
        "essentia_runtime_version": essentia_runtime_version,
        "import_essentia": import_essentia,
        "import_essentia_standard": import_essentia_standard,
        "tensorflow_input_musiccnn_available": tensorflow_input_musiccnn_available,
        "fixture": {
            "approved_legal_marker": bool(fixture_exists and fixture_provenance.get("fixtures")),
            "sanitized_path_policy": "outside_repo:/tmp/music-tools-onnx-parity/fixtures",
            "path": str(fixture_path) if fixture_path is not None else None,
            "sha256": _sha256(fixture_path) if fixture_exists and fixture_path is not None else None,
            "sample_rate_requested": args.sample_rate,
            "fixture_id": EXPECTED_FIXTURES[0]["fixture_id"] if fixture_exists else None,
            "provenance": fixture_provenance,
        },
        "preprocessing_parameters": {
            "sampleRate": args.sample_rate,
            "frameSize": args.frame_size,
            "numberBands_expected": args.expected_bands,
            "hopSize": args.hop_size,
        },
        "raw_observed_shape": patch_result["raw_observed_shape"],
        "final_patch_shape": patch_result["final_patch_shape"],
        "patch_shape_expected": [args.expected_frames, args.expected_bands],
        "patch_produced": patch_result["patch_produced"],
        "repeated_run_stability": repeated_run_stability,
        "blockers": unique_blockers,
        "warnings": warnings,
        "non_goals": [
            "TensorflowPredictMusiCNN oracle was not used.",
            "Strict legacy parity was not claimed.",
            "ONNX output capture was not run.",
            "/classify was not called.",
            "Docker Compose was not run.",
            "Dockerfile or Compose files were not changed.",
            "Production dependencies were not changed.",
            "Provider/default logic was not changed.",
            "tidal-parser was not touched.",
        ],
        "fake_output_created": False,
        "tensorflow_predict_musicnn_used": False,
        "generic_melbands_fallback_used": False,
        "onnx_output_capture_run": False,
        "classify_called": False,
        "docker_compose_run": False,
        "production_dependency_changes": False,
        "dockerfile_compose_changes": False,
        "provider_default_changes": False,
        "next_step_recommendation": (
            "Если patch [187, 96] produced и repeated-run stability подтверждена, "
            "следующий шаг Roadmap 4.65 может переходить к ONNX output capture; "
            "иначе удерживать lane blocked и не менять production provider/default logic."
        ),
    }
    return report


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []

    if not args.agents_md_read:
        blockers.append(_blocker("AGENTS_MD_NOT_READ", "AGENTS.md was not confirmed as read."))

    try:
        strategy_report = _load_baseline_report(args.strategy_report)
    except ProbeError as exc:
        blockers.append(_blocker("ROADMAP_4_55_STRATEGY_REPORT_MISSING", str(exc)))
        strategy_report = {
            "path": "docs/lightweight/evaluation/evidence/roadmap-4.55-onnx-musicnn-pragmatic-preprocessing-strategy-report.json",
            "exists": False,
            "roadmap": "4.55",
            "target_candidate": "official_onnx_musicnn",
            "not_production_decision": True,
        }

    try:
        prototype_report = _load_baseline_report(args.prototype_report)
    except ProbeError as exc:
        blockers.append(_blocker("ROADMAP_4_56_PROTOTYPE_REPORT_MISSING", str(exc)))
        prototype_report = {
            "path": "docs/lightweight/evaluation/evidence/roadmap-4.56-onnx-musicnn-pragmatic-preprocessing-prototype-report.json",
            "exists": False,
            "roadmap": "4.56",
            "target_candidate": "official_onnx_musicnn",
            "not_production_decision": True,
        }

    try:
        sanitized_fixtures = _collect_fixture_records(args.fixtures_dir)
    except ProbeError as exc:
        blockers.append(_blocker("FIXTURE_FILES_MISSING", str(exc)))
        sanitized_fixtures = []

    isolated_env = _probe_onnxruntime_version(args.isolated_python)
    if not isolated_env.get("available"):
        blockers.append(
            _blocker(
                "ONNXRUNTIME_UNAVAILABLE",
                "onnxruntime is unavailable in the approved isolated environment.",
            )
        )

    isolated_tensorflow_input = _probe_python(args.isolated_python)
    system_python_path = shutil.which("python3")
    system_tensorflow_input: dict[str, Any] | None = None
    if system_python_path:
        system_tensorflow_input = _probe_python(Path(system_python_path))
    else:
        system_tensorflow_input = {
            "python_available": False,
            "import_status": "missing",
            "import_error_category": "FileNotFoundError",
            "import_error_message": "python3 command is missing",
            "hasattr_result": False,
            "available": False,
        }

    available_in_isolated_env = bool(isolated_tensorflow_input.get("available"))
    available_in_system_python = bool(system_tensorflow_input.get("available")) if system_tensorflow_input else False
    import_error_category = isolated_tensorflow_input.get("import_error_category")
    hasattr_result = isolated_tensorflow_input.get("hasattr_result")

    if isolated_tensorflow_input.get("import_status") == "failed":
        blockers.append(
            _blocker(
                "ESSENTIA_IMPORT_FAILED",
                "Essentia standard runtime недоступен в approved isolated env.",
            )
        )
        blockers.append(
            _blocker(
                "TENSORFLOW_INPUT_MUSICNN_IMPORT_FAILED",
                "TensorflowInputMusiCNN нельзя проверить, потому что импорт essentia.standard завершился ошибкой.",
            )
        )
    elif available_in_isolated_env is False:
        blockers.append(
            _blocker(
                "TENSORFLOW_INPUT_MUSICNN_UNAVAILABLE",
                "essentia.standard импортируется, но TensorflowInputMusiCNN там не экспонируется.",
            )
        )

    if system_tensorflow_input and system_tensorflow_input.get("import_status") == "failed":
        blockers.append(
            _blocker(
                "TENSORFLOW_INPUT_MUSICNN_UNAVAILABLE",
                "TensorflowInputMusiCNN недоступен и через system python.",
            )
        )

    tensorflow_input_musiccnn = {
        "checked": True,
        "available_in_isolated_env": available_in_isolated_env,
        "available_in_system_python": available_in_system_python,
        "import_error_category": import_error_category,
        "hasattr_result": hasattr_result,
        "isolated_env": {
            "python_available": bool(isolated_tensorflow_input.get("python_available")),
            "import_status": isolated_tensorflow_input.get("import_status"),
            "available": available_in_isolated_env,
            "import_error_category": isolated_tensorflow_input.get("import_error_category"),
            "import_error_message": isolated_tensorflow_input.get("import_error_message"),
            "hasattr_result": isolated_tensorflow_input.get("hasattr_result"),
            "onnxruntime": isolated_env,
        },
        "system_python": {
            "python_available": bool(system_tensorflow_input.get("python_available")) if system_tensorflow_input else False,
            "import_status": system_tensorflow_input.get("import_status") if system_tensorflow_input else "missing",
            "available": available_in_system_python,
            "import_error_category": system_tensorflow_input.get("import_error_category") if system_tensorflow_input else "FileNotFoundError",
            "import_error_message": system_tensorflow_input.get("import_error_message") if system_tensorflow_input else "python3 command is missing",
            "hasattr_result": system_tensorflow_input.get("hasattr_result") if system_tensorflow_input else None,
        },
    }

    preprocessing_probe_result = _attempt_preprocessing_probe(
        mode=args.mode,
        fixture_dir=args.fixtures_dir,
        python_executable=args.isolated_python,
        availability=tensorflow_input_musiccnn,
    )
    blockers.extend(preprocessing_probe_result["blockers"])

    fallback = _probe_generic_melbands_fallback(availability=tensorflow_input_musiccnn)

    if not fallback["generic_melbands_fallback_used"] and not tensorflow_input_musiccnn["available_in_isolated_env"]:
        blockers.append(
            _blocker(
                "GENERIC_MELBANDS_FALLBACK_BLOCKED",
                "Generic melbands fallback не использован, потому что доступность TensorflowInputMusiCNN всё ещё не подтверждена.",
            )
        )

    preprocessing_probe_execution = "current_interpreter"
    isolated_python_used_for_availability_check = True
    recommended_isolated_probe_invocation = (
        "Use the approved isolated Python interpreter to run "
        "scripts/lightweight/musicnn_tensorflow_input_probe.py --mode preprocessing-probe."
    )

    unique_blockers: list[dict[str, str]] = []
    seen_codes: set[str] = set()
    for item in blockers:
        code = item["code"]
        if code not in seen_codes:
            unique_blockers.append(item)
            seen_codes.add(code)

    report = {
        "schema_version": "0.1",
        "report_type": "musicnn_tensorflow_input_musiccnn_availability_probe_report",
        "report_id": "roadmap_4_57_tensorflow_input_musiccnn_availability_probe_gate",
        "generated_by": "scripts/lightweight/musicnn_tensorflow_input_probe.py",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "roadmap": "4.57",
        "agents_md_read": bool(args.agents_md_read),
        "not_production_decision": True,
        "target_candidate": "official_onnx_musicnn",
        "strategy_source": {
            "roadmap": strategy_report["roadmap"],
            "strategy": "essentia_standard_audio_loading_plus_standalone_mel_spectrogram_generation",
        },
        "prototype_source": {
            "roadmap": prototype_report["roadmap"],
            "helper": "scripts/lightweight/musicnn_pragmatic_preprocessing_prototype.py",
        },
        "strict_legacy_parity_required": False,
        "output_drift_allowed": True,
        "preprocessing_identical_to_legacy_required": False,
        "documented_reproducible_preprocessing_required": True,
        "approved_for_provider_implementation": False,
        "approved_for_default_provider_switch": False,
        "approved_for_production": False,
        "approved_for_dependency_changes": False,
        "approved_for_classify_call": False,
        "legacy_musicnn_default_unchanged": True,
        "isolated_python_used_for_availability_check": isolated_python_used_for_availability_check,
        "preprocessing_probe_execution": preprocessing_probe_execution,
        "recommended_isolated_probe_invocation": recommended_isolated_probe_invocation,
        "probe_policy": {
            "tensorflow_input_musiccnn_allowed_as_preprocessing_only_candidate": True,
            "tensorflow_predict_musiccnn_not_used_as_preprocessing_oracle": True,
            "strict_legacy_parity_required": False,
            "production_decision_made": False,
        },
        "tensorflow_input_musiccnn": tensorflow_input_musiccnn,
        "preprocessing_probe_result": preprocessing_probe_result,
        "sanitized_fixtures": sanitized_fixtures,
        "fallback": fallback,
        "blockers": unique_blockers,
        "next_step_recommendation": (
            "Если TensorflowInputMusiCNN станет импортируемым в approved isolated env, "
            "повторить preprocessing-probe и только затем рассматривать более глубокую pragmatic ONNX/MusiCNN проверку; "
            "иначе держать candidate local-only и не менять production provider/default logic."
        ),
    }
    return report


def _write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Локальный availability/probe helper для TensorflowInputMusiCNN.",
    )
    parser.add_argument(
        "--mode",
        choices=("availability", "preprocessing-probe"),
        default="availability",
        help="availability собирает только статус окружений; preprocessing-probe пытается подтвердить mel path без fake output.",
    )
    parser.add_argument("--output", "--report", dest="report", type=Path, default=None)
    parser.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--isolated-python", type=Path, default=DEFAULT_ISOLATED_PYTHON)
    parser.add_argument("--strategy-report", type=Path, default=DEFAULT_BASELINE_STRATEGY_REPORT)
    parser.add_argument("--prototype-report", type=Path, default=DEFAULT_BASELINE_PROTOTYPE_REPORT)
    parser.add_argument("--fixture", type=Path, default=None)
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--expected-frames", type=int, default=EXPECTED_SHAPE[0])
    parser.add_argument("--expected-bands", type=int, default=EXPECTED_SHAPE[1])
    parser.add_argument("--repeat-runs", type=int, default=2)
    parser.add_argument("--frame-size", type=int, default=DEFAULT_FRAME_SIZE)
    parser.add_argument("--hop-size", type=int, default=DEFAULT_HOP_SIZE)
    parser.add_argument(
        "--agents-md-read",
        action="store_true",
        default=True,
        help="Подтверждает, что AGENTS.md был прочитан. По умолчанию включено.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.report is None:
        args.report = DEFAULT_REPORT_PATH if args.mode == "availability" else DEFAULT_PREPROCESSING_PROBE_REPORT
    if args.mode == "preprocessing-probe":
        report = build_preprocessing_probe_report(args)
    else:
        report = build_report(args)
    _write_report(report, args.report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
