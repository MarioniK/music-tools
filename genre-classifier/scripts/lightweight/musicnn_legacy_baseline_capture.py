#!/usr/bin/env python3
"""Capture legacy MusiCNN baseline outputs for local-only fixtures.

This helper is intentionally CLI-only and local-only. It does not import the
production app, provider factory, ONNX, or TensorFlow explicitly before
Essentia. It mirrors the legacy MusiCNN runtime path closely enough for scoped
baseline capture: normalize audio with ffmpeg, load 16 kHz mono audio through
Essentia, run TensorflowPredictMusiCNN, and write sanitized JSON.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


EXPECTED_FIXTURE_FILES = (
    "john_bartmann__earning_happiness__cc0.mp3",
    "john_bartmann__happy_clappy__cc0.mp3",
    "john_bartmann__home_at_last__cc0.mp3",
)

FIXTURE_IDS = {
    "john_bartmann__earning_happiness__cc0.mp3": "john_bartmann_earning_happiness_cc0",
    "john_bartmann__happy_clappy__cc0.mp3": "john_bartmann_happy_clappy_cc0",
    "john_bartmann__home_at_last__cc0.mp3": "john_bartmann_home_at_last_cc0",
}

NON_GENRE_DESCRIPTORS = {
    "female vocalists",
    "male vocalists",
}


def _normalize_genre_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower().replace("-", " ").replace("_", " ")
    text = " ".join(text.split())
    return text or None


def _normalize_genres(raw_genres: list[dict[str, Any]], min_prob: float = 0.05) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    tags = []

    for item in raw_genres:
        if float(item.get("prob", 0.0)) < min_prob:
            continue
        tag = _normalize_genre_value(item.get("tag"))
        if tag:
            tags.append(tag)

    tag_set = set(tags)

    def add(tag: str) -> None:
        normalized = _normalize_genre_value(tag)
        if normalized and normalized not in NON_GENRE_DESCRIPTORS and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    if "indie rock" in tag_set:
        add("indie rock")
    elif "indie" in tag_set and "rock" in tag_set:
        add("indie rock")

    if "experimental rock" in tag_set:
        add("experimental rock")
    elif "experimental" in tag_set and "rock" in tag_set:
        add("experimental rock")

    if "jazz rock" in tag_set:
        add("jazz rock")
    elif "jazz" in tag_set and "rock" in tag_set:
        add("jazz rock")
    elif "jazz" in tag_set and "instrumental" in tag_set and "experimental" in tag_set:
        add("avant jazz")

    if "alternative rock" in tag_set:
        add("alternative rock")
    elif "alternative" in tag_set and "rock" in tag_set:
        add("alternative rock")

    if "instrumental rock" in tag_set:
        add("instrumental rock")
    elif "instrumental" in tag_set and "rock" in tag_set:
        add("instrumental rock")

    if "electronic" in tag_set:
        add("electronic")

    for tag in tags:
        add(tag)

    return result[:8]


def _load_classes(model_json: Path) -> list[str]:
    with model_json.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    classes = metadata.get("classes")
    if not isinstance(classes, list) or not classes:
        raise RuntimeError("MODEL_METADATA_CLASSES_MISSING")
    return [str(item) for item in classes]


def _normalize_audio(input_path: Path, output_path: Path) -> None:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(output_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("FFMPEG_NORMALIZATION_FAILED")
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("FFMPEG_OUTPUT_MISSING")


def _capture_fixture(
    fixture_path: Path,
    fixture_id: str,
    model_pb: Path,
    classes: list[str],
    essentia_standard: Any,
    numpy_module: Any,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="musicnn-baseline-") as temp_dir:
        wav_path = Path(temp_dir) / "input.wav"
        _normalize_audio(fixture_path, wav_path)

        audio = essentia_standard.MonoLoader(
            filename=str(wav_path),
            sampleRate=16000,
        )()
        activations = essentia_standard.TensorflowPredictMusiCNN(
            graphFilename=str(model_pb),
        )(audio)

    mean_scores = numpy_module.mean(activations, axis=0)
    pairs = [
        {
            "tag": str(label).lower(),
            "prob": round(float(score), 4),
        }
        for label, score in zip(classes, mean_scores)
    ]
    pairs.sort(key=lambda item: item["prob"], reverse=True)
    top_pairs = pairs[:8]

    return {
        "fixture_id": fixture_id,
        "output_shape": list(getattr(activations, "shape", [])),
        "top_labels": [item["tag"] for item in top_pairs],
        "top_scores": [item["prob"] for item in top_pairs],
        "genres": top_pairs,
        "genres_pretty": _normalize_genres(top_pairs),
        "warnings": [],
    }


def capture_baseline(args: argparse.Namespace) -> dict[str, Any]:
    fixture_dir = Path(args.fixtures_dir)
    model_pb = Path(args.model_pb)
    model_json = Path(args.model_json)
    outputs: list[dict[str, Any]] = []
    blockers: list[dict[str, str]] = []

    if not fixture_dir.is_dir():
        return _blocked("FIXTURE_PATH_NOT_VISIBLE_IN_ONE_OFF_CONTAINER", "Fixture directory is not visible.")
    missing = [name for name in EXPECTED_FIXTURE_FILES if not (fixture_dir / name).is_file()]
    if missing:
        return _blocked("FIXTURE_BIND_MOUNT_FAILED", "Expected fixture MP3 files are not visible.")
    if not model_pb.is_file() or not model_json.is_file():
        return _blocked("BASELINE_CAPTURE_FAILED", "Legacy MusiCNN model files are not visible.")

    try:
        import essentia.standard as es
    except Exception as exc:  # pragma: no cover - exercised only in runtime container
        return _blocked("ESSENTIA_IMPORT_FAILED", _safe_error(exc))

    if not hasattr(es, "TensorflowPredictMusiCNN"):
        return _blocked("BASELINE_IMPORT_FAILED", "TensorflowPredictMusiCNN is unavailable through essentia.standard.")

    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - exercised only in runtime container
        return _blocked("BASELINE_CAPTURE_FAILED", _safe_error(exc))

    try:
        classes = _load_classes(model_json)
    except Exception as exc:
        return _blocked("BASELINE_CAPTURE_FAILED", _safe_error(exc))

    for name in EXPECTED_FIXTURE_FILES:
        fixture_id = FIXTURE_IDS[name]
        try:
            outputs.append(_capture_fixture(fixture_dir / name, fixture_id, model_pb, classes, es, np))
        except Exception as exc:  # pragma: no cover - exercised only in runtime container
            blockers.append(
                {
                    "fixture_id": fixture_id,
                    "code": "BASELINE_CAPTURE_FAILED",
                    "message": _safe_error(exc),
                }
            )

    return {
        "report_type": "musicnn_legacy_baseline_capture_output",
        "baseline_capture_succeeded": not blockers,
        "fixture_count": len(EXPECTED_FIXTURE_FILES),
        "import_policy_used": [
            "essentia_first",
            "no_explicit_tensorflow_before_essentia",
            "production_like_legacy_musicnn_path",
            "fresh_python_process",
        ],
        "fixture_path_visible": True,
        "expected_mp3_files_visible": True,
        "tensorflow_predict_musicnn_available": True,
        "baseline_outputs": outputs if not blockers else [],
        "blockers": blockers,
    }


def _blocked(code: str, message: str) -> dict[str, Any]:
    return {
        "report_type": "musicnn_legacy_baseline_capture_output",
        "baseline_capture_succeeded": False,
        "fixture_count": len(EXPECTED_FIXTURE_FILES),
        "import_policy_used": [
            "essentia_first",
            "no_explicit_tensorflow_before_essentia",
            "production_like_legacy_musicnn_path",
            "fresh_python_process",
        ],
        "fixture_path_visible": False,
        "expected_mp3_files_visible": False,
        "tensorflow_predict_musicnn_available": False,
        "baseline_outputs": [],
        "blockers": [{"code": code, "message": message}],
    }


def _safe_error(exc: Exception) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    for marker in ("/tmp/music-tools-onnx-parity", "/opt/music-tools", "/app/"):
        text = text.replace(marker, "[redacted]")
    return text.splitlines()[0][:240]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-dir", required=True)
    parser.add_argument("--model-pb", default="/app/app/models/msd-musicnn-1.pb")
    parser.add_argument("--model-json", default="/app/app/models/msd-musicnn-1.json")
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = capture_baseline(args)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if payload["baseline_capture_succeeded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
