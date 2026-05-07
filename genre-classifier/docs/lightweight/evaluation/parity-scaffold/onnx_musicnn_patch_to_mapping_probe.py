#!/usr/bin/env python3
"""Изолированный probe для вертикальной цепочки ONNX/MusiCNN patch-to-mapping.

Скрипт предназначен только для local-only проверки явно переданных внешних
артефактов. Он не использует app/provider imports, не вызывает `/classify`,
не делает Docker-запусков и не пытается находить артефакты неявно.

Проверяются только:

- версия и путь Python;
- версия `onnxruntime` и доступные providers;
- наличие `CPUExecutionProvider`;
- явные пути к ONNX model, classes metadata и patch artifact;
- чтение model/classes metadata без download/implicit discovery;
- ONNX Runtime inference только при наличии явного patch artifact;
- shape input patch `[187, 96]`;
- формы runtime outputs;
- локальное минимальное mapping-преобразование для `genres` и
  `genres_pretty`, если inference выполнен.

Это не production migration и не runtime smoke через provider.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Sequence


SERVICE_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold"
    / "onnx-musicnn-patch-to-mapping-probe-report.json"
)
EXPECTED_ONNXRUNTIME_VERSION = "1.25.1"
EXPECTED_PATCH_SHAPE = [187, 96]
EXPECTED_ACTIVATIONS_COUNT = 50
EXPECTED_EMBEDDINGS_COUNT = 200
DEFAULT_TOP_N = 5

CANONICAL_ALLOWED_GENRES = frozenset(
    [
        "acoustic",
        "alternative",
        "alternative rock",
        "ambient",
        "avant jazz",
        "blues",
        "chillout",
        "classic rock",
        "country",
        "dance",
        "dream pop",
        "easy listening",
        "electro",
        "electronic",
        "electronica",
        "experimental",
        "experimental rock",
        "folk",
        "funk",
        "hard rock",
        "heavy metal",
        "hip hop",
        "house",
        "indie",
        "indie pop",
        "indie rock",
        "instrumental",
        "instrumental rock",
        "jazz",
        "jazz rock",
        "leftfield",
        "metal",
        "pop",
        "post punk",
        "progressive rock",
        "punk",
        "rnb",
        "rock",
        "shoegaze",
        "soul",
        "synth pop wave",
        "trip hop",
    ]
)

GENRE_ALIAS_TO_CANONICAL = {
    "avant-jazz": "avant jazz",
    "dream-pop": "dream pop",
    "hip hop": "hip hop",
    "hip-hop": "hip hop",
    "left field": "leftfield",
    "left-field": "leftfield",
    "post-punk": "post punk",
    "r&b": "rnb",
    "rhythm and blues": "rnb",
    "synth-pop wave": "synth pop wave",
    "trip-hop": "trip hop",
}


class ProbeError(RuntimeError):
    """Ошибка изолированного probe без tracebacks для пользователя."""


def _resolve_external_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    return Path(path_value)


def _path_is_external(path: Path) -> bool:
    try:
        return not path.resolve().is_relative_to(SERVICE_ROOT)
    except Exception:
        return True


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _load_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    text = re.sub(r"[-_]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text or None


def _normalize_candidate_label(value: Any) -> str | None:
    normalized = _normalize_text(value)
    if not normalized:
        return None

    canonical = GENRE_ALIAS_TO_CANONICAL.get(normalized, normalized)
    if canonical not in CANONICAL_ALLOWED_GENRES:
        return None

    return canonical


def _load_numpy_module() -> Any:
    try:
        import numpy as np  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - handled in report
        raise ProbeError("numpy unavailable in isolated probe environment") from exc

    return np


def _probe_onnxruntime() -> dict[str, Any]:
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


def _extract_schema_shapes_from_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {
            "output_names": [],
            "activations_shape": [],
            "embeddings_shape": [],
        }

    outputs = metadata.get("outputs")
    if not isinstance(outputs, list):
        return {
            "output_names": [],
            "activations_shape": [],
            "embeddings_shape": [],
        }

    output_names: list[str] = []
    activations_shape: list[int] = []
    embeddings_shape: list[int] = []

    for output in outputs:
        if not isinstance(output, dict):
            continue

        output_name = output.get("name")
        if isinstance(output_name, str) and output_name:
            output_names.append(output_name)

        shape = output.get("shape")
        if not isinstance(shape, list):
            continue

        normalized_shape = [int(item) for item in shape if isinstance(item, int)]
        if normalized_shape == [1, EXPECTED_ACTIVATIONS_COUNT]:
            activations_shape = normalized_shape
        elif normalized_shape == [1, EXPECTED_EMBEDDINGS_COUNT]:
            embeddings_shape = normalized_shape

    return {
        "output_names": output_names,
        "activations_shape": activations_shape,
        "embeddings_shape": embeddings_shape,
    }


def _load_classes_metadata(classes_path: Path) -> tuple[list[str], dict[str, Any]]:
    try:
        classes_metadata = _load_json(classes_path)
    except FileNotFoundError as exc:
        raise ProbeError("explicit classes path is missing") from exc
    except json.JSONDecodeError as exc:
        raise ProbeError("explicit classes metadata is not valid JSON") from exc

    if isinstance(classes_metadata, dict):
        classes = classes_metadata.get("classes")
        schema = classes_metadata.get("schema")
    else:
        classes = classes_metadata
        schema = None

    if not isinstance(classes, list) or not classes:
        raise ProbeError("explicit classes metadata does not contain a classes list")

    normalized_classes = []
    for label in classes:
        normalized = _normalize_text(label)
        if not normalized:
            raise ProbeError("explicit classes metadata contains invalid labels")
        normalized_classes.append(normalized)

    return normalized_classes, _extract_schema_shapes_from_metadata(schema)


def _inspect_model_session(model_path: Path, providers: Sequence[str]) -> dict[str, Any]:
    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - handled in report
        raise ProbeError("onnxruntime unavailable in isolated probe environment") from exc

    try:
        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = 1
        session_options.inter_op_num_threads = 1
        session = ort.InferenceSession(
            str(model_path),
            sess_options=session_options,
            providers=list(providers) or None,
        )
    except Exception as exc:
        raise ProbeError(f"unable to open explicit ONNX model artifact: {exc}") from exc

    output_names = [output.name for output in session.get_outputs()]
    output_shapes: list[list[int]] = []
    for output in session.get_outputs():
        shape: list[int] = []
        for item in output.shape:
            if isinstance(item, int):
                shape.append(item)
        output_shapes.append(shape)

    activations_shape: list[int] = []
    embeddings_shape: list[int] = []
    for shape in output_shapes:
        if shape == [1, EXPECTED_ACTIVATIONS_COUNT]:
            activations_shape = shape
        elif shape == [1, EXPECTED_EMBEDDINGS_COUNT]:
            embeddings_shape = shape

    return {
        "output_names": output_names,
        "output_shapes": output_shapes,
        "activations_shape": activations_shape,
        "embeddings_shape": embeddings_shape,
        "input_names": [input_info.name for input_info in session.get_inputs()],
        "input_shapes": [
            [item for item in input_info.shape if isinstance(item, int)]
            for input_info in session.get_inputs()
        ],
    }


def _load_patch_array(patch_path: Path) -> Any:
    np = _load_numpy_module()

    if not patch_path.is_file():
        raise ProbeError("explicit patch artifact is missing")

    suffix = patch_path.suffix.lower()
    if suffix == ".npy":
        return np.load(patch_path, allow_pickle=False)
    if suffix == ".npz":
        archive = np.load(patch_path, allow_pickle=False)
        if len(archive.files) != 1:
            raise ProbeError("explicit patch archive must contain exactly one array")
        return archive[archive.files[0]]
    if suffix == ".json":
        data = _load_json(patch_path)
        return np.asarray(data, dtype=np.float32)

    raise ProbeError("unsupported explicit patch artifact format")


def _coerce_patch_array(patch_array: Any) -> tuple[list[int], list[float]]:
    np = _load_numpy_module()
    array = np.asarray(patch_array, dtype=np.float32)
    shape = list(array.shape)

    if shape != EXPECTED_PATCH_SHAPE:
        raise ProbeError(
            f"patch shape mismatch: expected {EXPECTED_PATCH_SHAPE}, got {shape or '[]'}"
        )

    return shape, array


def _build_candidate_genres(activations: Sequence[float], classes: Sequence[str], top_n: int) -> list[dict[str, Any]]:
    scored_items = []
    for index, (activation, label) in enumerate(zip(activations, classes)):
        scored_items.append(
            (
                index,
                {
                    "tag": str(label).lower(),
                    "prob": round(float(activation), 4),
                },
            )
        )

    scored_items.sort(key=lambda item: (-item[1]["prob"], item[0]))
    return [item[1] for item in scored_items[:top_n]]


def _build_candidate_genres_pretty(candidate_genres: Sequence[dict[str, Any]], top_n: int) -> list[str]:
    tags = []
    for item in candidate_genres:
        tag = _normalize_candidate_label(item.get("tag"))
        if tag:
            tags.append(tag)

    tag_set = set(tags)
    result: list[str] = []

    def add(tag: str) -> None:
        normalized = _normalize_candidate_label(tag)
        if normalized and normalized not in result:
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

    return result[:top_n]


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    python_info = {
        "version": platform.python_version(),
        "executable": sys.executable,
    }

    onnxruntime_info = _probe_onnxruntime()
    model_path = _resolve_external_path(args.onnx_model_path)
    classes_path = _resolve_external_path(args.classes_path)
    patch_path = _resolve_external_path(args.patch_path)

    artifacts = {
        "implicit_discovery_used": False,
        "onnx_model_path_provided": model_path is not None,
        "onnx_model_path_external": bool(model_path and _path_is_external(model_path)),
        "onnx_model_path": str(model_path) if model_path is not None else None,
        "classes_path_provided": classes_path is not None,
        "classes_path_external": bool(classes_path and _path_is_external(classes_path)),
        "classes_path": str(classes_path) if classes_path is not None else None,
        "patch_path_provided": patch_path is not None,
        "patch_path_external": bool(patch_path and _path_is_external(patch_path)),
        "patch_path": str(patch_path) if patch_path is not None else None,
    }

    blockers: list[dict[str, str]] = []
    warnings: list[str] = []

    def add_blocker(code: str, message: str) -> None:
        blockers.append({"code": code, "message": message})

    if model_path is None or classes_path is None:
        add_blocker(
            "EXPLICIT_ARTIFACT_PATHS_NOT_AVAILABLE",
            "explicit ONNX model path and/or classes path are not available.",
        )

    classes: list[str] = []
    classes_schema = {
        "output_names": [],
        "activations_shape": [],
        "embeddings_shape": [],
    }
    output_schema = {
        "output_names": [],
        "output_shapes": [],
        "activations_shape": [],
        "embeddings_shape": [],
        "input_names": [],
        "input_shapes": [],
    }

    if model_path is not None and model_path.is_file():
        try:
            output_schema = _inspect_model_session(
                model_path,
                onnxruntime_info["available_providers"]
                if onnxruntime_info["cpu_execution_provider_available"]
                else [],
            )
        except ProbeError as exc:
            add_blocker("ONNX_MODEL_INSPECTION_FAILED", str(exc))
    elif model_path is not None:
        add_blocker(
            "EXPLICIT_ARTIFACT_PATHS_NOT_AVAILABLE",
            "explicit ONNX model path was provided but the file is missing.",
        )

    if classes_path is not None and classes_path.is_file():
        try:
            classes, classes_schema = _load_classes_metadata(classes_path)
        except ProbeError as exc:
            add_blocker("CLASSES_METADATA_READ_FAILED", str(exc))
    elif classes_path is not None:
        add_blocker(
            "EXPLICIT_ARTIFACT_PATHS_NOT_AVAILABLE",
            "explicit classes path was provided but the file is missing.",
        )

    if patch_path is None:
        add_blocker(
            "EXPLICIT_PATCH_INPUT_NOT_AVAILABLE",
            "explicit patch input artifact is not available.",
        )
    elif not patch_path.is_file():
        add_blocker(
            "EXPLICIT_PATCH_INPUT_NOT_AVAILABLE",
            "explicit patch path was provided but the file is missing.",
        )

    if onnxruntime_info["import_ok"] and not onnxruntime_info["cpu_execution_provider_available"]:
        warnings.append(
            "CPUExecutionProvider is unavailable; isolated probe will not attempt inference."
        )

    if classes and model_path is not None and patch_path is None:
        warnings.append(
            "ONNX output names and shapes were sourced from explicit model/classes metadata only because patch input is unavailable."
        )

    if not output_schema["output_names"] and classes_schema["output_names"]:
        output_schema["output_names"] = classes_schema["output_names"]
    if not output_schema["activations_shape"] and classes_schema["activations_shape"]:
        output_schema["activations_shape"] = classes_schema["activations_shape"]
    if not output_schema["embeddings_shape"] and classes_schema["embeddings_shape"]:
        output_schema["embeddings_shape"] = classes_schema["embeddings_shape"]

    patch_input = {
        "available": False,
        "shape": [],
        "expected_shape": EXPECTED_PATCH_SHAPE,
        "shape_match": False,
    }
    onnx_outputs = {
        "inference_run": False,
        "output_names": output_schema["output_names"],
        "activations_shape": output_schema["activations_shape"],
        "embeddings_shape": output_schema["embeddings_shape"],
    }
    mapping = {
        "classes_count": len(classes) if classes else None,
        "activations_count": None,
        "classes_activations_count_match": None,
        "candidate_genres": [],
        "candidate_genres_pretty": [],
    }

    if patch_path is not None and patch_path.is_file() and not blockers:
        try:
            np = _load_numpy_module()
            patch_array = _load_patch_array(patch_path)
            patch_shape, patch_tensor = _coerce_patch_array(patch_array)
            patch_input.update(
                {
                    "available": True,
                    "shape": patch_shape,
                    "shape_match": patch_shape == EXPECTED_PATCH_SHAPE,
                }
            )
            import onnxruntime as ort  # type: ignore[import-not-found]
        except Exception as exc:
            add_blocker(
                "ONNXRUNTIME_UNAVAILABLE",
                f"onnxruntime import failed in isolated probe environment: {exc}",
            )
        else:
            providers = onnxruntime_info["available_providers"]
            selected_provider = "CPUExecutionProvider" if "CPUExecutionProvider" in providers else None
            if selected_provider is None:
                add_blocker(
                    "CPU_EXECUTION_PROVIDER_UNAVAILABLE",
                    "CPUExecutionProvider is not available for isolated inference.",
                )
            else:
                if model_path is None or classes_path is None:
                    add_blocker(
                        "EXPLICIT_ARTIFACT_PATHS_NOT_AVAILABLE",
                        "inference requires explicit model and classes paths.",
                    )
                else:
                    try:
                        session_options = ort.SessionOptions()
                        session_options.intra_op_num_threads = 1
                        session_options.inter_op_num_threads = 1
                        session = ort.InferenceSession(
                            str(model_path),
                            sess_options=session_options,
                            providers=[selected_provider],
                        )
                        input_name = session.get_inputs()[0].name
                        feed_array = np.asarray(patch_tensor, dtype=np.float32)
                        if feed_array.ndim == 2:
                            feed_array = np.expand_dims(feed_array, axis=0)
                        runtime_outputs = session.run(None, {input_name: feed_array})
                        onnx_outputs["inference_run"] = True
                        output_metadata = session.get_outputs()
                        onnx_outputs["output_names"] = [output.name for output in output_metadata]

                        activations_values: list[float] | None = None
                        for output in runtime_outputs:
                            array = np.asarray(output)
                            if list(array.shape) == [1, EXPECTED_ACTIVATIONS_COUNT]:
                                activations_values = [float(value) for value in array.reshape(-1)]
                                onnx_outputs["activations_shape"] = [EXPECTED_ACTIVATIONS_COUNT]
                            elif list(array.shape) == [1, EXPECTED_EMBEDDINGS_COUNT]:
                                onnx_outputs["embeddings_shape"] = [EXPECTED_EMBEDDINGS_COUNT]

                        if activations_values is None:
                            for output in runtime_outputs:
                                array = np.asarray(output)
                                if array.ndim == 2 and array.shape[-1] == EXPECTED_ACTIVATIONS_COUNT:
                                    activations_values = [float(value) for value in array.reshape(-1)]
                                    onnx_outputs["activations_shape"] = [EXPECTED_ACTIVATIONS_COUNT]
                                    break

                        if activations_values is None:
                            add_blocker(
                                "ACTIVATIONS_OUTPUT_NOT_FOUND",
                                "runtime outputs did not contain a 50-wide activations tensor.",
                            )
                        else:
                            mapping["activations_count"] = len(activations_values)
                            mapping["classes_activations_count_match"] = (
                                len(activations_values) == len(classes) if classes else None
                            )
                            if classes and len(activations_values) == len(classes):
                                candidate_genres = _build_candidate_genres(
                                    activations_values,
                                    classes,
                                    args.top_n,
                                )
                                mapping["candidate_genres"] = candidate_genres
                                mapping["candidate_genres_pretty"] = _build_candidate_genres_pretty(
                                    candidate_genres,
                                    args.top_n,
                                )
                            elif classes:
                                add_blocker(
                                    "ACTIVATIONS_CLASSES_COUNT_MISMATCH",
                                    "activations count does not match classes count.",
                                )

                        if not onnx_outputs["embeddings_shape"]:
                            for output in runtime_outputs:
                                array = np.asarray(output)
                                if array.ndim == 2 and array.shape[-1] == EXPECTED_EMBEDDINGS_COUNT:
                                    onnx_outputs["embeddings_shape"] = [EXPECTED_EMBEDDINGS_COUNT]
                                    break

                        if not onnx_outputs["embeddings_shape"]:
                            warnings.append("Runtime outputs did not expose a 200-wide embeddings tensor.")
                    except Exception as exc:
                        add_blocker(
                            "ONNX_RUNTIME_INFERENCE_FAILED",
                            f"isolated ONNX Runtime inference failed: {exc}",
                        )

    if not onnx_outputs["inference_run"]:
        warnings.append(
            "ONNX inference was not executed because the explicit patch artifact was unavailable."
        )

    return {
        "schema_version": "0.1",
        "report_type": "onnx_musicnn_patch_to_mapping_probe_report",
        "roadmap": "4.77",
        "not_production_decision": True,
        "isolated_vertical_probe_only": True,
        "classify_called": False,
        "runtime_smoke_run": False,
        "production_approval": False,
        "python": python_info,
        "onnxruntime": onnxruntime_info,
        "artifacts": artifacts,
        "patch_input": patch_input,
        "onnx_outputs": onnx_outputs,
        "mapping": mapping,
        "production_boundaries": {
            "production_requirements_changed": False,
            "docker_changed": False,
            "provider_default_unchanged": True,
            "onnx_musicnn_disabled_by_default": True,
            "tidal_parser_touched": False,
            "response_shape_changed": False,
        },
        "blockers": blockers,
        "warnings": warnings,
        "next_step_recommendation": (
            "Proceed to Roadmap 4.78 explicit provider direct smoke only after an explicit patch artifact is available."
        ),
    }


def _write_report(report_path: Path, report: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Изолированный probe ONNX/MusiCNN patch-to-mapping chain."
    )
    parser.add_argument(
        "--onnx-model-path",
        required=True,
        help="Явный путь к external ONNX model metadata / artifact.",
    )
    parser.add_argument(
        "--classes-path",
        required=True,
        help="Явный путь к external classes metadata artifact.",
    )
    parser.add_argument(
        "--patch-path",
        required=False,
        help="Явный путь к external patch artifact (опционально).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Путь для JSON report.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help="Количество верхних кандидатов для mapping-вывода.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report_path = Path(args.output)
    report = _build_report(args)
    _write_report(report_path, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
