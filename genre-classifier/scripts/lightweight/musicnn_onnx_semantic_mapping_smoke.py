#!/usr/bin/env python3
"""Roadmap 4.66 local-only ONNX/MusiCNN semantic mapping smoke helper.

Скрипт остаётся вне production runtime и не:

- вызывает `/classify`;
- меняет provider wiring или default provider;
- меняет production dependencies;
- запускает Docker Compose;
- сравнивает TensorFlow baseline с ONNX;
- заявляет strict parity или production readiness.

Он использует уже подтверждённое Roadmap 4.65 local-only ONNX evidence,
локальный ONNX артефакт и metadata/classes из текущего MusiCNN JSON, чтобы
показать, как activations `[50]` сопоставляются с controlled vocabulary.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

DEFAULT_REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-semantic-mapping-smoke-report.json"
)
DEFAULT_ROADMAP_4_65_REPORT = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-output-capture-report.json"
)
DEFAULT_FIXTURE_PATH = Path("/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3")
DEFAULT_ONNX_MODEL_PATH = Path("/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx")
DEFAULT_METADATA_PATH = Path("/tmp/music-tools-onnx-parity/msd-musicnn-1.json")
DEFAULT_ISOLATED_PYTHON = Path("/tmp/music-tools-onnx-parity/venv/bin/python")

EXPECTED_PATCH_SHAPE = [187, 96]
EXPECTED_ACTIVATIONS_SHAPE = [50]
EXPECTED_EMBEDDINGS_SHAPE = [200]
DEFAULT_TOP_N = 10

NON_GENRE_DESCRIPTOR_HINTS = {
    "beautiful",
    "catchy",
    "chill",
    "female vocalist",
    "female vocalists",
    "happy",
    "male vocalist",
    "male vocalists",
    "mellow",
    "party",
    "sad",
    "sexy",
}

ERA_PATTERN = re.compile(r"^\d{2}s$")


class SmokeError(Exception):
    """Ожидаемая ошибка для local-only smoke helper."""


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def _load_capture_helper():
    helper_path = SERVICE_ROOT / "scripts/lightweight/musicnn_onnx_output_capture.py"
    spec = importlib.util.spec_from_file_location("musicnn_onnx_output_capture", helper_path)
    if spec is None or spec.loader is None:
        raise SmokeError("Unable to load output capture helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_roadmap_4_65_report(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    if data.get("roadmap") != "4.65":
        raise SmokeError(f"Unexpected roadmap value in 4.65 evidence: {data.get('roadmap')}")
    if data.get("status") != "completed":
        raise SmokeError("Roadmap 4.65 evidence is not marked as completed")

    activations = data.get("outputs", {}).get("activations", {})
    embeddings = data.get("outputs", {}).get("embeddings", {})
    preprocessing = data.get("preprocessing", {})
    repeated = data.get("repeated_run_stability", {})

    if activations.get("normalized_shape") != EXPECTED_ACTIVATIONS_SHAPE:
        raise SmokeError(f"Unexpected activations shape in 4.65 evidence: {activations.get('normalized_shape')}")
    if embeddings.get("normalized_shape") != EXPECTED_EMBEDDINGS_SHAPE:
        raise SmokeError(f"Unexpected embeddings shape in 4.65 evidence: {embeddings.get('normalized_shape')}")
    if preprocessing.get("final_patch_shape") != EXPECTED_PATCH_SHAPE:
        raise SmokeError(f"Unexpected preprocessing patch shape in 4.65 evidence: {preprocessing.get('final_patch_shape')}")
    if repeated.get("stable") is not True or repeated.get("max_abs_diff") != 0.0 or repeated.get("mean_abs_diff") != 0.0:
        raise SmokeError("Roadmap 4.65 evidence does not confirm repeated-run stability")

    return {
        "roadmap": "4.65",
        "report_path": "docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-output-capture-report.json",
        "patch_shape": preprocessing.get("final_patch_shape"),
        "activations_shape": activations.get("normalized_shape"),
        "embeddings_shape": embeddings.get("normalized_shape"),
        "top_activation_indices": activations.get("top_activation_indices", []),
        "top_activation_scores": activations.get("top_activation_scores", []),
        "stable": True,
    }


def _load_metadata(path: Path) -> list[str]:
    data = _load_json(path)
    classes = data.get("classes")
    if not isinstance(classes, list) or not classes:
        raise SmokeError("metadata/classes list is missing")

    normalized_classes: list[str] = []
    for index, item in enumerate(classes):
        if not isinstance(item, str) or not item.strip():
            raise SmokeError(f"metadata/classes[{index}] is not a non-empty string")
        normalized_classes.append(item)

    if len(normalized_classes) != EXPECTED_ACTIVATIONS_SHAPE[0]:
        raise SmokeError(
            f"metadata/classes count {len(normalized_classes)} does not match activations {EXPECTED_ACTIVATIONS_SHAPE[0]}"
        )

    return normalized_classes


def _collect_fixture_info(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SmokeError(f"Fixture is missing: {path}")

    return {
        "path": str(path),
        "sha256": _sha256(path),
        "committed_to_repo": False,
    }


def _probe_onnxruntime(python_executable: Path) -> dict[str, Any]:
    if not python_executable.is_file():
        return {
            "available": False,
            "version": None,
            "providers": [],
            "error_category": "FileNotFoundError",
            "error_message": "isolated python executable is missing",
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
                "        'providers': [],"
                "        'error_category': type(exc).__name__,"
                "        'error_message': str(exc)"
                "    }, ensure_ascii=False))\n"
                "else:\n"
                "    print(json.dumps({"
                "        'available': True,"
                "        'version': ort.__version__,"
                "        'providers': ort.get_available_providers(),"
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
            "providers": [],
            "error_category": "SubprocessError",
            "error_message": (probe.stderr or probe.stdout or "onnxruntime probe failed").strip(),
        }

    payload = json.loads(probe.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        raise SmokeError("onnxruntime probe returned invalid JSON")
    return payload


def _generate_patch(capture_helper, fixture_path: Path) -> dict[str, Any]:
    return capture_helper._generate_tensorflow_input_patch(fixture_path)


def _run_onnx_inference(model_path: Path, patch: Any) -> dict[str, Any]:
    try:
        import numpy as np
        import onnxruntime as ort
    except Exception as exc:  # pragma: no cover - local runtime dependent
        raise SmokeError(_safe_error(exc)) from exc

    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(model_path), sess_options=options, providers=["CPUExecutionProvider"])

    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if not inputs:
        raise SmokeError("onnxruntime session has no inputs")

    input_meta = inputs[0]
    input_shape = list(input_meta.shape)
    feed_array = patch
    if len(input_shape) == 3 and input_shape[-2:] == EXPECTED_PATCH_SHAPE:
        feed_array = np.expand_dims(patch, axis=0)
    elif len(input_shape) != 2 or input_shape != EXPECTED_PATCH_SHAPE:
        raise SmokeError(f"unexpected ONNX input shape: {input_shape}")

    run_1_raw = session.run(None, {input_meta.name: feed_array})
    output_names = [item.name for item in outputs]
    output_map = {name: value for name, value in zip(output_names, run_1_raw)}

    activations = output_map.get("activations")
    embeddings = output_map.get("embeddings")
    if activations is None or embeddings is None:
        raise SmokeError(f"expected ONNX outputs not found: {output_names}")

    activations_array = np.asarray(activations).reshape(-1)
    embeddings_array = np.asarray(embeddings).reshape(-1)

    return {
        "input_metadata": {
            "name": input_meta.name,
            "shape": input_shape,
            "type": input_meta.type,
        },
        "output_metadata": [
            {"name": item.name, "shape": list(item.shape), "type": item.type}
            for item in outputs
        ],
        "activations": activations_array.tolist(),
        "embeddings_shape": list(embeddings_array.shape),
        "activations_shape": list(activations_array.shape),
        "embeddings": embeddings_array.tolist(),
    }


def _normalize_label(label: str) -> str | None:
    text = label.strip().lower().replace("-", " ").replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text or None


def _classify_mapping(label: str, normalize_genre_label) -> dict[str, Any]:
    normalized = _normalize_label(label)
    mapped_genre = normalize_genre_label(label)
    if mapped_genre:
        return {
            "mapping_status": "mapped",
            "mapped_genre": mapped_genre,
            "pretty": mapped_genre,
            "reason": "Входит в текущий controlled vocabulary.",
        }

    descriptor_like = (
        normalized in NON_GENRE_DESCRIPTOR_HINTS
        or bool(normalized and ERA_PATTERN.match(normalized))
        or bool(normalized and "vocalist" in normalized)
    )
    if descriptor_like:
        return {
            "mapping_status": "non_genre_descriptor",
            "mapped_genre": None,
            "pretty": None,
            "reason": "Не жанр: descriptor/mood/era term вне controlled vocabulary.",
        }

    return {
        "mapping_status": "unmapped",
        "mapped_genre": None,
        "pretty": None,
        "reason": "Не сопоставляется с текущим controlled vocabulary.",
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    capture_helper = _load_capture_helper()
    roadmap_4_65 = _validate_roadmap_4_65_report(args.baseline_report)
    classes = _load_metadata(args.metadata_path)
    fixture = _collect_fixture_info(args.fixture_path)
    runtime_probe = _probe_onnxruntime(args.isolated_python)

    report: dict[str, Any] = {
        "schema_version": "0.1",
        "report_type": "onnx_musicnn_semantic_mapping_smoke_report",
        "report_id": "roadmap_4_66_onnx_musiccnn_activation_to_genre_semantic_mapping_smoke",
        "generated_by": "scripts/lightweight/musicnn_onnx_semantic_mapping_smoke.py",
        "title": "Roadmap 4.66 - ONNX/MusiCNN activation-to-genre semantic mapping smoke",
        "roadmap": "4.66",
        "status": "blocked",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "isolated_local_onnx_semantic_mapping_smoke",
        "scope_confirmations": {
            "service": "genre-classifier",
            "local_only": True,
            "classify_called": False,
            "provider_implementation_changed": False,
            "default_provider_changed": False,
            "production_dependencies_changed": False,
            "docker_changed": False,
            "tidal_parser_touched": False,
            "response_shape_change_required": False,
            "classify_contract_change_required": False,
        },
        "agents_md_read": True,
        "inputs": {
            "source": "Roadmap 4.65 local-only ONNX evidence + local metadata/classes + /tmp music-tools-onnx-parity fixture/model artifacts",
            "patch_shape": roadmap_4_65["patch_shape"],
            "activations_shape": roadmap_4_65["activations_shape"],
            "embeddings_shape": roadmap_4_65["embeddings_shape"],
        },
        "metadata": {
            "classes_found": classes,
            "classes_count": len(classes),
            "classes_count_matches_activations": len(classes) == EXPECTED_ACTIVATIONS_SHAPE[0],
            "metadata_source_sanitized": {
                "path": str(args.metadata_path),
                "sha256": _sha256(args.metadata_path),
                "local_only": True,
            },
            "index_order_usable": True,
        },
        "top_n": [],
        "mapping_summary": {
            "top_n": args.top_n,
            "mapped_count": 0,
            "unmapped_count": 0,
            "non_genre_descriptor_count": 0,
            "leakage_controlled": True,
        },
        "candidate_output_shape": {"genres": [], "genres_pretty": []},
        "compatibility": {
            "response_shape_change_required": False,
            "classify_contract_change_required": False,
            "legacy_parity_claimed": False,
            "production_readiness_claimed": False,
        },
        "blockers": [],
        "non_goals_confirmed": [
            "not /classify integration",
            "not provider implementation",
            "default provider remains legacy_musicnn",
            "TensorFlow baseline not run",
            "TensorFlow vs ONNX comparison not run",
            "no production inference",
        ],
        "evidence": {
            "roadmap_4_65_report_path": roadmap_4_65["report_path"],
            "fixture": fixture,
            "onnxruntime": runtime_probe,
        },
    }

    if not runtime_probe.get("available"):
        report["status"] = "blocked"
        report["blockers"].append(
            {
                "code": "ONNXRUNTIME_NOT_AVAILABLE",
                "message": runtime_probe.get("error_message") or "onnxruntime is not available in the isolated environment",
            }
        )
        report["evidence"]["onnx_inference"] = None
        return report

    try:
        patch_info = _generate_patch(capture_helper, args.fixture_path)
        onnx_info = _run_onnx_inference(args.onnx_model_path, patch_info["patch"])
    except Exception as exc:
        report["status"] = "blocked"
        report["blockers"].append({"code": "SMOKE_CAPTURE_FAILED", "message": _safe_error(exc)})
        report["evidence"]["onnx_inference"] = None
        return report

    activations = onnx_info["activations"]
    mapped_top_items: list[dict[str, Any]] = []
    top_n_items: list[dict[str, Any]] = []

    from app.genre_normalization import normalize_audio_prediction_genres
    from app.genres.normalization import normalize_genre_label

    ranked = sorted(enumerate(activations), key=lambda pair: pair[1], reverse=True)
    limit = min(int(args.top_n), len(ranked))

    for rank, (index, score) in enumerate(ranked[:limit], start=1):
        label = classes[index]
        mapping = _classify_mapping(label, normalize_genre_label)
        item = {
            "rank": rank,
            "index": int(index),
            "label": label,
            "score": float(score),
            "mapping_status": mapping["mapping_status"],
            "mapped_genre": mapping["mapped_genre"],
            "pretty": mapping["pretty"],
            "reason": mapping["reason"],
        }
        top_n_items.append(item)
        if mapping["mapped_genre"]:
            mapped_top_items.append(
                {
                    "tag": mapping["mapped_genre"],
                    "prob": round(float(score), 4),
                }
            )

    candidate_genres = mapped_top_items[:8]
    candidate_genres_pretty = normalize_audio_prediction_genres(candidate_genres, min_prob=0.05)

    mapped_count = sum(1 for item in top_n_items if item["mapping_status"] == "mapped")
    descriptor_count = sum(1 for item in top_n_items if item["mapping_status"] == "non_genre_descriptor")
    unmapped_count = sum(1 for item in top_n_items if item["mapping_status"] != "mapped")

    report["status"] = "completed"
    report["inputs"]["patch_shape"] = roadmap_4_65["patch_shape"]
    report["evidence"]["onnx_inference"] = {
        "input_metadata": onnx_info["input_metadata"],
        "output_metadata": onnx_info["output_metadata"],
        "patch_shape": patch_info["final_patch_shape"],
        "activations_shape": EXPECTED_ACTIVATIONS_SHAPE,
        "embeddings_shape": EXPECTED_EMBEDDINGS_SHAPE,
        "repeated_run_stability": {
            "source": roadmap_4_65["report_path"],
            "stable": roadmap_4_65["stable"],
            "max_abs_diff": 0.0,
            "mean_abs_diff": 0.0,
        },
    }
    report["top_n"] = top_n_items
    report["mapping_summary"] = {
        "top_n": limit,
        "mapped_count": mapped_count,
        "unmapped_count": unmapped_count,
        "non_genre_descriptor_count": descriptor_count,
        "leakage_controlled": descriptor_count == 0 and unmapped_count == 0,
    }
    report["candidate_output_shape"] = {
        "genres": candidate_genres,
        "genres_pretty": candidate_genres_pretty,
    }

    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Roadmap 4.66 local-only semantic mapping smoke helper")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Path to write the JSON report")
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=DEFAULT_ROADMAP_4_65_REPORT,
        help="Path to the Roadmap 4.65 output capture report",
    )
    parser.add_argument("--fixture-path", type=Path, default=DEFAULT_FIXTURE_PATH, help="Local-only fixture path")
    parser.add_argument("--onnx-model-path", type=Path, default=DEFAULT_ONNX_MODEL_PATH, help="Local ONNX model path")
    parser.add_argument(
        "--metadata-path",
        type=Path,
        default=DEFAULT_METADATA_PATH,
        help="Local metadata/classes JSON path",
    )
    parser.add_argument(
        "--isolated-python",
        type=Path,
        default=DEFAULT_ISOLATED_PYTHON,
        help="Isolated Python executable used for onnxruntime probing",
    )
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="Number of activation labels to report")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        report = build_report(args)
    except Exception as exc:
        failure = {
            "roadmap": "4.66",
            "status": "blocked",
            "title": "Roadmap 4.66 - ONNX/MusiCNN activation-to-genre semantic mapping smoke",
            "blockers": [{"code": "SMOKE_CAPTURE_FAILED", "message": _safe_error(exc)}],
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
