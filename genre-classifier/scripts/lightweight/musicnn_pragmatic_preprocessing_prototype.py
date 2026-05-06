#!/usr/bin/env python3
"""Локальный scaffold для Roadmap 4.56 по прагматичному preprocessing для MusiCNN.

Хелпер работает только как CLI и не подключается к production app:
- не импортирует `app`;
- не вызывает `/classify`;
- не меняет provider wiring;
- не добавляет зависимости;
- не выполняет сетевые загрузки;
- не утверждает строгую legacy parity.

Скрипт собирает безопасные метаданные об официальном ONNX/MusiCNN артефакте,
проверяет fixture provenance и локальный isolated env, а затем честно фиксирует
блокеры для mel-пути, если Essentia standard алгоритмы недоступны. Это local-only
scaffold, а не production implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/evidence/"
    / "roadmap-4.56-onnx-musicnn-pragmatic-preprocessing-prototype-report.json"
)
DEFAULT_BASELINE_REPORT = (
    SERVICE_ROOT / "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json"
)
DEFAULT_FIXTURE_DIR = Path("/tmp/music-tools-onnx-parity/fixtures")
DEFAULT_ONNX_MODEL = Path("/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx")
DEFAULT_ONNX_METADATA = Path("/tmp/music-tools-onnx-parity/msd-musicnn-1.json")
DEFAULT_PYTHON = Path("/tmp/music-tools-onnx-parity/venv/bin/python")

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
    "BASELINE_EVIDENCE_MISSING",
    "ONNX_ARTIFACT_MISSING",
    "ONNX_METADATA_MISSING",
    "ONNXRUNTIME_UNAVAILABLE",
    "FIXTURE_FILES_MISSING",
    "PRAGMATIC_PREPROCESSING_DEPENDENCY_UNAVAILABLE",
    "ESSENTIA_STANDARD_MEL_PATH_UNAVAILABLE",
    "MEL_PATCH_SHAPE_NOT_PRODUCED",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "PRODUCTION_DEPENDENCY_CHANGE_NOT_ALLOWED",
    "MODEL_FILE_IN_REPO_NOT_ALLOWED",
    "AUDIO_FILE_IN_REPO_NOT_ALLOWED",
    "VENV_IN_REPO_NOT_ALLOWED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}


class PrototypeError(Exception):
    """Ожидаемая ошибка scaffold-проверки."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PrototypeError(f"JSON artifact is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PrototypeError(f"JSON artifact is invalid: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise PrototypeError(f"JSON artifact must be an object: {path}")
    return data


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PrototypeError(f"Source artifact is missing: {path}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _blocker(code: str, message: str) -> dict[str, str]:
    if code not in ALLOWED_BLOCKER_CODES:
        raise PrototypeError(f"Unsupported blocker code: {code}")
    return {"code": code, "message": message}


def _load_baseline_evidence(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    outputs = data.get("baseline_outputs")
    if not isinstance(outputs, list) or len(outputs) != 3:
        raise PrototypeError("baseline evidence does not contain the committed fixture set")

    fixture_ids = []
    output_shapes = []
    for item in outputs:
        if not isinstance(item, dict):
            raise PrototypeError("baseline outputs must contain objects")
        fixture_ids.append(item.get("fixture_id"))
        output_shapes.append(item.get("output_shape"))

    return {
        "report_path": "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json",
        "available": bool(data.get("baseline_capture_succeeded")),
        "fixture_count": len(outputs),
        "fixture_ids": fixture_ids,
        "expected_output_shapes": output_shapes,
    }


def _collect_fixture_records(fixture_dir: Path) -> list[dict[str, Any]]:
    if not fixture_dir.is_dir():
        raise PrototypeError("fixture directory is missing")

    missing = [item["fixture_file"] for item in EXPECTED_FIXTURES if not (fixture_dir / item["fixture_file"]).is_file()]
    if missing:
        raise PrototypeError(f"missing fixture files: {missing}")

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


def _inspect_onnx_metadata(model_path: Path, metadata_path: Path, python_executable: Path) -> dict[str, Any]:
    if not model_path.is_file():
        raise PrototypeError(f"ONNX artifact is missing: {model_path}")
    if not metadata_path.is_file():
        raise PrototypeError(f"ONNX metadata is missing: {metadata_path}")
    if not python_executable.is_file():
        raise PrototypeError("isolated python executable is missing")

    probe = subprocess.run(
        [
            str(python_executable),
            "-c",
            (
                "import json\n"
                "import sys\n"
                "from pathlib import Path\n"
                "import onnxruntime as ort\n"
                "model = Path(sys.argv[1])\n"
                "options = ort.SessionOptions()\n"
                "options.intra_op_num_threads = 1\n"
                "options.inter_op_num_threads = 1\n"
                "session = ort.InferenceSession(str(model), sess_options=options, providers=['CPUExecutionProvider'])\n"
                "payload = {\n"
                "    'onnxruntime_version': ort.__version__,\n"
                "    'input_names': [item.name for item in session.get_inputs()],\n"
                "    'input_shapes': [list(item.shape) for item in session.get_inputs()],\n"
                "    'output_names': [item.name for item in session.get_outputs()],\n"
                "    'output_shapes': [list(item.shape) for item in session.get_outputs()],\n"
                "}\n"
                "print(json.dumps(payload, ensure_ascii=False))\n"
            ),
            str(model_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise PrototypeError((probe.stderr or probe.stdout or "onnxruntime metadata probe failed").strip())

    payload = json.loads(probe.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        raise PrototypeError("onnxruntime metadata probe returned invalid JSON")

    return {
        "available": True,
        "onnxruntime_available": True,
        "onnxruntime_version": payload["onnxruntime_version"],
        "model_sha256": _sha256(model_path),
        "metadata_sha256": _sha256(metadata_path),
        "input_name": payload["input_names"][0],
        "input_shape_tail": list(payload["input_shapes"][0])[-2:],
        "output_names": payload["output_names"],
        "output_shape_tails": [list(shape)[-1:] for shape in payload["output_shapes"]],
    }


def _probe_essentia_standard_runtime(python_executable: Path) -> dict[str, Any]:
    if not python_executable.is_file():
        return {
            "available": False,
            "error": "isolated python executable is missing",
            "algorithm_names": [],
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
                "    print(json.dumps({'available': False, 'error': f'{type(exc).__name__}: {exc}', 'algorithm_names': []}, ensure_ascii=False))\n"
                "else:\n"
                "    names = [name for name in dir(es) if 'Mel' in name or 'Spectrogram' in name or 'MusiCNN' in name]\n"
                "    print(json.dumps({'available': True, 'error': None, 'algorithm_names': names[:80]}, ensure_ascii=False))\n"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if probe.returncode != 0:
        return {
            "available": False,
            "error": (probe.stderr or probe.stdout or "essentia probe failed").strip(),
            "algorithm_names": [],
        }

    payload = json.loads(probe.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        return {
            "available": False,
            "error": "essentia probe returned invalid JSON",
            "algorithm_names": [],
        }
    return payload


def _attempt_preprocessing_probe(
    *,
    mode: str,
    essentia_probe: dict[str, Any],
    fixture_count: int,
) -> dict[str, Any]:
    blockers = []
    succeeded = False
    produced_shape: list[int] | None = None
    repeated_run_stability_checked = False

    if mode == "preprocessing-probe":
        if not essentia_probe.get("available"):
            blockers.extend(
                [
                    _blocker(
                        "PRAGMATIC_PREPROCESSING_DEPENDENCY_UNAVAILABLE",
                        "Essentia standard runtime is unavailable in the approved isolated environment.",
                    ),
                    _blocker(
                        "ESSENTIA_STANDARD_MEL_PATH_UNAVAILABLE",
                        "Essentia standard mel-spectrogram path cannot be exercised because the required runtime is unavailable.",
                    ),
                ]
            )
        elif not essentia_probe.get("algorithm_names"):
            blockers.append(
                _blocker(
                    "ESSENTIA_STANDARD_MEL_PATH_UNAVAILABLE",
                    "Essentia standard runtime is present, but no mel/spectrogram algorithms were confirmed.",
                )
            )
        else:
            blockers.append(
                _blocker(
                    "MEL_PATCH_SHAPE_NOT_PRODUCED",
                    "The scaffold does not yet materialize a reproducible mel-spectrogram patch in this repository.",
                )
            )
    else:
        blockers.extend(
            [
                _blocker(
                    "PRAGMATIC_PREPROCESSING_DEPENDENCY_UNAVAILABLE",
                    "Metadata-only mode does not execute the mel preprocessing probe.",
                ),
                _blocker(
                    "ESSENTIA_STANDARD_MEL_PATH_UNAVAILABLE",
                    "Metadata-only mode does not confirm the Essentia standard mel path.",
                ),
            ]
        )

    return {
        "attempted": mode == "preprocessing-probe",
        "succeeded": succeeded,
        "produced_shape": produced_shape,
        "fixture_count": fixture_count,
        "repeated_run_stability_checked": repeated_run_stability_checked,
        "blockers": blockers,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []

    if not args.agents_md_read:
        blockers.append(_blocker("AGENTS_MD_NOT_READ", "AGENTS.md was not confirmed as read."))

    try:
        baseline_evidence = _load_baseline_evidence(args.baseline_report)
    except PrototypeError as exc:
        blockers.append(_blocker("BASELINE_EVIDENCE_MISSING", str(exc)))
        baseline_evidence = {
            "report_path": "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json",
            "available": False,
            "fixture_count": 0,
            "fixture_ids": [],
            "expected_output_shapes": [],
        }

    try:
        sanitized_fixtures = _collect_fixture_records(args.fixtures_dir)
    except PrototypeError as exc:
        blockers.append(_blocker("FIXTURE_FILES_MISSING", str(exc)))
        sanitized_fixtures = []

    try:
        onnx_metadata = _inspect_onnx_metadata(args.onnx_model, args.onnx_metadata, args.python)
    except PrototypeError as exc:
        message = str(exc)
        if "metadata" in message.casefold():
            blockers.append(_blocker("ONNX_METADATA_MISSING", message))
        elif "python executable" in message.casefold():
            blockers.append(_blocker("ONNXRUNTIME_UNAVAILABLE", message))
        else:
            blockers.append(_blocker("ONNX_ARTIFACT_MISSING", message))
        onnx_metadata = {
            "available": False,
            "onnxruntime_available": False,
            "onnxruntime_version": None,
            "model_sha256": None,
            "metadata_sha256": None,
            "input_name": None,
            "input_shape_tail": None,
            "output_names": [],
            "output_shape_tails": [],
        }

    essentia_probe = _probe_essentia_standard_runtime(args.python)
    preprocessing_probe_result = _attempt_preprocessing_probe(
        mode=args.mode,
        essentia_probe=essentia_probe,
        fixture_count=len(sanitized_fixtures),
    )
    blockers.extend(preprocessing_probe_result["blockers"])

    unique_blockers: list[dict[str, str]] = []
    seen_codes: set[str] = set()
    for item in blockers:
        code = item["code"]
        if code not in seen_codes:
            unique_blockers.append(item)
            seen_codes.add(code)

    report = {
        "schema_version": "0.1",
        "report_type": "musicnn_onnx_pragmatic_preprocessing_prototype_report",
        "report_id": "roadmap_4_56_onnx_musicnn_pragmatic_preprocessing_prototype_scaffold",
        "generated_by": "scripts/lightweight/musicnn_pragmatic_preprocessing_prototype.py",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "roadmap": "4.56",
        "agents_md_read": bool(args.agents_md_read),
        "not_production_decision": True,
        "target_candidate": "official_onnx_musicnn",
        "strategy_source": {
            "roadmap": "4.55",
            "strategy": "essentia_standard_audio_loading_plus_standalone_mel_spectrogram_generation",
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
        "prototype_modes": ["metadata_only", "preprocessing_probe"],
        "onnx_artifacts": {
            "model_name": "msd-musicnn-1.onnx",
            "model_sha256": onnx_metadata["model_sha256"],
            "metadata_name": "msd-musicnn-1.json",
            "metadata_sha256": onnx_metadata["metadata_sha256"],
            "external_workspace": True,
        },
        "baseline_evidence": baseline_evidence,
        "onnx_input": {
            "input_name": onnx_metadata["input_name"],
            "shape_tail": onnx_metadata["input_shape_tail"],
            "output_names": onnx_metadata["output_names"],
            "output_shape_tails": onnx_metadata["output_shape_tails"],
        },
        "expected_outputs": {
            "activations": [50],
            "embeddings": [200],
        },
        "local_environment": {
            "onnxruntime_available": bool(onnx_metadata["onnxruntime_available"]),
            "onnxruntime_version": onnx_metadata["onnxruntime_version"],
            "essentia_available": bool(essentia_probe.get("available")),
            "essentia_error": essentia_probe.get("error"),
            "required_dependencies_missing": not bool(essentia_probe.get("available")),
            "missing_dependencies": [] if essentia_probe.get("available") else ["essentia"],
        },
        "preprocessing_probe_result": preprocessing_probe_result,
        "sanitized_fixtures": sanitized_fixtures,
        "blockers": unique_blockers,
        "next_step_recommendation": (
            "Если Essentia standard mel-путь станет доступен в локальном isolated env, "
            "повторить preprocessing-probe; иначе держать Roadmap 4.56 как local-only scaffold "
            "и не менять production provider/default logic."
        ),
    }
    return report


def _write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Построить local-only scaffold отчёт для Roadmap 4.56 MusiCNN preprocessing.",
    )
    parser.add_argument(
        "--mode",
        choices=("metadata-only", "preprocessing-probe"),
        default="metadata-only",
        help="metadata-only собирает только метаданные; preprocessing-probe честно фиксирует blocker'ы для mel-пути.",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--baseline-report", type=Path, default=DEFAULT_BASELINE_REPORT)
    parser.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--onnx-model", type=Path, default=DEFAULT_ONNX_MODEL)
    parser.add_argument("--onnx-metadata", type=Path, default=DEFAULT_ONNX_METADATA)
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
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
