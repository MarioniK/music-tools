from dataclasses import dataclass
import json
from typing import List
from urllib import error, request

from app.core import settings
from app.clients.llm_runtime_contract import (
    LocalLlmRuntimeRequest,
    LocalLlmRuntimeRequestInput,
    LocalLlmRuntimeRequestOptions,
    LocalLlmRuntimeValidationError,
    parse_local_llm_runtime_response,
)

LOCAL_HTTP_UNKNOWN_MODEL_NAME = "local-http-unknown-model"


@dataclass(frozen=True)
class LlmClientGenreScore:
    tag: str
    score: float


@dataclass(frozen=True)
class LlmInferenceResult:
    genres: List[LlmClientGenreScore]
    model_name: str


class LlmInferenceClient(object):
    def infer_genres(self, audio_path: str) -> LlmInferenceResult:
        raise NotImplementedError


class StubLlmInferenceClient(LlmInferenceClient):
    def infer_genres(self, audio_path: str) -> LlmInferenceResult:
        _ = audio_path

        return LlmInferenceResult(
            genres=[
                LlmClientGenreScore(tag="indie rock", score=0.91),
                LlmClientGenreScore(tag="dream pop", score=0.73),
                LlmClientGenreScore(tag="ambient", score=0.41),
            ],
            model_name="llm-scaffold-v1",
        )


class LocalHttpLlmInferenceClient(LlmInferenceClient):
    def __init__(self, endpoint: str, timeout_seconds: float):
        if not endpoint:
            raise ValueError("LLM_LOCAL_HTTP_ENDPOINT is required for local_http client")

        self._endpoint = endpoint
        self._timeout_seconds = float(timeout_seconds)

    def infer_genres(self, audio_path: str) -> LlmInferenceResult:
        runtime_request = LocalLlmRuntimeRequest(
            request_id=None,
            input=LocalLlmRuntimeRequestInput(text=audio_path),
            options=LocalLlmRuntimeRequestOptions(),
        )
        payload = json.dumps(runtime_request.to_payload()).encode("utf-8")
        http_request = request.Request(
            self._endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except (error.URLError, TimeoutError) as exc:
            raise RuntimeError("local llm runtime request failed") from exc

        try:
            parsed = json.loads(response_body)
            runtime_response = parse_local_llm_runtime_response(parsed)
            genres = [
                LlmClientGenreScore(
                    tag=item.name,
                    score=item.score,
                )
                for item in runtime_response.labels
            ]
        except (LocalLlmRuntimeValidationError, json.JSONDecodeError) as exc:
            raise LocalLlmRuntimeValidationError("invalid local llm runtime response") from exc

        model_name = _resolve_runtime_model_name(runtime_response.model)

        return LlmInferenceResult(genres=genres, model_name=model_name)


def _resolve_runtime_model_name(model) -> str:
    if isinstance(model, str):
        normalized_model = model.strip()
        if normalized_model:
            return normalized_model

    return LOCAL_HTTP_UNKNOWN_MODEL_NAME


def get_default_llm_inference_client(settings_module=settings) -> LlmInferenceClient:
    client_name = settings_module.get_configured_llm_client_name()

    if client_name == settings_module.LLM_CLIENT_STUB:
        return StubLlmInferenceClient()

    if client_name == settings_module.LLM_CLIENT_LOCAL_HTTP:
        return LocalHttpLlmInferenceClient(
            endpoint=settings_module.get_configured_llm_local_http_endpoint(),
            timeout_seconds=settings_module.get_configured_llm_local_http_timeout_seconds(),
        )

    raise ValueError("Unknown LLM_CLIENT: {}".format(client_name))
