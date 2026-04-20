from app.clients.llm import LlmInferenceClient, get_default_llm_inference_client
from app.providers.base import GenreProvider, ProviderGenreScore, ProviderResult


class LlmGenreProvider(GenreProvider):
    def __init__(self, client: LlmInferenceClient = None):
        self._client = client or get_default_llm_inference_client()

    def classify(self, audio_path: str) -> ProviderResult:
        inference_result = self._client.infer_genres(audio_path)

        return ProviderResult(
            genres=[
                ProviderGenreScore(tag=item.tag, score=item.score)
                for item in inference_result.genres
            ],
            provider_name="llm",
            model_name=inference_result.model_name,
        )
