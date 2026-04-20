from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


class LocalLlmRuntimeValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class LocalLlmRuntimeRequestInput:
    text: str


@dataclass(frozen=True)
class LocalLlmRuntimeRequestOptions:
    max_labels: Optional[int] = None
    temperature: Optional[float] = None


@dataclass(frozen=True)
class LocalLlmRuntimeRequest:
    input: LocalLlmRuntimeRequestInput
    options: LocalLlmRuntimeRequestOptions
    request_id: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)

        if self.request_id is None:
            payload.pop("request_id")

        if self.options.max_labels is None:
            payload["options"].pop("max_labels")

        if self.options.temperature is None:
            payload["options"].pop("temperature")

        return payload


@dataclass(frozen=True)
class LocalLlmRuntimeLabel:
    name: str
    score: Optional[float] = None


@dataclass(frozen=True)
class LocalLlmRuntimeResponse:
    ok: bool
    labels: List[LocalLlmRuntimeLabel]
    model: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def parse_local_llm_runtime_response(payload) -> LocalLlmRuntimeResponse:
    if not isinstance(payload, dict):
        raise LocalLlmRuntimeValidationError("runtime response must be an object")

    if "ok" not in payload or not isinstance(payload["ok"], bool):
        raise LocalLlmRuntimeValidationError("runtime response ok must be a bool")

    if "labels" not in payload:
        raise LocalLlmRuntimeValidationError("runtime response labels are required")

    labels_payload = payload["labels"]
    if not isinstance(labels_payload, list):
        raise LocalLlmRuntimeValidationError("runtime response labels must be a list")

    labels = [_parse_local_llm_runtime_label(item) for item in labels_payload]

    model = payload.get("model")
    if model is not None and not isinstance(model, str):
        raise LocalLlmRuntimeValidationError("runtime response model must be a string or null")

    meta = payload.get("meta")
    if meta is not None and not isinstance(meta, dict):
        raise LocalLlmRuntimeValidationError("runtime response meta must be an object or null")

    return LocalLlmRuntimeResponse(
        ok=payload["ok"],
        labels=labels,
        model=model,
        meta=meta,
    )


def _parse_local_llm_runtime_label(payload) -> LocalLlmRuntimeLabel:
    if not isinstance(payload, dict):
        raise LocalLlmRuntimeValidationError("runtime label must be an object")

    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        raise LocalLlmRuntimeValidationError("runtime label name must be a non-empty string")

    score = payload.get("score")
    if score is not None and not isinstance(score, (int, float)):
        raise LocalLlmRuntimeValidationError("runtime label score must be numeric or null")

    return LocalLlmRuntimeLabel(name=name, score=None if score is None else float(score))
