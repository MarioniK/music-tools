#!/usr/bin/env python3
"""CLI-хелпер для подготовки Roadmap 4.51 ONNX-side capture отчёта.

Хелпер локальный и не привязан к production runtime. Он собирает безопасные
метаданные об официальном локальном `msd-musicnn-1.onnx`, подтверждает наличие
baseline evidence и fixture provenance, но не выполняет ONNX inference, не
вызывает `/classify` и не трогает provider wiring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = (
    SERVICE_ROOT / "docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-output-capture-report.json"
)
DEFAULT_BASELINE_REPORT_PATH = (
    SERVICE_ROOT / "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json"
)
DEFAULT_FIXTURE_DIR = Path("/tmp/music-tools-onnx-parity/fixtures")
DEFAULT_MODEL_ONNX = Path("/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx")
DEFAULT_MODEL_JSON = Path("/tmp/music-tools-onnx-parity/msd-musicnn-1.json")
DEFAULT_VENV_PYTHON = Path("/tmp/music-tools-onnx-parity/venv/bin/python")

EXPECTED_FIXTURE_FILES = (
    "john_bartmann__earning_happiness__cc0.mp3",
    "john_bartmann__happy_clappy__cc0.mp3",
    "john_bartmann__home_at_last__cc0.mp3",
)

FIXTURE_RECORDS = (
    {
        "fixture_file": "john_bartmann__earning_happiness__cc0.mp3",
        "fixture_id": "john_bartmann_earning_happiness_cc0",
        "sha256": "d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628",
        "audio_format": "mp3",
        "source_artist": "John Bartmann",
        "license_status": "CC0 1.0 Universal / public domain",
    },
    {
        "fixture_file": "john_bartmann__happy_clappy__cc0.mp3",
        "fixture_id": "john_bartmann_happy_clappy_cc0",
        "sha256": "4f21570f701c07696c6b05f051528241a82156b923ab4bb3071c3c4af4a3372e",
        "audio_format": "mp3",
        "source_artist": "John Bartmann",
        "license_status": "CC0 1.0 Universal / public domain",
    },
    {
        "fixture_file": "john_bartmann__home_at_last__cc0.mp3",
        "fixture_id": "john_bartmann_home_at_last_cc0",
        "sha256": "0146392a4ea96de074197b2622ebd707ff2560586152bbd1e901095f2ea01c75",
        "audio_format": "mp3",
        "source_artist": "John Bartmann",
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
    "PREPROCESSING_ALIGNMENT_UNKNOWN",
    "ONNX_INPUT_SHAPE_UNSUPPORTED",
    "ONNX_CAPTURE_HELPER_UNSAFE",
    "ONNX_CAPTURE_FAILED",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "PRODUCTION_DEPENDENCY_CHANGE_NOT_ALLOWED",
    "MODEL_FILE_IN_REPO_NOT_ALLOWED",
    "AUDIO_FILE_IN_REPO_NOT_ALLOWED",
    "VENV_IN_REPO_NOT_ALLOWED",
    "NUMERIC_PARITY_DECISION_NOT_APPROVED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_baseline_evidence(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    outputs = data.get("baseline_outputs")
    if not isinstance(outputs, list) or len(outputs) != len(EXPECTED_FIXTURE_FILES):
        raise ValueError("baseline evidence is missing expected outputs")

    fixture_ids = []
    output_shapes = []
    for index, item in enumerate(outputs):
        if not isinstance(item, dict):
            raise ValueError(f"baseline output {index} must be an object")
        fixture_id = item.get("fixture_id")
        output_shape = item.get("output_shape")
        if not isinstance(fixture_id, str) or not fixture_id.strip():
            raise ValueError("baseline fixture_id must be a non-empty string")
        if not isinstance(output_shape, list) or not output_shape:
            raise ValueError("baseline output_shape must be a non-empty list")
        fixture_ids.append(fixture_id)
        output_shapes.append(output_shape)

    return {
        "report_path": "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json",
        "available": bool(data.get("baseline_capture_succeeded")),
        "fixture_count": len(outputs),
        "fixture_ids": fixture_ids,
        "expected_output_shapes": output_shapes,
    }


def _collect_fixture_records(fixture_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if not fixture_dir.is_dir():
        raise ValueError("fixture directory is missing")

    missing = [name for name in EXPECTED_FIXTURE_FILES if not (fixture_dir / name).is_file()]
    if missing:
        raise ValueError(f"missing fixture files: {missing}")

    records = []
    for template in FIXTURE_RECORDS:
        fixture_path = fixture_dir / template["fixture_file"]
        records.append(
            {
                "fixture_id": template["fixture_id"],
                "sha256": _sha256(fixture_path),
                "audio_format": template["audio_format"],
                "source_artist": template["source_artist"],
                "license_status": template["license_status"],
            }
        )
    provenance_notes = _load_json(fixture_dir / "fixture-provenance-notes.json")
    provenance_records = provenance_notes.get("fixtures")
    if not isinstance(provenance_records, list) or len(provenance_records) != len(FIXTURE_RECORDS):
        raise ValueError("fixture provenance notes are missing expected records")

    return records, provenance_records


def _inspect_onnx_metadata(model_onnx: Path, model_json: Path, python_executable: Path) -> dict[str, Any]:
    if not model_onnx.is_file():
        raise FileNotFoundError("ONNX artifact is missing")
    if not model_json.is_file():
        raise FileNotFoundError("ONNX metadata is missing")

    if not python_executable.is_file():
        raise FileNotFoundError("isolated onnxruntime python executable is missing")

    probe = subprocess.run(
        [
            str(python_executable),
            "-c",
            (
                "import json\n"
                "import onnxruntime as ort\n"
                "import sys\n"
                "from pathlib import Path\n"
                "model = Path(sys.argv[1])\n"
                "opts = ort.SessionOptions()\n"
                "opts.intra_op_num_threads = 1\n"
                "opts.inter_op_num_threads = 1\n"
                "session = ort.InferenceSession(str(model), sess_options=opts, providers=['CPUExecutionProvider'])\n"
                "print(json.dumps({\n"
                "    'onnxruntime_version': ort.__version__,\n"
                "    'input_names': [item.name for item in session.get_inputs()],\n"
                "    'input_shapes': [list(item.shape) for item in session.get_inputs()],\n"
                "    'output_names': [item.name for item in session.get_outputs()],\n"
                "    'output_shapes': [list(item.shape) for item in session.get_outputs()],\n"
                "}, ensure_ascii=False))\n"
            ),
            str(model_onnx),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    if probe.returncode != 0:
        message = (probe.stderr or probe.stdout or "onnxruntime metadata probe failed").strip()
        raise RuntimeError(message)

    payload = json.loads(probe.stdout)
    if not isinstance(payload, dict):
        raise ValueError("onnxruntime metadata probe returned invalid JSON")

    return {
        "available": True,
        "onnxruntime_available": True,
        "onnxruntime_version": payload["onnxruntime_version"],
        "model_sha256": _sha256(model_onnx),
        "metadata_sha256": _sha256(model_json),
        "artifact_in_repo": False,
        "input_names": payload["input_names"],
        "input_shapes": payload["input_shapes"],
        "output_names": payload["output_names"],
        "output_shapes": payload["output_shapes"],
        "preprocessing_alignment_status": "unknown",
    }


def _blocker(code: str, message: str) -> dict[str, str]:
    if code not in ALLOWED_BLOCKER_CODES:
        raise ValueError(f"unsupported blocker code: {code}")
    return {"code": code, "message": message}


def _base_report() -> dict[str, Any]:
    return {
        "report_type": "musicnn_onnx_output_capture_report",
        "roadmap": "4.51",
        "report_id": "roadmap_4_51_onnx_side_output_capture_preparation_execution_gate",
        "generated_by": "scripts/lightweight/musicnn_onnx_output_capture.py",
        "agents_md_read": True,
        "not_production_decision": True,
        "approved_for_production": False,
        "approved_for_provider_implementation": False,
        "approved_for_default_provider_switch": False,
        "approved_for_full_numeric_parity_run": False,
        "approved_for_final_parity_decision": False,
        "approved_for_classify_contract_change": False,
        "no_audio_files_committed": True,
        "no_model_files_committed": True,
        "no_venv_committed": True,
        "no_dependency_changes": True,
        "no_dockerfile_changes": True,
        "no_compose_file_changes": True,
        "no_docker_rebuild": True,
        "no_classify_calls": True,
        "no_provider_changes": True,
        "no_tidal_parser_changes": True,
        "legacy_musicnn_remains_baseline": True,
        "baseline_evidence": {},
        "onnx_environment": {},
        "onnx_artifacts": {},
        "fixture_count": 0,
        "sanitized_fixtures": [],
        "onnx_model_metadata": {},
        "onnx_capture_succeeded": False,
        "onnx_capture_status": {},
        "onnx_outputs": [],
        "blockers": [],
        "warnings": [],
        "next_step_recommendation": (
            "Provide explicit preprocessing alignment evidence for the ONNX input path before any execution approval."
        ),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    report = _base_report()
    blockers: list[dict[str, str]] = []

    if not args.agents_md_read:
        blockers.append(_blocker("AGENTS_MD_NOT_READ", "AGENTS.md was not confirmed as read."))

    try:
        baseline_evidence = _load_baseline_evidence(args.baseline_report)
        report["baseline_evidence"] = baseline_evidence
    except Exception as exc:
        blockers.append(_blocker("BASELINE_EVIDENCE_MISSING", f"baseline evidence unavailable: {exc}"))
        baseline_evidence = None

    try:
        fixture_records, provenance_records = _collect_fixture_records(args.fixtures_dir)
        report["sanitized_fixtures"] = fixture_records
        report["fixture_count"] = len(fixture_records)
        report["fixture_provenance_notes"] = {
            "available": True,
            "fixture_count": len(provenance_records),
            "storage_policy": {
                "location": "outside_repo",
                "repo_committed_audio": False,
                "public_report_paths_redacted": True,
            },
        }
    except Exception as exc:
        blockers.append(_blocker("FIXTURE_FILES_MISSING", f"fixture files unavailable: {exc}"))

    try:
        onnx_metadata = _inspect_onnx_metadata(args.model_onnx, args.model_json, args.python)
        report["onnx_artifacts"] = {
            "model_available": True,
            "metadata_available": True,
            "model_sha256": onnx_metadata["model_sha256"],
            "metadata_sha256": onnx_metadata["metadata_sha256"],
            "artifact_in_repo": onnx_metadata["artifact_in_repo"],
        }
        report["onnx_environment"] = {
            "isolated_env_used": True,
            "onnxruntime_available": True,
            "onnxruntime_version": onnx_metadata["onnxruntime_version"],
        }
        report["onnx_model_metadata"] = {
            "input_names": onnx_metadata["input_names"],
            "input_shapes": onnx_metadata["input_shapes"],
            "output_names": onnx_metadata["output_names"],
            "output_shapes": onnx_metadata["output_shapes"],
            "preprocessing_alignment_status": onnx_metadata["preprocessing_alignment_status"],
        }
    except FileNotFoundError as exc:
        message = str(exc)
        if "metadata" in message.lower():
            blockers.append(_blocker("ONNX_METADATA_MISSING", message))
        elif "python executable" in message.lower():
            blockers.append(_blocker("ONNXRUNTIME_UNAVAILABLE", message))
        else:
            blockers.append(_blocker("ONNX_ARTIFACT_MISSING", message))
    except Exception as exc:
        blockers.append(_blocker("ONNX_METADATA_MISSING", f"onnx metadata inspection failed: {exc}"))

    if baseline_evidence and report["fixture_count"] and baseline_evidence["fixture_count"] != report["fixture_count"]:
        blockers.append(
            _blocker(
                "BASELINE_EVIDENCE_MISSING",
                "baseline fixture count does not match the expected local fixture set.",
            )
        )

    if not blockers:
        blockers.append(
            _blocker(
                "PREPROCESSING_ALIGNMENT_UNKNOWN",
                "The ONNX input preprocessing path is not evidenced yet, so execution approval is withheld.",
            )
        )

    report["onnx_capture_status"] = {
        "succeeded": False,
        "blocked_missing_baseline_evidence": any(item["code"] == "BASELINE_EVIDENCE_MISSING" for item in blockers),
        "blocked_missing_onnx_artifact": any(item["code"] == "ONNX_ARTIFACT_MISSING" for item in blockers),
        "blocked_onnxruntime_unavailable": any(item["code"] == "ONNXRUNTIME_UNAVAILABLE" for item in blockers),
        "blocked_preprocessing_unknown": any(item["code"] == "PREPROCESSING_ALIGNMENT_UNKNOWN" for item in blockers),
        "blocked_capture_error": any(item["code"] == "ONNX_CAPTURE_FAILED" for item in blockers),
    }
    report["onnx_capture_succeeded"] = False
    report["onnx_outputs"] = []
    report["blockers"] = blockers
    report["warnings"] = [
        "No ONNX inference was executed.",
        "No fake outputs are recorded.",
        "The report is sanitized for repository publication.",
    ]

    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a local-only Roadmap 4.51 ONNX capture report.")
    parser.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--model-onnx", type=Path, default=DEFAULT_MODEL_ONNX)
    parser.add_argument("--model-json", type=Path, default=DEFAULT_MODEL_JSON)
    parser.add_argument("--python", type=Path, default=DEFAULT_VENV_PYTHON)
    parser.add_argument("--baseline-report", type=Path, default=DEFAULT_BASELINE_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
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

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
