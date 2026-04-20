from dataclasses import dataclass
import json
from typing import List
from urllib import error, request

from app.core import settings


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
        payload = json.dumps({"audio_path": audio_path}).encode("utf-8")
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
            model_name = str(parsed["model_name"])
            genres_payload = parsed["genres"]
            genres = [
                LlmClientGenreScore(
                    tag=str(item["tag"]),
                    score=float(item["score"]),
                )
                for item in genres_payload
            ]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("invalid local llm runtime response") from exc

        return LlmInferenceResult(genres=genres, model_name=model_name)


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
