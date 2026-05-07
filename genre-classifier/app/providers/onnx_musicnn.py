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
ONNX_MUSICNN_MODEL_PATH_SETTING = "get_configured_onnx_musicnn_model_path"
ONNX_MUSICNN_METADATA_PATH_SETTING = "get_configured_onnx_musicnn_metadata_path"


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
        """Выполняет explicit opt-in классификацию через локальные артефакты.

        Default provider не меняется: этот путь активируется только когда
        `GENRE_PROVIDER=onnx_musicnn` выбран явно.
        """

        return self.classify_with_explicit_artifacts(audio_path)

    def classify_with_explicit_artifacts(self, audio_path: str, top_n: Optional[int] = None) -> ProviderResult:
        """Выполняет explicit-only direct smoke через локальные артефакты.

        Метод предназначен для isolated evaluation/probe сценариев. Он не
        меняет default provider, не трогает `/classify` и не выполняется на
        module import path. Все optional runtime зависимости подгружаются
        лениво внутри этого boundary.
        """

        runtime_status = self.describe_runtime_status()
        if not runtime_status["available"]:
            raise RuntimeError(self._format_unsupported_message(runtime_status))

        activations, classes = self._run_explicit_inference(audio_path)
        return self.build_provider_result_from_outputs(
            activations,
            classes,
            model_name=ONNX_MUSICNN_RUNTIME_MODEL_NAME,
            top_n=self._top_n if top_n is None else top_n,
        )

    def describe_runtime_status(self):
        model_path = self._get_model_path()
        metadata_path = self._get_metadata_path()
        reasons = []

        if model_path is None:
            reasons.append("onnx model path not configured")
        elif not model_path.exists():
            reasons.append("onnx model artifact missing")

        metadata = None
        if metadata_path is None:
            reasons.append("onnx metadata path not configured")
        elif not metadata_path.exists():
            reasons.append("onnx metadata artifact missing")
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

        if not reasons:
            try:
                self._load_onnxruntime()
            except RuntimeError as exc:
                reasons.append(str(exc))

        if not reasons:
            try:
                self._load_essentia_standard()
            except RuntimeError as exc:
                reasons.append(str(exc))

        return {
            "provider_name": ONNX_MUSICNN_PROVIDER_NAME,
            "available": not reasons,
            "model_path": str(model_path) if model_path is not None else None,
            "metadata_path": str(metadata_path) if metadata_path is not None else None,
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
        return self._get_configured_path(ONNX_MUSICNN_MODEL_PATH_SETTING)

    def _get_metadata_path(self) -> Path:
        return self._get_configured_path(ONNX_MUSICNN_METADATA_PATH_SETTING)

    def _get_configured_path(self, getter_name: str):
        getter = getattr(self._settings, getter_name, None)
        if getter is None:
            return None

        configured_path = getter()
        if configured_path in (None, ""):
            return None

        if isinstance(configured_path, Path):
            return configured_path

        return Path(configured_path)

    def _load_metadata(self, metadata_path: Path):
        try:
            with metadata_path.open("r", encoding="utf-8") as handle:
                metadata = json.load(handle)
        except FileNotFoundError as exc:
            raise RuntimeError("onnx metadata artifact missing") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("onnx metadata artifact is invalid JSON") from exc

        if not isinstance(metadata, dict):
            raise RuntimeError("onnx metadata artifact has invalid format")

        return metadata

    def _extract_classes_from_metadata(self, metadata) -> List[str]:
        classes = metadata.get("classes")
        if not isinstance(classes, list) or not classes:
            raise RuntimeError("onnx metadata classes unavailable")

        normalized_classes = []
        for label in classes:
            normalized_label = _normalize_candidate_label(label)
            if normalized_label is None:
                raise RuntimeError("onnx metadata classes contain invalid labels")
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

    def _run_explicit_inference(self, audio_path: str):
        model_path = self._get_model_path()
        metadata_path = self._get_metadata_path()

        if model_path is None:
            raise RuntimeError("onnx model path not configured")
        if metadata_path is None:
            raise RuntimeError("onnx metadata path not configured")

        metadata = self._load_metadata(metadata_path)
        classes = self._extract_classes_from_metadata(metadata)
        onnxruntime = self._load_onnxruntime()
        essentia_standard = self._load_essentia_standard()
        patch = self._build_tensorflow_input_patch(essentia_standard, audio_path)
        activations = self._run_onnx_inference(onnxruntime, model_path, patch)

        return activations, classes

    def _build_tensorflow_input_patch(self, essentia_standard, audio_path: str):
        audio_file = Path(audio_path)
        if not audio_file.is_file():
            raise RuntimeError("audio artifact missing")

        import numpy as np

        audio = essentia_standard.MonoLoader(filename=str(audio_file), sampleRate=16000)()
        tensor = essentia_standard.TensorflowInputMusiCNN()

        rows = []
        for frame in essentia_standard.FrameGenerator(
            audio,
            frameSize=512,
            hopSize=256,
            startFromZero=True,
            lastFrameToEndOfFile=True,
        ):
            bands = tensor(frame)
            rows.append([float(value) for value in bands])

        if not rows:
            raise RuntimeError("TensorflowInputMusiCNN produced no rows")

        normalized_rows = rows
        if len(normalized_rows) < 187:
            last_row = list(normalized_rows[-1])
            while len(normalized_rows) < 187:
                normalized_rows.append(list(last_row))
        else:
            normalized_rows = normalized_rows[:187]

        if any(len(row) != 96 for row in normalized_rows):
            raise RuntimeError("TensorflowInputMusiCNN patch width normalization failed")

        patch = np.asarray(normalized_rows, dtype=np.float32)
        if patch.shape != (187, 96):
            raise RuntimeError("TensorflowInputMusiCNN patch shape normalization failed")

        if not np.isfinite(patch).all():
            raise RuntimeError("TensorflowInputMusiCNN patch contains non-finite values")

        return patch

    def _run_onnx_inference(self, onnxruntime, model_path: Path, patch):
        import numpy as np

        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1

        session = onnxruntime.InferenceSession(
            str(model_path),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )

        inputs = session.get_inputs()
        outputs = session.get_outputs()
        if not inputs:
            raise RuntimeError("onnxruntime session has no inputs")
        if not outputs:
            raise RuntimeError("onnxruntime session has no outputs")

        input_meta = inputs[0]
        input_shape = list(input_meta.shape)
        feed_array = patch
        if len(input_shape) == 3 and input_shape[-2:] == [187, 96]:
            feed_array = np.expand_dims(patch, axis=0)
        elif len(input_shape) != 2 or input_shape != [187, 96]:
            raise RuntimeError(f"unexpected ONNX input shape: {input_shape}")

        run_outputs = session.run(None, {input_meta.name: feed_array})
        output_names = [item.name for item in outputs]
        output_map = {name: value for name, value in zip(output_names, run_outputs)}

        if "activations" not in output_map:
            raise RuntimeError("onnx outputs did not include an 'activations' tensor")
        if "embeddings" not in output_map:
            raise RuntimeError("onnx outputs did not include an 'embeddings' tensor")

        return self._normalize_output_values(output_map["activations"])

    def _normalize_output_values(self, tensor):
        import numpy as np

        array = np.asarray(tensor, dtype=float)
        if array.size == 0:
            raise RuntimeError("invalid onnx output")

        if array.ndim == 1:
            values = array
        elif array.ndim == 2 and array.shape[0] == 1:
            values = array[0]
        else:
            values = np.mean(array, axis=0)

        normalized_values = [float(value) for value in np.asarray(values).reshape(-1).tolist()]
        if not normalized_values:
            raise RuntimeError("invalid onnx output")

        return normalized_values

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
