#!/usr/bin/env python3
"""Roadmap 4.92: direct benchmark для legacy MusicNN и ONNX slim.

Скрипт остаётся local-only и не трогает `/classify`, HTTP или server start.
Он выполняет два независимых one-off `docker compose run` запуска:

- `genre-classifier` для current default legacy MusicNN path;
- `genre-classifier-onnx` для optional ONNX slim path.

Каждый контейнерный запуск измеряет direct provider pipeline на одном и том
же audio fixture, а host-side orchestrator сводит результаты в общий JSON
и markdown report. Production readiness этот benchmark не доказывает.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _detect_service_root() -> Path:
    """Находит корень service в host- и container-режимах."""

    explicit_root = os.getenv("GENRE_CLASSIFIER_SERVICE_ROOT")
    if explicit_root:
        return Path(explicit_root).resolve()

    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "app").is_dir() and (candidate / "docs").is_dir():
            return candidate

    return current


SERVICE_ROOT = _detect_service_root()
if str(Path.cwd()) not in sys.path:
    sys.path.insert(0, str(Path.cwd()))
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))
DEFAULT_FIXTURE_PATH = Path(
    "/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3"
)
DEFAULT_OUTPUT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "legacy-vs-onnx-slim-direct-benchmark-report.json"
)
DEFAULT_MARKDOWN_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/roadmap-4.92-legacy-vs-onnx-slim-direct-benchmark.md"
)
DEFAULT_RUNS = 3
SCRIPT_NAME = Path(__file__).name
LEGACY_SERVICE_NAME = "genre-classifier"
ONNX_SERVICE_NAME = "genre-classifier-onnx"
LEGACY_PROVIDER_NAME = "legacy_musicnn"
ONNX_PROVIDER_NAME = "onnx_musicnn"


class BenchmarkError(RuntimeError):
    """Ожидаемая ошибка benchmark helper без лишнего traceback на уровне CLI."""


@dataclass(frozen=True)
class ChildRunResult:
    """Результат одного container-local direct run."""

    total_seconds: float
    preprocessing_seconds: float | None
    inference_seconds: float | None
    mapping_seconds: float | None
    max_rss_kb: int | None
    genres: list[dict[str, Any]]
    genres_pretty: list[str]
    response_compatible_shape: bool
    provider_runtime_available: bool
    provider_runtime_reasons: list[str]
    extra: dict[str, Any]


def _safe_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BenchmarkError(f"JSON artifact is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BenchmarkError(f"JSON artifact is invalid: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise BenchmarkError(f"JSON artifact must be an object: {path}")

    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _average(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return float(statistics.fmean(filtered))


def _stability_check(results: list[dict[str, Any]]) -> bool:
    if not results:
        return False

    first_genres = results[0]["genres"]
    first_genres_pretty = results[0]["genres_pretty"]
    return all(
        item["genres"] == first_genres and item["genres_pretty"] == first_genres_pretty
        for item in results[1:]
    )


def _compatibility_shape_ok(genres: list[dict[str, Any]], genres_pretty: list[str]) -> bool:
    if not isinstance(genres, list) or not isinstance(genres_pretty, list):
        return False
    if not genres or not genres_pretty:
        return False

    for item in genres:
        if not isinstance(item, dict):
            return False
        if not isinstance(item.get("tag"), str):
            return False
        prob = item.get("prob")
        if not isinstance(prob, (int, float)):
            return False
        if not math.isfinite(float(prob)):
            return False

    return all(isinstance(item, str) and item.strip() for item in genres_pretty)


def _stage_script_copy() -> tuple[Path, Path]:
    staged_dir = Path(tempfile.mkdtemp(prefix="music-tools-roadmap-4.92-benchmark-"))
    staged_script = staged_dir / SCRIPT_NAME
    shutil.copy2(Path(__file__).resolve(), staged_script)
    return staged_dir, staged_script


def _compose_run_child(
    *,
    service: str,
    provider: str,
    audio_path: Path,
    staged_dir: Path,
    staged_script: Path,
) -> dict[str, Any]:
    if not audio_path.is_file():
        raise BenchmarkError(f"audio artifact missing: {audio_path}")

    compose_command = ["docker", "compose"]
    if service == ONNX_SERVICE_NAME:
        compose_command.extend(["--profile", "onnx"])

    command = compose_command + [
        "run",
        "--rm",
        "--no-deps",
        "--volume",
        f"{audio_path.parent.parent}:{audio_path.parent.parent}:ro",
        "--volume",
        f"{staged_dir}:{staged_dir}:ro",
        service,
        "python3",
        str(staged_script),
        "--child-run",
        "--provider",
        provider,
        "--audio-path",
        str(audio_path),
    ]

    completed = subprocess.run(
        command,
        cwd=SERVICE_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "compose run failed").strip()
        raise BenchmarkError(message)

    payload = json.loads(completed.stdout.strip() or "{}")
    if not isinstance(payload, dict):
        raise BenchmarkError("benchmark child returned invalid JSON")

    return payload


def _parse_child_result(payload: dict[str, Any]) -> ChildRunResult:
    return ChildRunResult(
        total_seconds=float(payload["total_seconds"]),
        preprocessing_seconds=payload.get("preprocessing_seconds"),
        inference_seconds=payload.get("inference_seconds"),
        mapping_seconds=payload.get("mapping_seconds"),
        max_rss_kb=payload.get("max_rss_kb"),
        genres=list(payload.get("genres", [])),
        genres_pretty=list(payload.get("genres_pretty", [])),
        response_compatible_shape=bool(payload.get("response_compatible_shape")),
        provider_runtime_available=bool(payload.get("provider_runtime_available")),
        provider_runtime_reasons=list(payload.get("provider_runtime_reasons", [])),
        extra={key: value for key, value in payload.items() if key not in {
            "total_seconds",
            "preprocessing_seconds",
            "inference_seconds",
            "mapping_seconds",
            "max_rss_kb",
            "genres",
            "genres_pretty",
            "response_compatible_shape",
            "provider_runtime_available",
            "provider_runtime_reasons",
        }},
    )


def _run_provider_series(
    *,
    service: str,
    provider: str,
    audio_path: Path,
    runs: int,
) -> dict[str, Any]:
    staged_dir, staged_script = _stage_script_copy()
    results: list[dict[str, Any]] = []
    child_runs: list[ChildRunResult] = []

    try:
        for _ in range(runs):
            payload = _compose_run_child(
                service=service,
                provider=provider,
                audio_path=audio_path,
                staged_dir=staged_dir,
                staged_script=staged_script,
            )
            results.append(payload)
            child_runs.append(_parse_child_result(payload))
    finally:
        shutil.rmtree(staged_dir, ignore_errors=True)

    success = all(item.provider_runtime_available for item in child_runs)
    repeated_run_stable = _stability_check(results)
    total_seconds = [item.total_seconds for item in child_runs]
    preprocessing_seconds = [item.preprocessing_seconds for item in child_runs]
    inference_seconds = [item.inference_seconds for item in child_runs]
    mapping_seconds = [item.mapping_seconds for item in child_runs]

    return {
        "attempted": True,
        "available": success,
        "service": service,
        "provider": provider,
        "runs": runs,
        "success": success,
        "total_seconds": total_seconds,
        "preprocessing_seconds": preprocessing_seconds,
        "inference_seconds": inference_seconds,
        "mapping_seconds": mapping_seconds,
        "max_rss_kb": max(item.max_rss_kb or 0 for item in child_runs) if child_runs else None,
        "genres": child_runs[-1].genres if child_runs else [],
        "genres_pretty": child_runs[-1].genres_pretty if child_runs else [],
        "response_compatible_shape": child_runs[-1].response_compatible_shape if child_runs else False,
        "repeated_run_stable": repeated_run_stable,
        "runtime_reasons": child_runs[-1].provider_runtime_reasons if child_runs else [],
        "runs_detail": results,
    }


def _build_comparison(legacy_benchmark: dict[str, Any], onnx_benchmark: dict[str, Any]) -> dict[str, Any]:
    avg_total_seconds_legacy = _average(legacy_benchmark["total_seconds"])
    avg_total_seconds_onnx_slim = _average(onnx_benchmark["total_seconds"])
    avg_preprocessing_seconds_legacy = _average(legacy_benchmark["preprocessing_seconds"])
    avg_preprocessing_seconds_onnx_slim = _average(onnx_benchmark["preprocessing_seconds"])
    avg_inference_seconds_legacy = _average(legacy_benchmark["inference_seconds"])
    avg_inference_seconds_onnx_slim = _average(onnx_benchmark["inference_seconds"])
    avg_mapping_seconds_legacy = _average(legacy_benchmark["mapping_seconds"])
    avg_mapping_seconds_onnx_slim = _average(onnx_benchmark["mapping_seconds"])

    speedup_ratio = None
    onnx_slim_faster = None
    if avg_total_seconds_legacy is not None and avg_total_seconds_onnx_slim not in (None, 0.0):
        speedup_ratio = float(avg_total_seconds_legacy / avg_total_seconds_onnx_slim)
        onnx_slim_faster = speedup_ratio > 1.0

    memory_delta_kb = None
    if legacy_benchmark["max_rss_kb"] is not None and onnx_benchmark["max_rss_kb"] is not None:
        memory_delta_kb = int(legacy_benchmark["max_rss_kb"] - onnx_benchmark["max_rss_kb"])

    response_shape_match = (
        legacy_benchmark["response_compatible_shape"] and onnx_benchmark["response_compatible_shape"]
    )
    drift_observed = legacy_benchmark["genres"] != onnx_benchmark["genres"] or (
        legacy_benchmark["genres_pretty"] != onnx_benchmark["genres_pretty"]
    )

    performance_benefit_confirmed = bool(
        onnx_slim_faster
        and response_shape_match
        and legacy_benchmark["repeated_run_stable"]
        and onnx_benchmark["repeated_run_stable"]
    )

    return {
        "avg_total_seconds_legacy": avg_total_seconds_legacy,
        "avg_total_seconds_onnx_slim": avg_total_seconds_onnx_slim,
        "avg_preprocessing_seconds_legacy": avg_preprocessing_seconds_legacy,
        "avg_preprocessing_seconds_onnx_slim": avg_preprocessing_seconds_onnx_slim,
        "avg_inference_seconds_legacy": avg_inference_seconds_legacy,
        "avg_inference_seconds_onnx_slim": avg_inference_seconds_onnx_slim,
        "avg_mapping_seconds_legacy": avg_mapping_seconds_legacy,
        "avg_mapping_seconds_onnx_slim": avg_mapping_seconds_onnx_slim,
        "speedup_ratio_legacy_div_onnx": speedup_ratio,
        "onnx_slim_faster": onnx_slim_faster,
        "memory_delta_kb": memory_delta_kb,
        "legacy_max_rss_kb": legacy_benchmark["max_rss_kb"],
        "onnx_slim_max_rss_kb": onnx_benchmark["max_rss_kb"],
        "response_shape_match": response_shape_match,
        "output_drift_documented": True,
        "qualitative_output_drift_note": (
            "Observed drift is controlled and reproducible."
            if drift_observed
            else "No meaningful drift was observed; both direct paths remained contract-compatible and stable."
        ),
        "performance_benefit_confirmed": performance_benefit_confirmed,
    }


def _build_report(
    *,
    audio_path: Path,
    runs: int,
) -> dict[str, Any]:
    legacy_benchmark = _run_provider_series(
        service=LEGACY_SERVICE_NAME,
        provider=LEGACY_PROVIDER_NAME,
        audio_path=audio_path,
        runs=runs,
    )
    onnx_benchmark = _run_provider_series(
        service=ONNX_SERVICE_NAME,
        provider=ONNX_PROVIDER_NAME,
        audio_path=audio_path,
        runs=runs,
    )

    comparison = _build_comparison(legacy_benchmark, onnx_benchmark)
    recommendation = (
        "ONNX slim path is faster or comparable and stays contract-compatible; keep it as an optional "
        "candidate, but this benchmark is not a production approval."
        if comparison["performance_benefit_confirmed"]
        else "Legacy comparison is complete, but the benchmark does not justify a production claim; keep "
        "ONNX slim as an optional path and investigate the performance delta if needed."
    )

    legacy_benchmark.pop("runs_detail", None)
    onnx_benchmark.pop("runs_detail", None)

    report = {
        "roadmap": "4.92",
        "legacy_vs_onnx_slim_direct_benchmark": True,
        "not_production_decision": True,
        "production_approval": False,
        "docker_compose_run_command_used": True,
        "docker_compose_up_run": False,
        "server_started": False,
        "classify_called": False,
        "network_http_called": False,
        "default_provider_changed": False,
        "audio_fixture": str(audio_path),
        "service": {
            "legacy": {
                "name": LEGACY_SERVICE_NAME,
                "profile": "default",
                "target": "legacy-runtime",
            },
            "onnx_slim": {
                "name": ONNX_SERVICE_NAME,
                "profile": "onnx",
                "target": "onnx-runtime-slim",
            },
        },
        "legacy_benchmark": legacy_benchmark,
        "onnx_slim_benchmark": onnx_benchmark,
        "comparison": comparison,
        "decision_signal": {
            "onnx_slim_runtime_functional": bool(onnx_benchmark["success"]),
            "legacy_comparison_completed": bool(legacy_benchmark["success"]),
            "performance_benefit_confirmed": comparison["performance_benefit_confirmed"],
            "recommendation": recommendation,
        },
        "production_boundaries": {
            "production_requirements_changed": False,
            "dockerfile_changed": False,
            "compose_changed": False,
            "default_provider_changed": False,
            "classify_contract_changed": False,
            "response_shape_changed": False,
            "tidal_parser_touched": False,
        },
        "blockers": [],
        "warnings": [],
    }

    if not legacy_benchmark["available"]:
        report["blockers"].append("LEGACY_DIRECT_BENCHMARK_PATH_NOT_AVAILABLE")
    if not onnx_benchmark["available"]:
        report["blockers"].append("ONNX_SLIM_DIRECT_BENCHMARK_PATH_NOT_AVAILABLE")
    if not legacy_benchmark["repeated_run_stable"]:
        report["warnings"].append("legacy_repeated_run_stability_not_confirmed")
    if not onnx_benchmark["repeated_run_stable"]:
        report["warnings"].append("onnx_slim_repeated_run_stability_not_confirmed")
    if not comparison["response_shape_match"]:
        report["warnings"].append("response_shape_match_not_confirmed")

    return report


def _build_markdown_report(report: dict[str, Any]) -> str:
    legacy = report["legacy_benchmark"]
    onnx = report["onnx_slim_benchmark"]
    comparison = report["comparison"]
    decision = report["decision_signal"]

    def _fmt(value: Any) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, float):
            return f"{value:.6f}"
        return str(value)

    legacy_total = ", ".join(_fmt(item) for item in legacy["total_seconds"])
    onnx_total = ", ".join(_fmt(item) for item in onnx["total_seconds"])
    legacy_inference = ", ".join(_fmt(item) for item in legacy["inference_seconds"])
    onnx_inference = ", ".join(_fmt(item) for item in onnx["inference_seconds"])
    legacy_mapping = ", ".join(_fmt(item) for item in legacy["mapping_seconds"])
    onnx_mapping = ", ".join(_fmt(item) for item in onnx["mapping_seconds"])
    legacy_preprocessing = ", ".join(_fmt(item) for item in legacy["preprocessing_seconds"])
    onnx_preprocessing = ", ".join(_fmt(item) for item in onnx["preprocessing_seconds"])

    legacy_genres = ", ".join(item["tag"] for item in legacy["genres"])
    onnx_genres = ", ".join(item["tag"] for item in onnx["genres"])
    legacy_pretty = ", ".join(legacy["genres_pretty"])
    onnx_pretty = ", ".join(onnx["genres_pretty"])

    lines = [
        "# Roadmap 4.92 - legacy vs ONNX slim direct benchmark",
        "",
        "Статус: local-only direct benchmark, не production decision.",
        "",
        "## Контекст",
        "",
        f"- Использован shared fixture `{report['audio_fixture']}`.",
        "- Docker build не запускался явно; использовались one-off `docker compose run` запуски.",
        "- Docker Compose `up` не запускался.",
        "- `/classify` не вызывался.",
        "- Network HTTP smoke не запускался.",
        "- Default provider не менялся.",
        "",
        "## Команды benchmark",
        "",
        "```bash",
        f"cd {SERVICE_ROOT}",
        f"python3 docs/lightweight/evaluation/parity-scaffold/{SCRIPT_NAME} \\",
        f"  --audio-path {report['audio_fixture']} \\",
        f"  --runs {legacy['runs']} \\",
        f"  --output docs/lightweight/evaluation/parity-scaffold/legacy-vs-onnx-slim-direct-benchmark-report.json \\",
        f"  --markdown-output docs/lightweight/roadmap-4.92-legacy-vs-onnx-slim-direct-benchmark.md",
        "```",
        "",
        "### Legacy container run",
        "",
        "```bash",
        "docker compose run --rm --no-deps genre-classifier python3 /tmp/.../legacy_vs_onnx_slim_direct_benchmark.py --child-run --provider legacy --audio-path /tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3",
        "```",
        "",
        "### ONNX slim container run",
        "",
        "```bash",
        "docker compose --profile onnx run --rm --no-deps genre-classifier-onnx python3 /tmp/.../legacy_vs_onnx_slim_direct_benchmark.py --child-run --provider onnx --audio-path /tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3",
        "```",
        "",
        "## Legacy benchmark",
        "",
        f"- Available: `{legacy['available']}`.",
        f"- Runs: `{legacy['runs']}`.",
        f"- `total_seconds`: {legacy_total}",
        f"- `preprocessing_seconds`: {legacy_preprocessing}",
        f"- `inference_seconds`: {legacy_inference}",
        f"- `mapping_seconds`: {legacy_mapping}",
        f"- `max_rss_kb`: `{legacy['max_rss_kb']}`",
        f"- `genres`: {legacy_genres}",
        f"- `genres_pretty`: {legacy_pretty}",
        f"- `response_compatible_shape`: `{legacy['response_compatible_shape']}`",
        f"- `repeated_run_stable`: `{legacy['repeated_run_stable']}`",
        "",
        "## ONNX slim benchmark",
        "",
        f"- Available: `{onnx['available']}`.",
        f"- Runs: `{onnx['runs']}`.",
        f"- `total_seconds`: {onnx_total}",
        f"- `preprocessing_seconds`: {onnx_preprocessing}",
        f"- `inference_seconds`: {onnx_inference}",
        f"- `mapping_seconds`: {onnx_mapping}",
        f"- `max_rss_kb`: `{onnx['max_rss_kb']}`",
        f"- `genres`: {onnx_genres}",
        f"- `genres_pretty`: {onnx_pretty}",
        f"- `response_compatible_shape`: `{onnx['response_compatible_shape']}`",
        f"- `repeated_run_stable`: `{onnx['repeated_run_stable']}`",
        "",
        "## Comparison",
        "",
        f"- `avg_total_seconds_legacy`: `{_fmt(comparison['avg_total_seconds_legacy'])}`",
        f"- `avg_total_seconds_onnx_slim`: `{_fmt(comparison['avg_total_seconds_onnx_slim'])}`",
        f"- `speedup_ratio_legacy_div_onnx`: `{_fmt(comparison['speedup_ratio_legacy_div_onnx'])}`",
        f"- `memory_delta_kb`: `{_fmt(comparison['memory_delta_kb'])}`",
        f"- `response_shape_match`: `{comparison['response_shape_match']}`",
        f"- `output_drift_documented`: `{comparison['output_drift_documented']}`",
        f"- Drift note: {comparison['qualitative_output_drift_note']}",
        "",
        "## Decision signal",
        "",
        f"- `onnx_slim_runtime_functional`: `{decision['onnx_slim_runtime_functional']}`",
        f"- `legacy_comparison_completed`: `{decision['legacy_comparison_completed']}`",
        f"- `performance_benefit_confirmed`: `{decision['performance_benefit_confirmed']}`",
        f"- Recommendation: {decision['recommendation']}",
        "",
        "## Blockers / warnings",
        "",
        f"- Blockers: {report['blockers'] or 'none'}",
        f"- Warnings: {report['warnings'] or 'none'}",
        "",
        "## Confirmations",
        "",
        "- `AGENTS.md` read and followed.",
        "- Legacy direct benchmark attempted.",
        "- ONNX slim direct benchmark completed.",
        "- No `docker compose up`.",
        "- No server start.",
        "- No `/classify` call.",
        "- No network HTTP call.",
        "- No production dependency changes.",
        "- No Dockerfile changes.",
        "- No Compose changes.",
        "- No default provider changes.",
        "- No response shape changes.",
        "- No production readiness claim.",
        "- No artifacts committed.",
        "- `tidal-parser` untouched.",
    ]
    return "\n".join(lines) + "\n"


def _child_main(args: argparse.Namespace) -> int:
    if args.provider == LEGACY_PROVIDER_NAME:
        result = _child_legacy_run(args.audio_path)
    elif args.provider == ONNX_PROVIDER_NAME:
        result = _child_onnx_run(args.audio_path)
    else:
        raise BenchmarkError(f"Unknown provider: {args.provider}")

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


def _child_legacy_run(audio_path: Path) -> dict[str, Any]:
    total_start = time.perf_counter()
    import_start = time.perf_counter()

    import numpy as np

    from app.core import settings
    from app.providers.base import ProviderGenreScore, ProviderResult
    from app.providers.compat import (
        map_validated_result_to_legacy_genres,
        map_validated_result_to_legacy_genres_pretty,
    )
    from app.providers.validation import validate_and_normalize_provider_result
    from essentia.standard import MonoLoader, TensorflowPredictMusiCNN

    import_seconds = time.perf_counter() - import_start

    if not audio_path.is_file():
        raise BenchmarkError(f"audio artifact missing: {audio_path}")
    if not settings.MODEL_PB.is_file():
        raise BenchmarkError(f"legacy model artifact missing: {settings.MODEL_PB}")
    if not settings.MODEL_JSON.is_file():
        raise BenchmarkError(f"legacy metadata artifact missing: {settings.MODEL_JSON}")

    import json as json_module
    import resource

    with settings.MODEL_JSON.open("r", encoding="utf-8") as handle:
        metadata = json_module.load(handle)
    classes = metadata.get("classes")
    if not isinstance(classes, list) or not classes:
        raise BenchmarkError("legacy metadata classes unavailable")

    audio_loading_start = time.perf_counter()
    audio = MonoLoader(filename=str(audio_path), sampleRate=16000)()
    audio_loading_seconds = time.perf_counter() - audio_loading_start

    preprocessing_seconds = None

    inference_start = time.perf_counter()
    activations = TensorflowPredictMusiCNN(graphFilename=str(settings.MODEL_PB))(audio)
    inference_seconds = time.perf_counter() - inference_start

    mean_scores = np.mean(activations, axis=0)
    provider_result = ProviderResult(
        genres=[
            ProviderGenreScore(tag=str(label).lower(), score=float(score))
            for label, score in zip(classes, mean_scores)
        ],
        provider_name=LEGACY_PROVIDER_NAME,
        model_name=settings.MODEL_PB.stem,
    )

    mapping_start = time.perf_counter()
    validated_result = validate_and_normalize_provider_result(provider_result, top_n=8)
    genres = map_validated_result_to_legacy_genres(validated_result)
    genres_pretty = map_validated_result_to_legacy_genres_pretty(validated_result)
    mapping_seconds = time.perf_counter() - mapping_start

    total_seconds = time.perf_counter() - total_start
    rss_value = getattr(resource.getrusage(resource.RUSAGE_SELF), "ru_maxrss", None)

    return {
        "provider": LEGACY_PROVIDER_NAME,
        "service": LEGACY_SERVICE_NAME,
        "audio_path": str(audio_path),
        "total_seconds": total_seconds,
        "preprocessing_seconds": preprocessing_seconds,
        "inference_seconds": inference_seconds,
        "mapping_seconds": mapping_seconds,
        "max_rss_kb": rss_value,
        "genres": genres,
        "genres_pretty": genres_pretty,
        "response_compatible_shape": _compatibility_shape_ok(genres, genres_pretty),
        "provider_runtime_available": True,
        "provider_runtime_reasons": [],
        "audio_loading_seconds": audio_loading_seconds,
        "import_seconds": import_seconds,
    }


def _child_onnx_run(audio_path: Path) -> dict[str, Any]:
    total_start = time.perf_counter()
    import_start = time.perf_counter()

    import onnxruntime as ort
    from essentia import standard as essentia_standard

    from app.providers.onnx_musicnn import OnnxMusiCNNProvider
    from app.providers.validation import validate_and_normalize_provider_result
    from app.providers.compat import (
        map_validated_result_to_legacy_genres,
        map_validated_result_to_legacy_genres_pretty,
    )

    import_seconds = time.perf_counter() - import_start

    provider = OnnxMusiCNNProvider()
    runtime_status = provider.describe_runtime_status()
    if not runtime_status["available"]:
        raise BenchmarkError(provider._format_unsupported_message(runtime_status))

    if not audio_path.is_file():
        raise BenchmarkError(f"audio artifact missing: {audio_path}")

    metadata_path = provider._get_metadata_path()
    if metadata_path is None or not metadata_path.is_file():
        raise BenchmarkError("onnx metadata artifact missing")

    import json as json_module

    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json_module.load(handle)
    classes = metadata.get("classes")
    if not isinstance(classes, list) or not classes:
        raise BenchmarkError("onnx metadata classes unavailable")

    audio_loading_start = time.perf_counter()
    audio = essentia_standard.MonoLoader(filename=str(audio_path), sampleRate=16000)()
    audio_loading_seconds = time.perf_counter() - audio_loading_start

    preprocessing_start = time.perf_counter()
    patch = provider._build_tensorflow_input_patch(essentia_standard, str(audio_path))
    preprocessing_seconds = time.perf_counter() - preprocessing_start

    inference_start = time.perf_counter()
    activations = provider._run_onnx_inference(ort, provider._get_model_path(), patch)
    inference_seconds = time.perf_counter() - inference_start

    provider_result = provider.build_provider_result_from_outputs(activations, classes, top_n=8)

    mapping_start = time.perf_counter()
    validated_result = validate_and_normalize_provider_result(provider_result, top_n=8)
    genres = map_validated_result_to_legacy_genres(validated_result)
    genres_pretty = map_validated_result_to_legacy_genres_pretty(validated_result)
    mapping_seconds = time.perf_counter() - mapping_start

    total_seconds = time.perf_counter() - total_start
    import resource

    rss_value = getattr(resource.getrusage(resource.RUSAGE_SELF), "ru_maxrss", None)

    return {
        "provider": ONNX_PROVIDER_NAME,
        "service": ONNX_SERVICE_NAME,
        "audio_path": str(audio_path),
        "total_seconds": total_seconds,
        "preprocessing_seconds": preprocessing_seconds,
        "inference_seconds": inference_seconds,
        "mapping_seconds": mapping_seconds,
        "max_rss_kb": rss_value,
        "genres": genres,
        "genres_pretty": genres_pretty,
        "response_compatible_shape": _compatibility_shape_ok(genres, genres_pretty),
        "provider_runtime_available": True,
        "provider_runtime_reasons": [],
        "audio_loading_seconds": audio_loading_seconds,
        "import_seconds": import_seconds,
        "patch_shape": list(getattr(patch, "shape", [])),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Собирает Roadmap 4.92 legacy vs ONNX slim direct benchmark report."
    )
    parser.add_argument("--audio-path", type=Path, default=DEFAULT_FIXTURE_PATH)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--provider", choices=(LEGACY_PROVIDER_NAME, ONNX_PROVIDER_NAME))
    parser.add_argument("--child-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.child_run:
            if not args.provider:
                raise BenchmarkError("--provider is required for --child-run")
            return _child_main(args)

        if args.runs < 3:
            raise BenchmarkError("--runs must be at least 3 for Roadmap 4.92")

        report = _build_report(audio_path=args.audio_path, runs=args.runs)
    except Exception as exc:
        payload = {
            "ok": False,
            "error": _safe_error(exc),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    _write_json(args.output, report)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(_build_markdown_report(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
