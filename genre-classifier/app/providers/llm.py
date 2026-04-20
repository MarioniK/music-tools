import logging

from app.clients.llm import LlmInferenceClient, get_default_llm_inference_client
from app.core import settings
from app.providers.base import GenreProvider, ProviderGenreScore, ProviderResult


logger = logging.getLogger("genre_classifier")


class LlmGenreProvider(GenreProvider):
    def __init__(self, client: LlmInferenceClient = None, settings_module=settings):
        self._client = client or get_default_llm_inference_client(settings_module=settings_module)

    def classify(self, audio_path: str) -> ProviderResult:
        client_name = self._client.__class__.__name__
        logger.info(
            "event=llm_inference_started provider_name=llm client_name=%s",
            client_name,
        )

        try:
            inference_result = self._client.infer_genres(audio_path)
        except Exception as exc:
            logger.error(
                "event=llm_inference_failed provider_name=llm client_name=%s error=%s",
                client_name,
                str(exc),
            )
            raise

        logger.info(
            "event=llm_inference_succeeded provider_name=llm client_name=%s model_name=%s genres_count=%d",
            client_name,
            inference_result.model_name,
            len(inference_result.genres),
        )

        return ProviderResult(
            genres=[
                ProviderGenreScore(tag=item.tag, score=item.score)
                for item in inference_result.genres
            ],
            provider_name="llm",
            model_name=inference_result.model_name,
        )
