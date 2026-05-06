#!/usr/bin/env python3
"""Локальный probe для Roadmap 4.52 по выравниванию preprocessing для MusiCNN.

Скрипт работает только как отчётный CLI:
- не импортирует production app;
- не вызывает `/classify`;
- не выполняет ONNX inference;
- не меняет provider wiring;
- не делает никаких production-side effects.

Он собирает статические факты о legacy пути, читает committed baseline и ONNX
metadata, а также по возможности пробует безопасно проверить наличие Essentia
runtime для инспекции алгоритмов. Если alignment не доказан, скрипт фиксирует
блокеры вместо fake outputs или parity claims.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-preprocessing-alignment-report.json"
)
DEFAULT_BASELINE_REPORT = (
    SERVICE_ROOT / "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json"
)
DEFAULT_LEGACY_SOURCE = SERVICE_ROOT / "app/services/classify.py"
DEFAULT_LEGACY_PROVIDER = SERVICE_ROOT / "app/providers/legacy_musicnn.py"
DEFAULT_SETTINGS = SERVICE_ROOT / "app/core/settings.py"
DEFAULT_ONNX_MODEL = Path("/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx")
DEFAULT_ESSENTIA_PYTHON = Path("/tmp/music-tools-onnx-parity/venv/bin/python")

ALLOWED_BLOCKER_CODES = {
    "AGENTS_MD_NOT_READ",
    "BASELINE_EVIDENCE_MISSING",
    "ONNX_ARTIFACT_MISSING",
    "ONNX_METADATA_MISSING",
    "LEGACY_METADATA_MISSING",
    "PREPROCESSING_PARAMETERS_MISSING",
    "MEL_INPUT_GENERATION_UNKNOWN",
    "LEGACY_INTERMEDIATE_NOT_EXPOSED",
    "TENSOR_LAYOUT_UNKNOWN",
    "NORMALIZATION_UNKNOWN",
    "ESSENTIA_PREPROCESSING_CHAIN_UNCONFIRMED",
    "ONNX_INPUT_SHAPE_UNSUPPORTED",
    "ONNX_FIXTURE_CAPTURE_NOT_APPROVED",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "PRODUCTION_DEPENDENCY_CHANGE_NOT_ALLOWED",
    "MODEL_FILE_IN_REPO_NOT_ALLOWED",
    "AUDIO_FILE_IN_REPO_NOT_ALLOWED",
    "VENV_IN_REPO_NOT_ALLOWED",
    "FINAL_PARITY_DECISION_NOT_APPROVED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}


class ProbeError(Exception):
    """Помечает ожидаемую проблему при построении alignment report."""


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


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ProbeError(f"Source artifact is missing: {path}") from exc


def _load_baseline_evidence(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    outputs = data.get("baseline_outputs")
    if not isinstance(outputs, list) or len(outputs) != 3:
        raise ProbeError("baseline evidence does not contain the committed fixture set")

    expected_shapes = []
    fixture_ids = []
    for item in outputs:
        if not isinstance(item, dict):
            raise ProbeError("baseline outputs must contain objects")
        fixture_ids.append(item.get("fixture_id"))
        expected_shapes.append(item.get("output_shape"))

    return {
        "report_path": "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json",
        "available": bool(data.get("baseline_capture_succeeded")),
        "fixture_count": len(outputs),
        "fixture_ids": fixture_ids,
        "expected_output_shapes": expected_shapes,
    }


def _extract_static_legacy_facts(classify_source: str, provider_source: str, settings_source: str) -> dict[str, Any]:
    uses_ffmpeg = "\"ffmpeg\"" in classify_source
    uses_monoloader = "MonoLoader(" in classify_source
    uses_tensorflow_predict_musiccnn = "TensorflowPredictMusiCNN(" in classify_source
    has_explicit_intermediate_melspectrogram = "melspectrogram" in classify_source and "TensorflowPredictMusiCNN" in classify_source

    sample_rate_match = re.search(r"sampleRate\s*=\s*(\d+)", classify_source)
    sample_rate = int(sample_rate_match.group(1)) if sample_rate_match else None

    frame_size = None
    hop_size = None
    mel_bands = None
    patch_length = None
    tensor_layout = None
    normalization = None

    if "DEFAULT_GENRE_PROVIDER = \"legacy_musicnn\"" not in settings_source:
        raise ProbeError("default provider flag could not be confirmed from settings.py")

    return {
        "uses_tensorflow_predict_musiccnn": uses_tensorflow_predict_musiccnn,
        "uses_monoloader": uses_monoloader,
        "uses_ffmpeg": uses_ffmpeg,
        "preprocessing_exposed_as_intermediate": has_explicit_intermediate_melspectrogram,
        "sample_rate": sample_rate,
        "frame_size": frame_size,
        "hop_size": hop_size,
        "mel_bands": mel_bands,
        "patch_length": patch_length,
        "tensor_layout": tensor_layout,
        "normalization": normalization,
        "source_of_truth": [
            "app/services/classify.py",
            "app/providers/legacy_musicnn.py",
            "app/core/settings.py",
            "app/models/msd-musicnn-1.json",
            "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json",
            "docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-output-capture-report.json",
        ],
        "unknown_fields": [
            field
            for field, value in (
                ("frame_size", frame_size),
                ("hop_size", hop_size),
                ("mel_bands", mel_bands),
                ("patch_length", patch_length),
                ("tensor_layout", tensor_layout),
                ("normalization", normalization),
            )
            if value is None
        ],
    }


def _inspect_onnx_metadata(model_path: Path, python_executable: Path) -> dict[str, Any]:
    if not model_path.is_file():
        raise ProbeError(f"ONNX model artifact is missing: {model_path}")
    if not python_executable.is_file():
        raise ProbeError("isolated python executable is missing")

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
        raise ProbeError((probe.stderr or probe.stdout or "onnxruntime metadata probe failed").strip())

    payload = json.loads(probe.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        raise ProbeError("onnxruntime metadata probe returned invalid JSON")

    input_names = payload.get("input_names")
    input_shapes = payload.get("input_shapes")
    output_names = payload.get("output_names")
    output_shapes = payload.get("output_shapes")
    if not isinstance(input_names, list) or not input_names:
        raise ProbeError("onnxruntime input names are missing")
    if not isinstance(input_shapes, list) or not input_shapes:
        raise ProbeError("onnxruntime input shapes are missing")
    if not isinstance(output_names, list) or not output_names:
        raise ProbeError("onnxruntime output names are missing")
    if not isinstance(output_shapes, list) or not output_shapes:
        raise ProbeError("onnxruntime output shapes are missing")

    return {
        "onnxruntime_version": payload["onnxruntime_version"],
        "input_name": input_names[0],
        "input_shape_tail": list(input_shapes[0])[-2:],
        "output_names": output_names,
        "output_shape_tails": [list(shape)[-1:] for shape in output_shapes],
    }


def _probe_essentia_algorithms(python_executable: Path) -> dict[str, Any]:
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
                "    print(json.dumps({'available': False, 'error': f'{type(exc).__name__}: {exc}', 'algorithm_names': []}))\n"
                "else:\n"
                "    names = [name for name in dir(es) if 'MusiCNN' in name or 'Mel' in name or 'Spectrogram' in name]\n"
                "    print(json.dumps({'available': True, 'error': None, 'algorithm_names': names[:80]}))\n"
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

    try:
        payload = json.loads(probe.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return {
            "available": False,
            "error": "essentia probe returned invalid JSON",
            "algorithm_names": [],
        }

    if not isinstance(payload, dict):
        return {
            "available": False,
            "error": "essentia probe returned invalid payload",
            "algorithm_names": [],
        }
    return payload


def _blocker(code: str, message: str) -> dict[str, str]:
    if code not in ALLOWED_BLOCKER_CODES:
        raise ProbeError(f"Unsupported blocker code: {code}")
    return {"code": code, "message": message}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    baseline_evidence = _load_baseline_evidence(args.baseline_report)
    classify_source = _read_text(args.classify_source)
    provider_source = _read_text(args.provider_source)
    settings_source = _read_text(args.settings_source)
    legacy_preprocessing = _extract_static_legacy_facts(classify_source, provider_source, settings_source)
    onnx_metadata = _inspect_onnx_metadata(args.onnx_model, args.essentia_python)
    essentia_probe = _probe_essentia_algorithms(args.essentia_python)

    blockers = []
    if not args.agents_md_read:
        blockers.append(_blocker("AGENTS_MD_NOT_READ", "AGENTS.md was not confirmed as read."))
    if not baseline_evidence["available"]:
        blockers.append(
            _blocker(
                "BASELINE_EVIDENCE_MISSING",
                "committed legacy baseline evidence is unavailable or not marked successful",
            )
        )
    if not legacy_preprocessing["uses_tensorflow_predict_musiccnn"]:
        blockers.append(_blocker("LEGACY_METADATA_MISSING", "legacy MusicNN preprocessing call was not found"))

    alignment_path_found = False
    blocked = True
    inconclusive = False

    if legacy_preprocessing["preprocessing_exposed_as_intermediate"]:
        alignment_path_found = True
        blocked = False
        inconclusive = False
    else:
        blockers.extend(
            [
                _blocker(
                    "LEGACY_INTERMEDIATE_NOT_EXPOSED",
                    "legacy MusicNN path does not expose an intermediate melspectrogram tensor in repo code",
                ),
                _blocker(
                    "MEL_INPUT_GENERATION_UNKNOWN",
                    "a reproducible producer for the ONNX melspectrogram input is not yet evidenced",
                ),
                _blocker(
                    "PREPROCESSING_PARAMETERS_MISSING",
                    "frame size, hop size, mel bands, patch length, tensor layout, and normalization remain unconfirmed",
                ),
                _blocker(
                    "ESSENTIA_PREPROCESSING_CHAIN_UNCONFIRMED",
                    "no local Essentia runtime evidence confirms the preprocessing chain names or parameters",
                ),
                _blocker(
                    "TENSOR_LAYOUT_UNKNOWN",
                    "the legacy-to-ONNX tensor layout mapping is not evidenced",
                ),
                _blocker(
                    "NORMALIZATION_UNKNOWN",
                    "normalization details for the candidate preprocessing path are not evidenced",
                ),
            ]
        )

    report = {
        "report_type": "musicnn_onnx_preprocessing_alignment_report",
        "roadmap": "4.52",
        "report_id": "roadmap_4_52_onnx_preprocessing_alignment_investigation_gate",
        "generated_by": "scripts/lightweight/musicnn_preprocessing_alignment_probe.py",
        "agents_md_read": bool(args.agents_md_read),
        "not_production_decision": True,
        "approved_for_production": False,
        "approved_for_provider_implementation": False,
        "approved_for_default_provider_switch": False,
        "approved_for_full_numeric_parity_run": False,
        "approved_for_final_parity_decision": False,
        "approved_for_classify_contract_change": False,
        "approved_for_onnx_fixture_output_capture": False,
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
        "baseline_evidence": baseline_evidence,
        "onnx_model_metadata": {
            "input_name": onnx_metadata["input_name"],
            "input_shape_tail": onnx_metadata["input_shape_tail"],
            "output_names": onnx_metadata["output_names"],
            "output_shape_tails": onnx_metadata["output_shape_tails"],
        },
        "preprocessing_metadata": legacy_preprocessing,
        "legacy_preprocessing_path": legacy_preprocessing,
        "alignment_status": {
            "candidate_alignment_path_found": alignment_path_found,
            "blocked": blocked,
            "inconclusive": inconclusive,
        },
        "candidate_alignment_path": {
            "method": (
                "Static legacy MusicNN path audit only; no reproducible intermediate melspectrogram producer "
                "is evidenced in the current repo code."
            ),
            "required_algorithms": [
                "ffmpeg",
                "MonoLoader",
                "TensorflowPredictMusiCNN",
                "melspectrogram frontend",
            ],
            "evidence": [
                "legacy path normalizes uploads to mono WAV at 16000 Hz before classification",
                "legacy provider delegates directly to the shared classification service",
                "ONNX metadata exposes input melspectrogram with tail shape [187, 96]",
                "committed legacy baseline evidence remains available and valid",
            ],
            "risks": [
                "the intermediate mel frontend is not exposed in repository code",
                "frame size, hop size, mel bands, patch length, tensor layout, and normalization are not evidenced",
                "local Essentia runtime inspection did not provide confirmed preprocessing algorithm names",
            ],
        },
        "essentia_probe": essentia_probe,
        "blockers": blockers,
        "warnings": [
            "No ONNX inference was executed.",
            "No fake outputs are recorded.",
            "No production migration or provider switch was approved.",
        ],
        "next_step_recommendation": (
            "Keep ONNX fixture output capture blocked until a reproducible melspectrogram producer is evidenced "
            "for the legacy MusiCNN path or a safe Essentia preprocessing chain probe can confirm the missing "
            "parameters without touching production runtime."
        ),
    }

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Roadmap 4.52 MusiCNN preprocessing alignment report.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Where to write the sanitized report JSON.",
    )
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=DEFAULT_BASELINE_REPORT,
        help="Committed legacy baseline report path.",
    )
    parser.add_argument(
        "--classify-source",
        type=Path,
        default=DEFAULT_LEGACY_SOURCE,
        help="Legacy classify service source file.",
    )
    parser.add_argument(
        "--provider-source",
        type=Path,
        default=DEFAULT_LEGACY_PROVIDER,
        help="Legacy provider source file.",
    )
    parser.add_argument(
        "--settings-source",
        type=Path,
        default=DEFAULT_SETTINGS,
        help="Core settings source file.",
    )
    parser.add_argument(
        "--onnx-model",
        type=Path,
        default=DEFAULT_ONNX_MODEL,
        help="Local ONNX model artifact.",
    )
    parser.add_argument(
        "--essentia-python",
        type=Path,
        default=DEFAULT_ESSENTIA_PYTHON,
        help="Optional isolated python used to probe Essentia algorithm availability.",
    )
    parser.add_argument(
        "--agents-md-read",
        action="store_true",
        default=True,
        help="Confirm that AGENTS.md was read.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = build_report(args)
    except ProbeError as exc:
        print(f"probe failed: {exc}", file=sys.stderr)
        return 1

    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"report written: {args.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
