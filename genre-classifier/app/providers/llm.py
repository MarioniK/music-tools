import logging

from app.clients.llm import (
    LlmInferenceClient,
    LlmInferenceResult,
    LocalLlmRuntimeHttpError,
    LocalLlmRuntimeTransportError,
    get_default_llm_inference_client,
)
from app.clients.llm_runtime_contract import LocalLlmRuntimeValidationError
from app.core import settings
from app.genres.postprocessing import postprocess_llm_genre_scores
from app.providers.base import GenreProvider, ProviderGenreScore, ProviderResult


logger = logging.getLogger("genre_classifier")


class LlmGenreProvider(GenreProvider):
    def __init__(self, client: LlmInferenceClient = None, settings_module=settings):
        self._client = client or get_default_llm_inference_client(settings_module=settings_module)

    def classify(self, audio_path: str) -> ProviderResult:
        client_name = self._client.__class__.__name__
        logger.info(
            "event=llm_provider_started provider_name=llm client_name=%s",
            client_name,
        )

        try:
            inference_result = self._client.infer_genres(audio_path)
        except Exception as exc:
            logger.error(
                "event=llm_provider_failed provider_name=llm client_name=%s failure_category=%s error=%s",
                client_name,
                _categorize_llm_provider_failure(exc),
                str(exc),
            )
            raise

        provider_result = _map_inference_result_to_provider_result(inference_result)

        logger.info(
            "event=llm_provider_succeeded provider_name=llm client_name=%s model_name=%s genres_count=%d",
            client_name,
            provider_result.model_name,
            len(provider_result.genres),
        )

        return provider_result


def _map_inference_result_to_provider_result(inference_result: LlmInferenceResult) -> ProviderResult:
    postprocessed_genres = postprocess_llm_genre_scores(inference_result.genres)

    return ProviderResult(
        genres=[
            ProviderGenreScore(tag=item.tag, score=item.score)
            for item in postprocessed_genres
        ],
        provider_name="llm",
        model_name=inference_result.model_name,
    )


def _categorize_llm_provider_failure(exc: Exception) -> str:
    if isinstance(exc, LocalLlmRuntimeHttpError):
        return "http_error"

    if isinstance(exc, LocalLlmRuntimeTransportError):
        return "transport_error"

    if isinstance(exc, LocalLlmRuntimeValidationError):
        return "validation_error"

    return "unexpected_error"
