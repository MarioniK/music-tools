import json
import math
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from app.core import settings
from app.genre_normalization import normalize_genre_value
from app.genres.normalization import normalize_genre_label
from app.providers.base import GenreProvider, ProviderGenreScore, ProviderResult

ONNX_MUSICNN_PROVIDER_NAME = "onnx_musicnn"
ONNX_MUSICNN_RUNTIME_MODEL_NAME = "onnx-musicnn-scaffold"
ONNX_MUSICNN_DEFAULT_TOP_N = 8
ONNX_MUSICNN_MODEL_FILENAME = "msd-musicnn-1.onnx"
ONNX_MUSICNN_METADATA_FILENAME = "msd-musicnn-1.json"


class OnnxMusiCNNProvider(GenreProvider):
    """Scaffold provider для будущего ONNX/MusiCNN пути.

    Provider остаётся disabled-by-default и пока не выполняет production
    inference. Реализация лишь открывает безопасные runtime- и mapping-boundary
    для последующих этапов.
    """

    def __init__(self, settings_module=settings, top_n: int = ONNX_MUSICNN_DEFAULT_TOP_N):
        self._settings = settings_module
        self._top_n = top_n

    def classify(self, audio_path: str) -> ProviderResult:
        runtime_status = self.describe_runtime_status()
        if not runtime_status["available"]:
            raise RuntimeError(self._format_unsupported_message(runtime_status))

        raise RuntimeError(
            "onnx_musicnn provider scaffold is disabled-by-default and inference is not implemented"
        )

    def describe_runtime_status(self):
        model_path = self._get_model_path()
        metadata_path = self._get_metadata_path()
        reasons = []

        if not model_path.exists():
            reasons.append(f"model artifact missing: {model_path.name}")

        metadata = None
        if not metadata_path.exists():
            reasons.append(f"metadata artifact missing: {metadata_path.name}")
        else:
            try:
                metadata = self._load_metadata(metadata_path)
            except RuntimeError as exc:
                reasons.append(str(exc))

        if metadata is not None:
            try:
                self._extract_classes_from_metadata(metadata)
            except RuntimeError as exc:
                reasons.append(str(exc))

        try:
            self._load_onnxruntime()
        except RuntimeError as exc:
            reasons.append(str(exc))

        try:
            self._load_essentia_standard()
        except RuntimeError as exc:
            reasons.append(str(exc))

        return {
            "provider_name": ONNX_MUSICNN_PROVIDER_NAME,
            "available": not reasons,
            "model_path": str(model_path),
            "metadata_path": str(metadata_path),
            "reasons": reasons,
        }

    def build_provider_result_from_outputs(
        self,
        activations: Iterable,
        classes: Sequence,
        *,
        model_name: Optional[str] = ONNX_MUSICNN_RUNTIME_MODEL_NAME,
        top_n: Optional[int] = None,
    ) -> ProviderResult:
        candidate_scores = build_candidate_scores(
            activations,
            classes,
            top_n=self._top_n if top_n is None else top_n,
        )
        return ProviderResult(
            genres=candidate_scores,
            provider_name=ONNX_MUSICNN_PROVIDER_NAME,
            model_name=model_name,
        )

    def _get_model_path(self) -> Path:
        return self._settings.MODELS_DIR / ONNX_MUSICNN_MODEL_FILENAME

    def _get_metadata_path(self) -> Path:
        return self._settings.MODELS_DIR / ONNX_MUSICNN_METADATA_FILENAME

    def _load_metadata(self, metadata_path: Path):
        try:
            with metadata_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError as exc:
            raise RuntimeError(f"metadata artifact missing: {metadata_path.name}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"metadata artifact is invalid JSON: {metadata_path.name}") from exc

    def _extract_classes_from_metadata(self, metadata) -> List[str]:
        classes = metadata.get("classes")
        if not isinstance(classes, list) or not classes:
            raise RuntimeError("metadata classes unavailable")

        normalized_classes = []
        for label in classes:
            normalized_label = _normalize_candidate_label(label)
            if normalized_label is None:
                raise RuntimeError("metadata classes contain invalid labels")
            normalized_classes.append(normalized_label)

        return normalized_classes

    def _load_onnxruntime(self):
        try:
            import onnxruntime  # noqa: F401
        except ModuleNotFoundError as exc:
            raise RuntimeError("onnxruntime unavailable") from exc

        return onnxruntime

    def _load_essentia_standard(self):
        try:
            from essentia import standard as essentia_standard  # noqa: F401
        except ModuleNotFoundError as exc:
            raise RuntimeError("essentia.standard unavailable") from exc

        if not hasattr(essentia_standard, "TensorflowInputMusiCNN"):
            raise RuntimeError("TensorflowInputMusiCNN unavailable")

        return essentia_standard

    def _format_unsupported_message(self, runtime_status) -> str:
        reasons = runtime_status.get("reasons") or []
        if reasons:
            return "onnx_musicnn provider scaffold unsupported: {}".format("; ".join(reasons))

        return "onnx_musicnn provider scaffold unsupported"


def build_candidate_scores(
    activations: Iterable,
    classes: Sequence,
    *,
    top_n: int = ONNX_MUSICNN_DEFAULT_TOP_N,
) -> List[ProviderGenreScore]:
    """Преобразует activations/classes в ранжированные кандидаты жанров."""
    if not isinstance(top_n, int) or top_n <= 0:
        raise RuntimeError("invalid top_n")

    activation_values = _coerce_activation_values(activations)
    class_labels = _coerce_class_labels(classes)

    if len(activation_values) != len(class_labels):
        raise RuntimeError("activations/classes count mismatch")

    scored_items = []
    for index, (activation, label) in enumerate(zip(activation_values, class_labels)):
        normalized_label = _normalize_candidate_label(label)
        if normalized_label is None:
            raise RuntimeError("invalid class label")

        scored_items.append(
            (
                index,
                ProviderGenreScore(
                    tag=normalized_label,
                    score=activation,
                ),
            )
        )

    scored_items.sort(key=lambda item: (-item[1].score, item[0]))
    return [item[1] for item in scored_items[:top_n]]


def _coerce_activation_values(activations: Iterable) -> List[float]:
    if isinstance(activations, (str, bytes)):
        raise RuntimeError("invalid activations")

    try:
        raw_values = list(activations)
    except TypeError as exc:
        raise RuntimeError("invalid activations") from exc

    if not raw_values:
        raise RuntimeError("invalid activations")

    normalized_values = []
    for value in raw_values:
        if isinstance(value, (list, tuple, dict, set)):
            raise RuntimeError("invalid activations shape")

        try:
            score = float(value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("invalid activations") from exc

        if not math.isfinite(score):
            raise RuntimeError("invalid activations")

        normalized_values.append(score)

    return normalized_values


def _coerce_class_labels(classes: Sequence) -> List[str]:
    if isinstance(classes, (str, bytes)):
        raise RuntimeError("invalid classes")

    try:
        raw_labels = list(classes)
    except TypeError as exc:
        raise RuntimeError("invalid classes") from exc

    if not raw_labels:
        raise RuntimeError("empty classes")

    normalized_labels = []
    for label in raw_labels:
        normalized_label = _normalize_candidate_label(label)
        if normalized_label is None:
            raise RuntimeError("invalid class label")
        normalized_labels.append(normalized_label)

    return normalized_labels


def _normalize_candidate_label(label):
    if isinstance(label, (list, tuple, dict, set)):
        return None

    normalized_label = normalize_genre_label(label)
    if normalized_label:
        return normalized_label

    fallback_label = normalize_genre_value(label)
    if fallback_label:
        return fallback_label

    return None
