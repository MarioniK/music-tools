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
DEFAULT_FIXTURE_DIR = Path("/tmp/music-tools-onnx-parity/fixtures")
DEFAULT_ISOLATED_PYTHON = Path("/tmp/music-tools-onnx-parity/venv/bin/python")
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
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--isolated-python", type=Path, default=DEFAULT_ISOLATED_PYTHON)
    parser.add_argument("--strategy-report", type=Path, default=DEFAULT_BASELINE_STRATEGY_REPORT)
    parser.add_argument("--prototype-report", type=Path, default=DEFAULT_BASELINE_PROTOTYPE_REPORT)
    parser.add_argument(
        "--agents-md-read",
        action="store_true",
        default=True,
        help="Подтверждает, что AGENTS.md был прочитан. По умолчанию включено.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = build_report(args)
    _write_report(report, args.report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
